""" Pascal statement AST nodes.
"""

from .expressions import Expression


class Statement:
    """ Base class of all statements """

    def __init__(self, location):
        self.location = location


class Compound(Statement):
    """ Statement consisting of a sequence of other statements """

    def __init__(self, statements, location):
        super().__init__(location)
        self.statements = statements
        assert all(isinstance(s, Statement) for s in self.statements)

    def __repr__(self):
        return "Compound"


class Empty(Statement):
    """ Empty statement which does nothing! """

    def __init__(self):
        super().__init__(None)

    def __repr__(self):
        return "NOP"


class Return(Statement):
    """ Return statement """

    def __init__(self, expr, loc):
        super().__init__(loc)
        self.expr = expr

    def __repr__(self):
        return "RETURN STATEMENT"


class Exit(Statement):
    """ Exit statement """

    def __repr__(self):
        return "EXIT STATEMENT"


class Assignment(Statement):
    """ Assignment statement with a left hand side and right hand side """

    def __init__(self, lval, rval, location):
        super().__init__(location)
        # TODO: what should lhs be?
        # assert isinstance(lval, Expression)
        assert isinstance(rval, Expression)
        self.lval = lval
        self.rval = rval

    def __repr__(self):
        return "ASSIGNMENT"


class If(Statement):
    """ If statement """

    def __init__(self, condition, truestatement, falsestatement, loc):
        super().__init__(loc)
        self.condition = condition
        self.truestatement = truestatement
        self.falsestatement = falsestatement

    def __repr__(self):
        return "IF-statement"


class CaseOf(Statement):
    """ Case-of statement """

    def __init__(self, expression, options, loc):
        super().__init__(loc)
        self.expression = expression
        self.options = options

    def __repr__(self):
        return "CASE-OF-statement"


class While(Statement):
    """ While statement """

    def __init__(self, condition, statement, loc):
        super().__init__(loc)
        self.condition = condition
        self.statement = statement

    def __repr__(self):
        return "WHILE-statement"


class Repeat(Statement):
    """ Repeat statement """

    def __init__(self, statement, condition, loc):
        super().__init__(loc)
        self.statement = statement
        self.condition = condition

    def __repr__(self):
        return "REPEAT-statement"


class For(Statement):
    """ For statement with a start, condition and final statement """

    def __init__(self, loop_var, start, direction, final, statement, loc):
        super().__init__(loc)
        self.loop_var = loop_var
        self.start = start
        self.direction = direction
        self.final = final
        self.statement = statement

    def __repr__(self):
        return "FOR-statement"


class With(Statement):
    """ The 'with' statement. """

    def __init__(self, record_variables, inner, location):
        super().__init__(location)
        self.record_variables = record_variables
        self.inner = inner


class Goto(Statement):
    def __init__(self, label, location):
        super().__init__(location)
        self.label = label


class Label(Statement):
    """ A label we can jump to. """

    def __init__(self, label, inner, location):
        super().__init__(location)
        self.label = label
        self.inner = inner


class ProcedureCall(Statement):
    def __init__(self, callee, arguments, location):
        super().__init__(location)
        self.callee = callee
        self.arguments = arguments


class BuiltinProcedureCall(Statement):
    """ A builtin procedure call. """

    def __init__(self, calls, location):
        super().__init__(location)
        self.calls = calls


__all__ = ["If", "Compound"]
