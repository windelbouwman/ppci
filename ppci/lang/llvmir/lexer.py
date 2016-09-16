
import re
from ...pcc.baselex import BaseLexer


class LlvmIrLexer(BaseLexer):
    types = [
        'void', 'double',
        'i64', 'i32', 'i16', 'i8', 'i1',
        'f32', 'f16']

    keywords = ['define',
                'ret', 'br',
                'x', 'zeroinitializer', 'undef',
                'alloca', 'load', 'store',
                'extractelement', 'insertelement', 'shufflevector',
                'add', 'sub', 'mul', 'shl',
                'fadd', 'fsub', 'fmul', 'fdiv', 'frem',
                'or', 'xor', 'and', 'true', 'false']
    glyphs = (
        ',', '=', '{', '}', '(', ')', '*', '<', '>')

    def __init__(self):
        # Construct the string of possible glyphs:
        op_txt = '|'.join(re.escape(g) for g in self.glyphs)
        tok_spec = [
            ('NUMBER', r'\d+', lambda typ, val: (typ, int(val))),
            ('GID', r'@[A-Za-z\d_]+', self.handle_id),
            ('LID', r'%[A-Za-z\d_]+', self.handle_id),
            ('LBL', r'[A-Za-z_][A-Za-z\d_]*:', lambda typ, val: (typ, val)),
            ('ID', r'[A-Za-z_][A-Za-z\d_]*', self.handle_id),
            ('NEWLINE', r'\n', lambda typ, val: self.newline()),
            ('SKIP', r'[ \t]', None),
            ('GLYPH', op_txt, lambda typ, val: (val, val)),
        ]
        super().__init__(tok_spec)

    def handle_id(self, typ, val):
        if val in self.keywords:
            typ = val
        elif val in self.types:
            typ = 'type'
        return typ, val
