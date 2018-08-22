""" Functionality to tokenize and parse S-expressions.
"""

import io
from .common import SourceLocation
from .tools.handlexer import HandLexerBase, Char
from .tools.recursivedescent import RecursiveDescentParser


__all__ = ('parse_sexpr',)


def tokenize_sexpr(text):
    """ Generator that generates tokens for (WASM-compatible) S-expressions.

    Would need work to produce tokens suited for e.g. syntax highlighting,
    but good enough for now, to make the parser work.
    """
    lexer = SExpressionLexer()
    filename = '?'
    f = io.StringIO(text)
    characters = create_characters(f, filename)
    return lexer.tokenize(characters)


def create_characters(f, filename):
    """ Create a sequence of characters """
    for row, line in enumerate(f, 1):
        for col, char in enumerate(line, 1):
            loc = SourceLocation(filename, row, col, 1)
            yield Char(char, loc)


class SExpressionLexer(HandLexerBase):
    """ Lexical scanner for s expressions """
    def tokenize(self, characters):
        for token in super().tokenize(characters, self.lex_sexpr):
            # print(token)
            # Modify some values of tokens:
            if token.typ == 'string':
                token.val = token.val[1:-1]  # Strip of '"'
            elif token.typ == 'word':
                if token.val[0] in '-+.01234567890':  # maybe a number
                    try:
                        if '.' in token.val or 'e' in token.val.lower():
                            token.val = float(token.val)
                        elif token.val.startswith('0x'):
                            token.val = int(token.val, 16)
                        else:
                            token.val = int(token.val)
                    except ValueError:
                        pass
            yield token

    def lex_sexpr(self):
        c = self.next_char()
        if c is None:
            return  # EOF

        c = c.char
        if c == '(':
            if self.accept(';'):
                self.lex_block_comment()
            else:
                self.emit('(')
        elif c == ';':
            if self.accept(';'):
                self.lex_line_comment()
            else:
                self.lex_atom()
        elif c == ')':
            self.emit(')')
        elif c == '"':
            self.lex_string()
        elif c in ' \t\r\n':
            self.ignore()
        else:
            self.lex_atom()

        return self.lex_sexpr

    def lex_atom(self):
        while True:
            c = self.next_char()
            if c is None:
                break
            elif c.char in '() \t\r\n;':
                self.backup_char(c)
                break
        self.emit('word')

    def lex_line_comment(self):
        """ Eat all characters until end of line """
        while True:
            c = self.next_char()
            if c is None or c.char in '\n\r':
                break
        self.emit('comment')
        return

    def lex_block_comment(self):
        level = 1
        c2 = self.next_char(eof=False).char
        while level > 0:
            c1 = c2
            c2 = self.next_char(eof=False).char
            if c1 == ';' and c2 == ')':
                level -= 1
            elif c1 == '(' and c2 == ';':
                level += 1
        self.emit('comment')

    def lex_string(self):
        while True:
            if self.accept('\\'):
                self.next_char(eof=False)  # Accept any excaped char
            elif self.accept('"'):
                self.emit('string')
                break
            else:
                self.next_char(eof=False)


tokens2ignore = ('comment', )


def filtered(tokens):
    for token in tokens:
        if token.typ not in tokens2ignore:
            yield token


class SExpressionParser(RecursiveDescentParser):
    """ This class can be used to parse S-expressions. """
    def parse(self, tokens):
        self.init_lexer(tokens)
        expressions = []
        while not self.at_end:
            expressions.append(self.parse_sexpr())
        return expressions

    def parse_sexpr(self) -> tuple:
        values = []
        self.consume('(')
        while self.peek != ')':
            if self.at_end:
                self.error('Unexpected end of file')
            elif self.peek == '(':
                val = self.parse_sexpr()
            else:
                val = self.consume().val
            values.append(val)
        self.consume(')')
        return tuple(values)


def parse_sexpr(text: str, multiple=False) -> tuple:
    """ Parse S-expression given as string.
    Returns a tuple that represents the S-expression.
    """
    assert isinstance(text, str)

    expressions = parse_multiple_sexpr(text)
    if len(expressions) != 1:
        raise ValueError('Expected a single S-expression')
    return expressions[0]


def parse_multiple_sexpr(text: str) -> tuple:
    assert isinstance(text, str)
    # Check start ok
    tokens = filtered(tokenize_sexpr(text))
    parser = SExpressionParser()
    return parser.parse(tokens)
