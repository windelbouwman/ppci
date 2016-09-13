
from ...pcc.recursivedescent import RecursiveDescentParser
from .lexer import LlvmIrLexer


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
            self.parse_instruction()
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

    def parse_instruction(self):
        """ Parse an instruction """
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
