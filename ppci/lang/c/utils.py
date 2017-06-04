
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
            if node.body:
                self.visit(node.body)
        elif isinstance(node, nodes.Typedef):
            self.visit(node.typ)
        elif isinstance(node, nodes.Ternop):
            self.visit(node.a)
            self.visit(node.b)
            self.visit(node.c)
        elif isinstance(node, nodes.Binop):
            self.visit(node.a)
            self.visit(node.b)
        elif isinstance(node, nodes.Unop):
            self.visit(node.a)
        elif isinstance(node, nodes.Literal):
            pass
        elif isinstance(node, nodes.Cast):
            self.visit(node.to_typ)
            self.visit(node.expr)
        elif isinstance(node, nodes.Sizeof):
            self.visit(node.sizeof_typ)
        elif isinstance(node, nodes.ArrayIndex):
            self.visit(node.base)
            self.visit(node.index)
        elif isinstance(node, nodes.FieldSelect):
            self.visit(node.base)
            # self.visit(node.field)
        elif isinstance(node, nodes.FunctionCall):
            for argument in node.args:
                self.visit(argument)
        elif isinstance(node, nodes.QualifiedType):
            self.visit(node.typ)
        elif isinstance(node, nodes.FunctionType):
            for parameter in node.arguments:
                self.visit(parameter)
            self.visit(node.return_type)
        elif isinstance(node, nodes.PointerType):
            self.visit(node.pointed_type)
        elif isinstance(node, nodes.ArrayType):
            self.visit(node.element_type)
            # self.visit(node.size)
        elif isinstance(node, (nodes.StructType, nodes.UnionType)):
            pass
        elif isinstance(node, (nodes.EnumType,)):
            pass
        elif isinstance(node, (nodes.IdentifierType, nodes.BareType)):
            pass
        elif isinstance(node, nodes.Compound):
            for statement in node.statements:
                self.visit(statement)
        elif isinstance(node, nodes.For):
            if node.init:
                self.visit(node.init)
            if node.condition:
                self.visit(node.condition)
            if node.post:
                self.visit(node.post)
            self.visit(node.body)
        elif isinstance(node, nodes.If):
            self.visit(node.condition)
            self.visit(node.yes)
            if node.no:
                self.visit(node.no)
        elif isinstance(node, nodes.While):
            self.visit(node.condition)
            self.visit(node.body)
        elif isinstance(node, nodes.DoWhile):
            self.visit(node.body)
            self.visit(node.condition)
        elif isinstance(node, nodes.Switch):
            self.visit(node.expression)
            self.visit(node.statement)
        elif isinstance(node, (nodes.Goto, nodes.Break, nodes.Continue)):
            pass
        elif isinstance(node, (nodes.Label, nodes.Default)):
            self.visit(node.statement)
        elif isinstance(node, (nodes.Case,)):
            self.visit(node.value)
            self.visit(node.statement)
        elif isinstance(node, nodes.Return):
            if node.value:
                self.visit(node.value)
        elif isinstance(node, nodes.Empty):
            pass
        elif isinstance(node, nodes.VariableAccess):
            pass
        else:
            raise NotImplementedError(str(type(node)))


class CAstPrinter(Visitor):
    """ Print AST of a C program """
    def __init__(self, file=None):
        self.indent = 0
        self.file = file

    def print(self, node):
        self.visit(node)

    def _print(self, node):
        print('  ' * self.indent + str(node), file=self.file)

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
        """ Render compilation unit as C """
        for declaration in cu.declarations:
            self.gen_declaration(declaration)

    def gen_declaration(self, declaration):
        """ Spit out a declaration """
        if isinstance(declaration, nodes.VariableDeclaration):
            self._print('{} {};'.format(
                self.gen_type(declaration.typ), declaration.name))
        elif isinstance(declaration, nodes.FunctionDeclaration):
            if declaration.body:
                self._print('{} {}'.format(
                    self.gen_type(declaration.typ), declaration.name))
                self.gen_statement(declaration.body)
            else:
                self._print('{} {};'.format(
                    self.gen_type(declaration.typ), declaration.name))
        elif isinstance(declaration, nodes.Typedef):
            self._print('typedef {} {};'.format(
                self.gen_type(declaration.typ), declaration.name))
        else:  # pragma: no cover
            raise NotImplementedError(str(declaration))

    def gen_type(self, typ):
        """ Generate a proper C-string for the given type """
        if isinstance(typ, nodes.BareType):
            return typ.type_id
        elif isinstance(typ, nodes.PointerType):
            return '{}*'.format(self.gen_type(typ.pointed_type))
        elif isinstance(typ, nodes.FunctionType):
            parameters = ', '.join(
                self.gen_type(p.typ) for p in typ.arguments)
            return '{}({})'.format(self.gen_type(typ.return_type), parameters)
        elif isinstance(typ, nodes.IdentifierType):
            return typ.name
        else:  # pragma: no cover
            raise NotImplementedError(str(typ))

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
        elif isinstance(expr, nodes.Literal):
            return str(expr.value)
        else:  # pragma: no cover
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
