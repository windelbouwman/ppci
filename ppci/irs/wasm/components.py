""" Classes to represent a WASM program. """

from io import BytesIO
import logging
import struct

from ._opcodes import OPERANDS, REVERZ, EVAL, OPCODES
from ...utils.leb128 import signed_leb128_encode, unsigned_leb128_encode
from ...utils.leb128 import unsigned_leb128_decode, signed_leb128_decode


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
    return struct.pack('<d', x)


def packf32(x):
    return struct.pack('<f', x)


def packu32(x):
    return struct.pack('<I', x)


def packstr(x):
    bb = x.encode('utf-8')
    return packvu32(len(bb)) + bb


def packvs64(x):
    bb = signed_leb128_encode(x)
    if not len(bb) <= 10:
        raise ValueError('Cannot pack {} into 10 bytes'.format(x))
    return bb


def packvs32(x):
    bb = signed_leb128_encode(x)
    if not len(bb) <= 5:  # 5 = ceil(32/7)
        raise ValueError('Cannot pack {} into 5 bytes'.format(x))
    return bb


def packvu32(x):
    bb = unsigned_leb128_encode(x)
    assert len(bb) <= 5
    return bb


def packvu7(x):
    bb = unsigned_leb128_encode(x)
    assert len(bb) == 1
    return bb


def packvu1(x):
    bb = unsigned_leb128_encode(x)
    assert len(bb) == 1
    return bb


def write_vector(f, elements):
    """ Write a sequence of elements to the given file """
    f.write(packvu32(len(elements)))  # count
    for element in elements:
        element.to_file(f)


class FileReader:
    """ Helper class that can read bytes from a file """
    def __init__(self, f):
        self.f = f

    def read(self, amount):
        if amount < 1:
            raise ValueError('Cannot read {} bytes'.format(amount))
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

    def read_byte(self):
        """ Read the value of a single byte """
        data = self.read(1)
        return data[0]

    def read_int(self):
        """ Read signed int """
        return signed_leb128_decode(self)

    def read_u32(self):
        return unsigned_leb128_decode(self)

    def read_f32(self) -> float:
        data = self.read(4)
        value, = struct.unpack('f', data)
        return value

    def read_f64(self) -> float:
        data = self.read(8)
        value, = struct.unpack('d', data)
        return value

    def read_bytes(self) -> bytes:
        """ Read raw bytes data """
        amount = self.read_u32()
        return self.read(amount)

    def read_str(self):
        """ Read a string """
        data = self.read_bytes()
        return data.decode('utf-8')

    def read_type(self):
        """ Read a wasm type """
        tp = self.read_byte()
        return LANG_TYPES_REVERSE[tp]

    def read_limits(self):
        """ Read min and max limits """
        mx_present = self.read(1)[0]
        assert mx_present in [0, 1]
        minimum = self.read_u32()
        if mx_present:
            maximum = self.read_u32()
        else:
            maximum = None
        return minimum, maximum

    def read_expression(self):
        """ Read instructions until an end marker is found """
        expr = []
        blocks = 1
        i = self.read_instruction()
        # keep track of if/block/loop etc:
        if i.opcode == 'end':
            blocks -= 1
        elif i.opcode in ('if', 'block', 'loop'):
            blocks += 1
        expr.append(i)
        while blocks:
            i = self.read_instruction()
            if i.opcode == 'end':
                blocks -= 1
            elif i.opcode in ('if', 'block', 'loop'):
                blocks += 1
            expr.append(i)
        return expr

    def read_instruction(self):
        """ Read a single instruction """
        return Instruction.from_reader(self)

    def read_vector(self, cls):
        """ Read a vector of the given types.

        Args:
            cls: A type with a static or classmethod from_reader which will
                be used to create the elements from the reader.

        Returns:
            A list of instances of cls.
        """
        count = self.read_u32()
        elements = []
        for _ in range(count):
            elements.append(cls.from_reader(self))
        return elements


def read_wasm(f):
    """ Read a wasm file

    Args:
        f: The file to read from

    Returns:
        A wasm module.
    """
    logger.info('Loading wasm module')
    return Module.from_file(f)


def eval_expr(expr):
    """ Evaluate a sequence of instructions """
    stack = []
    for i in expr:
        consumed_types, produced_types, action = EVAL[i.opcode]
        if action is None:
            raise RuntimeError('Cannot evaluate {}'.format(i.opcode))
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
    """ Base class for representing components of a WASM module, from the
    module to sections and instructions. These components can be shown as
    text or written as bytes.

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

    __slots__ = ['sections']

    def __init__(self, sections):
        super().__init__()
        self.sections = []
        section_ids = set()
        for section in sections:
            if not isinstance(section, Section):
                raise TypeError(
                    'Module expects a sequence of sections.')

            # Check duplicate sections:
            if section.id in section_ids:
                raise ValueError(
                    'Section {} defined twice!'.format(section.id))
            section_ids.add(section.id)

            self.sections.append(section)

        # Sort the sections
        self.sections.sort(key=lambda x: x.id)

    def __iter__(self):
        return iter(self.sections)

    def has_section(self, section):
        """ Determine if the module contains the given section type """
        section_map = {s.id: s for s in self.sections}
        return section.id in section_map

    def get_section(self, section):
        """ Get the given section from this module """
        return self.get_section_by_id(section.id)

    def get_section_by_id(self, section_id):
        """ Get a section given its id """
        section_map = {s.id: s for s in self.sections}
        return section_map[section_id]

    def get_type(self, index):
        """ Get a type based on index """
        type_section = self.get_section(TypeSection)
        return type_section.functionsigs[index]

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
        if data != b'\x00asm':
            raise ValueError('Magic wasm marker is invalid')
        version = struct.unpack('<I', r.read(4))[0]
        assert version == 1, version
        sections = []
        while True:
            section = section_from_reader(r)
            if not section:
                break
            sections.append(section)
        logger.info('Successfully loaded %s sections', len(sections))
        return cls(sections)


# Sections


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
        logger.debug('Writing section %s of %s bytes', self.id, len(payload))
        id = self.id
        assert id >= 0
        # Write it all
        f.write(packvu7(id))
        f.write(packvu32(len(payload)))
        if id == 0:  # custom section for debugging, future, or extension
            type_str = self.__class__.__name__.lower().split('section')[0]
            f.write(packstr(type_str))
        f.write(payload)

    def get_binary_section(self, f):
        raise NotImplementedError()  # Sections need to implement this


def section_from_reader(r):
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
        StartSection,
        DataSection,
    ]
    mp = {s.id: s for s in handled_sections}
    try:
        section_id = r.read_byte()
    except RuntimeError:
        return
    section_size = r.read_u32()
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
    """ Defines signatures of functions that are either imported or defined.
    """

    __slots__ = ['functionsigs']
    id = 1

    def __init__(self, functionsigs):
        super().__init__()
        for i, functionsig in enumerate(functionsigs):
            assert isinstance(functionsig, FunctionSig)
            # todo: remove this?

            # so we can resolve the index in Import objects
            functionsig.index = i
        self.functionsigs = functionsigs

    def to_text(self):
        return 'TypeSection(\n' \
            + self._get_sub_text(self.functionsigs, True) + '\n)'

    def get_binary_section(self, f):
        write_vector(f, self.functionsigs)

    @classmethod
    def from_reader(cls, reader):
        functionsigs = reader.read_vector(FunctionSig)
        return cls(functionsigs)


class ImportSection(Section):
    """ Defines the things to be imported in a module.
    """
    __slots__ = ['imports']
    id = 2

    def __init__(self, imports):
        super().__init__()
        for imp in imports:
            assert isinstance(imp, Import)
        self.imports = list(imports)

    def to_text(self):
        subtext = self._get_sub_text(self.imports, True)
        return 'ImportSection(\n' + subtext + '\n)'

    def get_binary_section(self, f):
        write_vector(f, self.imports)

    @classmethod
    def from_reader(cls, reader):
        return cls(reader.read_vector(Import))


class FunctionSection(Section):
    """ Declares for each function defined in this module which signature is
    associated with it. The items in this sections match 1-on-1 with the items
    in the code section.
    """

    __slots__ = ['indices']
    id = 3

    def __init__(self, indices):
        super().__init__()
        for i in indices:
            assert isinstance(i, int)
        self.indices = indices  # indices in the Type section

    def to_text(self):
        return 'FunctionSection(' \
            + ', '.join([str(i) for i in self.indices]) + ')'

    def get_binary_section(self, f):
        f.write(packvu32(len(self.indices)))
        for i in self.indices:
            f.write(packvu32(i))

    @classmethod
    def from_reader(cls, reader):
        count = reader.read_u32()
        indices = [reader.read_u32() for _ in range(count)]
        return cls(indices)


class TableSection(Section):
    """ Define stuff provided by the host system that WASM can use/reference,
    but cannot be expressed in WASM itself.
    """
    __slots__ = ['tables']
    id = 4

    def __init__(self, tables):
        super().__init__()
        assert len(tables) <= 1   # in MVP
        self.tables = tables

    def __iter__(self):
        return iter(self.tables)

    def get_binary_section(self, f):
        write_vector(f, self.tables)

    @classmethod
    def from_reader(cls, reader):
        return cls(reader.read_vector(Table))


class MemorySection(Section):
    """ Declares initial (and max) sizes of linear memory, expressed in
    WASM pages (64KiB). Only one default memory can exist in the MVP.
    """
    __slots__ = ['entries']
    id = 5

    def __init__(self, entries):
        super().__init__()
        assert len(entries) == 1   # in MVP
        self.entries = entries

    def __iter__(self):
        return iter(self.entries)

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
        count = reader.read_u32()
        entries = []
        for _ in range(count):
            minimum, maximum = reader.read_limits()
            if maximum is None:
                entries.append((minimum,))
            else:
                entries.append((minimum, maximum))
        return cls(entries)


MUTABILITY_TYPES = {'const': b'\x00', 'mut': b'\x01'}
MUTABILITY_TYPES2 = {v[0]: k for k, v in MUTABILITY_TYPES.items()}


class GlobalSection(Section):
    """ Defines the globals in a module. """
    __slots__ = ['globalz']
    id = 6

    def __init__(self, globalz):
        super().__init__()
        assert all(isinstance(g, Global) for g in globalz)
        self.globalz = globalz

    def to_text(self):
        subtext = self._get_sub_text(self.globalz, multiline=True)
        return 'GlobalSection(\n{}\n)'.format(subtext)

    def get_binary_section(self, f):
        write_vector(f, self.globalz)

    @classmethod
    def from_reader(cls, reader):
        return cls(reader.read_vector(Global))


class ExportSection(Section):
    """ Defines the names that this module exports.
    """
    __slots__ = ['exports']
    id = 7

    def __init__(self, exports):
        super().__init__()
        for export in exports:
            if not isinstance(export, Export):
                raise TypeError('exports must be a list of Export objects')
        self.exports = list(exports)

    def to_text(self):
        return 'ExportSection(\n' \
            + self._get_sub_text(self.exports, True) + '\n)'

    def get_binary_section(self, f):
        write_vector(f, self.exports)

    @classmethod
    def from_reader(cls, reader):
        """ Deserialize a single export entry """
        return cls(reader.read_vector(Export))


class StartSection(Section):
    """ Provide the index of the function to call at init-time. The func must
    have zero params and return values.
    """

    __slots__ = ['index']
    id = 8

    def __init__(self, index):
        super().__init__()
        self.index = index

    def to_text(self):
        return 'StartSection(' + str(self.index) + ')'

    def get_binary_section(self, f):
        f.write(packvu32(self.index))

    @classmethod
    def from_reader(cls, reader):
        """ Read in start section from reader object """
        index = reader.read_u32()
        return cls(index)


class ElementSection(Section):
    """ To initialize table elements. """
    __slots__ = ['elements']
    id = 9

    def __init__(self, elements):
        super().__init__()
        self.elements = elements

    def __iter__(self):
        return iter(self.elements)

    def get_binary_section(self, f):
        """ Write elements to file """
        write_vector(f, self.elements)

    @classmethod
    def from_reader(cls, reader):
        """ Read in table element section from reader object """
        return cls(reader.read_vector(Element))


class CodeSection(Section):
    """ The actual code for a module, one CodeSection per function.
    """
    __slots__ = ['functiondefs']
    id = 10

    def __init__(self, functiondefs):
        super().__init__()
        if not all(isinstance(f, FunctionDef) for f in functiondefs):
            raise TypeError('function defs must be all be FunctionDef')
        self.functiondefs = functiondefs

    def to_text(self):
        return 'CodeSection(\n' \
            + self._get_sub_text(self.functiondefs, True) + '\n)'

    def get_binary_section(self, f):
        """ Write contents to file """
        write_vector(f, self.functiondefs)

    @classmethod
    def from_reader(cls, reader):
        return cls(reader.read_vector(FunctionDef))


class DataSection(Section):
    """ Initialize the linear memory.
    Note that the initial contents of linear memory are zero.
    """

    __slots__ = ['chunks']
    id = 11

    def __init__(self, chunks):
        super().__init__()
        for chunk in chunks:
            assert len(chunk) == 3  # index, offset, bytes
            assert chunk[0] == 0  # always 0 in MVP
            assert isinstance(chunk[1], int)
            assert isinstance(chunk[2], bytes)
        self.chunks = chunks

    def __iter__(self):
        return iter(self.chunks)

    def to_text(self):
        chunkinfo = [
            (chunk[0], chunk[1], len(chunk[2])) for chunk in self.chunks]
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
        count = reader.read_u32()
        chunks = []
        for _ in range(count):
            index = reader.read_u32()
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

    __slots__ = ['modname', 'fieldname', 'kind', 'type_id']

    def __init__(self, modname: str, fieldname: str, kind, type_id: int):
        super().__init__()
        self.modname = modname
        self.fieldname = fieldname
        self.kind = kind  # function, table, mem or global
        # the signature-index for funcs, the type for table, memory or global
        self.type_id = type_id

    def to_text(self):
        return 'Import(%r, %r, %r, %r)' % (
            self.modname, self.fieldname, self.kind, self.type_id)

    def to_file(self, f):
        f.write(packstr(self.modname))
        f.write(packstr(self.fieldname))
        if self.kind == 'func':
            f.write(b'\x00')
            f.write(packvu32(self.type_id))
        else:
            raise RuntimeError('Can only import functions for now')

    @classmethod
    def from_reader(cls, reader):
        """ Deserialize import from a reader object """
        modname = reader.read_str()
        fieldname = reader.read_str()
        kind_id = reader.read_byte()
        mp = {0: 'func'}
        kind = mp[kind_id]
        type_index = reader.read_u32()
        return cls(modname, fieldname, kind, type_index)


class Export(WASMComponent):
    """ Export an object defined in this module. The index is the index
    in the corresponding index space (e.g. for functions this is the
    function index space which is basically the concatenation of
    functions in the import and code sections).
    """

    __slots__ = ['name', 'kind', 'index']
    TYPES = (
        ('func', 0),
        ('table', 1),
        ('memory', 2),
    )
    ID2TYPE = {t[1]: t[0] for t in TYPES}
    TYPE2ID = {t[0]: t[1] for t in TYPES}

    def __init__(self, name, kind, index):
        super().__init__()
        self.name = name
        if kind not in self.TYPE2ID:
            valid_types = ', '.join(self.TYPE2ID)
            raise ValueError('kind must be one of {}'.format(valid_types))
        self.kind = kind
        self.index = index

    def to_text(self):
        return 'Export(%r, %r, %i)' % (self.name, self.kind, self.index)

    def to_file(self, f):
        """ Write the export to file """
        f.write(packstr(self.name))
        type_id = self.TYPE2ID[self.kind]
        f.write(bytes([type_id]))
        f.write(packvu32(self.index))

    @classmethod
    def from_reader(cls, reader):
        """ Read an export """
        name = reader.read_str()
        kind = reader.read_byte()
        kind = cls.ID2TYPE[kind]
        index = reader.read_u32()
        return cls(name, kind, index)


class Global(WASMComponent):
    """ Global variable """
    def __init__(self, typ, mutability, value):
        super().__init__()
        self.typ = typ
        self.mutability = mutability
        self.value = value

    def to_text(self):
        return 'Global(%r, %r, %i)' % (self.typ, self.mutability, self.value)

    def to_file(self, f):
        """ Write global to file """
        f.write(LANG_TYPES[self.typ])
        f.write(MUTABILITY_TYPES[self.mutability])

        # Encode value as expression followed by end instruction
        Instruction('i32.const', (self.value,)).to_file(f)
        Instruction('end').to_file(f)

    @classmethod
    def from_reader(cls, reader):
        """ Deserialize a single global from a reader """
        typ = reader.read_type()
        mutability = MUTABILITY_TYPES2[reader.read_byte()]
        value_expr = reader.read_expression()
        value_type, value = eval_expr(value_expr)
        assert value_type == 'i32'
        return cls(typ, mutability, value)


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

    @classmethod
    def from_reader(cls, reader):
        """ Read a single element from a reader """
        table = reader.read(1)[0]
        offset_expr = reader.read_expression()
        offset_type, offset = eval_expr(offset_expr)
        count = reader.read_u32()
        indexes = []
        for _ in range(count):
            indexes.append(reader.read_u32())
        return cls(table, offset, indexes)


class FunctionSig(WASMComponent):
    """ Defines the signature of a WASM module that is imported or defined in
    this module.
    """
    __slots__ = ['params', 'returns', 'index']

    def __init__(self, params=(), returns=()):
        super().__init__()
        self.params = params
        self.returns = returns
        self.index = None

    def to_text(self):
        return 'FunctionSig(%r, %r)' % (list(self.params), list(self.returns))

    def to_file(self, f):
        # TODO: nonfunctions may also be supported in the future
        f.write(b'\x60')  # form
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
        num_params = reader.read_u32()
        params = tuple(reader.read_type() for _ in range(num_params))
        num_returns = reader.read_u32()
        returns = tuple(reader.read_type() for _ in range(num_returns))
        return cls(params=params, returns=returns)


class FunctionDef(WASMComponent):
    """ The definition (of the body) of a function. The instructions can be
    Instruction instances or strings/tuples describing the instruction.
    """

    __slots__ = ['locals', 'instructions']

    def __init__(self, locals, instructions):
        super().__init__()
        for loc in locals:
            assert isinstance(loc, str)  # valuetype
        self.locals = locals
        self.instructions = []
        for instruction in instructions:
            if isinstance(instruction, tuple):
                instruction = Instruction(instruction[0], instruction[1:])
            assert isinstance(instruction, Instruction), str(instruction)
            self.instructions.append(instruction)

    def to_text(self):
        """ Render function def as text """
        s = 'FunctionDef(' + str(list(self.locals)) + '\n'
        s += self._get_sub_text(self.instructions, True)
        s += '\n)'
        return s

    def to_file(self, f):
        """ Output to file """

        # Collect locals by type
        local_entries = []  # list of (count, type) tuples
        for loc_type in self.locals:
            if local_entries and local_entries[-1][1] == loc_type:
                local_entries[-1] = local_entries[-1][0] + 1, loc_type
            else:
                local_entries.append((1, loc_type))

        f3 = BytesIO()
        # number of local-entries in this func
        f3.write(packvu32(len(local_entries)))
        for count, typ in local_entries:
            f3.write(packvu32(count))  # number of locals of this type
            f3.write(LANG_TYPES[typ])

        # Instructions:
        for instruction in self.instructions:
            instruction.to_file(f3)
        f3.write(b'\x0b')  # end
        body = f3.getvalue()
        f.write(packvu32(len(body)))  # number of bytes in body
        f.write(body)

    @classmethod
    def from_reader(cls, reader):
        """ Deserialize a function definition """
        body_size = reader.read_u32()
        body = reader.read(body_size)

        reader2 = FileReader(BytesIO(body))
        num_local_pairs = reader2.read_u32()
        localz = []
        for _ in range(num_local_pairs):
            c = reader2.read_u32()
            t = reader2.read_type()
            localz.extend([t] * c)
        instructions = reader2.read_expression()
        remaining = reader2.f.read()
        assert remaining == bytes(), str(remaining)
        assert instructions[-1].opcode == 'end'
        return cls(localz, instructions[:-1])


class Instruction(WASMComponent):
    """ Class ro represent an instruction. """

    __slots__ = ['opcode', 'args']

    def __init__(self, opcode, args=()):
        super().__init__()
        self.opcode = opcode.lower()
        if self.opcode not in OPCODES:
            raise TypeError('Unknown instruction %r' % self.opcode)
        self.args = args
        operands = OPERANDS[self.opcode]
        if len(self.args) != len(operands):
            raise TypeError('Wrong amount of operands for %r' % self.opcode)

        for a, o in zip(args, operands):
            pass

    def __repr__(self):
        return '<Instruction %s>' % self.opcode

    def to_text(self):
        subtext = self._get_sub_text(self.args)
        if '\n' in subtext:
            return 'Instruction(' + repr(self.opcode) + ',\n' + subtext + '\n)'
        else:
            return 'Instruction(' + repr(self.opcode) + ', ' + subtext + ')'

    def to_file(self, f):
        """ Spit out instruction to file """

        # Our instruction
        f.write(bytes([OPCODES[self.opcode]]))

        # Prep args
        if self.opcode == 'call':
            assert isinstance(self.args[0], int)

        operands = OPERANDS[self.opcode]
        assert len(operands) == len(self.args)

        # Data comes after
        for o, arg in zip(operands, self.args):
            if o == 'i64':
                f.write(packvs64(arg))
            elif o == 'i32':
                f.write(packvs32(arg))
            elif o == 'u32':
                f.write(packvu32(arg))
            elif o == 'f32':
                f.write(packf32(arg))
            elif o == 'f64':
                f.write(packf64(arg))
            elif o == 'type':
                f.write(LANG_TYPES[arg])
            elif o == 'byte':
                f.write(bytes([arg]))
            elif o == 'br_table':
                assert self.opcode == 'br_table'
                f.write(packvu32(len(arg) - 1))
                for x in arg:
                    f.write(packvu32(x))
            else:
                # todo: e.g. constants
                raise TypeError('Unknown instruction arg %r' % o)

    @classmethod
    def from_reader(cls, reader):
        opcode = next(reader)
        typ = REVERZ[opcode]
        operands = OPERANDS[typ]
        # print(opcode, type, operands)
        args = []
        for operand in operands:
            if operand in ['i32', 'i64']:
                arg = reader.read_int()
            elif operand == 'u32':
                arg = reader.read_u32()
            elif operand == 'type':
                arg = reader.read_type()
            elif operand == 'byte':
                arg = reader.read_byte()
            elif operand == 'br_table':
                count = reader.read_u32()
                vec = []
                for _ in range(count + 1):
                    idx = reader.read_u32()
                    vec.append(idx)
                arg = vec
            elif operand == 'f32':
                arg = reader.read_f32()
            elif operand == 'f64':
                arg = reader.read_f64()
            else:  # pragma: no cover
                raise NotImplementedError(operand)
            args.append(arg)
        instruction = cls(typ, args)
        return instruction
