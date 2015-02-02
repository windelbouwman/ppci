"""
    Entry point when building c3 sources.
"""

import logging
import collections
from .lexer import Lexer
from .parser import Parser
from .codegenerator import CodeGenerator
from .scope import createTopScope, Scope
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

    def __init__(self, diag, topScope, packages):
        super().__init__(diag)
        self.topScope = topScope
        self.packages = packages

    def add_scope(self, pkg):
        """ Scope is attached to the correct modules. """
        self.logger.debug('Adding scoping to package {}'.format(pkg.name))
        self.pkg = pkg
        # Prepare top level scope and set scope to all objects:
        self.scopeStack = [self.topScope]
        modScope = Scope(self.CurrentScope)
        self.scopeStack.append(modScope)
        self.visit(pkg, self.enterScope, self.quitScope)
        assert len(self.scopeStack) == 2

        self.logger.debug('Resolving imports for package {}'.format(pkg.name))

        # Handle imports:
        for i in pkg.imports:
            if i not in self.packages:
                self.error('Cannot import {}'.format(i))
                continue
            pkg.scope.add_symbol(self.packages[i])

    @property
    def CurrentScope(self):
        return self.scopeStack[-1]

    def addSymbol(self, sym):
        if self.CurrentScope.has_symbol(sym.name):
            self.error('Redefinition of {0}'.format(sym.name), sym.loc)
        else:
            self.CurrentScope.add_symbol(sym)

    def enterScope(self, sym):
        # Attach scope to references:
        if type(sym) is Identifier:
            sym.scope = self.CurrentScope

        # Add symbols to current scope:
        if isinstance(sym, Symbol):
            self.addSymbol(sym)
            sym.scope = self.CurrentScope

        # Create subscope for items creating a scope:
        if type(sym) in self.scoped_types:
            newScope = Scope(self.CurrentScope)
            self.scopeStack.append(newScope)
            sym.innerScope = self.CurrentScope

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
        self.parser = Parser(diag, self)
        self.codegen = CodeGenerator(diag)
        self.top_scope = createTopScope(target)  # Scope with built in types

    def get_module(self, name):
        """ Gets or creates the module with the given name """
        if name not in self.modules:
            self.modules[name] = Module(name, None)
        return self.modules[name]

    def build(self, srcs, imps=()):
        """ Create IR-code from sources """
        assert isinstance(srcs, collections.Iterable)
        assert isinstance(imps, collections.Iterable)
        self.logger.debug('Building {} source files'.format(len(srcs)))
        self.logger.debug('Using {} includes'.format(len(imps)))
        self.ok = True
        self.modules = {}

        # Lexing and parsing stage (phase 1)
        s_pkgs = [self.do_parse(src) for src in srcs]
        i_pkgs = [self.do_parse(src) for src in imps]
        all_pkgs = s_pkgs + i_pkgs
        if not all(all_pkgs):
            self.ok = False
            self.logger.debug('Parsing failed')
            return

        self.logger.debug('Parsed {} packages'.format(len(all_pkgs)))

        self.fill_scopes(all_pkgs)

        if not all(pkg.ok for pkg in all_pkgs):
            self.ok = False
            self.logger.debug('Scope filling failed')
            return

        # Generate intermediate code (phase 2)
        # Only return ircode when everything is OK
        for pkg in s_pkgs:
            yield self.codegen.gencode(pkg)
        if not all(pkg.ok for pkg in all_pkgs):
            self.logger.debug('Code generation failed')
            self.ok = False
        self.logger.debug('C3 build complete!')

    def do_parse(self, src):
        """ Lexing and parsing stage (phase 1) """
        tokens = self.lexer.lex(src)
        pkg = self.parser.parse_source(tokens)
        return pkg

    def fill_scopes(self, all_pkgs):
        """ Fix scopes and package refs (phase 1.5) """
        packages = {pkg.name: pkg for pkg in all_pkgs}

        scopeFiller = ScopeFiller(self.diag, self.top_scope, packages)
        # Fix scopes:
        for pkg in all_pkgs:
            scopeFiller.add_scope(pkg)
