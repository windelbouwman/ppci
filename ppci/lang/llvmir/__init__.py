""" Front-end for the LLVM IR-code

This front-end can be used as an enabler for many other languages, for example
ADA and C++.

"""

from .parser import LlvmIrFrontend


__all__ = ['LlvmIrFrontend']
