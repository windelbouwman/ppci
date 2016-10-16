""" C Language lexer """

from ...pcc.baselex import BaseLexer
from ...common import make_num


class Lexer(BaseLexer):
    """ C lexer implementation. Skip out comments, and pass typenames and
    variable names as identifiers.
    """
    keywords = ['true', 'false',
                'else', 'if', 'while', 'for', 'return',
                'struct', 'enum',
                'typedef', 'static', 'const',
                'int', 'void', 'char', 'float', 'double']

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
            ('LEESTEKEN2', r'>>', lambda typ, val: (val, val)),
            ('LEESTEKEN', r'[+;,\(\){}=\-\*]', lambda typ, val: (val, val)),
            ('STRING', r'".*?"', lambda typ, val: (typ, val[1:-1]))
            ]
        super().__init__(tok_spec)

    def lex(self, src):
        s = src.read()
        return self.tokenize(s, eof=True)

    def handle_id(self, typ, val):
        if val in self.keywords:
            return (val, val)
        else:
            return (typ, val)
