from . import nodes, types, declarations, expressions, statements


class Visitor:
    """ Recursively visit all nodes """
    def visit(self, node):
        if isinstance(node, nodes.CompilationUnit):
            for d in node.declarations:
                self.visit(d)
        elif isinstance(node, declarations.VariableDeclaration):
            self.visit(node.typ)
            if node.initial_value:
                self.visit(node.initial_value)
        elif isinstance(node, declarations.FunctionDeclaration):
            self.visit(node.typ)
            if node.body:
                self.visit(node.body)
        elif isinstance(node, declarations.ParameterDeclaration):
            self.visit(node.typ)
        elif isinstance(node, declarations.EnumConstantDeclaration):
            if node.value:
                self.visit(node.value)
        elif isinstance(node, declarations.Typedef):
            self.visit(node.typ)
        elif isinstance(node, expressions.TernaryOperator):
            self.visit(node.a)
            self.visit(node.b)
            self.visit(node.c)
        elif isinstance(node, expressions.BinaryOperator):
            self.visit(node.a)
            self.visit(node.b)
        elif isinstance(node, expressions.UnaryOperator):
            self.visit(node.a)
        elif isinstance(node, expressions.Literal):
            pass
        elif isinstance(node, expressions.InitializerList):
            for element in node.elements:
                self.visit(element)
        elif isinstance(node, expressions.Cast):
            self.visit(node.to_typ)
            self.visit(node.expr)
        elif isinstance(node, expressions.Sizeof):
            self.visit(node.sizeof_typ)
        elif isinstance(node, expressions.ArrayIndex):
            self.visit(node.base)
            self.visit(node.index)
        elif isinstance(node, expressions.FieldSelect):
            self.visit(node.base)
        elif isinstance(node, expressions.FunctionCall):
            self.visit(node.callee)
            for argument in node.args:
                self.visit(argument)
        elif isinstance(node, types.FunctionType):
            for parameter in node.arguments:
                self.visit(parameter)
            self.visit(node.return_type)
        elif isinstance(node, types.PointerType):
            self.visit(node.element_type)
        elif isinstance(node, types.ArrayType):
            self.visit(node.element_type)
            if isinstance(node.size, expressions.CExpression):
                self.visit(node.size)
        elif isinstance(node, (types.StructType, types.UnionType)):
            pass
        elif isinstance(node, (types.EnumType,)):
            pass
        elif isinstance(node, types.BasicType):
            pass
        elif isinstance(node, statements.Compound):
            for statement in node.statements:
                self.visit(statement)
        elif isinstance(node, statements.For):
            if node.init:
                self.visit(node.init)
            if node.condition:
                self.visit(node.condition)
            if node.post:
                self.visit(node.post)
            self.visit(node.body)
        elif isinstance(node, statements.If):
            self.visit(node.condition)
            self.visit(node.yes)
            if node.no:
                self.visit(node.no)
        elif isinstance(node, statements.While):
            self.visit(node.condition)
            self.visit(node.body)
        elif isinstance(node, statements.DoWhile):
            self.visit(node.body)
            self.visit(node.condition)
        elif isinstance(node, statements.Switch):
            self.visit(node.expression)
            self.visit(node.statement)
        elif isinstance(
                node,
                (statements.Goto, statements.Break, statements.Continue)):
            pass
        elif isinstance(node, (statements.Label, statements.Default)):
            self.visit(node.statement)
        elif isinstance(node, (statements.Case,)):
            self.visit(node.statement)
        elif isinstance(node, statements.Return):
            if node.value:
                self.visit(node.value)
        elif isinstance(node, statements.Empty):
            pass
        elif isinstance(node, statements.DeclarationStatement):
            self.visit(node.declaration)
        elif isinstance(node, statements.ExpressionStatement):
            self.visit(node.expression)
        elif isinstance(node, expressions.VariableAccess):
            pass
        elif isinstance(node, expressions.BuiltInVaStart):
            self.visit(node.arg_pointer)
        elif isinstance(node, expressions.BuiltInVaArg):
            self.visit(node.arg_pointer)
            self.visit(node.typ)
        else:  # pragma: no cover
            raise NotImplementedError(str(type(node)))
