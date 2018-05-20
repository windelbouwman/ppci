""" Front-end for the LLVM IR-code

This front-end can be used as an enabler for many other languages, for example
ADA and C++.


Currently this module a work in progress. The first step is to parse the
llvm assembly. The next phase would be to convert that into ppci ir.

Another nice idea is to generate llvm ir code from ppci. When generating
and parsing are combined, the llvm optimizers can be used.

"""

from .frontend import LlvmIrFrontend, llvm_to_ir


__all__ = ['llvm_to_ir', 'LlvmIrFrontend']
