"""
    X86-64 target description.
"""

from ..target import Target
from ...binutils.assembler import BaseAssembler
from .instructions import isa
from .frame import X86Frame


class X86Target(Target):
    """ x86 target containing assembler, linker"""
    def __init__(self):
        super().__init__('x86')
        self.byte_sizes['int'] = 8  # For front end!
        self.byte_sizes['ptr'] = 8  # For front end!
        self.isa = isa
        self.assembler = BaseAssembler(self)
        self.FrameClass = X86Frame
        self.assembler.gen_asm_parser()
