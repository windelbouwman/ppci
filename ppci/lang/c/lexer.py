""" C Language lexer """

import re

from ...pcc.baselex import BaseLexer
from ...pcc.baselex import SimpleLexer, on
from ...common import make_num


def split_lines(lines):
    """ Split lines and remove the end of line """
    for line in lines:
        yield line.rstrip('\r\n')


def trigraph_filter(lines):
    """ Filter out trigraphs from the lines """
    for line in lines:
        yield line


def comments_filter(lines):
    """ Filter out line- and block-comments """
    begin_prog = re.compile('(\/\/)|(\/\*)')
    end_prog = re.compile('\*\/')

    in_block = False
    for line in lines:
        outline = ''
        while line:
            if in_block:
                if '*/' in line:
                    p
                else:
                    line = ''
            else:
                mo = begin_prog.search(line)
                if mo:
                    pass
                if '/*' in line:
                    pass

                if '//' in line:
                    outline = outline + line.split('//')[0] + ' '
                    line = ''

        yield outline


def continued_lines_filter(lines):
    """ Glue lines which end with a backslash '\\' """
    prev_line = ''
    for line in lines:
        if line.endswith('\\'):
            prev_line = prev_line + line[:-1]
        else:
            yield prev_line + line
            prev_line = ''

    # Return the last line:
    if prev_line:
        yield prev_line


class Lexer(SimpleLexer):
    """ Lexer used for the preprocessor """
    double_glyphs = (
        '##', '&&', '||', '<<', '>=', '==', '<=')
    single_glyphs = (
        ',', ';', '(', ')', '{', '}', '.', '#', '<', '>', '=', '!', '/',
        '+', '-', '*', '[', ']')
    glyphs = double_glyphs + single_glyphs
    op_txt = '|'.join(re.escape(g) for g in glyphs)

    keywords = ['true', 'false',
                'else', 'if', 'while', 'for', 'return',
                'struct', 'enum',
                'typedef', 'static', 'const',
                'int', 'void', 'char', 'float', 'double']

    def __init__(self):
        self.trigraph = False

    def lex(self, src, filename):
        self.filename = filename

        # TODO: this code can be improved for efficiency!
        r = split_lines(src)
        if self.trigraph:
            r = trigraph_filter(r)
        r = continued_lines_filter(r)
        s = '\n'.join(r)
        # print('=== lex ')
        # print(s)
        # print('=== end lex ')

        return self.tokenize(s)

    @on(r'[ \t]+')
    def handle_whitespace(self, val):
        return 'WS', ' '

    @on(r'[A-Za-z_][A-Za-z\d_]*')
    def handle_id(self, val):
        if val in self.keywords:
            return val, val
        else:
            return 'ID', val

    @on(r'//.*')
    def handle_single_line_comment(self, val):
        pass

    @on(r'/\*.*?\*/', flags=re.DOTALL, order=-2)
    def handle_multi_line_comment(self, val):
        pass

    @on(r'\n')
    def handle_newline(self, val):
        return 'BOL', val

    @on(r'".*?"')
    def handle_string(self, val):
        return 'STRING', val

    @on(r'\d+')
    def handle_numer(self, val):
        return 'NUMBER', val

    @on(op_txt)
    def handle_glyph(self, val):
        return val, val


class OldLexer(BaseLexer):
    """ C lexer implementation.

    Skip out comments, and pass typenames and
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
