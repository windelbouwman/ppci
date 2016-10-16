"""
    Visitor class.
"""

from . import astnodes as ast


class Visitor:
    """
        Visitor that can visit all nodes in the AST
        and run pre and post functions.
    """
    def __init__(self, pre=None, post=None):
        self.pre = pre
        self.post = post

    def visit(self, node):
        """ Visit a node and all its descendants """
        self.do(node)

    def do(self, node):
        """ Visit a single node """
        # Run pre function:
        if self.pre:
            self.pre(node)

        # Descent into subnodes:
        if isinstance(node, ast.Module):
            for decl in node.inner_scope:
                self.do(decl)
        elif isinstance(node, ast.Function):
            for symbol in node.inner_scope:
                self.do(symbol)
            self.do(node.typ)
            if node.body:
                self.do(node.body)
        elif isinstance(node, ast.Compound):
            for statement in node.statements:
                self.do(statement)
        elif isinstance(node, ast.If):
            self.do(node.condition)
            self.do(node.truestatement)
            self.do(node.falsestatement)
        elif isinstance(node, ast.While):
            self.do(node.condition)
            self.do(node.statement)
        elif isinstance(node, ast.For):
            self.do(node.init)
            self.do(node.condition)
            self.do(node.final)
            self.do(node.statement)
        elif isinstance(node, ast.Switch):
            self.do(node.expression)
            for option_val, option_code in node.options:
                if option_val is not None:
                    self.do(option_val)
                self.do(option_code)
        elif isinstance(node, ast.Assignment):
            self.do(node.lval)
            self.do(node.rval)
        elif isinstance(node, ast.FunctionCall):
            for arg in node.args:
                self.do(arg)
            self.do(node.proc)
        elif isinstance(node, ast.Return):
            if node.expr:
                self.do(node.expr)
        elif isinstance(node, ast.Binop):
            self.do(node.a)
            self.do(node.b)
        elif isinstance(node, ast.Unop):
            self.do(node.a)
        elif isinstance(node, ast.ExpressionStatement):
            self.do(node.ex)
        elif isinstance(node, ast.TypeCast):
            self.do(node.a)
            self.do(node.to_type)
        elif isinstance(node, ast.Sizeof):
            self.do(node.query_typ)
        elif isinstance(node, ast.Member):
            self.do(node.base)
        elif isinstance(node, ast.Index):
            self.do(node.base)
            self.do(node.i)
        elif isinstance(node, ast.Deref):
            self.do(node.ptr)
        elif isinstance(node, ast.Constant):
            self.do(node.typ)
            self.do(node.value)
        elif isinstance(node, ast.DefinedType):
            self.do(node.typ)
        elif isinstance(node, ast.Variable):
            self.do(node.typ)
        elif isinstance(node, ast.PointerType):
            self.do(node.ptype)
        elif isinstance(node, ast.BaseType):
            pass
        elif isinstance(node, ast.StructureType):
            for member in node.fields:
                self.do(member)
        elif isinstance(node, ast.StructField):
            self.do(node.typ)
        elif isinstance(node, ast.ArrayType):
            self.do(node.element_type)
            self.do(node.size)
        elif isinstance(node, ast.FunctionType):
            for param_type in node.parametertypes:
                self.do(param_type)
            self.do(node.returntype)
        elif isinstance(node, (ast.Identifier, ast.Literal, ast.Empty)):
            # Those nodes do not have child nodes.
            pass
        else:  # pragma: no cover
            raise NotImplementedError('Could not visit "{0}"'.format(node))

        # run post function
        if self.post:
            self.post(node)


class AstPrinter:
    """ Prints an AST as text """
    def print_ast(self, pkg, f):
        self.indent = 2
        self.f = f
        visitor = Visitor(self.print1, self.print2)
        visitor.visit(pkg)

    def print1(self, node):
        print(' ' * self.indent + str(node), file=self.f)
        self.indent += 2

    def print2(self, _):
        self.indent -= 2
