import logging
import struct
from ...common import CompilerError
from .symbol_table import Scope
from .nodes import symbols, types


class Context:
    """ A global context for all pascal objects of a program.

    This is a replacement for the otherwise global variables during
    the processing of pascal code.
    """

    logger = logging.getLogger("pascal.context")

    def __init__(self, arch_info):
        self.root_scope = create_top_scope(arch_info)
        self.var_map = {}
        self.programs = []
        self.units = []

    def add_program(self, program):
        self.programs.append(program)

    def get_type(self, name, reveil_defined=True):
        if isinstance(name, types.Type):
            typ = name
        else:
            typ = self.root_scope.get_symbol(name)
            assert isinstance(typ, symbols.DefinedType)

        if isinstance(typ, symbols.DefinedType) and reveil_defined:
            typ = self.get_type(typ.typ)

        return typ

    def equal_types(self, a, b, byname=False):
        """ Check if two types are equal """
        a = self.get_type(a)
        b = self.get_type(b)
        if type(a) is type(b):
            if isinstance(a, types.IntegerType):
                return a.bits == b.bits
            elif isinstance(a, types.PointerType):
                # If a pointed type is detected, stop structural
                # equivalence:
                return self.equal_types(a.ptype, b.ptype, byname=True)
            elif isinstance(a, symbols.DefinedType):
                # Try by name in case of defined types:
                return a.name == b.name
            elif isinstance(a, types.RecordType):
                if len(a.fields) != len(b.fields):
                    return False
                return all(
                    self.equal_types(am.typ, bm.typ)
                    for am, bm in zip(a.fields, b.fields)
                )
            elif isinstance(a, types.ArrayType):
                return self.equal_types(a.element_type, b.element_type)
            else:
                raise NotImplementedError(str(type(a)))

        return False

    def get_common_type(self, a, b, loc):
        """ Determine the greatest common type.

        This is used for coercing binary operators.
        For example
            int + float -> float
            byte + int -> int
            byte + byte -> byte
            pointer to x + int -> pointer to x
        """
        intType = self.get_type("integer")
        charType = self.get_type("char")
        table = {
            (intType, intType): intType,
            (intType, charType): intType,
            (charType, intType): intType,
            (charType, charType): charType,
            (intType, types.PointerType): intType,
        }
        typ_a = self.get_type(a.typ)
        typ_b = self.get_type(b.typ)

        if self.equal_types(typ_a, typ_b):
            return typ_a
        # Handle pointers:
        if isinstance(typ_a, types.PointerType) and self.equal_types(
            typ_b, "integer"
        ):
            return typ_a

        # Handle non-pointers:
        key = (typ_a, typ_b)
        if key not in table:
            raise CompilerError(
                "Types {} and {} do not commute".format(typ_a, typ_b), loc
            )
        return table[(typ_a, typ_b)]

    def pack_string(self, txt):
        """ Pack a string an int as length followed by text data """
        length = self.pack_int(len(txt))
        data = txt.encode("ascii")
        return length + data

    def pack_int(self, v, bits=None, signed=True):
        if bits is None:
            bits = self.get_type("integer").byte_size * 8
        mapping = {
            (8, False): "<B",
            (8, True): "<b",
            (16, False): "<H",
            (16, True): "<h",
            (32, False): "<I",
            (32, True): "<i",
            (64, False): "<Q",
            (64, True): "<q",
        }
        fmt = mapping[(bits, signed)]
        return struct.pack(fmt, v)


def create_top_scope(arch_info):
    """ Create a scope that is the root of the scope tree.

    This includes the built-in types.
    """
    scope = Scope()

    # buildin types:
    def register_type(name, typ):
        typedef = symbols.DefinedType(name, typ, None)
        scope.add_symbol(typedef)

    int_size = arch_info.get_size("int")

    int_type = types.SignedIntegerType(int_size)
    char_type = types.SignedIntegerType(1)
    register_type("integer", int_type)
    register_type("char", char_type)
    register_type("boolean", types.SignedIntegerType(int_size))

    # TODO: floating point?
    register_type("real", types.SignedIntegerType(int_size))

    # TODO: text file type?
    register_type("text", types.PointerType(int_size))

    # Construct string type from others:
    len_field = types.RecordField("len", int_type, None)
    txt = types.RecordField(
        "txt", types.ArrayType(char_type, 0, False, None), None
    )
    string_type = types.PointerType(types.RecordType([len_field, txt], None))
    register_type("string", string_type)

    max_int_value = 2 ** 31

    max_int = symbols.Constant("maxint", None, max_int_value, None)
    scope.add_symbol(max_int)

    # built-in functionsL
    def add_builtin_function(name):
        f = symbols.Function(name, None)
        scope.add_symbol(f)
        f.typ = types.FunctionType([], None)

    add_builtin_function("abs")
    add_builtin_function("sqr")
    add_builtin_function("sin")
    add_builtin_function("cos")
    add_builtin_function("exp")
    add_builtin_function("ln")
    add_builtin_function("sqrt")
    add_builtin_function("arctan")

    add_builtin_function("ord")
    add_builtin_function("chr")
    add_builtin_function("succ")
    add_builtin_function("pred")
    add_builtin_function("odd")

    add_builtin_function("trunc")
    add_builtin_function("round")

    def add_builtin_procedure(name):
        p = symbols.Procedure(name, None)
        scope.add_symbol(p)
        p.typ = types.ProcedureType([])

    add_builtin_procedure("new")
    add_builtin_procedure("dispose")
    add_builtin_procedure("rewrite")
    add_builtin_procedure("reset")
    add_builtin_procedure("read")
    add_builtin_procedure("readln")
    add_builtin_procedure("write")
    add_builtin_procedure("writeln")
    add_builtin_procedure("get")
    add_builtin_procedure("put")
    add_builtin_function("eof")
    add_builtin_function("eoln")

    add_builtin_procedure("pack")
    add_builtin_procedure("unpack")

    return scope
