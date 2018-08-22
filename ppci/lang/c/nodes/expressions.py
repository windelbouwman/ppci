""" Expression nodes """

# pylint: disable=R0903


from ...generic.nodes import Expression
from . import types


class CExpression(Expression):
    """ Base C expression with a type and location """
    def __init__(self, typ, lvalue, location):
        super().__init__(location)
        assert isinstance(typ, types.CType)
        self.typ = typ
        self.lvalue = lvalue


class FunctionCall(CExpression):
    """ Function call """
    def __init__(self, callee, args, typ, lvalue, location):
        super().__init__(typ, lvalue, location)
        self.callee = callee
        self.args = args

    def __repr__(self):
        return 'FunctionCall'


class TernaryOperator(CExpression):
    """ Ternary operator """
    def __init__(self, a, op, b, c, typ, lvalue, location):
        super().__init__(typ, lvalue, location)
        assert isinstance(a, Expression)
        assert isinstance(b, Expression)
        assert isinstance(c, Expression)
        assert op == '?'
        self.a = a
        self.op = op
        self.b = b
        self.c = c

    def __repr__(self):
        return 'TernOp {}'.format(self.op)


class BinaryOperator(CExpression):
    """ Binary operator """
    def __init__(self, a, op, b, typ, lvalue, location):
        super().__init__(typ, lvalue, location)
        assert isinstance(a, Expression)
        assert isinstance(b, Expression)
        self.a = a
        self.op = op
        self.b = b

    def __repr__(self):
        return "BinaryOperator {} <{}>".format(self.op, self.typ)


class UnaryOperator(CExpression):
    """ Unary operator """
    def __init__(self, op, a, typ, lvalue, location):
        super().__init__(typ, lvalue, location)
        assert isinstance(a, Expression)
        self.a = a
        self.op = op

    def __repr__(self):
        return 'UnaryOperator {}'.format(self.op)


class Cast(CExpression):
    """ A cast operation """
    def __init__(self, expr, typ, lvalue, location):
        super().__init__(typ, lvalue, location)
        self.to_typ = typ
        self.expr = expr

    def __repr__(self):
        return 'Cast {}'.format(self.to_typ)


class ImplicitCast(Cast):
    """ An implicit cast """
    pass


class Sizeof(CExpression):
    """ Sizeof operator """
    def __init__(self, sizeof_typ, typ, lvalue, location):
        super().__init__(typ, lvalue, location)
        self.sizeof_typ = sizeof_typ

    def __repr__(self):
        return 'Sizeof {}'.format(self.sizeof_typ)


class ArrayIndex(CExpression):
    """ Array indexing """
    def __init__(self, base, index, typ, lvalue, location):
        super().__init__(typ, lvalue, location)
        self.base = base
        self.index = index

    def __repr__(self):
        return 'Array index'


class FieldSelect(CExpression):
    """ Select a field in a struct """
    def __init__(self, base, field, typ, lvalue, location):
        super().__init__(typ, lvalue, location)
        self.base = base
        self.field = field

    def __str__(self):
        return 'Field select .{} <{}>'.format(self.field.name, self.typ)


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
    def __init__(self, value, typ, location):
        super().__init__(typ, False, location)
        self.value = value

    def __repr__(self):
        return "Literal {} <{}>".format(self.value, self.typ)


class CharLiteral(Literal):
    """ A character literal """
    def __repr__(self):
        return 'Char literal {}'.format(self.value)


class NumericLiteral(Literal):
    """ A numeric literal """
    def __repr__(self):
        return "Numeric literal {} <{}>".format(self.value, self.typ)


class StringLiteral(Literal):
    """ A string literal """
    def __repr__(self):
        return 'String literal {}'.format(self.value)


class InitializerList(Expression):
    """ A c style initializer list """
    def __init__(self, elements, loc):
        super().__init__(loc)
        self.elements = elements

    def __repr__(self):
        return 'Initializer list'

    def __len__(self):
        return len(self.elements)


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


class BuiltInOffsetOf(BuiltIn):
    """ Built-in function offsetof """
    def __init__(self, query_typ, member, typ, location):
        super().__init__(typ, False, location)
        self.query_typ = query_typ
        self.member = member
