"""
    X86-64 target description.
"""

from ..target import Target
from ...assembler import BaseAssembler
from .instructions import isa, reloc_map


class X86Assembler(BaseAssembler):
    def __init__(self, target):
        super().__init__(target)
        # Add isa instructions:
        self.gen_asm_parser(isa)


class X86Target(Target):
    """ x86 target containing assembler, linker"""
    def __init__(self):
        super().__init__('x86')

        self.reloc_map = reloc_map
        self.assembler = X86Assembler(self)
