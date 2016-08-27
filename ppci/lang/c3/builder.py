""" Entry point when building c3 sources. """

import logging
import collections
import io
from ...common import CompilerError, DiagnosticsManager
from ...irutils import Verifier
from ...binutils.debuginfo import DebugDb
from .lexer import Lexer
from .parser import Parser
from .typechecker import TypeChecker
from .codegenerator import CodeGenerator
from .scope import SemanticError
from .context import Context


class C3Builder:
    """ Generates IR-code from c3 source.

    Reports errors to the diagnostics system.
    """
    logger = logging.getLogger('c3')

    def __init__(self, diag, arch):
        self.diag = diag
        self.lexer = Lexer(diag)
        self.parser = Parser(diag)
        self.debug_db = DebugDb()
        self.codegen = CodeGenerator(diag, self.debug_db)
        self.verifier = Verifier()
        self.arch = arch

    def build(self, sources, imps=()):
        """ Create IR-code from sources.

        Returns:
            A context where modules are living in and a list of
            generated ir modules.

        Raises compiler error when something goes wrong.
        """
        assert isinstance(sources, collections.Iterable)
        assert isinstance(imps, collections.Iterable)
        self.logger.debug(
            'Building %d sources and %d includes', len(sources), len(imps))

        # Create a context where the modules can live:
        context = Context(self.arch)

        # Phase 1: Lexing and parsing stage
        for src in sources:
            self.do_parse(src, context)
        for src in imps:
            self.do_parse(src, context)

        # Phase 1.8: Handle imports:
        try:
            context.link_imports()
        except SemanticError as ex:
            self.diag.error(ex.msg, ex.loc)
            raise

        tc = TypeChecker(self.diag, context)
        tc.check()

        # Phase 1.9
        for module in context.modules:
            self.codegen.gen_globals(module, context)

        # Phase 2: Generate intermediate code
        # Only return ircode when everything is OK
        ir_modules = []
        for pkg in context.modules:
            ir_modules.append(self.codegen.gencode(pkg, context))

        # Hack to check for undefined variables:
        try:
            for ir_module in ir_modules:
                self.check_control_flow(ir_module)
        except CompilerError as ex:
            self.diag.error(ex.msg, ex.loc)
            raise

        self.logger.debug('C3 build complete!')
        return context, ir_modules, self.debug_db

    def check_control_flow(self, ir_module):
        # pas = Mem2RegPromotor(self.debug_db)
        # pas.run(ir_module)
        self.verifier.verify(ir_module)

    def do_parse(self, src, context):
        """ Lexing and parsing stage (phase 1) """
        tokens = self.lexer.lex(src)
        self.parser.parse_source(tokens, context)


def parse_expr(src):
    """ Parse a c3 expression from a string """
    parser = C3ExprParser()
    return parser.parse(src)


class C3ExprParser:
    """
        Generates IR-code from c3 source.
        Reports errors to the diagnostics system.
    """
    def __init__(self, arch):
        self.logger = logging.getLogger('c3')
        diag = DiagnosticsManager()
        self.diag = diag
        self.arch = arch
        self.lexer = Lexer(diag)
        self.parser = Parser(diag)

    def parse(self, src, context):
        """ Parse an expression """
        self.parser.current_scope = context.scope
        tokens = self.lexer.lex(io.StringIO(src))
        self.parser.init_lexer(tokens)
        expr = self.parser.parse_expression()
        return expr
