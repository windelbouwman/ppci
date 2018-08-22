""" Entry point when building c3 sources. """

import logging
import itertools
import io
from ...arch.arch_info import ArchInfo
from ...arch import get_arch
from ...common import DiagnosticsManager, get_file, CompilerError
from ...build.tasks import TaskError
from ...utils.reporting import DummyReportGenerator
from ...irutils import Verifier, verify_module
from .lexer import Lexer
from .parser import Parser
from .typechecker import TypeChecker
from .codegenerator import CodeGenerator
from .scope import SemanticError
from .context import Context


def c3_to_ir(sources, includes, march, reporter=None):
    """ Compile c3 sources to ir-code for the given architecture. """
    logger = logging.getLogger('c3c')
    march = get_arch(march)
    if not reporter:  # pragma: no cover
        reporter = DummyReportGenerator()

    logger.debug('C3 compilation started')
    reporter.heading(2, 'c3 compilation')
    sources = [get_file(fn) for fn in sources]
    includes = [get_file(fn) for fn in includes]
    diag = DiagnosticsManager()
    c3b = C3Builder(diag, march.info)

    try:
        _, ir_module = c3b.build(sources, includes)
        verify_module(ir_module)
    except CompilerError as ex:
        diag.error(ex.msg, ex.loc)
        diag.print_errors()
        raise TaskError('Compile errors')

    reporter.message('C3 compilation listings for {}'.format(sources))
    reporter.message('{} {}'.format(ir_module, ir_module.stats()))
    reporter.dump_ir(ir_module)
    return ir_module


class C3Builder:
    """ Generates IR-code from c3 source.

    Reports errors to the diagnostics system.
    """
    logger = logging.getLogger('c3')

    def __init__(self, diag, arch_info):
        assert isinstance(arch_info, ArchInfo)
        self.diag = diag
        self.lexer = Lexer(diag)
        self.parser = Parser(diag)
        self.codegen = CodeGenerator(diag)
        self.verifier = Verifier()
        self.arch_info = arch_info

    def build(self, sources, imps=()):
        """ Create IR-code from sources.

        Returns:
            A context where modules are living in and an
            ir-module.

        Raises compiler error when something goes wrong.
        """
        assert isinstance(sources, (tuple, list))
        assert isinstance(imps, (tuple, list))
        self.logger.debug(
            'Building %d sources and %d includes', len(sources), len(imps))

        # Create a context where the modules can live:
        context = Context(self.arch_info)

        # Phase 1: Lexing and parsing stage
        for src in itertools.chain(sources, imps):
            self.do_parse(src, context)

        # Phase 1.8: Handle imports:
        try:
            context.link_imports()
        except SemanticError as ex:
            self.diag.error(ex.msg, ex.loc)
            raise

        type_checker = TypeChecker(self.diag, context)
        type_checker.check()

        # Phase 2: Generate intermediate code
        ir_module = self.codegen.gen(context)

        # Check modules
        self.verifier.verify(ir_module)

        self.logger.debug('C3 build complete!')
        return context, ir_module

    def do_parse(self, src, context):
        """ Lexing and parsing stage (phase 1) """
        tokens = self.lexer.lex(src)
        self.parser.parse_source(tokens, context)


class C3ExprParser:
    """
        Generates IR-code from c3 source.
        Reports errors to the diagnostics system.
    """
    def __init__(self, arch_info):
        self.logger = logging.getLogger('c3')
        diag = DiagnosticsManager()
        self.diag = diag
        self.arch_info = arch_info
        self.lexer = Lexer(diag)
        self.parser = Parser(diag)

    def parse(self, src, context):
        """ Parse an expression """
        self.parser.current_scope = context.scope
        tokens = self.lexer.lex(io.StringIO(src))
        self.parser.init_lexer(tokens)
        expr = self.parser.parse_expression()
        # TODO:
        # type_checker = TypeChecker(self.diag, context)
        # type_checker.check_expr(expr)
        return expr
