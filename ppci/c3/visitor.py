from .astnodes import *


class Visitor:
    """
        Visitor that can visit all nodes in the AST
        and run pre and post functions.
    """
    def visit(self, node, f_pre=None, f_post=None):
        self.f_pre = f_pre
        self.f_post = f_post
        self.do(node)

    def do(self, node):
        # Run pre function:
        if self.f_pre:
            self.f_pre(node)

        # Descent into subnodes:
        if type(node) is Package:
            for decl in node.declarations:
                self.do(decl)
        elif type(node) is Function:
            for s in node.declarations:
                self.do(s)
            self.do(node.typ)
            if node.body:
                self.do(node.body)
        elif type(node) is Compound:
            for s in node.statements:
                self.do(s)
        elif type(node) is If:
            self.do(node.condition)
            self.do(node.truestatement)
            self.do(node.falsestatement)
        elif type(node) is While:
            self.do(node.condition)
            self.do(node.statement)
        elif type(node) is For:
            self.do(node.init)
            self.do(node.condition)
            self.do(node.final)
            self.do(node.statement)
        elif type(node) is Assignment:
            self.do(node.lval)
            self.do(node.rval)
        elif type(node) is FunctionCall:
            for arg in node.args:
                self.do(arg)
            self.do(node.proc)
        elif type(node) is Return:
            self.do(node.expr)
        elif type(node) is Binop:
            self.do(node.a)
            self.do(node.b)
        elif type(node) is Unop:
            self.do(node.a)
        elif type(node) is ExpressionStatement:
            self.do(node.ex)
        elif type(node) is TypeCast:
            self.do(node.a)
            self.do(node.to_type)
        elif type(node) is Sizeof:
            self.do(node.query_typ)
        elif type(node) is Member:
            self.do(node.base)
        elif type(node) is Index:
            self.do(node.base)
            self.do(node.i)
        elif type(node) is Deref:
            self.do(node.ptr)
        elif type(node) is Constant:
            self.do(node.typ)
            self.do(node.value)
        elif type(node) is DefinedType:
            self.do(node.typ)
        elif isinstance(node, Variable):
            self.do(node.typ)
        elif type(node) is PointerType:
            self.do(node.ptype)
        elif type(node) is StructureType:
            for m in node.mems:
                self.do(m.typ)
        elif type(node) is ArrayType:
            self.do(node.element_type)
            self.do(node.size)
        elif type(node) is FunctionType:
            for pt in node.parametertypes:
                self.do(pt)
            self.do(node.returntype)
        elif type(node) in [Identifier, Literal, Empty]:
            # Those nodes do not have child nodes.
            pass
        else:
            raise Exception('Could not visit "{0}"'.format(node))

        # run post function
        if self.f_post:
            self.f_post(node)


class AstPrinter:
    """ Prints an AST as text """
    def printAst(self, pkg, f):
        self.indent = 2
        self.f = f
        visitor = Visitor()
        visitor.visit(pkg, self.print1, self.print2)

    def print1(self, node):
        print(' ' * self.indent + str(node), file=self.f)
        self.indent += 2

    def print2(self, node):
        self.indent -= 2
