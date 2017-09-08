"""
Code for converting between PPCI-IR and WASM (Web Assembly)
"""

from ._opcodes import OPCODES, I
from .components import *
from .util import *
from .wasm2ppci import wasm_to_ppci
