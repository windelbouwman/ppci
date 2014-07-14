from .astnodes import Constant, Variable, Function, BaseType, Symbol
from .astnodes import ArrayType, StructureType, DefinedType, PointerType
from .astnodes import StructField


class Scope:
    """ A scope contains all symbols in a scope. It also has a parent scope,
        when looking for a symbol, also the parent scopes are checked. """
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent

    def __iter__(self):
        # Iterate in a deterministic manner:
        return iter(self.Constants + self.Variables + self.Functions)

    @property
    def Syms(self):
        """ Get all the symbols defined in this scope """
        syms = self.symbols.values()
        return sorted(syms, key=lambda v: v.name)

    @property
    def Types(self):
        return [s for s in self.Syms if isinstance(s, DefinedType)]

    @property
    def Constants(self):
        return [s for s in self.Syms if type(s) is Constant]

    @property
    def Variables(self):
        return [s for s in self.Syms if isinstance(s, Variable)]

    @property
    def Functions(self):
        return [s for s in self.Syms if type(s) is Function]

    def getSymbol(self, name):
        if name in self.symbols:
            return self.symbols[name]
        # Look for symbol:
        elif self.parent:
            return self.parent.getSymbol(name)
        else:
            raise KeyError(name)

    def __getitem__(self, key):
        return self.getSymbol(key)

    def hasSymbol(self, name):
        if name in self.symbols:
            return True
        elif self.parent:
            return self.parent.hasSymbol(name)
        else:
            return False

    def __contains__(self, name):
        return self.hasSymbol(name)

    def addSymbol(self, sym):
        assert sym.name not in self.symbols
        assert isinstance(sym, Symbol)
        self.symbols[sym.name] = sym

    def __repr__(self):
        return 'Scope with {} symbols'.format(len(self.symbols))


def createTopScope(target):
    scope = Scope()
    for tn in ['u64', 'u32', 'u16', 'u8']:
        scope.addSymbol(BaseType(tn))
    # buildin types:
    intType = BaseType('int')
    intType.bytesize = target.byte_sizes['int']
    scope.addSymbol(intType)
    scope.addSymbol(BaseType('double'))
    scope.addSymbol(BaseType('void'))
    scope.addSymbol(BaseType('bool'))
    byteType = BaseType('byte')
    byteType.bytesize = target.byte_sizes['byte']
    scope.addSymbol(byteType)

    # Construct string type from others:
    ln = StructField('len', intType)
    txt = StructField('txt', ArrayType(byteType, 0))
    strType = DefinedType('string', PointerType(StructureType([ln, txt])),
                          None)
    scope.addSymbol(strType)
    return scope
