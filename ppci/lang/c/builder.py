
import logging
import io
from .parser import CParser
from .preprocessor import CPreProcessor, prepare_for_parsing
from .codegenerator import CCodeGenerator


class CBuilder:
    """ C builder that converts C code into ir-code """
    logger = logging.getLogger('cbuilder')

    def __init__(self, march, coptions):
        self.march = march
        self.coptions = coptions
        self.cgen = None

    def build(self, src: io.TextIOBase, filename: str):
        self.logger.info('Starting C compilation')
        preprocessor = CPreProcessor(self.coptions)
        tokens = preprocessor.process(src, filename)
        parser = CParser(self.coptions)
        tokens = prepare_for_parsing(tokens, parser.keywords)

        compile_unit = parser.parse(tokens)
        cgen = CCodeGenerator(self.coptions, self.march)
        return cgen.gen_code(compile_unit)
