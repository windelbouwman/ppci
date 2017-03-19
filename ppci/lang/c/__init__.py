""" C front end. """

from .parser import CParser
from .preprocessor import CPreProcessor, prepare_for_parsing
from .nodes import Printer


__all__ = ['CBuilder', 'CPreProcessor', 'CParser', 'Printer']


class CBuilder:
    """ C builder that converts C code into ir-code """
    def __init__(self, march):
        self.march = march
        self.parser = CParser()
        self.cgen = None

    def build(self, src):
        preprocessor = CPreProcessor()
        filename = None
        tokens = preprocessor.process(src, filename)
        tokens = prepare_for_parsing(tokens)
        # self.tokens = self.lexer.lex(src)
        # preprocessor = CPreProcessor()
        self.parser.parse(tokens)
        # self.cgen.gen(s)
        # Printer().visit(cu)
