""" Lexer for pascal. """

import re
from ..common import SourceLocation, Token
from ..tools.baselex import SimpleLexer, on


class Lexer(SimpleLexer):
    """ Generates a sequence of token from an input stream """
    keywords = ['program',
                'type', 'const', 'var',
                'begin', 'end',
                'case', 'of',
                'if', 'then', 'else', 'while', 'for', 'do',
                'to', 'downto',
                'read', 'readln', 'write', 'writeln']
    double_glyphs = (
        ':=', '<>')
    single_glyphs = (
        ',', ';', '(', ')', '.', ':', '<', '>', '=')
    glyphs = double_glyphs + single_glyphs
    op_txt = '|'.join(re.escape(g) for g in glyphs)

    def __init__(self, diag):
        super().__init__()
        self.diag = diag

    def lex(self, input_file):
        filename = input_file.name if hasattr(input_file, 'name') else ''
        s = input_file.read()
        input_file.close()
        self.diag.add_source(filename, s)
        self.filename = filename
        return self.tokenize(s)

    def tokenize(self, text):
        """ Keeps track of the long comments """
        for token in super().tokenize(text):
            yield token
        loc = SourceLocation(self.filename, self.line, 0, 0)
        yield Token('EOF', 'EOF', loc)

    @on(r'[ \t\n]+')
    def handle_skip(self, val):
        pass

    @on(r'[A-Za-z_][A-Za-z\d_]*')
    def handle_id(self, val):
        val = val.lower()
        if val in self.keywords:
            typ = val
        else:
            typ = 'ID'
        return typ, val

    @on(r"'.*?'")
    def handle_string(self, val):
        return 'STRING', val[1:-1]

    @on(r"\d+")
    def handle_number(self, val):
        return 'NUMBER', int(val)

    @on('\(\*.*\*\)', flags=re.DOTALL, order=-2)
    def handle_oldcomment(self, val):
        pass

    @on('\{.*\}', flags=re.DOTALL, order=-1)
    def handle_comment(self, val):
        pass

    @on(op_txt)
    def handle_glyph(self, val):
        return val, val
