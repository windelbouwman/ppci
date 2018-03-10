"""
Tools for representing, loading and exporting WASM (Web Assembly),
and for converting between PPCI-IR and WASM.
"""

from .opcodes import I
from .components import *
from .wasm2ppci import wasm_to_ir
from .ppci2wasm import ir_to_wasm
from .arch import WasmArchitecture
from .util import run_wasm_in_node, export_wasm_example, run_wasm_in_notebook


def read_wasm(input) -> Module:
    """ Read wasm in the form of a string, tuple, bytes or file object.
    Returns a wasm Module object.
    """
    return Module(input)


def read_wat(f) -> Module:
    """ Read wasm module from file handle """
    wat = f.read()
    return Module(wat)


__all__ = list(globals())
