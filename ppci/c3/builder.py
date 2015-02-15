"""
    Entry point when building c3 sources.
"""

import logging
import collections
from .lexer import Lexer
from .parser import Parser
from .codegenerator import CodeGenerator
from .scope import Scope, Context
from .visitor import Visitor
from .astnodes import Module, Function, Identifier, Symbol


class C3Pass:
    def __init__(self, diag):
        self.diag = diag
        self.logger = logging.getLogger('c3')
        self.visitor = Visitor()

    def error(self, msg, loc=None):
        self.pkg.ok = False
        self.diag.error(msg, loc)

    def visit(self, pkg, pre, post):
        self.visitor.visit(pkg, pre, post)


class ScopeFiller(C3Pass):
    """ Pass that fills the scopes with symbols """
    scoped_types = [Module, Function]

    def add_scope(self, pkg, context):
        """ Scope is attached to the correct modules. """
        self.logger.debug('Adding scoping to package {}'.format(pkg.name))
        self.pkg = pkg
        # Prepare top level scope and set scope to all objects:
        self.scopeStack = [context.scope]
        mod_scope = Scope(self.current_scope)
        self.scopeStack.append(mod_scope)
        self.visit(pkg, self.enter_scope, self.quitScope)
        assert len(self.scopeStack) == 2

        self.logger.debug('Resolving imports for package {}'.format(pkg.name))

        # Handle imports:
        for i in pkg.imports:
            if context.has_module(i):
                pkg.scope.add_symbol(context.get_module(i))
            else:
                self.error('Cannot import {}'.format(i))

    @property
    def current_scope(self):
        """ Gets the current scope """
        return self.scopeStack[-1]

    def add_symbol(self, sym):
        """ Add a symbol to the current scope """
        if self.current_scope.has_symbol(sym.name, include_parent=False):
            self.error('Redefinition of {0}'.format(sym.name), sym.loc)
        else:
            self.current_scope.add_symbol(sym)

    def enter_scope(self, sym):
        # Attach scope to references, so they can be looked up:
        if type(sym) is Identifier:
            sym.scope = self.current_scope

        # Add symbols to current scope:
        if isinstance(sym, Symbol):
            self.add_symbol(sym)
            sym.scope = self.current_scope

        # Create subscope for items creating a scope:
        if type(sym) in self.scoped_types:
            scope = Scope(self.current_scope)
            self.scopeStack.append(scope)
            sym.innerScope = self.current_scope

    def quitScope(self, sym):
        # Pop out of scope:
        if type(sym) in self.scoped_types:
            self.scopeStack.pop(-1)


class Builder:
    """
        Generates IR-code from c3 source.
        Reports errors to the diagnostics system.
    """
    def __init__(self, diag, target):
        self.logger = logging.getLogger('c3')
        self.diag = diag
        self.lexer = Lexer(diag)
        self.parser = Parser(diag)
        self.sema = None
        self.codegen = CodeGenerator(diag)
        self.target = target

    def build(self, srcs, imps=()):
        """ Create IR-code from sources. Raises compiler error when something
            goes wrong. Returns a list of ir-code modules.
        """
        assert isinstance(srcs, collections.Iterable)
        assert isinstance(imps, collections.Iterable)
        self.logger.debug('Building {} source files'.format(len(srcs)))
        self.logger.debug('Using {} includes'.format(len(imps)))

        # Create a context where the modules can live:
        context = Context(self.target)

        # Lexing and parsing stage (phase 1)
        for src in srcs:
            self.do_parse(src, context)
        for src in imps:
            self.do_parse(src, context)

        self.logger.debug('Parsing complete')

        self.fill_scopes(context)

        # Phase 1.9
        for module in context.modules:
            self.codegen.gen_globals(module, context)

        # Generate intermediate code (phase 2)
        # Only return ircode when everything is OK
        ir_modules = []
        for pkg in context.modules:
            ir_modules.append(self.codegen.gencode(pkg, context))
        self.logger.debug('C3 build complete!')
        return ir_modules

    def do_parse(self, src, context):
        """ Lexing and parsing stage (phase 1) """
        tokens = self.lexer.lex(src)
        self.parser.parse_source(tokens, context)

    def fill_scopes(self, context):
        """ Fix scopes and package refs (phase 1.5) """
        scope_filler = ScopeFiller(self.diag)

        # Fix scopes:
        for pkg in context.modules:
            scope_filler.add_scope(pkg, context)
