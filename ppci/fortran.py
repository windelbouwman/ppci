
from .pcc.baselex import BaseLexer
from .common import Token, SourceLocation

"""
https://en.wikibooks.org/wiki/Fortran_77_Tutorial#Why_learn_Fortran.3F
"""


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
        op_txt = r'[,=+*/]'
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

    def handle_id(self, typ, val):
        return (typ, val)

    def tokenize(self, src):
        loc = SourceLocation('a.txt', 1, 1, 1)
        for line in src.split('\n'):
            line = line.rstrip()
            if not line:
                continue
            if line[0] == 'C':
                continue
            label, cont, statements = self.split_line(line)
            if label:
                yield Token('LABEL', label, loc)
            if statements:
                for token in super().tokenize(statements):
                    yield token

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
            return int2(line[0:5]), line[5] != ' ', line[6:]


class FortranParser:
    def __init__(self):
        self.lexer = FortranLexer()

    def parse(self, src):
        """ parse a piece of FORTRAN77 """
        for token in self.lexer.tokenize(src):
            print(token)
        print('===========')
