""" Code for converting between PPCI-IR and WASM (Web Assembly) """

from ._opcodes import OPCODES, I
from .components import *
from .util import *
from .wasm2ppci import wasm_to_ir, WasmToIrCompiler
from .ppci2wasm import ir_to_wasm, IrToWasmCompiler


__all__ = ['wasm_to_ir', 'ir_to_wasm', 'WasmToIrCompiler', 'IrToWasmCompiler']
