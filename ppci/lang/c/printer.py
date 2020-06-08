""" Ast to sourcecode printer.

"""

import io
from contextlib import contextmanager
from .nodes import types, declarations, expressions, statements


def render_ast(ast):
    """ Render a C program as text

    For example:

    >>> from ppci.lang.c import parse_text, print_ast, render_ast
    >>> ast = parse_text('int a;')
    >>> print_ast(ast)
    Compilation unit with 1 declarations
        Variable [storage=None typ=Basic type int name=a]
            Basic type int
    >>> render_ast(ast)
    int a;
    """
    CPrinter().print(ast)


def expr_to_str(expr):
    """ Render an expression as text.
    """
    print("foo", expr)
    f = io.StringIO()
    printer = CPrinter(f)
    return printer.gen_expr(expr)


def type_to_str(typ):
    """ Render a type as text """
    f = io.StringIO()
    printer = CPrinter(f)
    return printer.render_type(typ)


class CPrinter:
    """ Render a C program as text

    """

    def __init__(self, f=None):
        self._indent = 0
        self.f = f

    def print(self, compile_unit):
        """ Render compilation unit as C """
        for declaration in compile_unit.declarations:
            self.gen_declaration(declaration)

    def gen_declaration(self, declaration):
        """ Spit out a declaration """
        if isinstance(declaration, declarations.VariableDeclaration):
            if declaration.initial_value:
                self._print(
                    "{} = {};".format(
                        self.render_type(declaration.typ, declaration.name),
                        self.gen_expr(declaration.initial_value),
                    )
                )
            else:
                self._print(
                    "{};".format(
                        self.render_type(declaration.typ, declaration.name)
                    )
                )
        elif isinstance(declaration, declarations.FunctionDeclaration):
            if declaration.body:
                self._print(
                    "{}".format(
                        self.render_type(declaration.typ, declaration.name)
                    )
                )
                self.gen_statement(declaration.body)
                self._print()
            else:
                self._print(
                    "{};".format(
                        self.render_type(declaration.typ, declaration.name)
                    )
                )
        elif isinstance(declaration, declarations.Typedef):
            self._print(
                "typedef {};".format(
                    self.render_type(declaration.typ, declaration.name)
                )
            )
        else:  # pragma: no cover
            raise NotImplementedError(str(declaration))

    def render_type(self, typ, name=None):
        """ Generate a proper C-string for the given type """
        if name is None:
            name = ""
        if isinstance(typ, types.BasicType):
            if name:
                return "{} {}".format(typ.type_id, name)
            else:
                return str(typ.type_id)
        elif isinstance(typ, types.PointerType):
            return self.render_type(typ.element_type, "* {}".format(name))
        elif isinstance(typ, types.ArrayType):
            if isinstance(typ.size, expressions.CExpression):
                size = self.gen_expr(typ.size)
            else:
                size = ""
            return self.render_type(
                typ.element_type, "{}[{}]".format(name, size)
            )
        elif isinstance(typ, types.UnionType):
            return str(typ)  # self.render_type()
        elif isinstance(typ, types.StructType):
            return str(typ)  # self.render_type()
        elif isinstance(typ, types.FunctionType):
            parameters = ", ".join(
                self.render_type(p.typ, p.name) for p in typ.arguments
            )
            return self.render_type(
                typ.return_type, "{}({})".format(name, parameters)
            )
        # elif isinstance(typ, types.QualifiedType):
        #     qualifiers = ' '.join(typ.qualifiers)
        #     return self.render_type(
        #         typ.typ, '{} {}'.format(qualifiers, name))
        elif isinstance(typ, types.EnumType):
            return "{}".format(typ)
        elif isinstance(typ, types.BitFieldType):
            return "{}".format(typ)
        else:  # pragma: no cover
            raise NotImplementedError(str(typ))

    def gen_statement(self, statement):
        """ Render a single statement as text """
        if isinstance(statement, statements.Compound):
            self._print("{")
            with self._indented(1):
                for inner_statement in statement.statements:
                    self.gen_statement(inner_statement)
            self._print("}")
        elif isinstance(statement, statements.If):
            self._print("if ({})".format(self.gen_expr(statement.condition)))
            self.gen_statement(statement.yes)
            if statement.no:
                self._print("else")
                self.gen_statement(statement.no)
            self._print()
        elif isinstance(statement, statements.Switch):
            self._print(
                "switch ({})".format(self.gen_expr(statement.expression))
            )
            self.gen_statement(statement.statement)
        elif isinstance(statement, statements.Empty):
            pass
        elif isinstance(statement, statements.While):
            self._print(
                "while ({})".format(self.gen_expr(statement.condition))
            )
            self.gen_statement(statement.body)
            self._print()
        elif isinstance(statement, statements.DoWhile):
            self._print("do")
            self.gen_statement(statement.body)
            self._print(
                "while ({})".format(self.gen_expr(statement.condition))
            )
            self._print()
        elif isinstance(statement, statements.Goto):
            self._print("goto {};".format(statement.label))
        elif isinstance(statement, statements.Label):
            self._print("{}:".format(statement.name))
            self.gen_statement(statement.statement)
        elif isinstance(statement, statements.Case):
            self._print("case {}:".format(statement.value))
            with self._indented(1):
                self.gen_statement(statement.statement)
        elif isinstance(statement, statements.RangeCase):
            self._print(
                "case {} ... {}:".format(statement.value1, statement.value2)
            )
            with self._indented(1):
                self.gen_statement(statement.statement)
        elif isinstance(statement, statements.Default):
            self._print("default:")
            with self._indented(1):
                self.gen_statement(statement.statement)
        elif isinstance(statement, statements.Break):
            self._print("break;")
        elif isinstance(statement, statements.Continue):
            self._print("continue;")
        elif isinstance(statement, statements.For):
            self._print(
                "for ({}; {}; {})".format(
                    self.gen_expr(statement.init),
                    self.gen_expr(statement.condition),
                    self.gen_expr(statement.post),
                )
            )
            self.gen_statement(statement.body)
            self._print()
        elif isinstance(statement, statements.Return):
            if statement.value:
                self._print(
                    "return {};".format(self.gen_expr(statement.value))
                )
            else:
                self._print("return;")
        elif isinstance(statement, statements.InlineAssemblyCode):
            self._print("asm (")
            with self._indented(1):
                self._print(statement.template)
                self._print(":")
                outputs = ",".join(
                    "{} ({})".format(constraint, self.gen_expr(expression))
                    for constraint, expression in statement.output_operands
                )
                self._print(outputs)
                self._print(":")
                inputs = ",".join(
                    "{} ({})".format(constraint, self.gen_expr(expression))
                    for constraint, expression in statement.input_operands
                )
                self._print(inputs)
            self._print(");")
        elif isinstance(statement, statements.DeclarationStatement):
            self.gen_declaration(statement.declaration)
        elif isinstance(statement, statements.ExpressionStatement):
            self._print("{};".format(self.gen_expr(statement.expression)))
        else:  # pragma: no cover
            raise NotImplementedError(str(statement))

    def gen_expr(self, expr):
        """ Format an expression as text """
        if expr is None:
            return ""
        elif isinstance(expr, expressions.BinaryOperator):
            return "({} {} {})".format(
                self.gen_expr(expr.a), expr.op, self.gen_expr(expr.b)
            )
        elif isinstance(expr, expressions.TernaryOperator):
            return "({} ? {} : {})".format(
                self.gen_expr(expr.a),
                self.gen_expr(expr.b),
                self.gen_expr(expr.c),
            )
        elif isinstance(expr, expressions.UnaryOperator):
            return "({}){}".format(self.gen_expr(expr.a), expr.op)
        elif isinstance(expr, expressions.VariableAccess):
            return expr.name
        elif isinstance(expr, expressions.FieldSelect):
            base = self.gen_expr(expr.base)
            return "{}.{}".format(base, expr.field.name)
        elif isinstance(expr, expressions.ArrayIndex):
            base = self.gen_expr(expr.base)
            index = self.gen_expr(expr.index)
            return "{}[{}]".format(base, index)
        elif isinstance(expr, expressions.FunctionCall):
            args = ", ".join(map(self.gen_expr, expr.args))
            return "{}({})".format(self.gen_expr(expr.callee), args)
        elif isinstance(expr, expressions.Literal):
            return str(expr.value)
        elif isinstance(expr, int):
            return str(expr)
        elif isinstance(expr, expressions.Sizeof):
            if isinstance(expr.sizeof_typ, types.CType):
                thing = self.render_type(expr.sizeof_typ)
            else:
                thing = self.gen_expr(expr.sizeof_typ)
            return "sizeof({})".format(thing)
        elif isinstance(expr, expressions.ArrayInitializer):
            thing = ", ".join(self.gen_expr(e) for e in expr.values)
            return "{" + thing + "}"
        elif isinstance(expr, expressions.StructInitializer):
            thing = ", ".join(
                ".{}={}".format(f, self.gen_expr(e))
                for f, e in expr.values.items()
            )
            return "{" + thing + "}"
        elif isinstance(expr, expressions.UnionInitializer):
            thing = ".{}={}".format(expr.field, self.gen_expr(expr.value))
            return "{" + thing + "}"
        elif isinstance(expr, expressions.Cast):
            return "({})({})".format(
                self.render_type(expr.to_typ), self.gen_expr(expr.expr)
            )
        elif isinstance(expr, expressions.CompoundLiteral):
            return "({}) {{ {} }}".format(
                self.render_type(expr.typ), self.gen_expr(expr.init)
            )
        elif isinstance(expr, expressions.BuiltInOffsetOf):
            return "offsetof({}, {})".format(
                self.render_type(expr.query_typ), expr.member
            )
        else:  # pragma: no cover
            raise NotImplementedError(str(type(expr)))

    @contextmanager
    def _indented(self, amount):
        """ Context manager which increases and decreases the amount
        of indentation.
        """
        self._indent += amount
        yield
        self._indent -= amount

    def _print(self, txt=""):
        print(self._indent * "   " + txt, file=self.f)
