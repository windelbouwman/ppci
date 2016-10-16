from . import nodes
from .lexer import LlvmIrLexer
from .parser import LlvmIrParser
from .codegenerator import CodeGenerator


class LlvmIrFrontend:
    def __init__(self):
        context = nodes.Context()
        self.lexer = LlvmIrLexer(context)
        self.parser = LlvmIrParser(context)
        self.codegen = CodeGenerator()

    def compile(self, f):
        src = f.read()
        tokens = self.lexer.tokenize(src, eof=True)
        self.parser.init_lexer(tokens)
        module = self.parser.parse_module()
        return self.codegen.generate(module)
