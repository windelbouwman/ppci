
import logging
import io
from .context import CContext
from .parser import CParser
from .preprocessor import CPreProcessor, prepare_for_parsing
from .codegenerator import CCodeGenerator
from .utils import CAstPrinter


class CBuilder:
    """ C builder that converts C code into ir-code """
    logger = logging.getLogger('cbuilder')

    def __init__(self, march, coptions):
        self.march = march
        self.coptions = coptions
        self.cgen = None

    def build(self, src: io.TextIOBase, filename: str, reporter=None):
        if reporter:
            reporter.heading(2, 'C builder')
            reporter.message('Welcome to the C building report')
        cdialect = self.coptions['std']
        self.logger.info('Starting C compilation (%s)', cdialect)
        context = CContext(self.coptions, self.march)
        preprocessor = CPreProcessor(self.coptions)
        tokens = preprocessor.process(src, filename)
        parser = CParser(context)
        tokens = prepare_for_parsing(tokens, parser.keywords)

        compile_unit = parser.parse(tokens)
        if reporter:
            f = io.StringIO()
            printer = CAstPrinter(file=f)
            printer.print(compile_unit)
            reporter.heading(2, 'C-ast')
            reporter.message('Behold the abstract syntax tree of your C-code')
            reporter.dump_raw_text(f.getvalue())
        cgen = CCodeGenerator(context)
        return cgen.gen_code(compile_unit)
