"""
Fortran frontend

See also:

https://en.wikibooks.org/wiki/Fortran_77_Tutorial#Why_learn_Fortran.3F

The parser and lexer work close together in reading in the fortran source code.


See also:

For gotchas:

https://gcc.gnu.org/onlinedocs/gcc-3.3.5/g77/Gotchas-_0028Transforming_0029.html

https://github.com/antlr/grammars-v3/blob/master/fortran77/f77-antlr2.g

Other fortran implementations:

- f2py python implementation part of the numpy project.

- f2c fortran to c compiler.
see http://www.netlib.org/f2c/f2c.pdf
Quote:
'The program f2c is a horror, based on ancient code and hacked unmercifully. Users are only
supposed to look at its C output, not at its appalling inner workings'

- f77 is the original fortran compiler written by Stu Feldman.

"""


import re
from ...common import Token, SourceLocation, CompilerError
from ...pcc.grammar import Grammar, print_grammar
from ...pcc.lr import LrParserBuilder
from . import nodes


TYPES = (
    'INTEGER',
    'REAL')

KEYWORDS = (
    'CONTINUE',
    'DATA',
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


def get_fortran_parser():
    g = Grammar()
    letters = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    digits = list('0123456789')
    g.add_terminals(
        ['=', '+', '-', '/', ',',
         '(', ')'] + letters + digits)

    # Basics:
    for letter in letters:
        g.add_production('letter', [letter], lambda l: l.val)
    for digit in digits:
        g.add_production('digit', [digit], lambda l: l.val)
    for keyword in KEYWORDS:
        g.add_production(keyword.lower(), list(keyword))
    g.add_production('name', ['letter'], lambda l: l)

    g.add_production('program', ['A'])

    # Statements:
    g.add_production('stmt', ['name', '=', 'expr'])

    # Expressions:
    g.add_production('expr', ['(', 'expr', ')'], lambda *a: a[1])
    g.add_production('expr', ['expr1'], lambda e: e)
    g.add_production('expr1', ['expr1', '+', 'expr2'])
    g.add_production('expr1', ['expr2'], lambda e: e)
    g.add_production('expr2', ['expr5'], lambda e: e)
    g.add_production('expr5', ['name'])
    g.start_symbol = 'program'
    print_grammar(g)
    p = LrParserBuilder(g).generate_parser()
    return p


# get_fortran_parser()


class FortranLexer:
    """
        Handle the nice fortran syntax:
        column use
        1-5    label
        6      continuation character
        7-72   statements
        73-80  unused
    """
    def __init__(self):

        self.mode_progs = {}

        def mk(spec):
            tok_re = '|'.join(
                '(?P<{}>{})'.format(s[0], s[1]) for s in spec)
            return re.compile(tok_re).match

        # String handlers:
        str_spec = [
            ('HOLLERITZ', r"\d+[Hh]", self.handle_holleritz),
            ('STRING1', r'"[^"]*"', lambda typ, val: ('STRING', val[1:-1])),
            ('STRING2', r"'[^']*'", lambda typ, val: ('STRING', val[1:-1])),
        ]

        op_txt = r'[,=+\-*/\(\)]'
        tok_spec = str_spec + [
            ('REAL', r'(\d+\.\d+)|(\d+\.)', lambda typ, val: (typ, float(val))),
            ('NUMBER', r'\d+', lambda typ, val: (typ, int(val))),
            ('ID', r'[A-Za-z][A-Za-z\d_]*', self.handle_id),
            ('SKIP', r'[ \t]', None),
            ('LEESTEKEN', op_txt, lambda typ, val: (val, val)),
            ]
        self.mode_progs['S'] = mk(tok_spec)

        fmt_spec = str_spec + [
            ('FMTSPEC', 'A|(I\d+)|(\d+X)|(E\d+\.\d+)', lambda typ, val: (typ, val)),
            ('SKIP', r'[ \t]', None),
            ('LEESTEKEN', r'[\(\),]', lambda typ, val: (val, val)),
            ]
        self.mode_progs['F'] = mk(fmt_spec)

        all_spec = str_spec + tok_spec + fmt_spec
        self.func_map = {s[0]: s[2] for s in all_spec}

        self.mode = 'S'  # Mode of operation for the lexer
        self.row = 0
        self.col = 0
        self.pos = 0

    def get_mode(self):
        return self._mode

    def set_mode(self, m):
        self._mode = m
        self.gettok = self.mode_progs[m]

    mode = property(get_mode, set_mode)

    def lex(self, src):
        """ Initialize the lexer with some source code """
        self.filename = 'a.txt'
        self.row = 0
        self.col = 0
        self.tokens = self.tokenize(src)
        self.token = None
        self.next_token()

    def next_token(self):
        """ Take the next token from the stream """
        t = self.token
        self.token = self.tokens.__next__()
        # print("M", self.mode, 'CUR:', t, 'NXT:', self.token)
        return t

    @property
    def peak(self):
        """ Take a look at the next token in line """
        return self.token.typ

    def handle_id(self, typ, val):
        if val in KEYWORDS + TYPES:
            typ = val
        return (typ, val)

    def handle_holleritz(self, typ, val):
        ln = int(val[0:-1])
        skip = len(val) + ln
        typ = 'STRING'
        s1 = self.pos + len(val)
        s2 = s1 + ln
        val = self.txt[s1:s2]
        new_pos = self.pos + skip
        typ = 'STRING'
        return (typ, val, new_pos)

    def tokenize(self, src):
        """ Tokenize line by line """
        # Fortran is case insensitive, convert all to uppercase:
        src = src.upper()

        for line in src.split('\n'):
            col = 1
            self.row += 1
            line = line.rstrip()
            if not line:
                continue
            if line[0] == 'C':
                continue
            # print(line)
            label, cont, statements = self.split_line(line)
            if label:
                loc = SourceLocation(self.filename, self.row, 1, 1)
                yield Token('LABEL', label, loc)
            if statements:
                for token in self.tokenize_line(statements):
                    yield token
            col = len(line)
            loc = SourceLocation(self.filename, self.row, col, 1)
            yield Token('EOL', 'EOL', loc)

    def tokenize_line(self, txt):
        """ Generator that generates tokens from text
            It does not yield the EOF token.
        """
        self.pos = 0
        self.txt = txt
        mo = self.gettok(txt)
        while mo:
            typ = mo.lastgroup
            val = mo.group(typ)
            col = mo.start()
            length = mo.end() - mo.start()
            loc = SourceLocation(self.filename, self.row, col, length)
            func = self.func_map[typ]
            new_pos = mo.end()
            if func:
                res = func(typ, val)
                if res:
                    if len(res) == 2:
                        typ, val = res
                    elif len(res) == 3:
                        typ, val, new_pos = res
                    else:
                        raise NotImplementedError('Not implemented')
                    yield Token(typ, val, loc)
            self.pos = new_pos
            mo = self.gettok(txt, self.pos)
        if len(txt) != self.pos:
            char = txt[self.pos]
            raise CompilerError(
                'Unexpected char: {0} (0x{1:X})'.format(char, ord(char)))

    def split_line(self, line):
        """ Split fortran source line depending on column """
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
        self.lexer.lex(src)
        program = self.parse_program()
        return program

    @property
    def peak(self):
        return self.lexer.peak

    def consume(self, kind=None):
        if kind is None:
            kind = self.peak
        assert self.peak == kind
        return self.lexer.next_token()

    def has_consumed(self, kind):
        if self.peak == kind:
            self.consume(kind)
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
            # print('s=', statement)
            assert isinstance(statement, nodes.Statement), str(statement)
            statements.append(statement)
            self.consume('EOL')

        program = nodes.Program(name, variables, statements, loc)
        return program

    def parse_declaration(self):
        """ Parse variable declarations """
        variables = []
        typ = self.consume()
        assert typ.typ in TYPES
        name = self.consume('ID')
        variables.append(nodes.Variable(typ.val, name.val, name.loc))
        while self.has_consumed(','):
            name = self.consume('ID')
            variables.append(nodes.Variable(typ.val, name.val, name.loc))
        return variables

    def parse_statement(self):
        if self.peak == 'LABEL':
            label = self.consume('LABEL')
            # TODO: use it!
            print('label=', label.val)
        if self.peak == 'CONTINUE':
            return self.parse_continue()
        elif self.peak == 'DATA':
            return self.parse_data()
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
        var = nodes.VarRef(var.val, var.loc)
        loc = self.consume('=').loc
        expr = self.parse_expression()
        return nodes.Assignment(var, expr, loc)

    def parse_for(self):
        """ Parse a for loop statement """
        pass

    def parse_end(self):
        """ Parse end statement """
        self.consume('END')

    def parse_format(self):
        """ Parse a format statement """
        loc = self.consume('FORMAT').loc
        self.lexer.mode = 'F'
        spec_list = []
        self.consume('(')
        spec = self.parse_format_spec_item()
        spec_list.append(spec)
        while self.has_consumed(','):
            spec = self.parse_format_spec_item()
            spec_list.append(spec)
        self.lexer.mode = 'S'
        self.consume(')')
        return nodes.Format(loc)

    def parse_format_spec_item(self):
        if self.peak == 'STRING':
            return self.consume('STRING')
        else:
            return self.consume('FMTSPEC')

    def parse_continue(self):
        loc = self.consume('CONTINUE').loc
        return nodes.Continue(loc)

    def parse_data(self):
        loc = self.consume('DATA').loc
        nlist = []
        while True:
            d = self.consume('ID')
            nlist.append(d.val)
            if not self.has_consumed(','):
                break
        self.consume('/')
        clist = []
        while True:
            d = self.parse_const_value()
            if self.has_consumed('*'):
                r = d
                d = self.parse_const_value()
            clist.append(d)
            if not self.has_consumed(','):
                break
        self.consume('/')
        return nodes.Data(nlist, clist, loc)

    def parse_do(self):
        self.consume('DO')
        raise NotImplementedError()

    def parse_go(self):
        """ Parse go to syntax """
        loc = self.consume('GO').loc
        self.consume('TO')
        target = self.parse_label_ref()
        return nodes.GoTo(target, loc)

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
            return nodes.IfArith(expr, s1, s2, s3, loc)

    def parse_print(self):
        loc = self.consume('PRINT').loc
        fmt = self.parse_fmt_spec()
        args = []
        while self.has_consumed(','):
            arg = self.parse_term()
            args.append(arg)
        return nodes.Print(fmt, args, loc)

    def parse_read(self):
        loc = self.consume('READ').loc
        fmt = self.parse_fmt_spec()
        args = []
        while self.has_consumed(','):
            a = self.consume('ID')
            arg = nodes.VarRef(a.val, a.loc)
            args.append(arg)
        return nodes.Read(fmt, args, loc)

    def parse_stop(self):
        loc = self.consume('STOP').loc
        if self.peak == 'STRING':
            self.consume('STRING')
        return nodes.Stop('', loc)

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
        return nodes.Write(fmt, args, loc)

    def parse_label_ref(self):
        """ Parse a label reference, this can be a number or.. a variable? """
        l = self.consume('NUMBER')
        c = nodes.Const(l.val, 'INT', l.loc)
        return c

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
            return nodes.VarRef(ref.val, ref.loc)
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
            lhs = nodes.Binop(lhs, op.val, rhs, op.loc)
        return lhs

    def parse_const_value(self):
        return self.parse_term()

    def parse_term(self):
        if self.peak == 'ID':
            vname = self.consume()
            return nodes.VarRef(vname.val, vname.loc)
        elif self.peak == 'NUMBER':
            val = self.consume()
            return nodes.Const(val.val, 'INT', val.loc)
        elif self.peak == 'REAL':
            val = self.consume()
            return nodes.Const(val.val, 'REAL', val.loc)
        elif self.peak == '(':
            self.consume('(')
            expr = self.parse_expression()
            self.consume(')')
            return expr
        elif self.peak in ['-', '+']:
            # Unary minus!
            op = self.consume()
            a = self.parse_term()
            # TODO: a can be a string!
            return nodes.Unop(op.val, a, op.loc)
        elif self.peak == 'STRING':
            a = self.consume()
            return nodes.Const(a.val, 'STR', a.loc)
        else:
            raise NotImplementedError()


