import re
from ...common import CompilerError
from ..common import Token, SourceLocation

EOF = 'EOF'
EPS = 'EPS'


def on(pattern, flags=0, order=0):
    """ Register method to the given pattern """
    prog = re.compile(pattern, flags=flags)

    def wrapper(f):
        setattr(f, '$lex', (prog, order))
        return f
    return wrapper


class LexMeta(type):
    """ Meta class which inspects the functions decorated with 'on' """
    def __new__(cls, name, bases, attrs):
        lexmap = []
        for n, value in attrs.items():
            if n.startswith('__'):
                continue
            if hasattr(value, '$lex'):
                prog, order = getattr(value, '$lex')
                lexmap.append((prog, order, value))
        lexmap.sort(key=lambda l: l[1])
        attrs['lexmap'] = lexmap
        return type.__new__(cls, name, bases, attrs)


class Lexer:
    pass


class SimpleLexer(Lexer, metaclass=LexMeta):
    """ Simple class for lexing.

    Use this class by subclassing it and decorating handler methods
    with the 'on' function.
    """
    def gettok(self):
        """ Find a match at the given position """
        for prog, _, func in self.lexmap:
            mo = prog.match(self.txt, self.pos)
            if mo:
                column = mo.start() - self.line_start
                length = mo.end() - mo.start()
                loc = SourceLocation(self.filename, self.line, column, length)
                self.pos = mo.end()
                val = mo.group(0)

                # Update row and column information:
                if '\n' in val:
                    self.line += val.count('\n')
                    # TODO: this is wrong, and must be improved:
                    self.line_start = mo.start()

                # print(func, '"%s"' % val)

                res = func(self, val)
                if res:
                    typ, val = res
                    return Token(typ, val, loc)
                else:
                    return

        # No match found!
        char = self.txt[self.pos]
        column = self.pos - self.line_start
        loc = SourceLocation(self.filename, self.line, column, 1)
        raise CompilerError(
            'Unexpected char: {0} (0x{1:X})'.format(char, ord(char)),
            loc=loc)

    def tokenize(self, txt, eof=False):
        """ Generator that generates lexical tokens from text.

        Optionally yield the EOF token.
        """
        self.line = 1
        self.line_start = 0
        self.pos = 0
        self.txt = txt
        while len(txt) != self.pos:
            tok = self.gettok()
            if tok:
                yield tok

        # Emit 'eof' (end of file) if requested
        if eof:
            loc = SourceLocation(self.filename, self.line, 0, 0)
            yield Token(EOF, EOF, loc)


class BaseLexer(Lexer):
    """ Base class for a lexer.

    This class can be overridden to create a
    lexer. This class handles the regular expression generation and
    source position accounting.
    """
    def __init__(self, tok_spec):
        tok_re = '|'.join(
            '(?P<{}>{})'.format(pair[0], pair[1]) for pair in tok_spec)
        self.gettok = re.compile(tok_re).match
        self.func_map = {pair[0]: pair[2] for pair in tok_spec}
        self.filename = None
        self.line = 1
        self.line_start = 0
        self.pos = 0

    def feed(self, txt):
        """ Feeds the lexer with extra input """
        self.tokens = self.tokenize(txt)

    def tokenize(self, txt, eof=False):
        """ Generator that generates lexical tokens from text.

        Optionally yield the EOF token.
        """
        self.line = 1
        self.line_start = 0
        self.pos = 0
        self.txt = txt
        mo = self.gettok(txt)
        while mo:
            typ = mo.lastgroup
            val = mo.group(typ)
            column = mo.start() - self.line_start
            length = mo.end() - mo.start()
            loc = SourceLocation(self.filename, self.line, column, length)
            func = self.func_map[typ]
            new_pos = mo.end()
            if func:
                res = func(typ, val)
                if res:
                    typ, val = res
                    yield Token(typ, val, loc)
            self.pos = new_pos
            mo = self.gettok(txt, self.pos)
        if len(txt) != self.pos:
            char = txt[self.pos]
            column = self.pos - self.line_start
            loc = SourceLocation(self.filename, self.line, column, 1)
            raise CompilerError(
                'Unexpected char: {0} (0x{1:X})'.format(char, ord(char)),
                loc=loc)
        if eof:
            loc = SourceLocation(self.filename, self.line, 0, 0)
            yield Token(EOF, EOF, loc)

    def newline(self):
        """ Enters a new line """
        self.line_start = self.pos
        self.line = self.line + 1

    def next_token(self):
        try:
            return next(self.tokens)
        except StopIteration:
            loc = SourceLocation(self.filename, self.line, 0, 0)
            return Token(EOF, EOF, loc)
