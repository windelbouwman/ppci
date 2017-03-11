""" C Language lexer """

import re

from ...pcc.baselex import SimpleLexer, on


def split_lines(lines):
    """ Split lines and remove the end of line """
    for line in lines:
        yield line.rstrip('\r\n')


def trigraph_filter(lines):
    """ Filter out trigraphs from the lines """
    for line in lines:
        yield line


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
        return 'WS', val

    @on(r'[A-Za-z_][A-Za-z\d_]*')
    def handle_id(self, val):
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
