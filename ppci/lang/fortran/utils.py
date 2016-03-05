from . import nodes


class Visitor:
    """ Visit ast nodes """
    def visit(self, node):
        if isinstance(node, nodes.Program):
            for variable in node.variables:
                self.visit(variable)
            for statement in node.statements:
                self.visit(statement)
        elif isinstance(node, (nodes.Variable, nodes.Const, nodes.VarRef)):
            pass
        elif isinstance(node, (nodes.Continue, nodes.Stop)):
            pass
        elif isinstance(node, (nodes.Print, nodes.Read, nodes.Write)):
            for a in node.args:
                self.visit(a)
        elif isinstance(node, (nodes.Format, )):
            pass
        elif isinstance(node, nodes.Assignment):
            self.visit(node.var)
            self.visit(node.expr)
        elif isinstance(node, nodes.GoTo):
            self.visit(node.x)
        elif isinstance(node, nodes.IfArith):
            self.visit(node.s1)
            self.visit(node.s2)
            self.visit(node.s3)
        elif isinstance(node, nodes.Binop):
            self.visit(node.a)
            self.visit(node.b)
        elif isinstance(node, nodes.Unop):
            self.visit(node.a)
        elif isinstance(node, nodes.Data):
            for c in node.clist:
                self.visit(c)
        else:
            raise NotImplementedError('VISIT:{} {}'.format(node, type(node)))


class Printer(Visitor):
    def __init__(self):
        self.indent = 0

    def print(self, node):
        """ Print the AST """
        self.indent = 0
        self.visit(node)

    def visit(self, node):
        print(' '*self.indent + str(node))
        self.indent += 2
        super().visit(node)
        self.indent -= 2
