
import logging
from ...irutils import Verifier
from .context import Context
from .lexer import Lexer
from .parser import Parser
from .codegenerator import CodeGenerator


class PascalBuilder:
    """ Generates IR-code from pascal source. """
    logger = logging.getLogger('pascal-builder')

    def __init__(self, diag, arch_info):
        self.arch_info = arch_info
        self.diag = diag
        self.lexer = Lexer(diag)
        self.parser = Parser(diag)
        self.codegenerator = CodeGenerator(diag)
        self.verifier = Verifier()

    def build(self, sources):
        """ Build the given sources.

        Raises compiler error when something goes wrong.
        """
        assert isinstance(sources, (tuple, list))
        self.logger.debug('Building %d sources', len(sources))

        # Create a context where the modules can live:
        context = Context(self.arch_info)

        # Phase 1: Lexing and parsing stage
        for src in sources:
            self.do_parse(src, context)

        # Phase 2: Generate intermediate code
        ir_modules = []
        for program in context.programs:
            ir_modules.append(self.codegenerator.gencode(program, context))

        # Check modules
        for ir_module in ir_modules:
            self.verifier.verify(ir_module)

        self.logger.debug('build complete!')
        return ir_modules

    def do_parse(self, src, context):
        """ Lexing and parsing stage (phase 1) """
        tokens = self.lexer.lex(src)
        self.parser.parse_source(tokens, context)
