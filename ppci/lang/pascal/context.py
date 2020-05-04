import logging
import struct
from ...common import CompilerError
from .symbol_table import Scope
from .nodes import symbols, types, expressions


class Context:
    """ A global context for all pascal objects of a program.

    This is a replacement for the otherwise global variables during
    the processing of pascal code.
    """

    logger = logging.getLogger("pascal.context")

    def __init__(self, arch_info):
        self.root_scope = create_top_scope(arch_info)
        self.programs = []
        self.units = []

    def add_program(self, program):
        self.programs.append(program)

    def get_type(self, name):
        if isinstance(name, types.Type):
            typ = name
        else:
            typ = self.root_scope.get_symbol(name)
            assert isinstance(typ, symbols.DefinedType)

        if isinstance(typ, symbols.DefinedType):
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
            elif isinstance(a, types.FunctionType):
                return (
                    len(a.parameter_types) == len(b.parameter_types)
                    and all(
                        self.equal_types(pa, pb)
                        for pa, pb in zip(a.parameter_types, b.parameter_types)
                    )
                    and self.equal_types(a.return_type, b.return_type)
                )
            elif isinstance(a, types.ProcedureType):
                return len(a.parameter_types) == len(
                    b.parameter_types
                ) and all(
                    self.equal_types(pa, pb)
                    for pa, pb in zip(a.parameter_types, b.parameter_types)
                )
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
            elif isinstance(a, types.EnumType):
                return a is b
            elif isinstance(a, types.SetType):
                return self.equal_types(a.element_type, b.element_type)
            else:
                raise NotImplementedError(str(type(a)))

        return False

    def eval_const_expr(self, expr):
        """ Evaluate constant expression. """
        if isinstance(expr, expressions.Literal):
            if expr.typ.is_integer:
                value = int(expr.val)
            else:
                raise NotImplementedError()
        elif isinstance(expr, expressions.VariableAccess):
            if isinstance(expr.variable, symbols.Constant):
                value = self.eval_const_expr(expr.variable.value)
            else:
                raise NotImplementedError()
        else:
            raise NotImplementedError()
        return value

    def size_of(self, typ):
        # TODO:
        int_size = 8
        if isinstance(typ, types.IntegerType):
            size = int_size
        elif isinstance(typ, types.EnumType):
            size = int_size
        elif isinstance(typ, types.PointerType):
            size = int_size
        elif isinstance(typ, types.ArrayType):
            element_count = 1
            for dimension in typ.dimensions:
                if isinstance(dimension, types.SubRange):
                    upper = self.eval_const_expr(dimension.upper)
                    lower = self.eval_const_expr(dimension.lower)
                    cardinality = upper - lower
                elif isinstance(dimension, types.EnumType):
                    cardinality = len(dimension.values)
                else:
                    cardinality = int(dimension)
                element_count *= cardinality
            size = self.size_of(typ.element_type) * element_count
        else:
            raise NotImplementedError()
        return size

    def alignment(self, typ):
        # TODO
        return 8

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
    char_type = types.UnsignedIntegerType(1)
    register_type("integer", int_type)
    register_type("char", char_type)
    register_type("boolean", types.SignedIntegerType(int_size))

    # TODO: floating point?
    register_type("real", types.SignedIntegerType(int_size))

    # TODO: text file type?
    register_type("text", types.FileType(char_type, None))

    # Construct string type from others:
    len_field = types.RecordField("len", int_type, None)
    txt = types.RecordField(
        "txt", types.ArrayType(char_type, 0, False, None), None
    )
    string_type = types.PointerType(types.RecordType([len_field, txt], None))
    register_type("string", string_type)

    def add_constant(name, typ, value):
        constant = symbols.Constant(name, typ, value, None)
        scope.add_symbol(constant)

    max_int_value = 2 ** 31
    add_constant("maxint", int_type, max_int_value)

    # built-in functionsL
    def add_builtin_function(name):
        typ = types.FunctionType([], None)
        f = symbols.BuiltIn(name, typ)
        scope.add_symbol(f)
        # f.builtin = name

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
        typ = types.ProcedureType([])
        p = symbols.BuiltIn(name, typ)
        scope.add_symbol(p)
        # p.builtin = name

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
