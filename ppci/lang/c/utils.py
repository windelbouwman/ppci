
from . import nodes


class Visitor:
    """ Recursively visit all nodes """
    def visit(self, node):
        if isinstance(node, nodes.CompilationUnit):
            for d in node.declarations:
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
        elif isinstance(node, nodes.Cast):
            self.visit(node.to_typ)
            self.visit(node.expr)
        elif isinstance(node, nodes.Sizeof):
            self.visit(node.sizeof_typ)
        elif isinstance(node, nodes.FunctionCall):
            for argument in node.args:
                self.visit(argument)
        elif isinstance(node, nodes.FunctionType):
            for arg_type in node.arg_types:
                self.visit(arg_type)
        elif isinstance(node, nodes.PointerType):
            self.visit(node.pointed_type)
        elif isinstance(node, nodes.IdentifierType):
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
        elif isinstance(node, nodes.Empty):
            pass
        elif isinstance(node, nodes.VariableAccess):
            pass
        else:
            raise NotImplementedError(str(type(node)))


class CAstPrinter(Visitor):
    """ Print AST of a C program """
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


class CPrinter:
    """ Generate a C program """
    def __init__(self):
        self.indent = 0

    def print(self, cu):
        for declaration in cu.declarations:
            if isinstance(declaration, nodes.VariableDeclaration):
                self._print('{} {};'.format(
                    declaration.typ, declaration.name))
            elif isinstance(declaration, nodes.FunctionDeclaration):
                self._print('{} {};'.format(
                    declaration.typ, declaration.name))
                self.gen_statement(declaration.body)
            else:
                raise NotImplementedError(str(declaration))

    def gen_declaration(self, declaration):
        if isinstance(declaration, nodes.VariableDeclaration):
            self._print('{} {};'.format(
                declaration.typ, declaration.name))
        else:
            raise NotImplementedError(str(declaration))

    def gen_statement(self, statement):
        if isinstance(statement, nodes.Compound):
            self._print('{')
            self.indent += 1
            for inner_statement in statement.statements:
                self.gen_statement(inner_statement)
            self.indent -= 1
            self._print('}')
        elif isinstance(statement, nodes.If):
            self._print('if ({})'.format(self.gen_expr(statement.condition)))
            self.gen_statement(statement.yes)
            if statement.no:
                self._print('else')
                self.gen_statement(statement.no)
        elif isinstance(statement, nodes.Empty):
            pass
        elif isinstance(statement, nodes.While):
            self._print('while ({})'.format(
                self.gen_expr(statement.condition)))
            self.gen_statement(statement.body)
        elif isinstance(statement, nodes.DoWhile):
            self._print('do')
            self.gen_statement(statement.body)
            self._print('while ({})'.format(
                self.gen_expr(statement.condition)))
        elif isinstance(statement, nodes.For):
            self._print('for ({}; {}; {})'.format(
                self.gen_expr(statement.init),
                self.gen_expr(statement.condition),
                self.gen_expr(statement.post)))
            self.gen_statement(statement.body)
        elif isinstance(statement, nodes.Return):
            if statement.value:
                self._print('return {};'.format(
                    self.gen_expr(statement.value)))
            else:
                self._print('return;')
        elif isinstance(statement, nodes.Declaration):
            self.gen_declaration(statement)
        elif isinstance(statement, nodes.Expression):
            self._print('{};'.format(self.gen_expr(statement)))
        else:  # pragma: no cover
            raise NotImplementedError(str(statement))

    def gen_expr(self, expr):
        if isinstance(expr, nodes.Binop):
            return '({}) {} ({})'.format(
                self.gen_expr(expr.a), expr.op, self.gen_expr(expr.b))
        elif isinstance(expr, nodes.Unop):
            return '({}){}'.format(
                self.gen_expr(expr.a), expr.op)
        elif isinstance(expr, nodes.VariableAccess):
            return expr.name
        elif isinstance(expr, nodes.FunctionCall):
            args = ', '.join(map(self.gen_expr, expr.args))
            return '{}({})'.format(expr.name, args)
        elif isinstance(expr, nodes.Constant):
            return str(expr.value)
        else:
            raise NotImplementedError(str(expr))

    def _print(self, txt):
        print(self.indent * '  ' + txt)


def cnum(txt: str):
    """ Convert C number to integer """
    assert isinstance(txt, str)

    # Lower tha casing:
    num = txt.lower()

    # Determine base:
    if num.startswith('0x'):
        num = num[2:]
        base = 16
    elif num.startswith('0b'):
        num = num[2:]
        base = 2
    elif num.startswith('0'):
        base = 8
    else:
        base = 10

    # Determine suffix:
    type_specifiers = []
    while num.endswith(('l', 'u')):
        if num.endswith('u'):
            num = num[:-1]
            type_specifiers.append('unsigned')
        elif num.endswith('l'):
            num = num[:-1]
            type_specifiers.append('long')
        else:
            raise NotImplementedError()

    # Take the integer:
    return int(num, base)


def charval(txt: str):
    """ Get the character value of a char literal """
    # Wide char?
    if txt.startswith('L'):
        txt = txt[1:]

    # Strip out ' and '
    assert txt[0] == "'"
    assert txt[-1] == "'"
    txt = txt[1:-1]

    if txt.startswith('\\'):
        if txt[1] in '0123456789':
            return int(txt[1:])
        else:
            mp = {'n': 13}
            return mp[txt[1]]
    else:
        assert len(txt) == 1
    return ord(txt)
