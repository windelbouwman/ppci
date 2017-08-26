""" C Statements """

from ..generic.nodes import Statement, Compound


class If(Statement):
    """ If statement """
    def __init__(self, condition, yes, no, location):
        super().__init__(location)
        self.condition = condition
        self.yes = yes
        self.no = no

    def __repr__(self):
        return 'If'


class Switch(Statement):
    """ Switch statement """
    def __init__(self, expression, statement, location):
        super().__init__(location)
        self.expression = expression
        self.statement = statement

    def __repr__(self):
        return 'Switch'


class While(Statement):
    """ While statement """
    def __init__(self, condition, body, location):
        super().__init__(location)
        self.condition = condition
        self.body = body

    def __repr__(self):
        return 'While'


class DoWhile(Statement):
    """ Do-while statement """
    def __init__(self, body, condition, location):
        super().__init__(location)
        self.condition = condition
        self.body = body

    def __repr__(self):
        return 'Do-while'


class For(Statement):
    """ For statement """
    def __init__(self, init, condition, post, body, location):
        super().__init__(location)
        self.init = init
        self.condition = condition
        self.post = post
        self.body = body

    def __repr__(self):
        return 'For'


class Break(Statement):
    """ Break statement """
    def __repr__(self):
        return 'Break'


class Continue(Statement):
    """ Continue statement """
    def __repr__(self):
        return 'Continue'


class Case(Statement):
    """ Case statement """
    def __init__(self, value, typ, statement, location):
        super().__init__(location)
        self.value = value
        self.typ = typ
        self.statement = statement

    def __repr__(self):
        return 'Case'


class Default(Statement):
    """ Default statement """
    def __init__(self, statement, location):
        super().__init__(location)
        self.statement = statement

    def __repr__(self):
        return 'Default'


class Label(Statement):
    """ A label """
    def __init__(self, name, statement, location):
        super().__init__(location)
        self.name = name
        self.statement = statement

    def __repr__(self):
        return '{}:'.format(self.name)


class Goto(Statement):
    """ Goto statement """
    def __init__(self, label, location):
        super().__init__(location)
        self.label = label

    def __repr__(self):
        return 'Goto {}'.format(self.label)


class Return(Statement):
    """ Return statement """
    def __init__(self, value, location):
        super().__init__(location)
        self.value = value

    def __repr__(self):
        return 'Return'


class Empty(Statement):
    """ Do nothing! """
    def __repr__(self):
        return 'Empty'


class ExpressionStatement(Statement):
    def __init__(self, expression):
        super().__init__(expression.location)
        self.expression = expression

    def __repr__(self):
        return 'Expression statement'


class DeclarationStatement(Statement):
    def __init__(self, declaration, location):
        super().__init__(location)
        self.declaration = declaration

    def __repr__(self):
        return 'Declaration statement'


__all__ = ['If', 'Compound']
