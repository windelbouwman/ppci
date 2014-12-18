
import re
from ppci import Token, CompilerError, SourceLocation

EPS = 'EPS'
EOF = 'EOF'


class BaseLexer:
    """ Base class for a lexer. This class can be overridden to create a
        lexer. This class handles the regular expression generation and
        source position accounting.
    """
    def __init__(self, tok_spec):
        tok_re = '|'.join(
            '(?P<{}>{})'.format(pair[0], pair[1]) for pair in tok_spec)
        self.gettok = re.compile(tok_re).match
        self.func_map = {pair[0]: pair[2] for pair in tok_spec}
        self.filename = None

    def feed(self, txt):
        """ Feeds the lexer with extra input """
        self.tokens = self.tokenize(txt)

    def tokenize(self, txt):
        """ Generator that generates tokens from text
            It does not yield the EOF token.
        """
        self.line = 1
        self.line_start = 0
        self.pos = 0
        mo = self.gettok(txt)
        while mo:
            typ = mo.lastgroup
            val = mo.group(typ)
            column = mo.start() - self.line_start
            length = mo.end() - mo.start()
            loc = SourceLocation(self.filename, self.line, column, length)
            func = self.func_map[typ]
            if func:
                res = func(typ, val)
                if res:
                    typ, val = res
                    yield Token(typ, val, loc)
            self.pos = mo.end()
            mo = self.gettok(txt, self.pos)
        if len(txt) != self.pos:
            char = txt[self.pos]
            raise CompilerError(
                'Unexpected char: {0} (0x{1:X})'.format(char, ord(char)))

    def newline(self):
        """ Enters a new line """
        self.line_start = self.pos
        self.line = self.line + 1

    def next_token(self):
        try:
            return self.tokens.__next__()
        except StopIteration:
            loc = SourceLocation(self.filename, self.line, 0, 0)
            return Token(EOF, EOF, loc)
