""" Expression nodes """

# pylint: disable=R0903

from ...common import SourceLocation
from . import types


class CExpression:
    """ Base C expression with a type and location """

    __slots__ = ("location", "typ", "lvalue")

    def __init__(self, typ, lvalue, location: SourceLocation):
        assert isinstance(typ, types.CType)
        self.location = location
        self.typ = typ
        self.lvalue = lvalue


class FunctionCall(CExpression):
    """ Function call """

    __slots__ = ("callee", "args")

    def __init__(self, callee, args, typ, lvalue, location):
        super().__init__(typ, lvalue, location)
        self.callee = callee
        self.args = args

    def __repr__(self):
        return "FunctionCall"


class TernaryOperator(CExpression):
    """ Ternary operator """

    __slots__ = ("a", "op", "b", "c")

    def __init__(self, a, op, b, c, typ, lvalue, location):
        super().__init__(typ, lvalue, location)
        assert isinstance(a, CExpression)
        assert isinstance(b, CExpression)
        assert isinstance(c, CExpression)
        assert op == "?"
        self.a = a
        self.op = op
        self.b = b
        self.c = c

    def __repr__(self):
        return "TernOp {}".format(self.op)


class Initializer(CExpression):
    """ Initial value base class. """

    pass


class InitializerList(Initializer):
    """ Base initializer list. """

    pass


class StructInitializer(InitializerList):
    """ Struct initializer """

    def __init__(self, typ, location):
        super().__init__(typ, False, location)
        self.values = {}

    def __repr__(self):
        if len(self.values) > 4:
            return "Struct-initializer-with-{}-fields".format(len(self.values))
        else:
            return "Struct initializer: {}".format(self.values)


class UnionInitializer(InitializerList):
    """ Initial value for a union """

    def __init__(self, typ, location):
        super().__init__(typ, False, location)
        self.field = None
        self.value = None

    def __repr__(self):
        return "Union-initializer({}={})".format(self.field, self.value)


class ArrayInitializer(InitializerList):
    """ Initial value for array's """

    def __init__(self, typ, values, location):
        super().__init__(typ, False, location)
        self.values = values

    def __repr__(self):
        if len(self.values) > 4:
            return "Array-init({}, ...)".format(self.values[:4])
        else:
            return "Array-init({})".format(self.values)


class ImplicitInitialValue(Initializer):
    """ Uninitialized value. """

    pass


class BinaryOperator(CExpression):
    """ Binary operator """

    __slots__ = ("a", "op", "b")

    def __init__(self, a, op, b, typ, lvalue, location):
        super().__init__(typ, lvalue, location)
        assert isinstance(a, CExpression)
        assert isinstance(b, CExpression)
        self.a = a
        self.op = op
        self.b = b

    def __repr__(self):
        return "BinaryOperator {} <{}>".format(self.op, self.typ)


class UnaryOperator(CExpression):
    """ Unary operator """

    __slots__ = ("a", "op")

    def __init__(self, op, a, typ, lvalue, location):
        super().__init__(typ, lvalue, location)
        assert isinstance(a, CExpression)
        self.a = a
        self.op = op

    def __repr__(self):
        return "UnaryOperator {}".format(self.op)


class Cast(CExpression):
    """ A cast operation """

    __slots__ = ("to_typ", "expr")

    def __init__(self, expr, typ, lvalue, location):
        super().__init__(typ, lvalue, location)
        self.to_typ = typ
        self.expr = expr

    def __repr__(self):
        return "Cast {}".format(self.to_typ)

    def is_array_decay(self):
        """ Test if this cast is a pointer decay. """
        return self.to_typ.is_pointer and self.expr.typ.is_array


class ImplicitCast(Cast):
    """ An implicit cast """

    pass


class Sizeof(CExpression):
    """ Sizeof operator """

    def __init__(self, sizeof_typ, typ, lvalue, location):
        super().__init__(typ, lvalue, location)
        self.sizeof_typ = sizeof_typ

    def __repr__(self):
        return "Sizeof {}".format(self.sizeof_typ)


class ArrayIndex(CExpression):
    """ Array indexing """

    __slots__ = ("base", "index")

    def __init__(self, base, index, typ, lvalue, location):
        super().__init__(typ, lvalue, location)
        self.base = base
        self.index = index

    def __repr__(self):
        return "Array index"


class FieldSelect(CExpression):
    """ Select a field in a struct """

    __slots__ = ("base", "field")

    def __init__(self, base, field, typ, lvalue, location):
        super().__init__(typ, lvalue, location)
        self.base = base
        self.field = field

    def __str__(self):
        return "Field select .{} <{}>".format(self.field.name, self.typ)


class VariableAccess(CExpression):
    """ Access to a variable """

    def __init__(self, variable, typ, lvalue, location):
        super().__init__(typ, lvalue, location)
        self.variable = variable
        self.name = variable.name

    def __repr__(self):
        return "Id {} <{}>".format(self.name, self.typ)


class Literal(CExpression):
    """ Literal value such as 'h' or 1.22 """

    __slots__ = ("value",)

    def __init__(self, value, typ, lvalue, location):
        super().__init__(typ, lvalue, location)
        self.value = value

    def __repr__(self):
        return "Literal {} <{}>".format(self.value, self.typ)


class CharLiteral(Literal):
    """ A character literal """

    def __init__(self, value, typ, location):
        super().__init__(value, typ, False, location)

    def __repr__(self):
        return "Char literal '{}'".format(self.value)


class NumericLiteral(Literal):
    """ A numeric literal """

    def __init__(self, value, typ, location):
        super().__init__(value, typ, False, location)

    def __repr__(self):
        return "Numeric literal {} <{}>".format(self.value, self.typ)


class StringLiteral(Literal):
    """ A string literal """

    def __init__(self, value, typ, location):
        super().__init__(value, typ, True, location)

    def __repr__(self):
        return 'String literal "{}"'.format(self.value)

    def to_bytes(self):
        """ Convert this string literal to zero terminated byte string. """
        encoding = "latin1"
        data = self.value.encode(encoding) + bytes([0])
        return data


class CompoundLiteral(CExpression):
    """ Compound literal available since C99.

    For example:
    (char[]){'a', 'b'}

    See also:
    - https://en.cppreference.com/w/c/language/compound_literal
    """

    def __init__(self, typ, init, location):
        super().__init__(typ, True, location)
        self.init = init


class BuiltIn(CExpression):
    """ Build in function """

    pass


class BuiltInVaStart(BuiltIn):
    """ Built-in function va_start """

    def __init__(self, arg_pointer, location):
        super().__init__(arg_pointer.typ, False, location)
        self.arg_pointer = arg_pointer


class BuiltInVaArg(BuiltIn):
    """ Built-in function va_arg """

    def __init__(self, arg_pointer, typ, location):
        super().__init__(typ, False, location)
        self.arg_pointer = arg_pointer


class BuiltInVaCopy(BuiltIn):
    """ Built-in function va_copy """

    def __init__(self, dest, src, location):
        super().__init__(dest.typ, False, location)
        self.dest = dest
        self.src = src


class BuiltInOffsetOf(BuiltIn):
    """ Built-in function offsetof """

    def __init__(self, query_typ, member, typ, location):
        super().__init__(typ, False, location)
        self.query_typ = query_typ
        self.member = member
