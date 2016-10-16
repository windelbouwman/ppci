""" 6502 instructions """

from ..isa import Isa
from ..encoding import Instruction, Syntax


isa = Isa()


class Mos6500Instruction(Instruction):
    isa = isa


class Brk(Mos6500Instruction):
    syntax = Syntax(['brk'])

    def encode(self):
        return bytes([0])
