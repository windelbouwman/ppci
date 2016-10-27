""" This file contains the scope and context classes.

Scopes are used for scoping modules, functions.
A context is the space where the whole program lives.
"""

import itertools
from ...common import CompilerError
from .astnodes import Constant, Variable, Function, BaseType, Symbol
from .astnodes import ArrayType, StructureType, DefinedType, PointerType
from .astnodes import StructField
from .astnodes import SignedIntegerType, UnsignedIntegerType, FloatType


class SemanticError(CompilerError):
    """ Error thrown when a semantic issue is observed """
    pass


class Scope:
    """ A scope contains all symbols in a scope.

    It also has a parent scope,
    when looking for a symbol, also the parent scopes are checked. """
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent

    def __iter__(self):
        # Iterate in a deterministic manner:
        return itertools.chain(
            self.types, self.constants, self.variables, self.functions)

    @property
    def syms(self):
        """ Get all the symbols defined in this scope """
        syms = self.symbols.values()
        return sorted(syms, key=lambda v: v.name)

    @property
    def types(self):
        """ Returns all the types in this scope """
        return [s for s in self.syms if isinstance(s, DefinedType)]

    @property
    def constants(self):
        """ All defined constants in this scope """
        return [s for s in self.syms if isinstance(s, Constant)]

    @property
    def variables(self):
        """ All variables defined in the current scope """
        return [s for s in self.syms if isinstance(s, Variable)]

    @property
    def functions(self):
        """ Gets all the functions in the current scope """
        return [s for s in self.syms if isinstance(s, Function)]

    def get_symbol(self, name):
        """ Get symbol from this or parent scope """
        if name in self.symbols:
            return self.symbols[name]
        # Look for symbol:
        elif self.parent:
            return self.parent.get_symbol(name)
        else:  # pragma: no cover
            raise KeyError(name)

    def __getitem__(self, key):
        return self.get_symbol(key)

    def has_symbol(self, name, include_parent=True):
        """ Check if name is a defined symbol in this or parent scope """
        if name in self.symbols:
            return True
        elif self.parent and include_parent:
            return self.parent.has_symbol(name)
        else:
            return False

    def add_symbol(self, sym):
        """ Add a symbol to this scope """
        assert sym.name not in self.symbols
        assert isinstance(sym, Symbol)
        self.symbols[sym.name] = sym

    def __repr__(self):
        return 'Scope with {} symbols'.format(len(self.symbols))


def create_top_scope(arch):
    """ Create a scope that is the root of the scope tree.

    This includes the built-in types.
    """
    scope = Scope()

    # stdlib types:
    scope.add_symbol(UnsignedIntegerType('uint64_t', 8))
    scope.add_symbol(UnsignedIntegerType('uint32_t', 4))
    scope.add_symbol(UnsignedIntegerType('uint16_t', 2))
    scope.add_symbol(UnsignedIntegerType('uint8_t', 1))
    scope.add_symbol(SignedIntegerType('int64_t', 8))
    scope.add_symbol(SignedIntegerType('int32_t', 4))
    scope.add_symbol(SignedIntegerType('int16_t', 2))
    scope.add_symbol(SignedIntegerType('int8_t', 1))

    # buildin types:
    int_type = SignedIntegerType('int', arch.byte_sizes['int'])
    byte_type = UnsignedIntegerType('byte', 1)
    scope.add_symbol(int_type)
    scope.add_symbol(FloatType('double', 8, 52))
    scope.add_symbol(FloatType('float', 4, 23))
    scope.add_symbol(BaseType('void', 0))
    scope.add_symbol(BaseType('bool', arch.byte_sizes['int']))
    scope.add_symbol(byte_type)

    # Construct string type from others:
    len_field = StructField('len', int_type)
    txt = StructField('txt', ArrayType(byte_type, 0))
    string_type = PointerType(StructureType([len_field, txt]))
    string_def_type = DefinedType('string', string_type, True, None)
    scope.add_symbol(string_def_type)
    return scope
