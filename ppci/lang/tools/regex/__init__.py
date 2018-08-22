""" Regular expression routines.

Implement regular expressions using derivatives.

"""


from .regex import Symbol, SymbolSet, Kleene
from .parser import parse


__all__ = (
    'parse',
    'SymbolSet', 'Kleene')
