
import logging
import io
from .options import COptions
from .context import CContext
from .parser import CParser
from .semantics import CSemantics
from .preprocessor import CPreProcessor, prepare_for_parsing
from .codegenerator import CCodeGenerator
from .utils import print_ast


class CBuilder:
    """ C builder that converts C code into ir-code """
    logger = logging.getLogger('cbuilder')

    def __init__(self, arch_info, coptions):
        self.arch_info = arch_info
        self.coptions = coptions
        self.cgen = None

    def build(self, src: io.TextIOBase, filename: str, reporter=None):
        if reporter:
            reporter.heading(2, 'C builder')
            reporter.message(
                'Welcome to the C building report for {}'.format(filename))
        cdialect = self.coptions['std']
        self.logger.info('Starting C compilation (%s)', cdialect)

        context = CContext(self.coptions, self.arch_info)
        compile_unit = _parse(src, filename, context)

        if reporter:
            f = io.StringIO()
            print_ast(compile_unit, file=f)
            reporter.heading(2, 'C-ast')
            reporter.message('Behold the abstract syntax tree of your C-code')
            reporter.dump_raw_text(f.getvalue())
        cgen = CCodeGenerator(context)
        return cgen.gen_code(compile_unit)

    def _create_ast(self, src, filename):
        return create_ast(
            src, self.arch_info, filename=filename, coptions=self.coptions)


def parse_text(text, arch='x86_64'):
    """ Parse given C sourcecode into an AST """
    from ...api import get_arch
    f = io.StringIO(text)
    arch_info = get_arch(arch).info
    coptions = COptions()
    context = CContext(coptions, arch_info)
    return _parse(f, '?', context)


def create_ast(src, arch_info, filename='<snippet>', coptions=None):
    """ Create a C ast from the given source """
    if coptions is None:
        coptions = COptions()
    context = CContext(coptions, arch_info)
    return _parse(src, filename, context)


def _parse(src, filename, context):
    preprocessor = CPreProcessor(context.coptions)
    tokens = preprocessor.process(src, filename)
    semantics = CSemantics(context)
    parser = CParser(context.coptions, semantics)
    tokens = prepare_for_parsing(tokens, parser.keywords)
    ast = parser.parse(tokens)
    return ast


def parse_type(text, context, filename='foo.c'):
    """ Parse given C-type AST """
    # TODO: fix + ; hack below:
    src = io.StringIO(text + ';')
    preprocessor = CPreProcessor(context.coptions)
    tokens = preprocessor.process(src, filename)
    semantics = CSemantics(context)
    parser = CParser(context.coptions, semantics)
    tokens = prepare_for_parsing(tokens, parser.keywords)
    parser.init_lexer(tokens)
    parser.typedefs = set()
    return parser.parse_typename()
