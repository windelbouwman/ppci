from ...common import SourceLocation


class Node:
    """ Base class of all nodes in a AST """
    pass


# Types:
class Type(Node):
    """ Base class of all types """
    pass


# Expressions:
class Expression:
    """ Some nice common base class for expressions """
    def __init__(self, location: SourceLocation):
        self.location = location


# Statements
class Statement(Node):
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
        return 'Compound'
