""" Lexer for pascal. """

import re
from ...common import SourceLocation, Token
from ...pcc.baselex import BaseLexer


class Lexer(BaseLexer):
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

    def __init__(self, diag):
        self.diag = diag
        self.incomment = False

        # Construct the tricky string of possible glyphs:
        op_txt = '|'.join(re.escape(g) for g in self.glyphs)
        tok_spec = [
            ('NUMBER', r'\d+', lambda typ, val: (typ, int(val))),
            ('ID', r'[A-Za-z_][A-Za-z\d_]*', self.handle_id),
            ('NEWLINE', r'\n', lambda typ, val: self.newline()),
            ('SKIP', r'[ \t]', None),
            ('OLDCOMMENT', r'\(\*.*\*\)', None),
            ('SLCOMMENT', r'\{.*\}', None),
            ('GLYPH', op_txt, lambda typ, val: (val, val)),
            ('STRING', r"'.*?'", lambda typ, val: (typ, val[1:-1]))
            ]
        super().__init__(tok_spec)

    def lex(self, input_file):
        filename = input_file.name if hasattr(input_file, 'name') else ''
        s = input_file.read()
        input_file.close()
        self.diag.add_source(filename, s)
        self.filename = filename
        return self.tokenize(s)

    def handle_comment_start(self, typ, val):
        self.incomment = True

    def handle_comment_stop(self, typ, val):
        self.incomment = False

    def tokenize(self, text):
        """ Keeps track of the long comments """
        self.incomment = False
        for token in super().tokenize(text):
            if self.incomment:
                pass    # Wait until we are not in a comment section
            else:
                yield token
        loc = SourceLocation(self.filename, self.line, 0, 0)
        yield Token('EOF', 'EOF', loc)

    def handle_id(self, typ, val):
        val = val.lower()
        if val in self.keywords:
            typ = val
        return typ, val
