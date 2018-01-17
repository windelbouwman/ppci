""" Code for converting between PPCI-IR and WASM (Web Assembly) """

from .components import read_wasm
from .wasm2ppci import wasm_to_ir, WasmToIrCompiler
from .ppci2wasm import ir_to_wasm, IrToWasmCompiler
from .arch import WasmArchitecture
from .wat import wasm_to_wat


__all__ = [
    'wasm_to_ir', 'ir_to_wasm', 'read_wasm', 'wasm_to_wat',
    'WasmToIrCompiler', 'IrToWasmCompiler',
    'WasmArchitecture']
