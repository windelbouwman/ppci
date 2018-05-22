""" Functionality to tokenize and parse S-expressions.
"""

import io
from .common import Token, SourceLocation
from ..common import CompilerError
from .tools.handlexer import HandLexerBase, Char
from .tools.recursivedescent import RecursiveDescentParser


__all__ = ('parse_sexpr',)


def tokenize_sexpr_old(text):
    """ Generator that generates tokens for (WASM-compatible) S-expression code.
    Would need work to produce tokens suited for e.g. syntax highlighting,
    but good enough for now, to make the parser work.
    """

    comment_depth = 0
    word_start = -1
    in_string = ''
    filename = '?'

    i = -1
    while i < len(text):
        i += 1
        c = text[i:i+1]  # is '' last round so we can finish words at end of text
        next = text[i+1:i+2]
        loc = SourceLocation(filename, 1, i, 1)

        if comment_depth > 0:
            if c == '(' and next == ';':
                comment_depth += 1
                i += 1
            elif c == ';' and next == ')':
                assert comment_depth > 0
                comment_depth -= 1
                i += 1
                # if comment_depth == 0:
                #     yield ('comment', ...)
        elif in_string:
            if in_string == 2:
                in_string = 1
            elif c == '\\':
                in_string = 2
            elif c == '"':
                in_string = 0
                # drop the quotes
                yield Token('string', text[word_start+1:i], loc)
                word_start = -1
        else:
            token = None
            if c in ' \t\r\n':
                pass  # whitespace
            elif c == '(' and next == ';':
                comment_depth = 1
            elif c == ';' and next == ';':
                for j in range(i+1, len(text)):
                    if text[j] in '\r\n':
                        break
                token = Token('comment', text[i:j], loc)
                i = j
            elif c == '(':
                token = Token('bracket', '(', loc)
            elif c == ')':
                token = Token('bracket', ')', loc)
            elif c == '"':
                in_string = text[i:]
                word_start = i
                continue
            else:
                if word_start == -1:
                    word_start = i
                continue

            # Process word
            if word_start >= 0:
                word = text[word_start:i]
                word_start = -1
                if word[0] in '-+.01234567890':  # maybe a number
                    try:
                        if '.' in word or 'e' in word.lower():
                            word = float(word)
                        else:
                            word = int(word)
                    except ValueError:
                        pass
                # identifier or number or $xx thingy
                yield Token('word', word, loc)
            if token:
                yield token


def tokenize_sexpr(text):
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
            elif c.char in '() \t\r\n':
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

    def parse_sexpr(self):
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


def parse_sexpr(text, multiple=False):
    """ Parse S-expression given as string.
    Returns a tuple that represents the S-expression.
    """
    assert isinstance(text, str)

    expressions = parse_multiple_sexpr(text)
    if len(expressions) != 1:
        raise ValueError('Expected a single S-expression')
    return expressions[0]
    # Check start ok
    tokengen = filtered(tokenize_sexpr(text))
    for token in tokengen:
        if token.typ not in tokens2ignore:
            if token.val != '(':
                raise CompilerError(
                    'Expecting S-expression to open with "(".', token.loc)
            break
    # Parse
    result = _parse_expr(tokengen)
    # Check end ok
    more = ' '.join([str(token.val) for token in tokengen if token.typ not in tokens2ignore])
    if more:
        raise EOFError('Unexpected code after expr end: %r' % more)

    return result


def parse_multiple_sexpr(text):
    assert isinstance(text, str)
    # Check start ok
    tokens = filtered(tokenize_sexpr(text))
    parser = SExpressionParser()
    return parser.parse(tokens)


def _parse_expr(tokengen):
    val = []
    for token in tokengen:
        if token.typ in tokens2ignore:
            pass
        elif token.val == '(':
            val.append(_parse_expr(tokengen))  # recurse
        elif token.val == ')':
            return tuple(val)
        else:
            val.append(token.val)
    else:
        raise EOFError('Unexpected end')
