from ..target import Target
from .registers import r10, r11, r12, r13, r14, r15, Msp430Register
from ...ir import i8, i16, ptr
from .instructions import isa
from ..data_instructions import data_isa
from .frame import Msp430Frame
from ...binutils.assembler import BaseAssembler


class Msp430Target(Target):
    def __init__(self):
        super().__init__('msp430')
        self.byte_sizes['int'] = 2
        self.byte_sizes['ptr'] = 2
        self.value_classes[i16] = Msp430Register
        self.value_classes[ptr] = Msp430Register
        self.value_classes[i8] = Msp430Register
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
