""" Front-end for the LLVM IR-code

This front-end can be used as an enabler for many other languages, for example
ADA and C++.

"""

import re
from ..pcc.baselex import BaseLexer, SourceLocation, Token
from ..pcc.recursivedescent import RecursiveDescentParser


class LlvmIrLexer(BaseLexer):
    keywords = ['define',
                'ret',
                'mul']
    glyphs = (
        ',', '=', '{', '}', '(', ')')

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


class LlvmIrParser(RecursiveDescentParser):
    def parse_module(self):
        """ Parse a module """
        while not self.at_end:
            self.parse_function()

    def parse_function(self):
        """ Parse a function """
        self.consume('define')
        self.parse_type()
        name = self.parse_name(global_name=True)
        self.consume('(')
        arg = self.parse_arg()
        while self.has_consumed(','):
            arg = self.parse_arg()
        self.consume(')')
        self.consume('{')
        while self.peak != '}':
            self.parse_statement()
        self.consume('}')
        print(name)

    def parse_arg(self):
        self.parse_type()
        self.parse_name()

    def parse_type(self):
        self.consume('ID')

    def parse_name(self, global_name=False):
        if global_name:
            return self.consume('GID').val
        else:
            return self.consume('LID').val

    def parse_statement(self):
        """ Parse a statement """
        if self.peak == 'LID':
            self.parse_value()
        elif self.peak == 'ret':
            self.parse_ret()
        else:  # pragma: no cover
            raise NotImplementedError(str(self.peak))

    def parse_value(self):
        """ Parse assignment to an ssa value """
        name = self.parse_name()
        self.consume('=')
        print(name, '=')
        self.consume('mul')
        self.parse_type()
        arg = self.parse_name()
        while self.has_consumed(','):
            arg = self.parse_name()

    def parse_ret(self):
        self.consume('ret')
        self.parse_type()
        arg = self.parse_name()
        print('ret', arg)


class LlvmIrFrontend:
    def __init__(self):
        self.lexer = LlvmIrLexer()
        self.parser = LlvmIrParser()

    def compile(self, f):
        src = f.read()
        tokens = self.lexer.tokenize(src)
        self.parser.init_lexer(tokens)
        self.parser.parse_module()
