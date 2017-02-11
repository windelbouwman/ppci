import itertools
from . import nodes


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
        return [s for s in self.syms if isinstance(s, nodes.DefinedType)]

    @property
    def constants(self):
        """ All defined constants in this scope """
        return [s for s in self.syms if isinstance(s, nodes.Constant)]

    @property
    def variables(self):
        """ All variables defined in the current scope """
        return [s for s in self.syms if isinstance(s, nodes.Variable)]

    @property
    def functions(self):
        """ Gets all the functions in the current scope """
        return [s for s in self.syms if isinstance(s, nodes.Function)]

    def __getitem__(self, key):
        return self.get_symbol(key)

    def get_symbol(self, name: str):
        """ Get symbol from this or parent scope """
        assert isinstance(name, str)
        if name in self.symbols:
            return self.symbols[name]
        elif self.parent:
            return self.parent.get_symbol(name)
        else:  # pragma: no cover
            raise KeyError(name)

    def has_symbol(self, name: str, include_parent=True):
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
        assert isinstance(sym, nodes.Symbol)
        self.symbols[sym.name] = sym

    def __repr__(self):
        return 'Scope with {} symbols'.format(len(self.symbols))
