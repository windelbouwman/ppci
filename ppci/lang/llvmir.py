""" Front-end for the LLVM IR-code

This front-end can be used as an enabler for many other languages, for example
ADA and C++.

"""

import re
from ..pcc.baselex import BaseLexer
from ..pcc.recursivedescent import RecursiveDescentParser


class LlvmIrLexer(BaseLexer):
    keywords = ['define',
                'ret',
                'mul']
    glyphs = (
        ',', '=', '{', '}', '(', ')')

    def __init__(self, diag):
        self.diag = diag
        self.incomment = False

        # Construct the string of possible glyphs:
        op_txt = '|'.join(re.escape(g) for g in self.glyphs)
        tok_spec = [
            ('NUMBER', r'\d+', lambda typ, val: (typ, int(val))),
            ('ID', r'[A-Za-z_][A-Za-z\d_]*', lambda typ, val: (typ, val)),
            ('SKIP', r'[ \t\n]', None),
            ('GLYPH', op_txt, lambda typ, val: (val, val)),
        ]
        super().__init__(tok_spec)


class LlvmIrParser(RecursiveDescentParser):
    def parse_module(self):
        """ Parse a module """
        while not self.at_end:
            self.parse_function()

    def parse_function(self):
        """ Parse a function """
        self.consume('define')
        self.parse_type()
        self.parse_name()
        self.consume('(')
        arg = self.parse_arg()
        while self.has_consumed(','):
            arg = self.parse_arg()
        self.consume(')')
        self.consume('{')
        self.parse_statement()
        self.consume('}')

    def parse_type(self):
        self.parse_id()

    def parse_statement(self):
        """ Parse a statement """
        pass


class LlvmIrFrontend:
    def __init__(self):
        self.parser = LlvmIrParser()

    def compile(self, f):
        self.parser.parse_module()
