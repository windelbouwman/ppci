"""
    X86-64 target description.
"""

from ..target import Target
from ...assembler import BaseAssembler
from .instructions import isa


class X86Target(Target):
    """ x86 target containing assembler, linker"""
    def __init__(self):
        super().__init__('x86')
        self.isa = isa
        self.assembler = BaseAssembler(self)
        self.assembler.gen_asm_parser()
