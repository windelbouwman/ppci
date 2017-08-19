
import logging
import io
from .options import COptions
from .context import CContext
from .parser import CParser
from .semantics import CSemantics
from .preprocessor import CPreProcessor, prepare_for_parsing
from .codegenerator import CCodeGenerator
from .utils import CAstPrinter


class CBuilder:
    """ C builder that converts C code into ir-code """
    logger = logging.getLogger('cbuilder')

    def __init__(self, arch_info, coptions):
        self.arch_info = arch_info
        self.coptions = coptions
        self.cgen = None

    def build(self, src: io.TextIOBase, filename: str, debug_db,
            reporter=None):
        if not debug_db:
            raise ValueError('Please provide a debug db')
        if reporter:
            reporter.heading(2, 'C builder')
            reporter.message(
                'Welcome to the C building report for {}'.format(filename))
        cdialect = self.coptions['std']
        self.logger.info('Starting C compilation (%s)', cdialect)
        context = CContext(self.coptions, self.arch_info)
        preprocessor = CPreProcessor(self.coptions)
        tokens = preprocessor.process(src, filename)
        semantics = CSemantics(context)
        parser = CParser(context, semantics)
        tokens = prepare_for_parsing(tokens, parser.keywords)

        compile_unit = parser.parse(tokens)
        if reporter:
            f = io.StringIO()
            printer = CAstPrinter(file=f)
            printer.print(compile_unit)
            reporter.heading(2, 'C-ast')
            reporter.message('Behold the abstract syntax tree of your C-code')
            reporter.dump_raw_text(f.getvalue())
        cgen = CCodeGenerator(context, debug_db)
        return cgen.gen_code(compile_unit)


def create_ast(src, arch_info, filename='<snippet>', coptions=None):
    """ Create a C ast from the given source """
    if coptions is None:
        coptions = COptions()
    context = CContext(coptions, arch_info)
    preprocessor = CPreProcessor(coptions)
    tokens = preprocessor.process(src, filename)
    semantics = CSemantics(context)
    parser = CParser(context, semantics)
    tokens = prepare_for_parsing(tokens, parser.keywords)
    ast = parser.parse(tokens)
    return ast
