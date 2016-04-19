"""
    Entry point when building c3 sources.
"""

import logging
import collections
from ...common import CompilerError
from ...irutils import Verifier
from ...opt.mem2reg import Mem2RegPromotor
from .lexer import Lexer
from .parser import Parser
from .codegenerator import CodeGenerator
from .scope import Context, SemanticError
from ...binutils.debuginfo import DebugDb


class C3Builder:
    """
        Generates IR-code from c3 source.
        Reports errors to the diagnostics system.
    """
    def __init__(self, diag, arch):
        self.logger = logging.getLogger('c3')
        self.diag = diag
        self.lexer = Lexer(diag)
        self.parser = Parser(diag)
        self.debug_db = DebugDb()
        self.codegen = CodeGenerator(diag, self.debug_db)
        self.verifier = Verifier()
        self.target = arch

    def build(self, srcs, imps=()):
        """
            Create IR-code from sources. Raises compiler error when something
            goes wrong.
            Returns a context where modules are living in and a list of
            generated ir modules.
        """
        assert isinstance(srcs, collections.Iterable)
        assert isinstance(imps, collections.Iterable)
        self.logger.debug(
            'Building %d sources and %d includes', len(srcs), len(imps))

        # Create a context where the modules can live:
        context = Context(self.target)

        # Phase 1: Lexing and parsing stage
        for src in srcs:
            self.do_parse(src, context)
        for src in imps:
            self.do_parse(src, context)

        # Phase 1.8: Handle imports:
        self.logger.debug('Resolving imports')
        try:
            for mod in context.modules:
                for imp in mod.imports:
                    if context.has_module(imp):
                        if mod.inner_scope.has_symbol(imp):
                            raise SemanticError("Redefine of {}".format(imp))
                        mod.inner_scope.add_symbol(context.get_module(imp))
                    else:
                        msg = 'Cannot import {}'.format(imp)
                        raise SemanticError(msg)
        except SemanticError as ex:
            self.diag.error(ex.msg, ex.loc)
            raise

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
        pas = Mem2RegPromotor(self.debug_db)
        pas.run(ir_module)
        self.verifier.verify(ir_module)

    def do_parse(self, src, context):
        """ Lexing and parsing stage (phase 1) """
        tokens = self.lexer.lex(src)
        self.parser.parse_source(tokens, context)
