""" Lexer for pascal. """

import re
from ..common import SourceLocation, Token
from ..tools.baselex import SimpleLexer, on


class Lexer(SimpleLexer):
    """ Generates a sequence of token from an input stream """

    keywords = [
        "and",
        "array",
        "begin",
        "case",
        "const",
        "div",
        "else",
        "end",
        "downto",
        "false",
        "file",
        "forward",
        "function",
        "goto",
        "if",
        "in",
        "for",
        "do",
        "label",
        "mod",
        "nil",
        "not",
        "of",
        "or",
        "packed",
        "program",
        "procedure",
        "record",
        "repeat",
        "set",
        "then",
        "to",
        "true",
        "type",
        "until",
        "var",
        "while",
        "with",
    ]
    double_glyphs = (":=", "<>", "<=", ">=", "..", "(.", ".)")
    single_glyphs = (
        ",",
        ";",
        "(",
        ")",
        ".",
        ":",
        "<",
        ">",
        "=",
        "-",
        "+",
        "*",
        "/",
        "[",
        "]",
        "@",
        "^",
    )
    glyphs = double_glyphs + single_glyphs
    op_txt = "|".join(re.escape(g) for g in glyphs)

    def __init__(self, diag):
        super().__init__()
        self.diag = diag

    def lex(self, input_file):
        filename = input_file.name if hasattr(input_file, "name") else ""
        s = input_file.read()
        input_file.close()
        self.diag.add_source(filename, s)
        self.filename = filename
        return self.tokenize(s)

    def tokenize(self, text):
        """ Keeps track of the long comments """
        for token in super().tokenize(text):
            # Convert some lexical alternatives:
            if token.typ == "(.":
                token.typ = "["
            elif token.typ == ".)":
                token.typ = "]"

            yield token
        loc = SourceLocation(self.filename, self.line, 0, 0)
        yield Token("EOF", "EOF", loc)

    @on(r"[ \t\n]+")
    def handle_skip(self, val):
        pass

    @on(r"[A-Za-z_][A-Za-z\d_]*")
    def handle_id(self, val):
        val = val.lower()
        if val in self.keywords:
            typ = val
        else:
            typ = "ID"
        return typ, val

    @on(r"'(('')|[^'])*'")
    def handle_string(self, val):
        return "STRING", val[1:-1]

    @on(r"\d+", order=-1)
    def handle_number(self, val):
        return "NUMBER", int(val)

    @on(r"\d+((\.\d+([eE][-+]?\d+)?)|([eE][-+]?\d+))", order=-2)
    def handle_float_number(self, val):
        return "NUMBER", float(val)

    @on(r"\(\*.*?\*\)", flags=re.DOTALL, order=-2)
    def handle_oldcomment(self, val):
        pass

    @on(r"\{.*?\}", flags=re.DOTALL, order=-1)
    def handle_comment(self, val):
        pass

    @on(op_txt)
    def handle_glyph(self, val):
        return val, val
