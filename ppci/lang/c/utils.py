
from . import nodes


class Visitor:
    """ Recursively visit all nodes """
    def visit(self, node):
        if isinstance(node, nodes.CompilationUnit):
            for d in node.decls:
                self.visit(d)
        elif isinstance(node, nodes.VariableDeclaration):
            self.visit(node.typ)
        elif isinstance(node, nodes.FunctionDeclaration):
            self.visit(node.typ)
            self.visit(node.body)
        elif isinstance(node, nodes.Binop):
            self.visit(node.a)
            self.visit(node.b)
        elif isinstance(node, nodes.Unop):
            self.visit(node.a)
        elif isinstance(node, nodes.Constant):
            pass
        elif isinstance(node, nodes.FunctionCall):
            for argument in node.args:
                self.visit(argument)
        elif isinstance(node, nodes.FunctionType):
            for arg_type in node.arg_types:
                self.visit(arg_type)
        elif isinstance(node, nodes.PointerType):
            self.visit(node.pointed_type)
        elif isinstance(node, (nodes.IntegerType, nodes.FloatingPointType)):
            pass
        elif isinstance(node, nodes.Compound):
            for statement in node.statements:
                self.visit(statement)
        elif isinstance(node, nodes.For):
            self.visit(node.init)
            self.visit(node.condition)
            self.visit(node.post)
            self.visit(node.body)
        elif isinstance(node, nodes.If):
            self.visit(node.condition)
            self.visit(node.yes)
            self.visit(node.no)
        elif isinstance(node, nodes.While):
            self.visit(node.condition)
            self.visit(node.body)
        elif isinstance(node, nodes.DoWhile):
            self.visit(node.body)
            self.visit(node.condition)
        elif isinstance(node, nodes.Return):
            self.visit(node.value)
        elif isinstance(node, nodes.VariableAccess):
            pass
        else:
            raise NotImplementedError(str(type(node)))


class Printer(Visitor):
    def __init__(self):
        self.indent = 0

    def print(self, node):
        self.visit(node)

    def _print(self, node):
        print('  ' * self.indent + str(node))

    def visit(self, node):
        self._print(node)
        self.indent += 1
        super().visit(node)
        self.indent -= 1
