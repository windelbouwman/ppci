"""
Fortran frontend

See also:

https://en.wikibooks.org/wiki/Fortran_77_Tutorial#Why_learn_Fortran.3F

"""


from .pcc.baselex import BaseLexer
from .common import Token, SourceLocation


class Node:
    def __init__(self, loc):
        self.loc = loc


class Program(Node):
    """ A fortran program """
    def __init__(self, name, variables, statements, loc):
        super().__init__(loc)
        self.name = name
        self.variables = variables
        self.statements = statements

    def __repr__(self):
        return 'PROGRAM {}'.format(self.name)


class Variable(Node):
    def __init__(self, typ, name, loc):
        super().__init__(loc)
        self.typ = typ
        self.name = name

    def __repr__(self):
        return 'VAR {} {}'.format(self.typ, self.name)


class Statement(Node):
    """ A single fortran statement """
    pass


class Assignment(Statement):
    def __init__(self, var, expr, loc):
        super().__init__(loc)
        self.var = var
        self.expr = expr

    def __repr__(self):
        return '{} = {}'.format(self.var, self.expr)


class Continue(Statement):
    """ Continue statement """
    def __repr__(self):
        return 'CONTINUE'


class Format(Statement):
    """ Format statement """
    def __repr__(self):
        return 'FORMAT (...)'


class GoTo(Statement):
    def __init__(self, loc):
        super().__init__(loc)


class IfArith(Statement):
    """ Arithmatic if """
    def __init__(self, expr, s1, s2, s3, loc):
        super().__init__(loc)
        self.expr = expr
        self.s1 = s1
        self.s2 = s2
        self.s3 = s3


class Print(Statement):
    def __init__(self, fmt, args, loc):
        super().__init__(loc)
        self.fmt = fmt
        self.args = args

    def __repr__(self):
        args2 = ', '.join(map(str, self.args))
        return 'PRINT {}, {}'.format(self.fmt, args2)


class Read(Statement):
    def __init__(self, fmt, args, loc):
        super().__init__(loc)
        self.fmt = fmt
        self.args = args

    def __repr__(self):
        args2 = ', '.join(map(str, self.args))
        return 'READ {}, {}'.format(self.fmt, args2)


class Stop(Statement):
    def __init__(self, msg, loc):
        super().__init__(loc)
        self.msg = msg


class Write(Statement):
    def __init__(self, fmt, args, loc):
        super().__init__(loc)
        self.fmt = fmt
        self.args = args

    def __repr__(self):
        args2 = ', '.join(map(str, self.args))
        return 'WRITE {}, {}'.format(self.fmt, args2)


class For(Statement):
    pass


class Expression(Node):
    pass


class Binop(Expression):
    """ Binary operation """
    def __init__(self, a, op, b, loc):
        super().__init__(loc)
        self.a = a
        self.op = op
        self.b = b

    def __repr__(self):
        return '({} {} {})'.format(self.a, self.op, self.b)


class VarRef(Expression):
    def __init__(self, vname, loc):
        super().__init__(loc)
        self.vname = vname

    def __repr__(self):
        return self.vname


class Const(Expression):
    def __init__(self, val, typ, loc):
        super().__init__(loc)
        self.val = val
        self.typ = typ

    def __repr__(self):
        return '{}<{}>'.format(self.typ, self.val)


TYPES = ('INTEGER', 'REAL')

KEYWORDS = (
    'CONTINUE',
    'DO',
    'END',
    'FORMAT',
    'GO',
    'IF',
    'PRINT',
    'PROGRAM',
    'READ',
    'STOP',
    'TO',
    'WRITE')


class FortranLexer(BaseLexer):
    """
        Handle the nice fortran syntax:
        column use
        1-5    label
        6      continuation character
        7-72   statements
        73-80  unused
    """
    def __init__(self):
        op_txt = r'[,=+\-*/\(\)]'
        tok_spec = [
            ('REAL', r'\d+\.\d+', lambda typ, val: (typ, float(val))),
            ('NUMBER', r'\d+', lambda typ, val: (typ, int(val))),
            ('ID', r'[A-Za-z][A-Za-z\d_]*', self.handle_id),
            ('SKIP', r'[ \t]', None),
            ('LEESTEKEN', op_txt, lambda typ, val: (val, val)),
            ('STRING1', r'"[^"]*"', lambda typ, val: ('STRING', val[1:-1])),
            ('STRING2', r"'[^']*'", lambda typ, val: ('STRING', val[1:-1]))
            ]
        super().__init__(tok_spec)
        # TODO: hollerith strings are special case

    def handle_id(self, typ, val):
        if val in KEYWORDS + TYPES:
            typ = val
        return (typ, val)

    def tokenize(self, src):
        loc = SourceLocation('a.txt', 1, 1, 1)
        for line in src.split('\n'):
            line = line.rstrip().upper()
            if not line:
                continue
            if line[0] == 'C':
                continue
            print(line)
            label, cont, statements = self.split_line(line)
            if label:
                yield Token('LABEL', label, loc)
            if statements:
                for token in super().tokenize(statements):
                    yield token
            yield Token('EOL', 'EOL', loc)

    def split_line(self, line):
        """ Split line depending on column """
        def int2(l):
            l = l.strip()
            if l:
                return int(l)
        if len(line) < 6:
            return int2(line), None, None
        elif len(line) < 7:
            return int2(line[0:5]), line[5] != ' ', None
        else:
            return int2(line[0:5]), line[5] != ' ', line[6:72]


class FortranParser:
    """ Parse some fortran language """
    def __init__(self):
        self.lexer = FortranLexer()

    def parse(self, src):
        """ parse a piece of FORTRAN77 """
        self.tokens = self.lexer.tokenize(src)
        self.next_token()
        program = self.parse_program()
        return program

    def next_token(self):
        self.token = self.tokens.__next__()
        print(self.token)

    @property
    def peak(self):
        return self.token.typ

    def consume(self, kind=None):
        if kind is None:
            kind = self.peak
        assert self.peak == kind
        t = self.token
        self.next_token()
        return t

    def has_consumed(self, kind):
        if self.peak == kind:
            self.consume()
            return True
        else:
            return False

    def parse_program(self):
        """ Parse a program """
        if self.peak == 'PROGRAM':
            loc = self.consume('PROGRAM').loc
            name = self.consume('ID').val
            self.consume('EOL')
        else:
            loc = None
            name = None

        variables = []
        while self.peak in TYPES:
            variables.extend(self.parse_declaration())
            self.consume('EOL')

        statements = []
        while self.peak != 'END':
            statement = self.parse_statement()
            print('s=', statement)
            assert isinstance(statement, Statement), str(statement)
            statements.append(statement)
            self.consume('EOL')

        program = Program(name, variables, statements, loc)
        return program

    def parse_declaration(self):
        """ Parse variable declarations """
        variables = []
        typ = self.consume()
        assert typ.typ in TYPES
        name = self.consume('ID')
        variables.append(Variable(typ.val, name.val, name.loc))
        while self.has_consumed(','):
            name = self.consume('ID')
            variables.append(Variable(typ.val, name.val, name.loc))
        return variables

    def parse_statement(self):
        if self.peak == 'LABEL':
            label = self.consume('LABEL')
            # TODO: use it!
            print('label=', label.val)
        if self.peak == 'CONTINUE':
            return self.parse_continue()
        elif self.peak == 'DO':
            return self.parse_do()
        elif self.peak == 'END':
            return self.parse_end()
        elif self.peak == 'FORMAT':
            return self.parse_format()
        elif self.peak == 'GO':
            return self.parse_go()
        elif self.peak == 'IF':
            return self.parse_if()
        elif self.peak == 'PRINT':
            return self.parse_print()
        elif self.peak == 'READ':
            return self.parse_read()
        elif self.peak == 'STOP':
            return self.parse_stop()
        elif self.peak == 'WRITE':
            return self.parse_write()
        elif self.peak == 'ID':
            return self.parse_assignment()
        else:
            raise NotImplementedError()

    def parse_assignment(self):
        """ Parse an assignment """
        var = self.consume('ID')
        var = VarRef(var.val, var.loc)
        loc = self.consume('=').loc
        expr = self.parse_expression()
        return Assignment(var, expr, loc)

    def parse_for(self):
        pass

    def parse_end(self):
        self.consume('END')

    def parse_format(self):
        loc = self.consume('FORMAT').loc
        self.consume('(')
        self.consume(')')
        return Format(loc)

    def parse_continue(self):
        loc = self.consume('CONTINUE').loc
        return Continue(loc)

    def parse_do(self):
        self.consume('DO')
        raise NotImplementedError()

    def parse_go(self):
        """ Parse go to syntax """
        loc = self.consume('GO').loc
        self.consume('TO')
        target = self.consume('NUMBER')
        return GoTo(loc)

    def parse_if(self):
        loc = self.consume('IF').loc
        self.consume('(')
        expr = self.parse_expression()
        self.consume(')')
        if self.peak == 'THEN':
            raise NotImplementedError()
        else:
            s1 = self.parse_label_ref()
            self.consume(',')
            s2 = self.parse_label_ref()
            self.consume(',')
            s3 = self.parse_label_ref()
            return IfArith(expr, s1, s2, s3, loc)

    def parse_print(self):
        loc = self.consume('PRINT').loc
        fmt = self.parse_fmt_spec()
        args = []
        while self.has_consumed(','):
            arg = self.parse_term()
            args.append(arg)
        return Print(fmt, args, loc)

    def parse_read(self):
        loc = self.consume('READ').loc
        fmt = self.parse_fmt_spec()
        args = []
        while self.has_consumed(','):
            a = self.consume('ID')
            arg = VarRef(a.val, a.loc)
            args.append(arg)
        return Read(fmt, args, loc)

    def parse_stop(self):
        loc = self.consume('STOP').loc
        if self.peak == 'STRING':
            self.consume('STRING')
        return Stop('', loc)

    def parse_write(self):
        loc = self.consume('WRITE').loc
        if self.has_consumed('('):
            unit = self.parse_unit_spec()
            self.consume(',')
            fmt = self.parse_fmt_spec()
            self.consume(')')
        else:
            raise NotImplementedError()
        args = []
        if self.peak != 'EOL':
            arg = self.parse_term()
            args.append(arg)
        while self.has_consumed(','):
            arg = self.parse_term()
            args.append(arg)
        return Write(fmt, args, loc)

    def parse_label_ref(self):
        """ Parse a label reference, this can be a number or.. a variable? """
        l = self.consume('NUMBER')
        return l.val

    def parse_fmt_spec(self):
        """ Parse a format specifier """
        if self.peak == '*':
            return self.consume('*').val
        else:
            return self.consume('NUMBER').val

    def parse_unit_spec(self):
        """ Parse a unit (file) specifier """
        if self.peak == '*':
            return self.consume('*').val
        elif self.peak == 'ID':
            ref = self.consume('ID')
            return VarRef(ref.val, ref.loc)
        else:
            return self.consume('NUMBER').val

    def parse_expression(self, bp=0):
        """
            Welcome to expression parsing!

            Solve this using precedence parsing with binding power.
        """
        BPS = {
            '+': (50, 0),
            '-': (50, 0),
            '*': (60, 0),
            '/': (60, 0),
            '**': (70, 1),
        }
        lhs = self.parse_term()
        while self.peak in BPS and BPS[self.peak][0] >= bp:
            op = self.consume()
            bp2, x = BPS[op.typ]
            rhs = self.parse_expression(bp2 + x)
            lhs = Binop(lhs, op.val, rhs, op.loc)
        return lhs

    def parse_term(self):
        if self.peak == 'ID':
            vname = self.consume()
            return VarRef(vname.val, vname.loc)
        elif self.peak == 'NUMBER':
            val = self.consume()
            return Const(val.val, 'INT', val.loc)
        elif self.peak == 'REAL':
            val = self.consume()
            return Const(val.val, 'REAL', val.loc)
        elif self.peak == 'STRING':
            a = self.consume()
            return Const(a.val, 'STR', a.loc)
        else:
            raise NotImplementedError()


class Visitor:
    def visit(self, node):
        if isinstance(node, Program):
            for variable in node.variables:
                self.visit(variable)
            for statement in node.statements:
                self.visit(statement)
        elif isinstance(node, (Variable, Const, VarRef)):
            pass
        elif isinstance(node, (Print, Read)):
            for a in node.args:
                self.visit(a)
        elif isinstance(node, Assignment):
            self.visit(node.var)
            self.visit(node.expr)
        elif isinstance(node, Binop):
            self.visit(node.a)
            self.visit(node.b)
        else:
            raise NotImplementedError('VISIT:{} {}'.format(node, type(node)))


class Printer(Visitor):
    def print(self, node):
        self.indent = 0
        self.visit(node)

    def visit(self, node):
        print(' '*self.indent + str(node))
        self.indent += 2
        super().visit(node)
        self.indent -= 2


class FortranBuilder:
    def __init__(self):
        self.parser = FortranParser()

    def build(self, src):
        ast = self.parser.parse(src)
        mods = []
        gen(ast)
        return mods
