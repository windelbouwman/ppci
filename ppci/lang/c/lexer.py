"""
    C Language lexer
"""

from ...pcc.baselex import BaseLexer


class Lexer(BaseLexer):
    """ C lexer """
    keywords = ['true', 'false',
                'else', 'if', 'while', 'for', 'return',
                'struct', 'enum',
                'typedef']

    def __init__(self):
        tok_spec = [
            ('REAL', r'\d+\.\d+', lambda typ, val: (typ, float(val))),
            ('HEXNUMBER', r'0x[\da-fA-F]+',
             lambda typ, val: ('NUMBER', make_num(val))),
            ('NUMBER', r'\d+', lambda typ, val: (typ, int(val))),
            ('ID', r'[A-Za-z_][A-Za-z\d_]*', self.handle_id),
            ('NEWLINE', r'\n', lambda typ, val: self.newline()),
            ('SKIP', r'[ \t]', None),
            ('COMMENTS', r'//.*', None),
            ('LONGCOMMENTBEGIN', r'\/\*', self.handle_comment_start),
            ('LONGCOMMENTEND', r'\*\/', self.handle_comment_stop),
            ('LEESTEKEN', op_txt, lambda typ, val: (val, val)),
            ('STRING', r'".*?"', lambda typ, val: (typ, val[1:-1]))
            ]
        super().__init__(tok_spec)

    def lex(self, src):
        pass
