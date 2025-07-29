"""Functionality to tokenize and parse S-expressions."""

import io
import enum
from .tools.handlexer import HandLexerBase
from .tools.recursivedescent import RecursiveDescentParser


__all__ = ("parse_sexpr",)


def tokenize_sexpr(text):
    """Generator that generates tokens for (WASM-compatible) S-expressions.

    Would need work to produce tokens suited for e.g. syntax highlighting,
    but good enough for now, to make the parser work.
    """
    filename = "?"
    f = io.StringIO(text)
    lexer = SExpressionLexer()
    return filtered(lexer.tokenize(f, filename))


class STokenType(enum.Enum):
    LPAR = 1
    RPAR = 2
    WORD = 3
    STRING = 4
    EOF = 9


def create_chunks(f):
    """Create a sequence of chunks"""
    for row, line in enumerate(f, 1):
        yield (row, 1, line)


class SExpressionLexer(HandLexerBase):
    """Lexical scanner for s expressions"""

    def tokenize(self, f, filename):
        chunks = create_chunks(f)
        for token in super().tokenize(filename, chunks, self.lex_sexpr):
            # Modify some values of tokens:
            if token.typ == "string":
                token.val = token.val[1:-1]  # Strip of '"'
            elif token.typ == "word":
                if token.val[0] in "-+.01234567890":  # maybe a number
                    try:
                        if "." in token.val or "e" in token.val.lower():
                            token.val = float(token.val)
                        elif token.val.startswith("0x"):
                            token.val = int(token.val, 16)
                        else:
                            token.val = int(token.val)
                    except ValueError:
                        pass
            yield token
        yield self.make_token("EOF", "EOF")

    def lex_sexpr(self):
        c = self.next_char()
        if c is None:
            return  # EOF

        if c == "(":
            if self.accept(";"):
                self.lex_block_comment()
            else:
                self.emit("(")
        elif c == ";":
            if self.accept(";"):
                self.lex_line_comment()
            else:
                self.lex_atom()
        elif c == ")":
            self.emit(")")
        elif c == '"':
            self.lex_string()
        elif c in " \t\r\n":
            self.ignore()
        else:
            self.lex_atom()

        return self.lex_sexpr

    def lex_atom(self):
        while True:
            c = self.next_char()
            if c is None:
                break
            elif c in "() \t\r\n;":
                self.backup_char(c)
                break
        self.emit("word")

    def lex_line_comment(self):
        """Eat all characters until end of line"""
        while True:
            c = self.next_char()
            if c is None or c in "\n\r":
                break
        self.emit("comment")
        return

    def lex_block_comment(self):
        level = 1
        c2 = self.next_char(eof=False)
        while level > 0:
            c1 = c2
            c2 = self.next_char(eof=False)
            if c1 == ";" and c2 == ")":
                level -= 1
            elif c1 == "(" and c2 == ";":
                level += 1
        self.emit("comment")

    def lex_string(self):
        while True:
            if self.accept("\\"):
                self.next_char(eof=False)  # Accept any excaped char
            elif self.accept('"'):
                self.emit("string")
                break
            else:
                self.next_char(eof=False)


tokens2ignore = ("comment",)


def filtered(tokens):
    for token in tokens:
        if token.typ not in tokens2ignore:
            yield token


class SExpressionParser(RecursiveDescentParser):
    """This class can be used to parse S-expressions."""

    def parse(self, tokens) -> tuple["SExpression"]:
        self.init_lexer(tokens)
        expressions = []
        while self.peek != "EOF":
            expressions.append(self.parse_sexpr())
        return tuple(expressions)

    def parse_sexpr(self) -> "SList":
        """Parse a single S expression enclosed in parenthesis"""
        values = []
        loc = self.consume("(").loc
        while self.peek != ")":
            if self.peek == "EOF":
                self.error("Unexpected end of file")
            elif self.peek == "(":
                val = self.parse_sexpr()
            else:
                tok = self.next_token()
                if tok.typ == "string":
                    val = SString(tok.val, tok.loc)
                elif tok.typ == "word":
                    val = SSymbol(tok.val, tok.loc)
                else:
                    raise NotImplementedError(tok.typ)
                    val = tok.val
            values.append(val)
        self.consume(")")
        return SList(values, loc)


def parse_sexpr(text: str, multiple=False) -> "SExpression":
    """Parse S-expression given as string.
    Returns a tuple that represents the S-expression.
    """
    assert isinstance(text, str)

    expressions = parse_s_expressions(text)
    if len(expressions) != 1:
        raise ValueError("Expected a single S-expression")
    return expressions[0]


def parse_sexpr_as_tuple(text: str):
    """Parse text into a tuple."""
    return parse_sexpr(text).as_tuple()


def parse_s_expressions(text: str) -> tuple["SExpression"]:
    assert isinstance(text, str)
    # Check start ok
    tokens = tokenize_sexpr(text)
    parser = SExpressionParser()
    return parser.parse(tokens)


class SExpression:
    """A S-expression"""

    def __init__(self, loc):
        self.loc = loc

    def is_symbol(self, value: str) -> bool:
        return False


class SList(SExpression):
    def __init__(self, values: list[SExpression], loc):
        super().__init__(loc)
        self.values = values

    def __len__(self) -> int:
        return len(self.values)

    def __getitem__(self, index):
        return self.values[index]

    def as_tuple(self):
        values = []
        for v in self.values:
            if isinstance(v, SList):
                v = v.as_tuple()
            else:
                v = v.value
            values.append(v)
        return tuple(values)


class SValue(SExpression):
    def __init__(self, value: str, loc):
        super().__init__(loc)
        self.value = value

    def get_value(self) -> str:
        return self.value


class SSymbol(SValue):
    def __init__(self, value: str, loc):
        super().__init__(value, loc)

    def is_symbol(self, value: str) -> bool:
        return self.value == value

    def get_symbol(self) -> str:
        return self.value


class SString(SValue):
    """String  S-expression"""

    def __init__(self, value: str, loc):
        super().__init__(value, loc)

    def get_string(self) -> str:
        return self.value


class SInteger(SValue):
    def __init__(self, value: int, loc):
        super().__init__(value, loc)


class SFloat(SValue):
    def __init__(self, value: float, loc):
        super().__init__(value, loc)
