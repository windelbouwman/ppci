"""
Tools for representing, loading and exporting WASM (Web Assembly),
and for converting between PPCI-IR and WASM.
"""

from .opcodes import I
from .components import *
from .components import Ref
from .wasm2ppci import wasm_to_ir
from .ppci2wasm import ir_to_wasm
from .arch import WasmArchitecture
from .util import run_wasm_in_node, export_wasm_example
from .util import run_wasm_in_notebook, has_node
from ._instantiate import instantiate


def read_wasm(input) -> Module:
    """ Read wasm in the form of a string, tuple, bytes or file object.
    Returns a wasm Module object.
    """
    return Module(input)


def read_wat(f) -> Module:
    """ Read wasm module from file handle """
    wat = f.read()
    return Module(wat)


def wasmify(func, target='native'):
    """ Convert a Python function to a WASM function, compiled
    to native code. Assumes that all variables are floats.
    Can be used as a decorator, like Numba!
    """
    
    from ppci.lang.python import python_to_wasm
    from ppci.wasm import instantiate
    
    def f64_print(x: float) -> None:
        print(x)
    
    wa = python_to_wasm(func)
    imports = {'env':{'f64_print': f64_print}}
    mod = instantiate(wa, imports, target=target)
    wasmfunc = getattr(mod.exports, func.__name__)
    return wasmfunc


__all__ = list(globals())
