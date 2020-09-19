""" Regular expression routines.

Implement regular expressions using derivatives.

Largely copied from: https://github.com/MichaelPaddon/epsilon

Implementation of this logic:
https://en.wikipedia.org/wiki/Brzozowski_derivative

Another good resource on regular expressions:
https://swtch.com/~rsc/regexp/

"""

from .regex import Symbol, SymbolSet, Kleene, EPSILON, NULL
from .parser import parse
from .compiler import compile
from .scanner import make_scanner, scan
from .codegen import generate_code


__all__ = (
    "parse",
    "compile",
    "Symbol",
    "SymbolSet",
    "Kleene",
    "generate_code",
)
