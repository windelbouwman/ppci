"""
    Contains classes for the abstract syntax tree (AST) nodes for the C
    language.
"""


class Cu:
    def __init__(self, decls):
        self.decls = decls

    def __repr__(self):
        return 'Cu'


class DeclSpec:
    """ Contains a type and a set of modifiers """
    def __init__(self):
        self.typ = None
        self.modifiers = []

    def has_type(self):
        return self.typ is not None

    def __repr__(self):
        return '[decl-spec typ={} mod={}]'.format(self.typ, self.modifiers)


class Decl:
    def __init__(self):
        self.typ = None
        self.modifiers = []
        self.name = None
        self.f = False

    @property
    def is_function(self):
        return self.f

    def __repr__(self):
        return '[decl typ={} name={}]'.format(self.typ, self.name)


class If:
    """ If statement """
    def __init__(self, condition, yes, no):
        self.condition = condition
        self.yes = yes
        self.no = no


class Switch:
    """ Switch statement """
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body


class While:
    """ While statement """
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body


class DoWhile:
    """ Do while statement """
    def __init__(self, body, condition):
        self.condition = condition
        self.body = body


class For:
    """ For statement """
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body


class Break:
    """ Break statement """
    pass


class Case:
    """ Case statement """
    def __init__(self, value):
        self.value = value


class Goto:
    """ Goto statement """
    pass


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

    def __repr__(self):
        return '(BINOP {} {} {})'.format(self.a, self.op, self.b)


class Visitor:
    def visit(self, node):
        if isinstance(node, Cu):
            for d in node.decls:
                self.visit(d)
        elif isinstance(node, Binop):
            self.visit(node.a)
            self.visit(node.b)
        elif isinstance(node, Decl):
            pass
        else:
            raise NotImplementedError(str(type(node)))


class Printer(Visitor):
    def __init__(self):
        self.indent = 0

    def visit(self, node):
        print(node)
        self.indent += 2
        super().visit(node)
        self.indent -= 2
