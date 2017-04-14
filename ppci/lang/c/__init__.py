""" C front end. """

from .lexer import CLexer
from .parser import CParser
from .preprocessor import CPreProcessor, prepare_for_parsing
from .nodes import Printer
from .options import COptions


__all__ = [
    'CBuilder', 'CLexer', 'COptions', 'CPreProcessor', 'CParser', 'Printer']


class CBuilder:
    """ C builder that converts C code into ir-code """
    def __init__(self, march, coptions):
        self.march = march
        self.coptions = coptions
        self.parser = CParser()
        self.cgen = None

    def build(self, src):
        preprocessor = CPreProcessor(self.coptions)
        filename = None
        lines = preprocessor.process(src, filename)
        tokens = prepare_for_parsing(lines)
        # self.tokens = self.lexer.lex(src)
        # preprocessor = CPreProcessor()
        self.parser.parse(tokens)
        # self.cgen.gen(s)
        # Printer().visit(cu)
