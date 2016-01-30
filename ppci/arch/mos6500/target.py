from ..target import Target, VCall
from ...binutils.assembler import BaseAssembler
from .instructions import isa


class Mos6500Target(Target):
    def __init__(self):
        super().__init__('6500')
        self.isa = isa
        self.assembler = BaseAssembler()
        self.assembler.gen_asm_parser(isa)
