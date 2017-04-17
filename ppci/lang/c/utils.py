
from . import nodes


class Visitor:
    def visit(self, node):
        if isinstance(node, nodes.CompilationUnit):
            for d in node.decls:
                self.visit(d)
        elif isinstance(node, nodes.Binop):
            self.visit(node.a)
            self.visit(node.b)
        elif isinstance(node, nodes.Declaration):
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
