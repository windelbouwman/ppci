from ..arch import Architecture
from ...binutils.assembler import BaseAssembler
from .instructions import isa


class Mcs6500Arch(Architecture):
    name = 'mcs6500'

    def __init__(self, options=None):
        super().__init__(options=options)
        self.isa = isa
        self.assembler = BaseAssembler()
        self.assembler.gen_asm_parser(isa)
