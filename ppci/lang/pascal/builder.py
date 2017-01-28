
import logging
from ...irutils import Verifier
from .lexer import Lexer
from .parser import Parser


class PascalBuilder:
    """ Generates IR-code from pascal source. """
    logger = logging.getLogger('pascal')

    def __init__(self, diag, arch, debug_db):
        self.diag = diag
        self.lexer = Lexer(diag)
        self.parser = Parser(diag)
        self.debug_db = debug_db
        self.verifier = Verifier()
        self.arch = arch

    def build(self, sources):
        """ Build the given sources.

        Raises compiler error when something goes wrong.
        """
        assert isinstance(sources, (tuple, list))
        self.logger.debug('Building %d sources', len(sources))

        # Create a context where the modules can live:
        # context = Context(self.arch)
        context = None

        # Phase 1: Lexing and parsing stage
        for src in sources:
            self.do_parse(src, context)

        # Phase 1.8: Handle imports:
        # try:
        #    context.link_imports()
        # except SemanticError as ex:
        #    self.diag.error(ex.msg, ex.loc)
        #    raise

        # type_checker = TypeChecker(self.diag, context)
        # type_checker.check()

        # TODO: generate code!
        # Phase 1.9
        # for module in context.modules:
        #    self.codegen.gen_globals(module, context)

        # Phase 2: Generate intermediate code
        # Only return ircode when everything is OK
        ir_modules = []
        # for pkg in context.modules:
        #    ir_modules.append(self.codegen.gencode(pkg, context))

        # Check modules
        for ir_module in ir_modules:
            self.verifier.verify(ir_module)

        self.logger.debug('build complete!')
        return context, ir_modules

    def do_parse(self, src, context):
        """ Lexing and parsing stage (phase 1) """
        tokens = self.lexer.lex(src)
        self.parser.parse_source(tokens, context)
