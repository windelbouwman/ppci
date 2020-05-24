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

from ..lang.sexpr import parse_sexpr


def this_is_js():
    return False  # For PyScript


logger = logging.getLogger("wasm")

# The toplevel field names that can be in a module, in their preferred order.

SECTION_IDS = {  # Note: order matters!
    "custom": 0,
    "type": 1,
    "import": 2,
    "function": 3,  # this section maps funcs to types
    "table": 4,
    "memory": 5,
    "global": 6,
    "export": 7,
    "start": 8,
    "elem": 9,
    "func": 10,  # the field is called func,
    "code": 10,  # but the section is called code
    "data": 11,
}

if sys.version_info < (3, 6):
    SECTION_IDS = OrderedDict(sorted(SECTION_IDS.items(), key=lambda i: i[1]))


def check_id(id):
    if isinstance(id, int):
        if not id >= 0:
            raise ValueError("Integer id must be >= 0.")
    elif isinstance(id, str):
        if not id.startswith("$"):
            raise ValueError("String id must start with $.")
    elif isinstance(id, Ref):
        pass
    else:
        raise ValueError("Id must be int or str.")
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
            arg = input[0]
            if isinstance(arg, tuple):
                return self._from_tuple(arg)
            elif isinstance(arg, str) and "(" in arg:
                return self._from_string(arg)
            elif isinstance(arg, bytes):
                return self._from_bytes(arg)
            elif hasattr(arg, "read"):
                assert not hasattr(arg, "read_module")
                return self._from_file(arg)

        # Else, more direct instantiation
        self._from_args(*input)

    def __repr__(self):
        return "<WASM-%s>" % (self.__class__.__name__)

    def show(self):
        """ Print the S-expression of the component.
        """
        print(self.to_string())

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
            "type",
            "func",
            "memory",
            "table",
            "global",
            "local",
            "label",
        ]
        if space not in valid_spaces:
            raise ValueError("space must be one of {}".format(valid_spaces))
        self.space = space
        if index is None and name is None:
            raise ValueError("You must provide index or name for a Ref")
        self.index = index
        self.name = name

    def __str__(self):
        # Preferably use a name, if available:
        if self.name:
            return self.name
        else:
            return str(self.index)

    def __repr__(self):
        return "Ref(space={},index={},name={})".format(
            self.space, self.index, self.name
        )

    def resolve(self, id_maps):
        if self.index is None:
            id_map = id_maps[self.space]
            if self.name in id_map:
                return id_map[self.name]
            else:
                raise ValueError("Cannot resolve {}".format(repr(self)))
        else:
            return self.index

    @property
    def is_zero(self):
        """ Check if we refer to element 0 """
        if self.name:
            return self.name == "$0"
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

    __slots__ = ("id", "definitions")  # id is only for documentation purposes

    def _from_args(self, *definitions):
        self._from_tuple(definitions)

    def _from_tuple(self, t):
        """ Initialize from tuple.
        """

        from .text import load_tuple

        load_tuple(self, t)

    def _from_file(self, f):
        from .binary.reader import BinaryFileReader

        reader = BinaryFileReader(f)
        reader.read_module(self)

    def to_string(self):
        from .text.writer import TextWriter

        writer = TextWriter()
        return writer.write_module(self)

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
        from .binary.writer import BinaryFileWriter

        writer = BinaryFileWriter(f)
        writer.write_module(self)

    # Module-specific stuff

    def __iter__(self):
        return iter(self.definitions)

    def __getitem__(self, i):
        if isinstance(i, int):
            return self.definitions[i]
        elif isinstance(i, str):
            i = "func" if i == "code" else i
            return [d for d in self.definitions if d.__name__ == i]
        else:
            raise IndexError("Module can only be indexed with int and str")

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
        assert not definitions.pop("code")  # use func instead
        assert not definitions.pop("function")  # this section is implicit
        return definitions

    def show_interface(self):
        """ Show the (signature of) imports and exports in a human
        friendly manner.
        """
        types = self["type"]
        imports = self["import"]
        exports = self["export"]
        functions = self["func"]
        n_func_imports = sum(c.kind == "func" for c in imports)
        print("Imports:")
        for c in imports:
            if c.kind == "func":
                sig = types[c.info[0].index]
                params_s = ", ".join([p[1] for p in sig.params])
                result_s = ", ".join([r for r in sig.results])
                print(
                    "  {}.{}:".format(c.modname, c.name).ljust(20),
                    "[{}] -> [{}]".format(params_s, result_s),
                )
            else:
                print("  {}:".format(c.kind).ljust(20), '"{}"'.format(c.name))

        print("Exports:")
        for c in exports:
            if c.kind == "func":
                func = functions[c.ref.index - n_func_imports]
                sig = types[func.ref.index]
                params_s = ", ".join([p[1] for p in sig.params])
                result_s = ", ".join([r for r in sig.results])
                print(
                    "  {}:".format(c.name).ljust(20),
                    "[{}] -> [{}]".format(params_s, result_s),
                )
            else:
                print("  {}:".format(c.kind).ljust(20), '"{}"'.format(c.name))


class Instruction(WASMComponent):
    """ Class ro represent an instruction (an opcode plus arguments). """

    __slots__ = ("opcode", "args")

    def _from_args(self, opcode, *args):
        for arg in args:
            assert isinstance(arg, (str, int, float, Ref, list))

        self.opcode = opcode
        self.args = args

    def __repr__(self):
        return "<Instruction %s>" % self.opcode

    def __getitem__(self, i):
        # Make it feel a bit like a named tuple
        return getattr(self, self.__slots__[i])

    def to_string(self):
        from .text.writer import TextWriter

        writer = TextWriter()
        return writer.write_instruction(self)


class BlockInstruction(Instruction):
    """ An instruction that represents a block of instructions.
    (block, loop or if). The args consists of a single element indicating the
    result type. It can optionally have an id.
    """

    __slots__ = ("id",)  # id can be None

    def _from_args(self, opcode, *args):
        if len(args) == 2:
            id, *args = args
        else:
            id = None
        self.id = id
        return super()._from_args(opcode, *args)

    def to_string(self):
        from .text.writer import TextWriter

        writer = TextWriter()
        return writer.write_block_instruction(self)


# Definition classes


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

    __slots__ = ("id", "params", "results")

    def _from_args(self, id, params, results):
        assert isinstance(id, (int, str))
        assert isinstance(params, (tuple, list))
        assert isinstance(results, (tuple, list))
        assert all(isinstance(el, tuple) and len(el) == 2 for el in params)
        assert all(isinstance(el, str) for el in results)
        self.id = check_id(id)
        self.params = tuple(params)
        self.results = tuple(results)

    def to_string(self):
        from .text.writer import TextWriter

        writer = TextWriter()
        writer.write_type_definition(self)
        return writer.finish()


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
        * table: ('funcref', min, max), where max can be None.
        * memory: (min, max), where max can be None.
        * global: (typ, mutable)
    """

    __slots__ = ("modname", "name", "kind", "id", "info")

    def _from_args(self, modname, name, kind, id, info):
        assert kind in ("func", "table", "memory", "global")
        assert isinstance(info, tuple)
        self.modname = modname
        self.name = name
        self.kind = kind
        self.id = check_id(id)
        self.info = info

    def to_string(self):
        from .text.writer import TextWriter

        writer = TextWriter()
        writer.write_import_definition(self)
        return writer.finish()


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
    * kind: the kind of data stored in the table, only 'funcref' in v1.
    * min: the minimum (initial) table size.
    * max: the maximum table size, or None.

    """

    __slots__ = ("id", "kind", "min", "max")

    def _from_args(self, id, kind, min, max):
        self.id = check_id(id)
        assert kind in ("funcref",)  # More kinds in future versions
        self.kind = kind
        self.min = min
        self.max = max

    def to_string(self):
        from .text.writer import TextWriter

        writer = TextWriter()
        writer.write_table_definition(self)
        return writer.finish()


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

    __slots__ = ("id", "min", "max")

    def _from_args(self, id, min, max=None):
        # assert isinstance(id, str)  # otherwise hard to dinstinguis from ints
        self.id = check_id(id)
        self.min = min
        self.max = max

    def to_string(self):
        from .text.writer import TextWriter

        writer = TextWriter()
        writer.write_memory_definition(self)
        return writer.finish()


class Global(Definition):
    """ A global variable.

    Attributes:

    * id: the id of this global definition in the globals name/index space.
    * typ: the value type of the global.
    * mutable: whether this global is mutable (can hurt performance).
    * init: an instruction to initialize the global (e.g. a i32.const).

    """

    __slots__ = ("id", "typ", "mutable", "init")

    def _from_args(self, id, typ, mutable, init):
        assert isinstance(init, list)
        self.id = check_id(id)
        self.typ = typ
        self.mutable = bool(mutable)
        self.init = init

    def to_string(self):
        from .text.writer import TextWriter

        writer = TextWriter()
        writer.write_global_definition(self)
        return writer.finish()


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

    __slots__ = ("name", "kind", "ref")  # (export "name" (func $ref))

    def _from_args(self, name, kind, ref):
        assert isinstance(ref, Ref)
        assert kind in ("func", "table", "memory", "global")
        self.name = name
        self.kind = kind
        self.ref = ref

    def to_string(self):
        return '(export "%s" (%s %s))' % (self.name, self.kind, self.ref)


class Start(Definition):
    """ Define the index of the function to call at init-time. The func must
    have zero params and return values. There must be at most 1 start
    definition.

    Attributes:

    * ref: the reference to the function to mark as the start function.

    """

    __slots__ = ("ref",)

    def _from_args(self, ref):
        self.ref = check_id(ref)

    def to_string(self):
        return "(start %s)" % self.ref


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

    __slots__ = ("id", "ref", "locals", "instructions")  # ref to type

    def _from_args(self, id, ref, locals, instructions):
        if not isinstance(ref, Ref):
            raise TypeError("ref must be of type Ref")
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
            blocktypes = ("block", "loop", "if")
            self.instructions = [
                (BlockInstruction if i[0] in blocktypes else Instruction)(*i)
                for i in instructions
            ]

    def __repr__(self):
        return "<WASM-Func %s>" % (self.id)

    def to_string(self):
        """ Render function def as text """
        from .text.writer import TextWriter

        writer = TextWriter()
        writer.write_func_definition(self)
        return writer.finish()


class Elem(Definition):
    """ Define elements to populate a table.

    Flat form and abbreviations:

    * Elements can be defined inline inside Table expressions, this is resolved
      by the Module class.

    Attributes:

    * ref: the table id that this element applies to.
    * offset: the element offset, expressed as an instruction list
      (i.e. [i32.const, end])
    * refs: a list of function references.
    """

    __slots__ = ("ref", "offset", "refs")

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
        from .text.writer import TextWriter

        writer = TextWriter()
        writer.write_elem_definition(self)
        return writer.finish()


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

    __slots__ = ("ref", "offset", "data")

    def _from_args(self, ref, offset, data):
        # Check
        assert isinstance(offset, list)
        if not isinstance(data, bytes):
            raise TypeError("data must be bytes")
        # Set
        self.ref = check_id(ref)
        assert isinstance(self.ref, Ref)
        self.offset = offset
        self.data = data

    def to_string(self):
        from .text.writer import TextWriter

        writer = TextWriter()
        writer.write_data_definition(self)
        return writer.finish()


class Custom(Definition):
    """ Custom binary data.
    """

    __slots__ = ("name", "data")

    def _from_args(self, name, data):
        assert isinstance(name, str)
        assert isinstance(data, bytes)
        self.name = name
        self.data = data

    def to_string(self):
        raise NotImplementedError("Cannot convert custom section to string.")


# Do some validation on the classes
DEFINITION_CLASSES = {}  # classes that represent a WASM module definition


def _validate():
    names1 = set()
    for name, value in globals().items():
        if isinstance(value, type) and issubclass(value, Definition):
            if value is not Definition:
                names1.add(name.lower())
                DEFINITION_CLASSES[name.lower()] = value

    names2 = set(SECTION_IDS).difference(["code", "function"])
    if names1 != names2:
        raise RuntimeError(
            "Class validation failed:"
            + "\n  Unknown field clases: %s" % names1.difference(names2)
            + "\n  Missing field classes: %s" % names2.difference(names1)
        )


_validate()

__all__ = [
    "WASMComponent",
    "Instruction",
    "BlockInstruction",
    "Module",
    "Definition",
]
__all__ += [cls.__name__ for cls in DEFINITION_CLASSES.values()]
