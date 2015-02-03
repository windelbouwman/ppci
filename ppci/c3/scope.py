"""
    This file contains the scope and context classes.
    Scopes are used for scoping modules, functions.
    A context is the space where the whole program lives.
"""

from .astnodes import Constant, Variable, Function, BaseType, Symbol
from .astnodes import ArrayType, StructureType, DefinedType, PointerType
from .astnodes import StructField
from . import astnodes as ast
from ..common import CompilerError


class SemanticError(CompilerError):
    """ Error thrown when a semantic issue is observed """
    pass


class Scope:
    """ A scope contains all symbols in a scope. It also has a parent scope,
        when looking for a symbol, also the parent scopes are checked. """
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent

    def __iter__(self):
        # Iterate in a deterministic manner:
        return iter(self.constants + self.Variables + self.Functions)

    @property
    def Syms(self):
        """ Get all the symbols defined in this scope """
        syms = self.symbols.values()
        return sorted(syms, key=lambda v: v.name)

    @property
    def types(self):
        """ Returns all the types in this scope """
        return [s for s in self.Syms if isinstance(s, DefinedType)]

    @property
    def constants(self):
        """ All defined constants in this scope """
        return [s for s in self.Syms if type(s) is Constant]

    @property
    def Variables(self):
        return [s for s in self.Syms if isinstance(s, Variable)]

    @property
    def Functions(self):
        return [s for s in self.Syms if type(s) is Function]

    def get_symbol(self, name):
        """ Get symbol from this or parent scope """
        if name in self.symbols:
            return self.symbols[name]
        # Look for symbol:
        elif self.parent:
            return self.parent.get_symbol(name)
        else:
            raise KeyError(name)

    def __getitem__(self, key):
        return self.get_symbol(key)

    def has_symbol(self, name):
        """ Check if name is a defined symbol in this or parent scope """
        if name in self.symbols:
            return True
        elif self.parent:
            return self.parent.has_symbol(name)
        else:
            return False

    def __contains__(self, name):
        return self.has_symbol(name)

    def add_symbol(self, sym):
        """ Add a symbol to this scope """
        assert sym.name not in self.symbols
        assert isinstance(sym, Symbol)
        self.symbols[sym.name] = sym

    def __repr__(self):
        return 'Scope with {} symbols'.format(len(self.symbols))


def createTopScope(target):
    """ Create a scope that is the root of the scope tree. This includes
        the built-in types """
    scope = Scope()

    # stdlib types:
    scope.add_symbol(BaseType('uint64_t', 8))
    scope.add_symbol(BaseType('uint32_t', 4))
    scope.add_symbol(BaseType('uint16_t', 2))
    scope.add_symbol(BaseType('uint8_t', 1))

    # buildin types:
    int_type = BaseType('int', target.byte_sizes['int'])
    scope.add_symbol(int_type)
    scope.add_symbol(BaseType('double', 8))
    scope.add_symbol(BaseType('void', 0))
    scope.add_symbol(BaseType('bool', 1))
    byte_type = BaseType('byte', 1)
    scope.add_symbol(byte_type)

    # Construct string type from others:
    len_field = StructField('len', int_type)
    txt = StructField('txt', ArrayType(byte_type, 0))
    string_type = PointerType(StructureType([len_field, txt]))
    string_def_type = DefinedType('string', string_type, None)
    scope.add_symbol(string_def_type)
    return scope


class Context:
    """ A context is the space where all modules live in.
        It is actually the container of modules and the top
        level scope.
    """
    def __init__(self, target):
        self.scope = createTopScope(target)
        self.module_map = {}

    def has_module(self, name):
        return name in self.module_map

    def get_module(self, name):
        """ Gets or creates the module with the given name """
        if name not in self.module_map:
            self.module_map[name] = ast.Module(name, None)
        return self.module_map[name]

    @property
    def modules(self):
        return self.module_map.values()

    def resolve_symbol(self, sym):
        """ Find out what is designated with x """
        if type(sym) is ast.Member:
            base = self.resolve_symbol(sym.base)
            if type(base) is not ast.Module:
                raise SemanticError('Base is not a module', sym.loc)
            scope = base.innerScope
            name = sym.field
        elif type(sym) is ast.Identifier:
            scope = sym.scope
            name = sym.target
        else:
            raise NotImplementedError(str(sym))

        if name in scope:
            sym = scope[name]
        else:
            raise SemanticError('{} undefined'.format(name), sym.loc)
        assert isinstance(sym, ast.Symbol)
        return sym
