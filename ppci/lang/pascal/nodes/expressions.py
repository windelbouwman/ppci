""" Expression AST nodes.
"""

from .symbols import Variable
from .types import Type


class Expression:
    """ Expression base class """

    is_bool = False

    def __init__(self, typ, location):
        if not isinstance(typ, Type):
            raise ValueError("typ must be some Type")
        self.typ = typ
        self.location = location


class Sizeof(Expression):
    """ Sizeof built-in contraption """

    def __init__(self, typ: Type, location):
        super().__init__(None, location)
        self.query_typ = typ


class Deref(Expression):
    """ Data pointer dereference """

    def __init__(self, ptr, typ, location):
        super().__init__(typ, location)
        assert isinstance(ptr, Expression)
        self.ptr = ptr

    def __repr__(self):
        return "DEREF {}".format(self.ptr)


class TypeCast(Expression):
    """ Type cast expression to another type """

    def __init__(self, to_type, x, location):
        super().__init__(to_type, location)
        self.to_type = to_type
        self.a = x

    def __repr__(self):
        return "TYPECAST {}".format(self.to_type)


class Member(Expression):
    """ Field reference of some object, can also be package selection """

    def __init__(self, base, field, typ, location):
        super().__init__(typ, location)
        assert isinstance(base, Expression)
        assert isinstance(field, str)
        self.base = base
        self.field = field

    def __repr__(self):
        return "{}.{}".format(self.base, self.field)


class Index(Expression):
    """ Index something, for example an array """

    def __init__(self, base, index, typ, location):
        super().__init__(typ, location)
        self.base = base
        self.index = index

    def __repr__(self):
        return "Index {}".format(self.index)


class VariableAccess(Expression):
    """ Access a variable """

    def __init__(self, variable: Variable, location):
        super().__init__(variable.typ, location)
        self.variable = variable

    def __repr__(self):
        return "Read from {}".format(self.variable)


class Unop(Expression):
    """ Operation on one operand, typically 'op' 'expr' """

    arithmatic_ops = ("+", "-")
    logical_ops = ("not",)
    pointer_ops = ("&", "*")
    cond_ops = logical_ops
    all_ops = cond_ops + pointer_ops + arithmatic_ops

    def __init__(self, op, a: Expression, typ, location):
        super().__init__(typ, location)
        assert isinstance(a, Expression)
        assert isinstance(op, str)
        assert op in self.all_ops
        self.a = a
        self.op = op

    def __repr__(self):
        return "UNOP {}".format(self.op)

    @property
    def is_bool(self):
        """ Test if this binop is a boolean """
        return self.op in self.cond_ops


class Binop(Expression):
    """ Expression taking two operands and one operator """

    arithmatic_ops = (
        "+",
        "-",
        "*",
        "/",
        "%",
        ">>",
        "<<",
        "&",
        "|",
        "^",
        "div",
        "mod",
    )
    logical_ops = ("and", "or", "in")
    compare_ops = ("=", "<>", "<", ">", "<=", ">=")
    cond_ops = logical_ops + compare_ops
    all_ops = arithmatic_ops + cond_ops

    def __init__(self, a: Expression, op, b: Expression, typ, location):
        super().__init__(typ, location)
        assert isinstance(a, Expression), type(a)
        assert isinstance(b, Expression)
        assert isinstance(op, str)
        assert op in self.all_ops
        self.a = a
        self.b = b
        self.op = op  # Operation: '+', '-', '*', '/', 'mod'

    def __repr__(self):
        return "BINOP {}".format(self.op)

    @property
    def is_bool(self):
        """ Test if this binop is a boolean """
        return self.op in self.cond_ops


class Literal(Expression):
    """ Constant value or string """

    def __init__(self, val, typ, location):
        super().__init__(typ, location)
        self.val = val

    def __repr__(self):
        return "LITERAL {}".format(self.val)


class ExpressionList(Expression):
    """ List of expressions """

    def __init__(self, expressions, loc):
        super().__init__(None, loc)
        self.expressions = expressions

    def __repr__(self):
        return "List [{}]".format(self.expressions)


class NamedExpressionList(Expression):
    """ List of named expressions """

    def __init__(self, expressions, loc):
        super().__init__(None, loc)
        self.expressions = expressions

    def __repr__(self):
        return "NamedList [{}]".format(self.expressions)


class FunctionCall(Expression):
    """ Call to a some function """

    def __init__(self, callee, args, typ, location):
        super().__init__(typ, location)
        self.callee = callee
        self.args = args

    def __repr__(self):
        return "function-call {0} ".format(self.callee)


class BuiltInFunctionCall(Expression):
    def __init__(self, func, args, typ, location):
        super().__init__(typ, location)
        self.func = func
        self.args = args
