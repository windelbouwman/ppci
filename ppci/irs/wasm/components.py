"""
The field classes to represent a WASM program.
"""

from io import BytesIO
import logging
from struct import pack as spack, unpack as sunpack

from . import OPCODES
from ._opcodes import OPERANDS, REVERZ, EVAL
from ...utils.leb128 import signed_leb128_encode, unsigned_leb128_encode
from ...utils.leb128 import unsigned_leb128_decode


logger = logging.getLogger('wasm')
LANG_TYPES = {
    'i32': b'\x7f',
    'i64': b'\x7e',
    'f32': b'\x7d',
    'f64': b'\x7c',
    'anyfunc': b'\x70',
    'func': b'\x60',
    'emptyblock': b'\x40',  # pseudo type for representing an empty block_type
    }
LANG_TYPES_REVERSE = {v[0]: k for k, v in LANG_TYPES.items()}


def packf64(x):
    return spack('<d', x)


def packu32(x):
    return spack('<I', x)


def packstr(x):
    bb = x.encode('utf-8')
    return packvu32(len(bb)) + bb


def packvs64(x):
    bb = signed_leb128_encode(x)
    assert len(bb) <= 8
    return bb


def packvs32(x):
    bb = signed_leb128_encode(x)
    assert len(bb) <= 4
    return bb


def packvu32(x):
    bb = unsigned_leb128_encode(x)
    assert len(bb) <= 4
    return bb


def packvu7(x):
    bb = unsigned_leb128_encode(x)
    assert len(bb) == 1
    return bb


def packvu1(x):
    bb = unsigned_leb128_encode(x)
    assert len(bb) == 1
    return bb


class FileReader:
    """ Helper class that can read bytes from a file """
    def __init__(self, f):
        self.f = f

    def read(self, amount):
        data = self.f.read(amount)
        if len(data) != amount:
            raise RuntimeError('Reading beyond end of file')
        return data

    def bytefile(self, f):
        b = f.read(1)
        while b:
            yield b[0]
            b = f.read(1)

    def __next__(self):
        b = self.read(1)
        return b[0]

    def read_int(self):
        # TODO: use signed leb128?
        return unsigned_leb128_decode(self)

    def read_uint(self):
        return unsigned_leb128_decode(self)

    def read_bytes(self):
        """ Read raw bytes data """
        l = self.read_int()
        return self.read(l)

    def read_str(self):
        """ Read a string """
        data = self.read_bytes()
        return data.decode('utf-8')

    def read_type(self):
        tp = next(self)
        return LANG_TYPES_REVERSE[tp]

    def read_limits(self):
        """ Read min and max limits """
        mx_present = self.read(1)[0]
        assert mx_present in [0, 1]
        minimum = self.read_int()
        if mx_present:
            maximum = self.read_int()
        else:
            maximum = None
        return minimum, maximum

    def read_expression(self):
        """ Read instructions until an end marker is found """
        expr = []
        blocks = 1
        i = self.read_instruction()
        # keep track of if/block/loop etc:
        if i.type == 'end':
            blocks -= 1
        elif i.type in ('if', 'block', 'loop'):
            blocks += 1
        expr.append(i)
        while blocks:
            i = self.read_instruction()
            if i.type == 'end':
                blocks -= 1
            elif i.type in ('if', 'block', 'loop'):
                blocks += 1
            expr.append(i)
        return expr

    def read_instruction(self):
        """ Read a single instruction """
        return Instruction.from_reader(self)


def read_wasm(f):
    """ Read a wasm file """
    logger.info('Loading wasm module')
    return Module.from_file(f)


def eval_expr(expr):
    """ Evaluate a sequence of instructions """
    stack = []
    for i in expr:
        consumed_types, produced_types, action = EVAL[i.type]
        if action is None:
            raise RuntimeError('Cannot evaluate {}'.format(i.type))
        # Gather stack values:
        values = []
        for t in consumed_types:
            vt, v = stack.pop(-1)
            assert vt == t
            values.append(v)

        # Perform magic action of instruction:
        values = action(i, values)

        # Push results on tha stack:
        assert len(values) == len(produced_types)
        for vt, v in zip(produced_types, values):
            stack.append((vt, v))

    if len(stack) == 1:
        return stack[0]
    else:
        raise ValueError('Expression does not leave value on stack!')


class WASMComponent:
    """ Base class for representing components of a WASM module, from the module
    to sections and instructions. These components can be shown as text or
    written as bytes.

    Methods:
    * `to_bytes()` - Get the bytes that represent the binary WASM for this
      component.
    * `show()` - Print a textual representation of the component.
    * `to_file(f)` - Write the binary representation of this component to a
      file.
    * `to_text()` - Return a textual representation of this component.

    """

    __slots__ = []

    def __init__(self):
        pass

    def __repr__(self):
        return '<WASM-%s>' % self.__class__.__name__

    def _get_sub_text(self, subs, multiline=False):
        # Collect sub texts
        texts = []
        charcount = 0
        haslf = False
        for sub in subs:
            if isinstance(sub, WASMComponent):
                text = sub.to_text()
            else:
                text = repr(sub)
            charcount += len(text)
            texts.append(text)
            haslf = haslf or '\n' in text
        # Put on one line or multiple lines
        if multiline or haslf or charcount > 70:
            lines = []
            for text in texts:
                for line in text.splitlines():
                    lines.append(line)
            lines = ['    ' + line for line in lines]
            return '\n'.join(lines)
        else:
            return ', '.join(texts)

    def to_bytes(self):
        """ Get the bytes that represent the binary WASM for this component.
        """
        f = BytesIO()
        self.to_file(f)
        return f.getvalue()

    def show(self):
        """ Print a textual representation of the component.
        """
        print(self.to_text())

    def to_file(self, f):
        """ Write the binary representation of this component to a file.
        Implemented in the subclasses.
        """
        raise NotImplementedError()

    def to_text(self):
        """ Return a textual representation of this component.
        Implemented in the subclasses.
        """
        raise NotImplementedError()


class Module(WASMComponent):
    """ Class to represent a WASM module; the toplevel unit of code.
    The subcomponents of a module are objects that derive from `Section`.
    It is recommended to provide `Function` and `ImportedFunction` objects,
    from which the module will polulate the function-related sections, and
    handle the binding of the function index space.
    """

    __slots__ = ['sections', 'func_id_to_index']

    def __init__(self, sections):
        # Process sections, filter out high-level functions
        self.sections = []
        has_lowlevel_funcs = False
        functions = []
        start_section = None
        import_section = None
        export_section = None
        for section in sections:
            if isinstance(section, (Function, ImportedFuncion)):
                functions.append(section)
            elif isinstance(section, Section):
                self.sections.append(section)
                if isinstance(section, (TypeSection, CodeSection)):
                    has_lowlevel_funcs = True
                elif isinstance(section, StartSection):
                    start_section = section
                elif isinstance(section, ImportSection):
                    import_section = section
                elif isinstance(section, ExportSection):
                    if export_section:
                        raise ValueError('Export section given twice!')
                    export_section = section
            else:
                raise TypeError('Module expects a Function, ImportedFunction, or a Section.')

        # Process high level function desctiptions?
        if functions and has_lowlevel_funcs:
            raise TypeError('Module cannot have both Functions/ImportedFunctions and FunctionDefs/FunctionSigs.')
        elif functions:
            self._process_functions(
                functions, start_section, import_section, export_section)

        # Sort the sections
        self.sections.sort(key=lambda x: x.id)

        # Prepare functiondefs
        for section in reversed(self.sections):
            if isinstance(section, CodeSection):
                for funcdef in section.functiondefs:
                    funcdef.module = self
                break

    def __iter__(self):
        return iter(self.sections)

    def _process_functions(self, functions, start_section, import_section, export_section):

        # Prepare processing functions. In the order of imported and then defined,
        # because that's the order of the function index space. We use the function
        # index also for the signature index, though that's not strictly necessary
        # (e.g. functions can share a signature).
        # Function index space is used in, calls, exports, elementes, start function.
        auto_sigs = []
        auto_defs = []
        auto_imports = []
        auto_exports = []
        auto_start = None
        function_index = 0
        self.func_id_to_index = {}
        # Process imported functions
        for func in functions:
            if isinstance(func, ImportedFuncion):
                auto_sigs.append(FunctionSig(func.params, func.returns))
                auto_imports.append(Import(func.modname, func.fieldname, 'function', function_index))
                if func.export:
                    auto_exports.append((func.idname, 'function', function_index))
                self.func_id_to_index[func.idname] = function_index
                function_index += 1
        # Process defined functions
        for func in functions:
            if isinstance(func, Function):
                auto_sigs.append(FunctionSig(func.params, func.returns))
                auto_defs.append(FunctionDef(func.locals, func.instructions))
                if func.export:
                    auto_exports.append((func.idname, 'function', function_index))
                if func.idname == '$main' and start_section is None:
                    auto_start = StartSection(function_index)
                self.func_id_to_index[func.idname] = function_index
                function_index += 1

        # Insert auto-generated function sigs and defs
        self.sections.append(TypeSection(auto_sigs))
        self.sections.append(CodeSection(auto_defs))
        # Insert auto-generated imports
        if import_section is None:
            import_section = ImportSection([])
            self.sections.append(import_section)
        import_section.imports.extend(auto_imports)
        # Insert auto-generated exports
        if export_section is None:
            export_section = ExportSection([])
            self.sections.append(export_section)
        export_section.exports.extend(auto_exports)
        # Insert function section
        self.sections.append(
            FunctionSection(list(range(len(auto_imports), function_index))))

        # Insert start section
        if auto_start is not None:
            self.sections.append(auto_start)

    def to_text(self):
        return 'Module(\n' + self._get_sub_text(self.sections, True) + '\n)'

    def to_file(self, f):
        """ Write this wasm module to file """
        f.write(b'\x00asm')
        f.write(packu32(1))  # version, must be 1 for now
        for section in self.sections:
            section.to_file(f)

    @classmethod
    def from_file(cls, f):
        """ Read module from file """
        r = FileReader(f)
        module = cls.from_reader(r)
        return module

    @classmethod
    def from_reader(cls, r):
        data = r.read(4)
        assert data == b'\x00asm'
        version = sunpack('<I', r.read(4))[0]
        assert version == 1, version
        sections = []
        while True:
            section = section_from_reader(r)
            if not section:
                break
            sections.append(section)
        logger.info('Successfully loaded %s sections', len(sections))
        return cls(sections)


class Function:
    """ High-level description of a function. The linking is resolved
    by the module.
    """

    __slots__ = ['idname', 'params', 'returns', 'locals', 'instructions', 'export']

    def __init__(self, idname, params=None, returns=None, locals=None, instructions=None, export=False):
        assert isinstance(idname, str)
        assert isinstance(params, (tuple, list))
        assert isinstance(returns, (tuple, list))
        assert isinstance(locals, (tuple, list))
        assert isinstance(instructions, (tuple, list))
        self.idname = idname
        self.params = params
        self.returns = returns
        self.locals = locals
        self.instructions = instructions
        self.export = bool(export)


class ImportedFuncion:
    """ High-level description of an imported function. The linking is resolved
    by the module.
    """

    __slots__ = ['idname', 'params', 'returns', 'modname', 'fieldname', 'export']

    def __init__(self, idname, params, returns, modname, fieldname, export=False):
        assert isinstance(idname, str)
        assert isinstance(params, (tuple, list))
        assert isinstance(returns, (tuple, list))
        assert isinstance(modname, str)
        assert isinstance(fieldname, str)
        self.idname = idname
        self.params = params
        self.returns = returns
        self.modname = modname
        self.fieldname = fieldname
        self.export = bool(export)


## Sections


class Section(WASMComponent):
    """Base class for module sections.
    """

    __slots__ = []
    id = -1

    def to_text(self):
        return '%s()' % self.__class__.__name__

    def to_file(self, f):
        f2 = BytesIO()
        self.get_binary_section(f2)
        payload = f2.getvalue()
        id = self.id
        assert id >= 0
        # Write it all
        f.write(packvu7(id))
        f.write(packvu32(len(payload)))
        if id == 0:  # custom section for debugging, future, or extension
            type = self.__cass__.__name__.lower().split('section')[0]
            f.write(pack_str(type))
        f.write(payload)

    def get_binary_section(self, f):
        raise NotImplementedError()  # Sections need to implement this


def section_from_reader(r):
    # mp = {s.id: s for s in cls.__subclasses__() if hasattr(s, 'id') and s.id > 0}
    handled_sections = [
        TypeSection,
        ImportSection,
        FunctionSection,
        TableSection,
        MemorySection,
        GlobalSection,
        ExportSection,
        ElementSection,
        CodeSection,
        DataSection,
    ]
    mp = {s.id: s for s in handled_sections}
    try:
        section_id = r.read_int()
    except RuntimeError:
        return
    section_size = r.read_int()
    section_content = r.read(section_size)
    f2 = BytesIO(section_content)
    r2 = FileReader(f2)
    logger.debug(
        'Loading section type %s of %s bytes', section_id, section_size)
    if section_id in mp:
        shiny_section = mp[section_id].from_reader(r2)
        assert not f2.read()
        return shiny_section
    else:
        logger.warning('Unhandled section %s', section_id)
        r.read(section_size)


class TypeSection(Section):
    """ Defines signatures of functions that are either imported or defined in this module.
    """

    __slots__ = ['functionsigs']
    id = 1

    def __init__(self, functionsigs):
        for i, functionsig in enumerate(functionsigs):
            assert isinstance(functionsig, FunctionSig)
            # todo: remove this?
            functionsig.index = i  # so we can resolve the index in Import objects
        self.functionsigs = functionsigs

    def to_text(self):
        return 'TypeSection(\n' + self._get_sub_text(self.functionsigs, True) + '\n)'

    def get_binary_section(self, f):
        f.write(packvu32(len(self.functionsigs)))  # count
        for functionsig in self.functionsigs:
            functionsig.to_file(f)

    @classmethod
    def from_reader(cls, r):
        count = r.read_int()
        functionsigs = [FunctionSig.from_reader(r) for _ in range(count)]
        print(functionsigs)
        return cls(functionsigs)


class ImportSection(Section):
    """ Defines the things to be imported in a module.
    """
    __slots__ = ['imports']
    id = 2

    def __init__(self, imports):
        for imp in imports:
            assert isinstance(imp, Import)
        self.imports = list(imports)

    def to_text(self):
        return 'ImportSection(\n' + self._get_sub_text(self.imports, True) + '\n)'

    def get_binary_section(self, f):
        f.write(packvu32(len(self.imports)))  # count
        for imp in self.imports:
            imp.to_file(f)

    @classmethod
    def from_reader(cls, r):
        count = r.read_int()
        imports = [Import.from_reader(r) for _ in range(count)]
        return cls(imports)


class FunctionSection(Section):
    """ Declares for each function defined in this module which signature is
    associated with it. The items in this sections match 1-on-1 with the items
    in the code section.
    """

    __slots__ = ['indices']
    id = 3

    def __init__(self, indices):
        for i in indices:
            assert isinstance(i, int)
        self.indices = indices  # indices in the Type section

    def to_text(self):
        return 'FunctionSection(' + ', '.join([str(i) for i in self.indices]) + ')'

    def get_binary_section(self, f):
        f.write(packvu32(len(self.indices)))
        for i in self.indices:
            f.write(packvu32(i))

    @classmethod
    def from_reader(cls, reader):
        count = reader.read_int()
        indices = [reader.read_int() for _ in range(count)]
        return cls(indices)


class TableSection(Section):
    """ Define stuff provided by the host system that WASM can use/reference,
    but cannot be expressed in WASM itself.
    """
    __slots__ = ['tables']
    id = 4

    def __init__(self, tables):
        assert len(tables) <= 1   # in MVP
        self.tables = tables

    def get_binary_section(self, f):
        f.write(packvu32(len(self.tables)))
        for table in self.tables:
            table.to_file(f)

    @classmethod
    def from_reader(cls, reader):
        count = reader.read_int()
        tables = [Table.from_reader(reader) for _ in range(count)]
        return cls(tables)


class MemorySection(Section):
    """ Declares initial (and max) sizes of linear memory, expressed in
    WASM pages (64KiB). Only one default memory can exist in the MVP.
    """
    __slots__ = ['entries']
    id = 5

    def __init__(self, entries):
        assert len(entries) == 1   # in MVP
        self.entries = entries

    def to_text(self):
        entries = ', '.join([str(i) for i in self.entries])
        return 'MemorySection({})'.format(entries)

    def get_binary_section(self, f):
        f.write(packvu32(len(self.entries)))
        for entrie in self.entries:
            # resizable_limits
            if isinstance(entrie, int):
                entrie = (entrie, )
            if len(entrie) == 1:
                f.write(packvu1(0))
                f.write(packvu32(entrie[0]))  # initial, no max
            else:
                f.write(packvu1(1))
                f.write(packvu32(entrie[0]))  # initial
                f.write(packvu32(entrie[1]))  # maximum

    @classmethod
    def from_reader(cls, reader):
        count = reader.read_int()
        entries = []
        for _ in range(count):
            minimum, maximum = reader.read_limits()
            if maximum is None:
                entries.append((minimum,))
            else:
                entries.append((minimum, maximum))
        return cls(entries)


MUTABILITY_TYPES = {'const': b'\x00', 'mut': b'\x01'}


class GlobalSection(Section):
    """ Defines the globals in a module. """
    __slots__ = ['globalz']
    id = 6

    def __init__(self, globalz):
        assert all(isinstance(g, Global) for g in globalz)
        self.globalz = globalz

    def to_text(self):
        globalz = ', '.join([str(g) for g in self.globalz])
        return 'GlobalSection({})'.format(globalz)

    def get_binary_section(self, f):
        f.write(packvu32(len(self.globalz)))
        for g in self.globalz:
            f.write(LANG_TYPES[g.typ])
            f.write(MUTABILITY_TYPES[g.mutability])

            # Encode value as expression followed by end instruction
            Instruction('i32.const', (g.value,)).to_file(f)
            Instruction('end').to_file(f)

    @classmethod
    def from_reader(cls, reader):
        count = reader.read_int()
        globalz = []
        for _ in range(count):
            raise NotImplementedError()
            reader.read_expression()
        return cls(globalz)


class ExportSection(Section):
    """ Defines the names that this module exports.
    """
    __slots__ = ['exports']
    id = 7

    def __init__(self, exports):
        for export in exports:
            assert isinstance(export, Export)
        self.exports = list(exports)

    def to_text(self):
        return 'ExportSection(\n' + self._get_sub_text(self.exports, True) + '\n)'

    def get_binary_section(self, f):
        f.write(packvu32(len(self.exports)))
        for export in self.exports:
            export.to_file(f)

    @classmethod
    def from_reader(cls, reader):
        count = reader.read_int()
        exports = [Export.from_reader(reader) for _ in range(count)]
        return cls(exports)


class StartSection(Section):
    """ Provide the index of the function to call at init-time. The func must
    have zero params and return values.
    """

    __slots__ = ['index']
    id = 8

    def __init__(self, index):
        self.index = index

    def to_text(self):
        return 'StartSection(' + str(self.index) + ')'

    def get_binary_section(self, f):
        f.write(packvu32(self.index))


class ElementSection(Section):
    """ To initialize table elements. """
    __slots__ = ['elements']
    id = 9

    def __init__(self, elements):
        self.elements = elements

    def get_binary_section(self, f):
        f.write(packvu32(len(self.elements)))
        for element in self.elements:
            element.to_file(f)


class CodeSection(Section):
    """ The actual code for a module, one CodeSection per function.
    """
    __slots__ = ['functiondefs']
    id = 10

    def __init__(self, functiondefs):
        for functiondef in functiondefs:
            assert isinstance(functiondef, FunctionDef)
        self.functiondefs = functiondefs

    def to_text(self):
        return 'CodeSection(\n' + self._get_sub_text(self.functiondefs, True) + '\n)'

    def get_binary_section(self, f):
        f.write(packvu32(len(self.functiondefs)))
        for functiondef in self.functiondefs:
            functiondef.to_file(f)

    @classmethod
    def from_reader(cls, reader):
        count = reader.read_int()
        function_defs = [
            FunctionDef.from_reader(reader) for _ in range(count)]
        return cls(function_defs)


class DataSection(Section):
    """ Initialize the linear memory.
    Note that the initial contents of linear memory are zero.
    """

    __slots__ = ['chunks']
    id = 11

    def __init__(self, chunks):
        for chunk in chunks:
            assert len(chunk) == 3  # index, offset, bytes
            assert chunk[0] == 0  # always 0 in MVP
            assert isinstance(chunk[1], int)
            assert isinstance(chunk[2], bytes)
        self.chunks = chunks

    def to_text(self):
        chunkinfo = [(chunk[0], chunk[1], len(chunk[2])) for chunk in self.chunks]
        return 'DataSection(' + ', '.join([str(i) for i in chunkinfo]) + ')'

    def get_binary_section(self, f):
        f.write(packvu32(len(self.chunks)))
        for chunk in self.chunks:
            f.write(packvu32(chunk[0]))

            # Encode offset as expression followed by end instruction
            Instruction('i32.const', (chunk[1],)).to_file(f)
            Instruction('end').to_file(f)

            # Encode as u32 length followed by data:
            f.write(packvu32(len(chunk[2])))
            f.write(chunk[2])

    @classmethod
    def from_reader(cls, reader):
        count = reader.read_int()
        chunks = []
        for _ in range(count):
            index = reader.read_int()
            offset_expr = reader.read_expression()
            offset_type, offset = eval_expr(offset_expr)
            assert offset_type == 'i32'
            content = reader.read_bytes()
            chunks.append((index, offset, content))
        return cls(chunks)


# Non-section components


class Import(WASMComponent):
    """ Import objects (from other wasm modules or from the host environment).
    The type argument is an index in the type-section (signature) for funcs
    and a string type for table, memory and global.
    """

    __slots__ = ['modname', 'fieldname', 'kind', 'type']

    def __init__(self, modname, fieldname, kind, type):
        self.modname = modname
        self.fieldname = fieldname
        self.kind = kind  # function, table, mem or global
        self.type = type  # the signature-index for funcs, the type for table, memory or global

    def to_text(self):
        return 'Import(%r, %r, %r, %r)' % (self.modname, self.fieldname, self.kind, self.type)

    def to_file(self, f):
        f.write(packstr(self.modname))
        f.write(packstr(self.fieldname))
        if self.kind == 'function':
            f.write(b'\x00')
            f.write(packvu32(self.type))
        else:
            raise RuntimeError('Can only import functions for now')

    @classmethod
    def from_reader(cls, reader):
        modname = reader.read_str()
        fieldname = reader.read_str()
        kind_id = reader.read(1)[0]
        mp = {0: 'function'}
        kind = mp[kind_id]
        index = reader.read_int()
        return cls(modname, fieldname, kind, index)


class Export(WASMComponent):
    """ Export an object defined in this module. The index is the index
    in the corresponding index space (e.g. for functions this is the
    function index space which is basically the concatenation of
    functions in the import and code sections).
    """

    __slots__ = ['name', 'kind', 'index']

    def __init__(self, name, kind, index):
        self.name = name
        self.kind = kind
        self.index = index

    def to_text(self):
        return 'Export(%r, %r, %i)' % (self.name, self.kind, self.index)

    def to_file(self, f):
        f.write(packstr(self.name))
        if self.kind == 'function':
            f.write(b'\x00')
            f.write(packvu32(self.index))
        else:
            raise RuntimeError('Can only export functions for now')

    @classmethod
    def from_reader(cls, reader):
        name = reader.read_str()
        kind = reader.read(1)[0]
        mp = {0: 'function', 1: 'table', 2: 'mem'}
        kind = mp[kind]
        index = reader.read_int()
        return cls(name, kind, index)


class Global:
    """ Global variable """
    def __init__(self, typ, mutability, value):
        self.typ = typ
        self.mutability = mutability
        self.value = value


class Table:
    """ A table with for example function points """
    def __init__(self, minimum, maximum=None):
        self.typ = 'anyfunc'
        self.minimum = minimum
        self.maximum = maximum

    def to_file(self, f):
        f.write(LANG_TYPES[self.typ])
        # indicate if max is present:
        if self.maximum is None:
            f.write(bytes([0]))
        else:
            f.write(bytes([1]))
        f.write(packvu32(self.minimum))
        if self.maximum is not None:
            f.write(packvu32(self.maximum))

    @classmethod
    def from_reader(cls, reader):
        tp = reader.read(1)[0]
        assert tp == 0x70
        minimum, maximum = reader.read_limits()
        return cls(minimum=minimum, maximum=maximum)


class Element:
    def __init__(self, table, offset, indexes):
        self.table = table
        self.offset = offset
        self.indexes = indexes

    def to_file(self, f):
        f.write(bytes([self.table]))  # Table

        # Offset as an expression with explicit end:
        Instruction('i32.const', (self.offset,)).to_file(f)
        Instruction('end').to_file(f)
        f.write(packvu32(len(self.indexes)))
        for i in self.indexes:
            f.write(packvu32(i))


class FunctionSig(WASMComponent):
    """ Defines the signature of a WASM module that is imported or defined in
    this module.
    """
    __slots__ = ['params', 'returns', 'index']

    def __init__(self, params=(), returns=()):
        self.params = params
        self.returns = returns
        self.index = None

    def to_text(self):
        return 'FunctionSig(%r, %r)' % (list(self.params), list(self.returns))

    def to_file(self, f):
        f.write(b'\x60')  # form -> nonfunctions may also be supported in the future
        f.write(packvu32(len(self.params)))  # params
        for paramtype in self.params:
            f.write(LANG_TYPES[paramtype])
        f.write(packvu1(len(self.returns)))  # returns
        for rettype in self.returns:
            f.write(LANG_TYPES[rettype])

    @classmethod
    def from_reader(cls, reader):
        form = reader.read(1)
        assert form == b'\x60'
        num_params = reader.read_int()
        params = tuple(reader.read_type() for _ in range(num_params))
        num_returns = reader.read_int()
        returns = tuple(reader.read_type() for _ in range(num_returns))
        return cls(params=params, returns=returns)


class FunctionDef(WASMComponent):
    """ The definition (of the body) of a function. The instructions can be
    Instruction instances or strings/tuples describing the instruction.
    """

    __slots__ = ['locals', 'instructions', 'module']

    def __init__(self, locals, instructions):
        for loc in locals:
            assert isinstance(loc, str)  # valuetype
        self.locals = locals
        self.instructions = []
        for instruction in instructions:
            if isinstance(instruction, tuple):
                instruction = Instruction(instruction[0], instruction[1:])
            assert isinstance(instruction, Instruction), str(instruction)
            self.instructions.append(instruction)
        self.module = None

    def to_text(self):
        s = 'FunctionDef(' + str(list(self.locals)) + '\n'
        s += self._get_sub_text(self.instructions, True)
        s += '\n)'
        return s

    def to_file(self, f):

        # Collect locals by type
        local_entries = []  # list of (count, type) tuples
        for loc_type in self.locals:
            if local_entries and local_entries[-1] == loc_type:
                local_entries[-1] = local_entries[-1][0] + 1, loc_type
            else:
                local_entries.append((1, loc_type))

        f3 = BytesIO()
        f3.write(packvu32(len(local_entries)))  # number of local-entries in this func
        for localentry in local_entries:
            f3.write(packvu32(localentry[0]))  # number of locals of this type
            f3.write(LANG_TYPES[localentry[1]])
        for instruction in self.instructions:
            instruction.to_file(f3)
        f3.write(b'\x0b')  # end
        body = f3.getvalue()
        f.write(packvu32(len(body)))  # number of bytes in body
        f.write(body)

    @classmethod
    def from_reader(cls, reader):
        body_size = reader.read_int()
        body = reader.read(body_size)

        reader2 = FileReader(BytesIO(body))
        num_local_pairs = reader2.read_int()
        localz = []
        for tgi in range(num_local_pairs):
            c = reader2.read_int()
            t = reader2.read_type()
            localz.extend([t] * c)
        instructions = reader2.read_expression()
        remaining = reader2.f.read()
        assert remaining == bytes(), str(remaining)
        assert instructions[-1].type == 'end'
        return cls(localz, instructions[:-1])


class Instruction(WASMComponent):
    """ Class ro represent an instruction. """

    __slots__ = ['type', 'instructions', 'args']

    def __init__(self, type, args=()):
        self.type = type.lower()
        if self.type not in OPCODES:
            raise TypeError('Unknown instruction %r' % self.type)
        self.args = args
        operands = OPERANDS[self.type]
        if len(self.args) != len(operands):
            raise TypeError('Wrong amount of operands for %r' % self.type)
        for a, o in zip(args, operands):
            pass

    def __repr__(self):
        return '<Instruction %s>' % self.type

    def to_text(self):
        subtext = self._get_sub_text(self.args)
        if '\n' in subtext:
            return 'Instruction(' + repr(self.type) + ',\n' + subtext + '\n)'
        else:
            return 'Instruction(' + repr(self.type) + ', ' + subtext + ')'

    def to_file(self, f):
        if self.type not in OPCODES:
            raise TypeError('Unknown instruction %r' % self.type)

        # Our instruction
        f.write(bytes([OPCODES[self.type]]))

        # Prep args
        if self.type == 'call':
            assert isinstance(self.args[0], int)

        # Data comes after
        for arg in self.args:
            if isinstance(arg, (float, int)):
                if self.type.startswith('f64.'):
                    f.write(packf64(arg))
                elif self.type.startswith('i64.'):
                    f.write(packvs64(arg))
                elif self.type.startswith('i32.'):
                    f.write(packvs32(arg))
                elif self.type.startswith('i') or self.type.startswith('f'):
                    raise RuntimeError('Unsupported instruction arg for %s' % self.type)
                else:
                    f.write(packvu32(arg))
            elif isinstance(arg, str):
                f.write(LANG_TYPES[arg])
            else:
                raise TypeError('Unknown instruction arg %r' % arg)  # todo: e.g. constants

    @classmethod
    def from_reader(cls, reader):
        opcode = next(reader)
        type = REVERZ[opcode]
        operands = OPERANDS[type]
        args = []
        for o in operands:
            if o == 'i32':
                arg = reader.read_int()
            elif o == 'u32':
                arg = reader.read_uint()
            elif o == 'type':
                arg = reader.read_type()
            elif o == 'f32':
                arg = reader.read_f32()
            elif o == 'f64':
                arg = reader.read_f64()
            else:
                raise NotImplementedError(o)
            args.append(arg)
        type = REVERZ[opcode]
        return cls(type, args)


# Collect field classes
_exportable_classes = WASMComponent, Function, ImportedFuncion
__all__ = [name for name in globals()
           if isinstance(globals()[name], type) and issubclass(globals()[name], _exportable_classes)]
