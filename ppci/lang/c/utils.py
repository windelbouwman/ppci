
import re
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
        elif isinstance(node, declarations.ValueDeclaration):
            pass
        elif isinstance(node, declarations.Typedef):
            self.visit(node.typ)
        elif isinstance(node, expressions.Ternop):
            self.visit(node.a)
            self.visit(node.b)
            self.visit(node.c)
        elif isinstance(node, expressions.Binop):
            self.visit(node.a)
            self.visit(node.b)
        elif isinstance(node, expressions.Unop):
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
            for argument in node.args:
                self.visit(argument)
        elif isinstance(node, types.QualifiedType):
            self.visit(node.typ)
        elif isinstance(node, types.FunctionType):
            for parameter in node.arguments:
                self.visit(parameter)
            self.visit(node.return_type)
        elif isinstance(node, types.PointerType):
            self.visit(node.element_type)
        elif isinstance(node, types.ArrayType):
            self.visit(node.element_type)
            # self.visit(node.size)
        elif isinstance(node, (types.StructType, types.UnionType)):
            pass
        elif isinstance(node, (types.EnumType,)):
            pass
        elif isinstance(node, (types.IdentifierType, types.BareType)):
            pass
        elif isinstance(node, nodes.Compound):
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
            self.visit(node.value)
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

    def render_type(self, typ, name):
        """ Generate a proper C-string for the given type """
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
        elif isinstance(typ, types.IdentifierType):
            return '{} {}'.format(typ.name, name)
        elif isinstance(typ, types.QualifiedType):
            qualifiers = ' '.join(typ.qualifiers)
            return self.render_type(
                typ.typ, '{} {}'.format(qualifiers, name))
        elif isinstance(typ, types.EnumType):
            return '{}'.format(typ)
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
        elif isinstance(statement, statements.If):
            self._print('if ({})'.format(self.gen_expr(statement.condition)))
            self.gen_statement(statement.yes)
            if statement.no:
                self._print('else')
                self.gen_statement(statement.no)
        elif isinstance(statement, statements.Empty):
            pass
        elif isinstance(statement, statements.While):
            self._print('while ({})'.format(
                self.gen_expr(statement.condition)))
            self.gen_statement(statement.body)
        elif isinstance(statement, statements.DoWhile):
            self._print('do')
            self.gen_statement(statement.body)
            self._print('while ({})'.format(
                self.gen_expr(statement.condition)))
        elif isinstance(statement, statements.For):
            self._print('for ({}; {}; {})'.format(
                self.gen_expr(statement.init),
                self.gen_expr(statement.condition),
                self.gen_expr(statement.post)))
            self.gen_statement(statement.body)
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
        else:  # pragma: no cover
            raise NotImplementedError(str(expr))

    def _print(self, txt=''):
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


def replace_escape_codes(txt: str):
    """ Replace escape codes inside the given text """
    prog = re.compile(
        r'(\\[0-7]{1,3})|(\\x[0-9a-fA-F]+)|'
        r'(\\[\'"?\\abfnrtv])|(\\u[0-9a-fA-F]{4})|(\\U[0-9a-fA-F]{8})')
    pos = 0
    endpos = len(txt)
    parts = []
    while pos != endpos:
        # Find next match:
        mo = prog.search(txt, pos)
        if mo:
            # We have an escape code:
            if mo.start() > pos:
                parts.append(txt[pos:mo.start()])
            # print(mo.groups())
            octal, hx, ch, uni1, uni2 = mo.groups()
            if octal:
                char = chr(int(octal[1:], 8))
            elif hx:
                char = chr(int(hx[2:], 16))
            elif ch:
                mp = {
                    'a': '\a',
                    'b': '\b',
                    'f': '\f',
                    'n': '\n',
                    'r': '\r',
                    't': '\t',
                    'v': '\v',
                    '\\': '\\',
                    '"': '"',
                    "'": "'",
                    '?': '?',
                }
                char = mp[ch[1:]]
            elif uni1:
                char = chr(int(uni1[2:], 16))
            elif uni2:
                char = chr(int(uni2[2:], 16))
            else:  # pragma: no cover
                raise RuntimeError()
            parts.append(char)
            pos = mo.end()
        else:
            # No escape code found:
            parts.append(txt[pos:])
            pos = endpos
    return ''.join(parts)


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
            mp = {
                'a': '\a',
                'b': '\b',
                'f': '\f',
                'n': '\n',
                'r': '\r',
                't': '\t',
                'v': '\v',
            }
            return mp[txt[1]]
    else:
        assert len(txt) == 1
    return ord(txt)
