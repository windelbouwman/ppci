"""
    X86-64 target description.
"""

from ..target import Target
from ...binutils.assembler import BaseAssembler
from ...ir import i64, i8, ptr
from ..data_instructions import data_isa
from .instructions import isa
from .registers import X86Register
from .frame import X86Frame


class X86Target(Target):
    """ x86 target containing assembler, linker"""
    def __init__(self):
        super().__init__('x86')
        self.value_classes[i64] = X86Register
        self.value_classes[ptr] = X86Register
        self.value_classes[i8] = X86Register
        self.byte_sizes['int'] = 8  # For front end!
        self.byte_sizes['ptr'] = 8  # For front end!
        self.isa = isa + data_isa
        self.assembler = BaseAssembler(self)
        self.FrameClass = X86Frame
        self.assembler.gen_asm_parser()
