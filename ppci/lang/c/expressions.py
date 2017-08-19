""" Expression nodes """

from ..generic.nodes import Expression
from . import types


class CExpression(Expression):
    # TODO: every expression must have a type.
    def __init__(self, typ, lvalue, location):
        super().__init__(location)
        assert isinstance(typ, types.CType)
        self.typ = typ
        self.lvalue = lvalue


class FunctionCall(Expression):
    """ Function call """
    def __init__(self, function, args, location):
        super().__init__(location)
        self.function = function
        self.name = function.name
        self.args = args

    def __repr__(self):
        return 'FunctionCall {}'.format(self.name)


class Ternop(CExpression):
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


class Binop(CExpression):
    """ Binary operator """
    def __init__(self, a, op, b, typ, lvalue, location):
        super().__init__(typ, lvalue, location)
        assert isinstance(a, Expression)
        assert isinstance(b, Expression)
        self.a = a
        self.op = op
        self.b = b

    def __repr__(self):
        return 'BinaryOp {}'.format(self.op)


class Unop(CExpression):
    """ Unary operator """
    def __init__(self, op, a, typ, lvalue, location):
        super().__init__(typ, lvalue, location)
        assert isinstance(a, Expression)
        self.a = a
        self.op = op

    def __repr__(self):
        return 'UnaryOp {}'.format(self.op)


class Cast(Expression):
    def __init__(self, to_typ, expr, location):
        super().__init__(location)
        self.to_typ = to_typ
        self.expr = expr

    def __repr__(self):
        return 'Cast {}'.format(self.to_typ)


class ImplicitCast(Cast):
    pass


class Sizeof(Expression):
    """ Sizeof operator """
    def __init__(self, sizeof_typ, location):
        super().__init__(location)
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


class FieldSelect(Expression):
    """ Select a field in a struct """
    def __init__(self, base, field, location):
        super().__init__(location)
        self.base = base
        self.field = field

    def __str__(self):
        return 'Field select .{}'.format(self.field.name)


class VariableAccess(Expression):
    def __init__(self, variable, location):
        super().__init__(location)
        self.variable = variable
        self.name = variable.name

    def __repr__(self):
        return 'Id {}'.format(self.name)


class Literal(CExpression):
    def __init__(self, value, typ, location):
        super().__init__(typ, False, location)
        self.value = value

    def __repr__(self):
        return 'Literal {}'.format(self.value)


class CharLiteral(Literal):
    """ A character literal """
    def __repr__(self):
        return 'Char literal {}'.format(self.value)


class NumericLiteral(Literal):
    def __repr__(self):
        return 'Numeric literal {}'.format(self.value)


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
