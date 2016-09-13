
import re
from ...pcc.baselex import BaseLexer, SourceLocation, Token


class LlvmIrLexer(BaseLexer):
    keywords = ['define',
                'ret',
                'mul']
    glyphs = (
        ',', '=', '{', '}', '(', ')', '*')

    def __init__(self):
        # Construct the string of possible glyphs:
        op_txt = '|'.join(re.escape(g) for g in self.glyphs)
        tok_spec = [
            ('NUMBER', r'\d+', lambda typ, val: (typ, int(val))),
            ('GID', r'@[A-Za-z\d_]+', self.handle_id),
            ('LID', r'%[A-Za-z\d_]+', self.handle_id),
            ('ID', r'[A-Za-z_][A-Za-z\d_]*', self.handle_id),
            ('SKIP', r'[ \t\n]', None),
            ('GLYPH', op_txt, lambda typ, val: (val, val)),
        ]
        super().__init__(tok_spec)

    def tokenize(self, text):
        """ Keeps track of the long comments """
        for token in super().tokenize(text):
            yield token
        loc = SourceLocation(self.filename, self.line, 0, 0)
        yield Token('EOF', 'EOF', loc)

    def handle_id(self, typ, val):
        if val in self.keywords:
            typ = val
        return typ, val

