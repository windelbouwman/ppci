from . import types, declarations, expressions, statements


class CPrinter:
    """ Render a C program as text """
    def __init__(self):
        self.indent = 0

    def print(self, cu):
        """ Render compilation unit as C """
        for declaration in cu.declarations:
            self.gen_declaration(declaration)

    def gen_declaration(self, declaration):
        """ Spit out a declaration """
        if isinstance(declaration, declarations.VariableDeclaration):
            if declaration.initial_value:
                self._print('{} = {};'.format(
                    self.render_type(declaration.typ, declaration.name),
                    self.gen_expr(declaration.initial_value)))
            else:
                self._print('{};'.format(
                    self.render_type(declaration.typ, declaration.name)))
        elif isinstance(declaration, declarations.FunctionDeclaration):
            if declaration.body:
                self._print('{}'.format(
                    self.render_type(declaration.typ, declaration.name)))
                self.gen_statement(declaration.body)
                self._print()
            else:
                self._print('{};'.format(
                    self.render_type(declaration.typ, declaration.name)))
        elif isinstance(declaration, declarations.Typedef):
            self._print('typedef {};'.format(
                self.render_type(declaration.typ, declaration.name)))
        else:  # pragma: no cover
            raise NotImplementedError(str(declaration))

    def render_type(self, typ, name=''):
        """ Generate a proper C-string for the given type """
        if name is None:
            name = ''
        if isinstance(typ, types.BareType):
            return '{} {}'.format(typ.type_id, name)
        elif isinstance(typ, types.PointerType):
            return self.render_type(typ.element_type, '* {}'.format(name))
        elif isinstance(typ, types.ArrayType):
            return self.render_type(typ.element_type, '{}[]'.format(name))
        elif isinstance(typ, types.FunctionType):
            parameters = ', '.join(
                self.render_type(p.typ, p.name) for p in typ.arguments)
            return self.render_type(
                typ.return_type, '{}({})'.format(name, parameters))
        elif isinstance(typ, types.QualifiedType):
            qualifiers = ' '.join(typ.qualifiers)
            return self.render_type(
                typ.typ, '{} {}'.format(qualifiers, name))
        elif isinstance(typ, types.EnumType):
            return '{}'.format(typ)
        else:  # pragma: no cover
            raise NotImplementedError(str(typ))

    def gen_statement(self, statement):
        if isinstance(statement, statements.Compound):
            self._print('{')
            self.indent += 1
            for inner_statement in statement.statements:
                self.gen_statement(inner_statement)
            self.indent -= 1
            self._print('}')
        elif isinstance(statement, statements.If):
            self._print('if ({})'.format(self.gen_expr(statement.condition)))
            self.gen_statement(statement.yes)
            if statement.no:
                self._print('else')
                self.gen_statement(statement.no)
            self._print()
        elif isinstance(statement, statements.Switch):
            self._print('switch ({})'.format(
                self.gen_expr(statement.expression)))
            self.gen_statement(statement.statement)
        elif isinstance(statement, statements.Empty):
            pass
        elif isinstance(statement, statements.While):
            self._print('while ({})'.format(
                self.gen_expr(statement.condition)))
            self.gen_statement(statement.body)
            self._print()
        elif isinstance(statement, statements.DoWhile):
            self._print('do')
            self.gen_statement(statement.body)
            self._print('while ({})'.format(
                self.gen_expr(statement.condition)))
            self._print()
        elif isinstance(statement, statements.Goto):
            self._print('goto {};'.format(statement.label))
        elif isinstance(statement, statements.Label):
            self._print('{}:'.format(statement.name))
            self.gen_statement(statement.statement)
        elif isinstance(statement, statements.Case):
            self._print('case {}:'.format(statement.value))
            self.indent += 1
            self.gen_statement(statement.statement)
            self.indent -= 1
        elif isinstance(statement, statements.Default):
            self._print('default:')
            self.indent += 1
            self.gen_statement(statement.statement)
            self.indent -= 1
        elif isinstance(statement, statements.Break):
            self._print('break;')
        elif isinstance(statement, statements.Continue):
            self._print('continue;')
        elif isinstance(statement, statements.For):
            self._print('for ({}; {}; {})'.format(
                self.gen_expr(statement.init),
                self.gen_expr(statement.condition),
                self.gen_expr(statement.post)))
            self.gen_statement(statement.body)
            self._print()
        elif isinstance(statement, statements.Return):
            if statement.value:
                self._print('return {};'.format(
                    self.gen_expr(statement.value)))
            else:
                self._print('return;')
        elif isinstance(statement, statements.DeclarationStatement):
            self.gen_declaration(statement.declaration)
        elif isinstance(statement, statements.ExpressionStatement):
            self._print('{};'.format(self.gen_expr(statement.expression)))
        else:  # pragma: no cover
            raise NotImplementedError(str(statement))

    def gen_expr(self, expr):
        if isinstance(expr, expressions.Binop):
            return '({}) {} ({})'.format(
                self.gen_expr(expr.a), expr.op, self.gen_expr(expr.b))
        elif isinstance(expr, expressions.Unop):
            return '({}){}'.format(
                self.gen_expr(expr.a), expr.op)
        elif isinstance(expr, expressions.VariableAccess):
            return expr.name
        elif isinstance(expr, expressions.FunctionCall):
            args = ', '.join(map(self.gen_expr, expr.args))
            return '{}({})'.format(expr.name, args)
        elif isinstance(expr, expressions.Literal):
            return str(expr.value)
        elif isinstance(expr, expressions.Sizeof):
            if isinstance(expr.sizeof_typ, types.CType):
                thing = self.render_type(expr.sizeof_typ)
            else:
                thing = self.gen_expr(expr.sizeof_typ)
            return 'sizeof({})'.format(thing)
        else:  # pragma: no cover
            raise NotImplementedError(str(expr))

    def _print(self, txt=''):
        print(self.indent * '  ' + txt)
