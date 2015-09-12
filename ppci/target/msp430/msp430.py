from ..target import Target
from .registers import r10, r11, r12, r13, r14, r15
from .instructions import isa
from ..data_instructions import data_isa
from .frame import Msp430Frame
from ...binutils.assembler import BaseAssembler


class Msp430Target(Target):
    def __init__(self):
        super().__init__('msp430')
        self.byte_sizes['int'] = 2  # For front end!
        self.byte_sizes['ptr'] = 2  # For front end!
        self.isa = isa + data_isa
        self.assembler = BaseAssembler(self)
        self.assembler.gen_asm_parser()

        self.FrameClass = Msp430Frame

        self.registers.append(r10)
        self.registers.append(r11)
        self.registers.append(r12)
        self.registers.append(r13)
        self.registers.append(r14)
        self.registers.append(r15)

    def get_runtime_src(self):
        return ''
