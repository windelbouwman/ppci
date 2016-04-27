from ..arch import Architecture, VCall
from ...binutils.assembler import BaseAssembler
from .instructions import isa


class Mos6500Arch(Architecture):
    name = '6500'

    def __init__(self, options=None):
        super().__init__(options=options)
        self.isa = isa
        self.assembler = BaseAssembler()
        self.assembler.gen_asm_parser(isa)
