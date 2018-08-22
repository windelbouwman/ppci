""" Classes to represent a WASM program.

* Module: the toplevel unit of deployment, loading, and compilation.
* Definition: child field of a module, there are several subclasses.
* Instruction: representation of a WASM instruction.

Every component (in particular the definitions) has an internal
representation, a text representation (WAT), a tuple representation and
a binary reprsentation. The internal representation is chosen to be
relatively compact, and is quite explicit (often similar to the binary
WASM format). The higher level structure may feel more similar to the
textual WASM format (e.g. support for named identifiers, and sections
being implicit). The code is able to consume text/tuples with abbreviations
(e.g. inline function signatures), but text export is mostly in flat form.

Common attribute names:

* id: id (name or index) of the definition.
* ref: an id used as a reference.
* typ: a value type (e.g. i32 or f64).
* kind: a type of definition (e.g. 'func' or 'import')

"""

# Example code:
# https://github.com/AndrewScheidecker/WAVM/blob/master/Test/wast/echo.wast
# https://github.com/mdn/webassembly-examples
#
# Validate WAT:
# https://cdn.rawgit.com/WebAssembly/wabt/aae5a4b7/demo/wat2wasm/

from io import BytesIO
import logging
import sys
from collections import OrderedDict

from .opcodes import OPERANDS, REVERZ, OPCODES, ArgType
from .util import bytes2datastring
from ..lang.sexpr import parse_sexpr
from .io import FileReader, FileWriter


this_is_js = lambda: False  # For PyScript

logger = logging.getLogger('wasm')

# The toplevel field names that can be in a module, in their preferred order.

SECTION_IDS = {  # Note: order matters!
    'custom': 0,
    'type': 1,
    'import': 2,
    'function': 3,  # this section maps funcs to types
    'table': 4,
    'memory': 5,
    'global': 6,
    'export': 7,
    'start': 8,
    'elem': 9,
    'func': 10,  # the field is called func,
    'code': 10,  # but the section is called code
    'data': 11,
    }

if sys.version_info < (3, 6):
    SECTION_IDS = OrderedDict(sorted(SECTION_IDS.items(), key=lambda i: i[1]))


def check_id(id):
    if isinstance(id, int):
        if not id >= 0:
            raise ValueError('Integer id must be >= 0.')
    elif isinstance(id, str):
        if not id.startswith('$'):
            raise ValueError('String id must start with $.')
    elif isinstance(id, Ref):
        pass
    else:
        raise ValueError('Id must be int or str.')
    return id


class WASMComponent:
    """ Base class for representing components of a WASM module, from the
    Module to Imports, Funct and Instruction. These components can be
    shown as text or written as bytes.

    Each component can be instantiated using:

    * its attributes (the most direct method).
    * a tuple representing an S-expression.
    * a string representing an S-expression.
    * a bytes object representing the binary form of a component.
    * a file object that contains the binary form of a component.

    """

    __slots__ = ()

    def __init__(self, *input):
        # Special input?
        if len(input) == 1:
            if isinstance(input[0], FileReader):
                return self._from_reader(input[0])
            elif isinstance(input[0], tuple):
                return self._from_tuple(input[0])
            elif isinstance(input[0], str) and '(' in input[0]:
                return self._from_string(input[0])
            elif isinstance(input[0], bytes):
                return self._from_bytes(input[0])
            elif hasattr(input[0], 'read'):
                return self._from_file(input[0])

        # Else, more direct instantiation
        self._from_args(*input)

    def __repr__(self):
        return '<WASM-%s>' % (self.__class__.__name__)

    def show(self):
        """ Print the S-expression of the component.
        """
        print(self.to_string())

    def _get_sub_string(self, subs, multiline=False):
        """ Helper method to get the string of a list of sub components,
        inserting newlines as needed.
        """
        # Collect sub texts
        texts = []
        charcount = 0
        haslf = False
        for sub in subs:
            if isinstance(sub, WASMComponent):
                text = sub.to_string()
            else:
                text = str(sub)  # or repr ...
            charcount += len(text)
            texts.append(text)
            haslf = haslf or '\n' in text
        # Put on one line or multiple lines
        if multiline or haslf or charcount > 70:
            lines = []
            indent = 4
            for text in texts:
                for line in text.splitlines():
                    if line.startswith(('(else', '(end')):
                        indent -= 4
                    lines.append(' ' * indent + line)
                    if line.startswith(('(block', '(loop', '(if', '(else')):
                        indent += 4
            return '\n'.join(lines)
        else:
            return ' '.join(texts)

    # From ...

    def _from_args(self):
        pass

    def _from_string(self, s):
        # This method typically does not need overloading
        t = parse_sexpr(s)
        self._from_tuple(t)

    def _from_tuple(self, t):
        # Implement this to be able to consume str
        raise NotImplementedError()

    def _from_bytes(self, b):
        self._from_file(BytesIO(b))

    def _from_file(self, f):
        self._from_reader(FileReader(f))

    def _from_reader(self, r):
        raise NotImplementedError()

    # To ...

    def to_string(self):
        """ Get the textual representation (S-expression) of this component.
        """
        raise NotImplementedError()

    def to_tuple(self):
        """ Get the component's tuple representation (by exporting to string
        and parsing the s-expression).
        """
        # TODO: should we reverse this logic,
        # by having to_string using to_tuple?
        s = self.to_string()
        return parse_sexpr(s)


class Ref:
    """ This is a reference to an object in one of the 5 spaces.

    space must be one of 'type', 'func', 'memory', 'table', 'global', 'local'
    index can be none
    """
    # TODO: idea:
    # wb: store reference to the object itself instead of an index?
    def __init__(self, space, index=None, name=None):
        valid_spaces = [
            'type', 'func', 'memory', 'table', 'global', 'local', 'label']
        if space not in valid_spaces:
            raise ValueError('space must be one of {}'.format(valid_spaces))
        self.space = space
        if index is None and name is None:
            raise ValueError('You must provide index or name for a Ref')
        self.index = index
        self.name = name

    def __str__(self):
        # Preferably use a name, if available:
        if self.name:
            return self.name
        else:
            return str(self.index)

    def __repr__(self):
        return 'Ref(space={},index={},name={})'.format(
            self.space, self.index, self.name)

    def resolve(self, id_maps):
        if self.index is None:
            id_map = id_maps[self.space]
            if self.name in id_map:
                return id_map[self.name]
            else:
                raise ValueError('Cannot resolve {}'.format(repr(self)))
        else:
            return self.index

    @property
    def is_zero(self):
        """ Check if we refer to element 0 """
        if self.name:
            return self.name == '$0'
        else:
            return self.index == 0

    @classmethod
    def from_value(cls, space, value):
        if isinstance(value, int):
            return cls(space, index=value)
        else:
            return cls(space, name=value)


class Module(WASMComponent):
    """ Class to represent a WASM module; the toplevel unit of code.

    The Module is a collection of definitions, which can be provided as
    text, tuples, or Definition objects.
    """

    __slots__ = ('id', 'definitions')  # id is only for documentation purposes

    def _from_args(self, *definitions):
        self._from_tuple(definitions)

    def _from_tuple(self, t):
        """ Initialize from tuple.
        """

        from .wat import load_tuple
        load_tuple(self, t)

    def to_string(self):
        # TODO: idea: first construct tuples, then pretty print these tuples
        # to strings.
        id_str = ' ' + self.id if self.id else ''
        defs_str = ''
        if self.definitions:
            defs_str = '\n%s\n' % self._get_sub_string(self.definitions, True)
        return '(module' + id_str + defs_str + ')\n'

    def to_bytes(self):
        """ Get the bytes that represent the binary WASM for this module.
        """
        f = BytesIO()
        self.to_file(f)
        return f.getvalue()

    def show_bytes(self):
        """ Show the binary representation of this WASM module.
        """
        # if not this_is_js():  (Artifact from trying PyScript)
        from ..utils.hexdump import hexdump
        hexdump(self.to_bytes())

    def to_file(self, f):
        """ Write this wasm module to file """
        self._to_writer(FileWriter(f))

    def _to_writer(self, f):
        f.write(b'\x00asm')
        f.write_u32(1)  # version, must be 1 for now

        # todo: allow custom section(s)
        # todo: WASM defines custom "name section": we can lookup names later!

        # Collect definitions, so we have the order right. The order is
        # probably already good because we read it as such, but better be safe.
        definitions = self.get_definitions_per_section()

        # Iterate over (possible) sections
        for section_name, section_id in SECTION_IDS.items():
            if section_name == 'code':
                continue  # we have 'func' instead

            # Prepare file to write this section to.
            # It is tempting to use f.tell() and write the size later, but
            # these variable-sized ints make this difficult.
            f2 = FileWriter(BytesIO())

            if section_name == 'function':
                if len(definitions['func']) == 0:
                    continue
                # Special section that binds sigs to imports and implementation
                f2.write_vu32(len(definitions['func']))
                for d in definitions['func']:
                    type_id = d.ref.index
                    f2.write_vu32(type_id)

            else:
                section_defs = definitions[section_name]
                if len(section_defs) == 0:
                    continue

                if section_name == 'start':
                    assert len(section_defs) == 1, 'Expected 0 or 1 start defs'
                    section_defs[0]._to_writer(f2)
                elif section_name == 'custom':
                    for d in section_defs:
                        f3 = FileWriter(BytesIO())
                        d._to_writer(f3)
                        payload = f3.f.getvalue()
                        #
                        f2.write_vu7(section_id)  # \x00
                        f2.write_vu32(len(payload))
                        f2.write(payload)
                else:
                    # Write how many definitions, and write each one
                    f2.write_vu32(len(section_defs))  # count
                    for index, d in enumerate(section_defs):
                        # Funcs need their param index/name space
                        # Note that id in Type.params can be int/str, not None
                        if section_name == 'func':
                            typedefs = definitions['type']
                            typedef = typedefs[d.ref.index]
                        # Write it!
                        d._to_writer(f2)

            # Write this section to our main file object
            payload = f2.f.getvalue()
            logger.debug('Writing section %s of %s bytes' %
                         (section_id, len(payload)))
            if section_name != 'custom':
                f.write_vu7(section_id)
                f.write_vu32(len(payload))
            f.write(payload)

    def _from_reader(self, reader):

        # Check header and version
        data = reader.read(4)
        if data != b'\x00asm':
            raise ValueError('Magic wasm marker is invalid')
        version = reader.read_u32()
        assert version == 1, version

        # Prepare
        section_id_to_name = {}
        for name, id in SECTION_IDS.items():
            if name != 'code':  # use "func" instead
                section_id_to_name[id] = name
        type4func = {}
        id_maps = {
            'type': {}, 'func': {}, 'table': {}, 'memory': {},
            'global': {},
        }

        # todo: we may assign id's inside the _from_reader() methods,
        # revisit when implementing the custom name section.

        # Read sections that contain definitions
        definitions = []
        while True:
            try:
                section_id = reader.read_byte()
            except EOFError:
                break
            # TODO: Validate section nbytes
            section_nbytes = reader.read_uint()
            section_name = section_id_to_name[section_id]
            section_data = reader.read(section_nbytes)
            logger.debug('Loading %s section', section_name)
            reader2 = FileReader(BytesIO(section_data))

            if section_name == 'function':
                # Read mapping of func id to type id (both indexes)
                nfuncs = reader2.read_uint()
                for i in range(nfuncs):
                    type4func[i] = reader2.read_uint()
            elif section_name == 'start':  # There is (at most) 1 start def
                definitions.append(Start(reader2))
            elif section_name == 'custom':
                name_len = reader2.read_uint()
                definitions.append(Custom(reader2.read(name_len).decode(),
                                          reader2.read()))
            else:
                ndefs = reader2.read_uint()  # for this section
                for i in range(ndefs):
                    Cls = DEFINITION_CLASSES[section_name]
                    d = Cls(reader2)
                    if section_name == 'func':
                        d.ref = Ref('type', index=type4func[i])
                    definitions.append(d)
                    if section_name == 'import':
                        id_map = id_maps[d.kind]
                        d.id = len(id_map)
                        id_map[d.id] = d.id
                    elif section_name in id_maps:
                        id_map = id_maps[section_name]
                        d.id = len(id_map)
                        id_map[d.id] = d.id

        logger.info('Loaded WASM module from binary with %i definitions' %
                    len(definitions))
        self.definitions = definitions
        self.id = None

    # Module-specific stuff

    def __iter__(self):
        return iter(self.definitions)

    def __getitem__(self, i):
        if isinstance(i, int):
            return self.definitions[i]
        elif isinstance(i, str):
            i = 'func' if i == 'code' else i
            return [d for d in self.definitions if d.__name__ == i]
        else:
            raise IndexError('Module can only be indexed with int and str')

    def add_definition(self, d):
        """ Add a definition to the module.
        """
        assert isinstance(d, Definition)
        self.definitions.append(d)

    def get_definitions_per_section(self):
        """ Get a dictionary that maps section names to definitions.
        Note that the 'code' section is named 'func'.
        Note that one can also use e.g. ``module['type']`` to get all typedefs.
        """
        definitions = dict((name, []) for name in SECTION_IDS)
        for d in self.definitions:
            definitions[d.__name__].append(d)
        assert not definitions.pop('code')  # use func instead
        assert not definitions.pop('function')  # this section is implicit
        return definitions

    def show_interface(self):
        """ Show the (signature of) imports and exports in a human
        friendly manner.
        """
        types = self['type']
        imports = self['import']
        exports = self['export']
        functions = self['func']
        n_func_imports = sum(c.kind == 'func' for c in imports)
        print('Imports:')
        for c in imports:
            if c.kind == 'func':
                sig = types[c.info[0].index]
                params_s = ', '.join([p[1] for p in sig.params])
                result_s = ', '.join([r for r in sig.result])
                print(
                    '  {}.{}:'.format(c.modname, c.name).ljust(20),
                    '[{}] -> [{}]'.format(params_s, result_s))
            else:
                print('  {}:'.format(c.kind).ljust(20), '"{}"'.format(c.name))

        print('Exports:')
        for c in exports:
            if c.kind == 'func':
                func = functions[c.ref.index - n_func_imports]
                sig = types[func.ref.index]
                params_s = ', '.join([p[1] for p in sig.params])
                result_s = ', '.join([r for r in sig.result])
                print(
                    '  {}:'.format(c.name).ljust(20),
                    '[{}] -> [{}]'.format(params_s, result_s))
            else:
                print('  {}:'.format(c.kind).ljust(20), '"{}"'.format(c.name))


def str2int(x):
    return int(x, 16) if x.startswith('0x') else int(x)


class Instruction(WASMComponent):
    """ Class ro represent an instruction (an opcode plus arguments). """

    __slots__ = ('opcode', 'args')

    def _from_args(self, opcode, *args):
        # Memory instructions have keyword args in text format :/
        if '.load' in opcode or '.store' in opcode:
            # Determine default args
            offset_arg = 0
            align_arg = 2 if '32.' in opcode else 3
            opcode2 = opcode.split('.')[-1]
            for align, nbytes in [(0, '8'), (1, '16'), (2, '32'), (3, '64')]:
                if nbytes in opcode2:
                    align_arg = align
            # Parse keyword args
            for arg in args:
                if isinstance(arg, str):
                    if arg.startswith('align='):
                        align_arg = str2int(arg.split('=')[-1])
                        # Store alignment as power of 2:
                        log2 = {
                            1: 0,
                            2: 1,
                            4: 2,
                            8: 3,
                            16: 4
                        }
                        align_arg = log2[align_arg]
                    elif arg.startswith('offset='):
                        offset_arg = str2int(arg.split('=')[-1])
            args = align_arg, offset_arg
        else:
            for arg in args:
                assert isinstance(arg, (str, int, float, Ref, list))

        self.opcode = opcode
        self.args = args

    def __repr__(self):
        return '<Instruction %s>' % self.opcode

    def __getitem__(self, i):
        # Make it feel a bit like a named tuple
        return getattr(self, self.__slots__[i])

    def to_string(self):
        args = self.args
        if '.load' in self.opcode or '.store' in self.opcode:
            if args[1] == 0:  # zero offset
                args = ('align=%i' % 2**args[0], )
            else:
                args = ('align=%i' % 2**args[0], 'offset=%i' % args[1])
        elif self.opcode == 'call_indirect':
            if args[1].index == 0:  # zero'th table
                args = ('(type %s)' % args[0], ) 
            else:
                args = ('(type %s)' % args[0], '(const.i64 %i)' % args[1].index)
        subtext = self._get_sub_string(args)
        if '\n' in subtext:
            return '(' + self.opcode + '\n' + subtext + '\n)'
        else:
            return '(' + self.opcode + ' ' * bool(subtext) + subtext + ')'

    # This is a list of functions to write argument of different types:
    wfm = {
        ArgType.TYPE: lambda writer, arg: writer.write_type(arg),
        ArgType.U32: lambda writer, arg: writer.write_vu32(arg),
        ArgType.LABELIDX: lambda writer, arg: writer.write_vu32(arg.index),
        ArgType.LOCALIDX: lambda writer, arg: writer.write_vu32(arg.index),
        ArgType.GLOBALIDX: lambda writer, arg: writer.write_vu32(arg.index),
        ArgType.FUNCIDX: lambda writer, arg: writer.write_vu32(arg.index),
        ArgType.TYPEIDX: lambda writer, arg: writer.write_vu32(arg.index),
        ArgType.TABLEIDX: lambda writer, arg: writer.write_vu32(arg.index),
        ArgType.I32: lambda writer, arg: writer.write_vs32(arg),
        ArgType.I64: lambda writer, arg: writer.write_vs64(arg),
        ArgType.F32: lambda writer, arg: writer.write_f32(arg),
        ArgType.F64: lambda writer, arg: writer.write_f64(arg),
    }

    def _to_writer(self, f):

        # Our instruction
        f.write(bytes([OPCODES[self.opcode]]))

        # Prep args for accessing named identifiers
        args = list(self.args)

        operands = OPERANDS[self.opcode]
        assert len(operands) == len(args)

        # Data comes after
        for o, arg in zip(operands, args):
            if o in self.wfm:
                self.wfm[o](f, arg)
            elif o == 'byte':
                f.write(bytes([arg]))
            elif o == 'br_table':
                assert self.opcode == 'br_table'
                f.write_vu32(len(arg) - 1)
                for x in arg:
                    f.write_vu32(x.index)
            else:
                raise TypeError('Unknown instruction arg %r' % o)

    # This is a list of functions to read specific argument types:
    rfm = {
        ArgType.TYPE: lambda reader: reader.read_type(),
        ArgType.U32: lambda reader: reader.read_uint(),
        ArgType.LABELIDX: lambda reader: Ref('label', index=reader.read_uint()),
        ArgType.LOCALIDX: lambda reader: Ref('local', index=reader.read_uint()),
        ArgType.GLOBALIDX: lambda reader: Ref('global', index=reader.read_uint()),
        ArgType.FUNCIDX: lambda reader: Ref('func', index=reader.read_uint()),
        ArgType.TYPEIDX: lambda reader: Ref('type', index=reader.read_uint()),
        ArgType.TABLEIDX: lambda reader: Ref('table', index=reader.read_uint()),
        ArgType.I32: lambda reader: reader.read_int(),
        ArgType.I64: lambda reader: reader.read_int(),
        ArgType.F32: lambda reader: reader.read_f32(),
        ArgType.F64: lambda reader: reader.read_f64(),
    }

    def _from_reader(self, reader):
        binopcode = next(reader)
        self.opcode = REVERZ[binopcode]
        operands = OPERANDS[self.opcode]
        # print(opcode, type, operands)
        args = []
        for operand in operands:
            if operand in self.rfm:
                arg = self.rfm[operand](reader)
            elif operand == 'byte':
                arg = reader.read_byte()
            elif operand == 'br_table':
                count = reader.read_uint()
                vec = []
                for _ in range(count + 1):
                    idx = Ref('label', index=reader.read_uint())
                    vec.append(idx)
                arg = vec
            else:  # pragma: no cover
                raise NotImplementedError(operand)
            args.append(arg)
        self.args = tuple(args)


class BlockInstruction(Instruction):
    """ An instruction that represents a block of instructions.
    (block, loop or if). The args consists of a single element indicating the
    result type. It can optionally have an id.
    """

    __slots__ = ('id', )  # id can be None

    def _from_args(self, opcode, *args):
        id = None
        if len(args) == 2:
            id, *args = args
        self.id = id
        return super()._from_args(opcode, *args)
    
    def _from_reader(self, reader):
        self.id = None
        return super()._from_reader(reader)
    
    def to_string(self):
        idtext = '' if self.id is None else ' ' + self.id
        a0 = self.args[0]
        subtext = '' if a0 is 'emptyblock' else ' (result ' + str(a0) + ')'
        return '(' + self.opcode + idtext + subtext + ')'


## Definition classes


class Definition(WASMComponent):
    """ Base class for definition components.

    A "definition" is a toplevel element in a WASM module that defines a
    type, function, import, etc.
    """

    __slots__ = ()

    def __getitem__(self, i):
        # Make it feel a bit like a named tuple
        return getattr(self, self.__slots__[i])

    @property
    def __name__(self):
        return self.__class__.__name__.lower()


class Type(Definition):
    """ Defines the signature of a WASM function that is imported or defined in
    this module.

    Flat form and abbreviations:

    * In the flat form, a module has type definitions, and these are refered to
      with "type uses": ``(type $xx)``.
    * A type use can be given to *define* the type rather than reference it,
      this is resolved by the Module class.
    * Multiple anonymous params may be combined: e.g. ``(param i32 i32)``, this
      is resoved by this class, and to_string() applies this abbreviation.

    Attributes:

    * id: the id (str/int) of this definition in the type name/index space.
    * params: a list of parameter tuples ($id, type), where id can be int.
    * result: a list if type strings (0 or 1 elements in v1).

    """

    __slots__ = ('id', 'params', 'result')

    def _from_args(self, id, params, result):
        assert isinstance(id, (int, str))
        assert isinstance(params, (tuple, list))
        assert isinstance(result, (tuple, list))
        assert all(isinstance(el, tuple) and len(el) == 2 for el in params)
        assert all(isinstance(el, str) for el in result)
        self.id = check_id(id)
        self.params = tuple(params)
        self.result = tuple(result)
        assert len(self.result) <= 1  # for now

    def to_string(self):
        s = '(type %s (func' % self.id
        last_anon = False
        for i in range(len(self.params)):
            id, typ = self.params[i]
            if isinstance(id, int):
                assert id == i
                if last_anon:
                    s += ' ' + typ
                else:
                    s += ' (param %s' % typ
                    last_anon = True
            else:
                s += ')' if last_anon else ''
                s += ' (param %s %s)' % (id, typ)
                last_anon = False
        s += ')' if last_anon else ''
        if self.result:
            s += ' (result ' + ' '.join(self.result) + ')'
        return s + '))'

    def _to_writer(self, f):
        f.write(b'\x60')  # form
        f.write_vu32(len(self.params))  # params
        for _, paramtype in self.params:
            f.write_type(paramtype)
        f.write_vu1(len(self.result))  # returns
        for rettype in self.result:
            f.write_type(rettype)

    def _from_reader(self, reader):
        form = reader.read(1)
        assert form == b'\x60'
        num_params = reader.read_uint()
        self.params = [(i, reader.read_type()) for i in range(num_params)]
        num_returns = reader.read_uint()
        self.result = [reader.read_type() for _ in range(num_returns)]


class Import(Definition):
    """ Import objects (from other wasm modules or from the host environment).
    Imports are handled at runtime by the host environment.

    Flat form and abbreviations:

    * Imports in flat form have a shape ``(import "foo" "bar" ...)``.
    * An import can be defined as func/table/memory/global that is "marked"
      as an import (e.g. ``(memory (import "foo" "bar") 1)``. This is resolved
      by the Module class.

    Attributes:

    * modname: module to import from, as interpreted by host system.
    * name: name of object to import, as interpreted by host system.
    * kind: 'func', 'table', 'memory', or 'global'.
    * id: the id to refer to the imported object.
    * info: a tuple who's content depends on the kind:
        * func: (ref, ) to the type (signature).
        * table: ('anyfunc', min, max), where max can be None.
        * memory: (min, max), where max can be None.
        * global: (typ, mutable)
    """

    __slots__ = ('modname', 'name', 'kind', 'id', 'info')

    def _from_args(self, modname, name, kind, id, info):
        assert kind in ('func', 'table', 'memory', 'global')
        assert isinstance(info, tuple)
        self.modname = modname
        self.name = name
        self.kind = kind
        self.id = check_id(id)
        self.info = info

    def to_string(self):
        # Get description
        if self.kind == 'func':
            desc = ['(type %s)' % self.info[0]]
        elif self.kind == 'table':
            desc = ['anyfunc']
            if self.info[2] is not None:
                desc = [str(self.info[1]), str(self.info[2]), 'anyfunc']
            elif self.info[1] != 0:
                desc = [str(self.info[1]), 'anyfunc']
        elif self.kind == 'memory':
            desc = [self.info[0]] if self.info[1] is None else list(self.info)
        elif self.kind == 'global':
            fmt = '(mut %s)' if self.info[1] else '%s'  # mutable?
            desc = [fmt % self.info[0]]
        # Populate description more
        if not (self.kind in ('memory', 'table') and self.id == '$0'):
            desc.insert(0, self.id)
        # Compose
        return '(import "%s" "%s" (%s %s))' % (
            self.modname, self.name, self.kind, ' '.join(str(i) for i in desc))

    def _to_writer(self, f):
        f.write_str(self.modname)
        f.write_str(self.name)
        if self.kind == 'func':
            f.write(b'\x00')
            # type-index, not func-
            int_ref = self.info[0].index
            f.write_vu32(int_ref)
        elif self.kind == 'table':
            f.write(b'\x01')
            table_kind, min, max = self.info
            f.write_type(table_kind)  # always 0x70 anyfunc in v1
            f.write_limits(min, max)
        elif self.kind == 'memory':
            f.write(b'\x02')
            min, max = self.info
            f.write_limits(min, max)
        elif self.kind == 'global':
            f.write(b'\x03')
            typ, mutable = self.info
            f.write_type(typ)
            f.write(bytes([int(mutable)]))
        else:  # pragma: no cover
            raise NotImplementedError(self.kind)

    def _from_reader(self, reader):
        self.modname = reader.read_str()
        self.name = reader.read_str()
        kind_id = reader.read_byte()
        if kind_id == 0:
            self.kind = 'func'
            self.info = (Ref('type', index=reader.read_uint()), )
        elif kind_id == 1:
            self.kind = 'table'
            table_kind = reader.read_type()
            min, max = reader.read_limits()
            self.info = table_kind, min, max
        elif kind_id == 2:
            self.kind = 'memory'
            min, max = reader.read_limits()
            self.info = min, max
        elif kind_id == 3:
            self.kind = 'global'
            self.info = reader.read_type(), bool(reader.read_byte())
        else:  # pragma: no cover
            raise NotImplementedError()


class Table(Definition):
    """ A resizable typed array of references (e.g. to functions) that could
    not otherwise be stored as raw bytes in Memory (for safety and portability
    reasons). Only one default table can exist in v1.

    A practical use-case is to store "function pointers" for e.g. callbacks.
    Tables allow doing that without actually exposing the memory location.

    Flat form and abbreviations:

    * Since v1 mandates a single table, the id is usually omitted.
    * Elements can be specified inline, this is resolved by the Module class.
    * The call_indirect instruction has one arg that specifies the signature,
      i.e. no support for inline typeuse.

    Attributes:

    * id: the id of this table definition in the table name/index space.
    * kind: the kind of data stored in the table, only 'anyfunc' in v1.
    * min: the minimum (initial) table size.
    * max: the maximum table size, or None.

    """

    __slots__ = ('id', 'kind', 'min', 'max')


    def _from_args(self, id, kind, min, max):
        self.id = check_id(id)
        assert kind in ('anyfunc', )  # More kinds in future versions
        self.kind = kind
        self.min = min
        self.max = max

    def to_string(self):
        id = '' if self.id == '$0' else ' %s' % self.id
        if self.max is None:
            minmax = '' if self.min == 0 else ' %i' % self.min
        else:
            minmax = ' %i %i' % (self.min, self.max)
        return '(table%s%s %s)' % (id, minmax, self.kind)

    def _to_writer(self, f):
        f.write_type(self.kind)  # always 0x70 anyfunc in v1
        f.write_limits(self.min, self.max)

    def _from_reader(self, reader):
        self.kind = reader.read_type()
        assert self.kind == 'anyfunc'
        self.min, self.max = reader.read_limits()


class Memory(Definition):
    """ Declares initial (and max) sizes of linear memory, expressed in
    WASM pages (64KiB). Only one default memory can exist in v1.

    Flat form and abbreviations:

    * Since v1 mandates a single memory, the id is usually omitted.
    * Data can be specified inline, this is resolved by the Module class.

    Attributes:

    * id: the id of this memory definition in the memory name/index space.
    * min: the minimum (initial) memory size.
    * max: the maximum memory size, or None.

    """

    __slots__ = ('id', 'min', 'max')

    def _from_args(self, id, min, max=None):
        # assert isinstance(id, str)  # otherwise hard to dinstinguis from ints
        self.id = check_id(id)
        self.min = min
        self.max = max

    def to_string(self):
        id = '' if self.id == '$0' else ' %s' % self.id
        min = ' %i' % self.min
        max = '' if self.max is None else ' %i' % self.max
        return '(memory%s%s%s)' % (id, min, max)

    def _to_writer(self, f):
        f.write_limits(self.min, self.max)

    def _from_reader(self, reader):
        self.min, self.max = reader.read_limits()


class Global(Definition):
    """ A global variable.

    Attributes:

    * id: the id of this global definition in the globals name/index space.
    * typ: the value type of the global.
    * mutable: whether this global is mutable (can hurt performance).
    * init: an instruction to initialize the global (e.g. a i32.const).

    """

    __slots__ = ('id', 'typ', 'mutable', 'init')

    def _from_args(self, id, typ, mutable, init):
        assert isinstance(init, list)
        self.id = check_id(id)
        self.typ = typ
        self.mutable = bool(mutable)
        self.init = init

    def to_string(self):
        init = ' '.join(i.to_string() for i in self.init)
        if self.mutable:
            return '(global %s (mut %s) %s)' % (self.id, self.typ, init)
        else:
            return '(global %s %s %s)' % (self.id, self.typ, init)

    def _to_writer(self, f):
        f.write_type(self.typ)
        f.write(bytes([int(self.mutable)]))

        # Encode value as expression followed by end instruction
        f.write_expression(self.init)

    def _from_reader(self, reader):
        self.typ = reader.read_type()
        self.mutable = bool(reader.read_byte())
        self.init = reader.read_expression()


class Export(Definition):
    """ Export an object defined in this module.

    Flat form and abbreviations:

    * Export in flat form have a shape ``(export "foo" ...)``.
    * An export can be defined as func/table/memory/global that is "marked"
      as an export (e.g. ``(memory (export "bar") 1)``. This is resolved
      by the Module class.

    Attributes:

    * name: the name by which to export this value.
    * kind: the kind of value to export ('func', 'table', or 'memory').
    * ref: a reference to the thing being exported (in the name/index space
      corresponding to kind).
    """

    __slots__ = ('name', 'kind', 'ref')  # (export "name" (func $ref))

    def _from_args(self, name, kind, ref):
        assert isinstance(ref, Ref)
        assert kind in ('func', 'table', 'memory', 'global')
        self.name = name
        self.kind = kind
        self.ref = ref

    def to_string(self):
        return '(export "%s" (%s %s))' % (self.name, self.kind, self.ref)

    def _to_writer(self, f):
        f.write_str(self.name)
        type_id = {'func': 0, 'table': 1, 'memory': 2, 'global': 3}[self.kind]
        f.write(bytes([type_id]))
        assert self.ref.space == self.kind
        int_ref = self.ref.index
        f.write_vu32(int_ref)

    def _from_reader(self, reader):
        self.name = reader.read_str()
        kind_id = reader.read_byte()
        self.kind = ['func', 'table', 'memory', 'global'][kind_id]
        self.ref = Ref(self.kind, index=reader.read_uint())


class Start(Definition):
    """ Define the index of the function to call at init-time. The func must
    have zero params and return values. There must be at most 1 start
    definition.

    Attributes:

    * ref: the reference to the function to mark as the start function.

    """

    __slots__ = ('ref', )

    def _from_args(self, ref):
        self.ref = check_id(ref)

    def to_string(self):
        return '(start %s)' % self.ref

    def _to_writer(self, f):
        assert self.ref.space == 'func'
        f.write_vu32(self.ref.index)

    def _from_reader(self, reader):
        self.ref = Ref('func', index=reader.read_uint())


class Func(Definition):
    """ The definition (i.e. instructions) of a function.

    Flat form and abbreviations:

    * In the flat form, it refers to a type (not define params inline).
    * Inline signatures are resolved by ...
    * Imported functions can be defined as e.g.
      ``(func $add (import "foo" "bar"))``, which resolves into an Import
      instead of a Func.
    * Multiple anonymous locals may be combined. This is resolved by this class
      and to_string() applies this abbreviation.

    Attributes:

    * id: the id of this func definition in the func name/index space.
    * ref: the reference to the type (i.e. signature).
    * locals: a list of ($id, typ) tuples. The id can be None to indicate
      implicit id's (note that the id is offset by the parameters).
    * instructions: a list of instructions (may be given as tuples).

    """

    # todo: force local ids to be either int or str?

    __slots__ = ('id', 'ref', 'locals', 'instructions')  # ref to type

    def _from_args(self, id, ref, locals, instructions):
        if not isinstance(ref, Ref):
            raise TypeError('ref must be of type Ref')
        assert isinstance(locals, (tuple, list))
        assert isinstance(instructions, (tuple, list))
        assert all(isinstance(el, tuple) and len(el) == 2 for el in locals)
        self.id = check_id(id)
        self.ref = ref
        self.locals = tuple(locals)
        # Parse instructions
        if instructions and isinstance(instructions[0], Instruction):
            self.instructions = instructions  # assume all are instructions
        else:
            blocktypes = ('block', 'loop', 'if')
            self.instructions = [
                (BlockInstruction if i[0] in blocktypes else Instruction)(*i)
                for i in instructions]

    def to_string(self):
        """ Render function def as text """
        s = ''
        last_anon = False
        for i in range(len(self.locals)):
            id, typ = self.locals[i]
            if id is None or isinstance(id, int):
                if id is not None:
                    assert id == i
                if last_anon:
                    s += ' ' + typ
                else:
                    s += ' (local %s' % typ
                    last_anon = True
            else:
                s += ')' if last_anon else ''
                s += ' (local %s %s)' % (id, typ)
                last_anon = False
        s += ')' if last_anon else ''
        locals_str = s

        s = '(func %s (type %s)' % (self.id, self.ref) + locals_str + '\n'
        s += self._get_sub_string(self.instructions, True)
        s += '\n)'
        return s

    def _to_writer(self, f):

        # You would expect the ref to be used here, but the WASM spec has a
        # separate function section for that. Not sure why.

        # Collect locals by type
        local_entries = []  # list of (count, type) tuples
        for loc_id, loc_type in self.locals:
            if local_entries and local_entries[-1][1] == loc_type:
                local_entries[-1] = local_entries[-1][0] + 1, loc_type
            else:
                local_entries.append((1, loc_type))

        f3 = FileWriter(BytesIO())
        # Number of local-entries in this func
        f3.write_vu32(len(local_entries))
        for count, loc_type in local_entries:
            f3.write_vu32(count)  # number of locals of this type
            f3.write_type(loc_type)

        # Instructions:
        for instruction in self.instructions:
            instruction._to_writer(f3)
        f3.write(b'\x0b')  # end
        body = f3.f.getvalue()
        f.write_vu32(len(body))  # number of bytes in body
        f.write(body)

    def _from_reader(self, reader):
        body_size = reader.read_uint()
        body = reader.read(body_size)

        reader2 = FileReader(BytesIO(body))
        num_local_pairs = reader2.read_uint()
        localz = []
        for _ in range(num_local_pairs):
            c = reader2.read_uint()
            t = reader2.read_type()
            localz.extend([(None, t)] * c)
        instructions = reader2.read_expression()
        remaining = reader2.f.read()
        assert remaining == bytes(), str(remaining)
        self.locals = localz
        self.instructions = instructions


class Elem(Definition):
    """ Define elements to populate a table.

    Flat form and abbreviations:

    * Elements can be defined inline inside Table expressions, this is resolved
      by the Module class.

    Attributes:

    * ref: the table id that this element applies to.
    * offset: the element offset, expressed as an instruction list (i.e. [i32.const, end])
    * refs: a list of function references.
    """

    __slots__ = ('ref', 'offset', 'refs')

    def _from_args(self, ref, offset, refs):
        # Check
        assert isinstance(offset, list)
        assert isinstance(refs, (tuple, list))
        # Set
        assert isinstance(ref, Ref)
        self.ref = check_id(ref)
        self.offset = offset
        self.refs = refs

    def to_string(self):
        ref = '' if self.ref.is_zero else ' %s' % self.ref
        offset = ' '.join(i.to_string() for i in self.offset)
        refs_as_str = ' '.join(str(i) for i in self.refs)
        return '(elem%s %s %s)' % (ref, offset, refs_as_str)

    def _to_writer(self, f):
        assert self.ref.space == 'table'
        f.write_vu32(self.ref.index)
        # Encode offset as expression followed by end instruction
        f.write_expression(self.offset)
        # Encode as u32 length followed by func indices:
        f.write_vu32(len(self.refs))
        for ref in self.refs:
            assert ref.space == 'func'
            f.write_vu32(ref.index)

    def _from_reader(self, reader):
        self.ref = Ref('table', index=reader.read_uint())
        self.offset = reader.read_expression()

        count = reader.read_uint()
        indexes = []
        for _ in range(count):
            indexes.append(Ref('func', index=reader.read_uint()))
        self.refs = indexes


class Data(Definition):
    """ Data to include in the module.

    Flat form and abbreviations:

    * Data can be defined inline inside Memory expressions, this is resolved
      by the Module class.

    Attributes:

    * ref: the memory id that this data applies to.
    * offset: the byte offset, expressed as an instruction (i.e. i32.const)
    * data: the binary data as a bytes object.
    """

    __slots__ = ('ref', 'offset', 'data')

    def _from_args(self, ref, offset, data):
        # Check
        assert isinstance(offset, list)
        if not isinstance(data, bytes):
            raise TypeError('data must be bytes')
        # Set
        self.ref = check_id(ref)
        assert isinstance(self.ref, Ref)
        self.offset = offset
        self.data = data

    def to_string(self):
        ref = '' if self.ref.is_zero else ' %s' % self.ref
        offset = ' '.join(i.to_string() for i in self.offset)
        data_as_str = bytes2datastring(self.data)  # repr(self.data)[2:-1]
        return '(data%s %s "%s")' % (ref, offset, data_as_str)

    def _to_writer(self, f):
        assert self.ref.space == 'memory'
        f.write_vu32(self.ref.index)

        # Encode offset as expression followed by end instruction
        f.write_expression(self.offset)

        # Encode as u32 length followed by data:
        f.write_vu32(len(self.data))
        f.write(self.data)

    def _from_reader(self, reader):
        self.ref = Ref('memory', index=reader.read_uint())
        self.offset = reader.read_expression()
        self.data = reader.read_bytes()


class Custom(Definition):
    """ Custom binary data.
    """
    
    __slots__ = ('name', 'data')
    
    def _from_args(self, name, data):
        assert isinstance(name, str)
        assert isinstance(data, bytes)
        self.name = name
        self.data = data

    def to_string(self):
        raise NotImplementedError('Cannot convert custom section to string.')
    
    def _to_writer(self, f):
        f.write_str(self.name)
        f.write(self.data)

    def _from_reader(self, reader):
        raise NotImplementedError()  # Module does it, because need nbytes of section


# Do some validation on the classes
DEFINITION_CLASSES = {}  # classes that represent a WASM module definition

def _validate():
    names1 = set()
    for name, value in globals().items():
        if isinstance(value, type) and issubclass(value, Definition):
            if value is not Definition:
                names1.add(name.lower())
                DEFINITION_CLASSES[name.lower()] = value

    names2 = set(SECTION_IDS).difference(['code', 'function'])
    if names1 != names2:
        raise RuntimeError('Class validation failed:' +
            '\n  Unknown field clases: %s' % names1.difference(names2) +
            '\n  Missing field classes: %s' % names2.difference(names1)
            )

_validate()

__all__ = ['WASMComponent', 'Instruction', 'BlockInstruction',
           'Module', 'Definition']
__all__ += [cls.__name__ for cls in DEFINITION_CLASSES.values()]
