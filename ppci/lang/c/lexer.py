""" C Language lexer """

import re
import logging

from ...common import Token
from ...pcc.baselex import SimpleLexer, on


class CToken(Token):
    """ C token (including optional preceeding spaces) """
    def __init__(self, typ, val, space, first, loc):
        super().__init__(typ, val, loc)
        self.space = space
        self.first = first

    def __repr__(self):
        return 'CToken({}, {}, "{}", {})'.format(
            self.typ, self.val, self.space, self.loc)

    def __str__(self):
        return self.space + self.val

    def copy(self, space=None, first=None):
        """ Return a new token which is a mildly modified copy """
        if space is None:
            space = self.space
        if first is None:
            first = self.first
        return CToken(self.typ, self.val, space, first, self.loc)


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
    logger = logging.getLogger('clexer')
    double_glyphs = (
        '##', '&&', '||', '<<', '>=', '==', '<=', '::')
    single_glyphs = (
        ',', ';', '(', ')', '{', '}', '.', '#', '<', '>', '=', '!', '/',
        '+', '-', '*', '[', ']', ':', '|', '&', '~', '^', '?')
    glyphs = double_glyphs + single_glyphs
    op_txt = '|'.join(re.escape(g) for g in glyphs)

    def __init__(self):
        self.trigraph = False

    def lex(self, src, filename):
        self.filename = filename
        self.logger.debug('Lexing %s', filename)

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

    def tokenize(self, txt, eof=False):
        """ Generate a lines of tokens which contain leading whitespace """
        space = ''
        first = True
        token = None
        for token in super().tokenize(txt, eof=eof):
            if token.typ == 'BOL':
                if first:
                    # Yield an extra start of line
                    yield CToken('BOL', '', '', first, token.loc)
                first = True
            elif token.typ == 'WS':
                space += token.val
            else:
                yield CToken(token.typ, token.val, space, first, token.loc)
                space = ''
                first = False

        # Emit last newline:
        if first and token:
            # Yield an extra start of line
            yield CToken('BOL', '', '', first, token.loc)

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

    @on(r'\d+L?')
    def handle_numer(self, val):
        return 'NUMBER', val

    @on(op_txt)
    def handle_glyph(self, val):
        return val, val
