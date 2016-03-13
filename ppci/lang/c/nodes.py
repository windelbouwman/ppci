"""
    Contains classes for the abstract syntax tree (AST) nodes for the C
    language.
"""


class IfStatement:
    """ If statement """
    def __init__(self, condition, yes, no):
        self.condition = condition


class WhileStatement:
    """ While statement """
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body


class ForStatement:
    """ For statement """
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body


class FunctionCall:
    """ Function call """
    def __init__(self, name, args):
        self.name = name
        self.args = args


class Assignment:
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs


class Binop:
    """ Binary operator """
    def __init__(self, a, op, b, loc):
        self.a = a
        self.op = op
        self.b = b
