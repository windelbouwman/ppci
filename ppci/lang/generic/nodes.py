
class Node:
    """ Base class of all nodes in a AST """
    pass


# Types:
class Type(Node):
    """ Base class of all types """
    pass


# Statements
class Statement(Node):
    """ Base class of all statements """
    def __init__(self, loc):
        self.loc = loc


class Compound(Statement):
    """ Statement consisting of a sequence of other statements """
    def __init__(self, statements, loc):
        super().__init__(loc)
        self.statements = statements
        # assert all(isinstance(s, Statement) for s in self.statements)

    def __repr__(self):
        return 'Compound'
