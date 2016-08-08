from ..isa import Isa
from ..encoding import FixedPattern, Instruction, Syntax
from ..token import bit_range, Token, u8


class Stm8OpToken(Token):
    def __init__(self):
        super().__init__(8)
    op = bit_range(0, 8)

    def encode(self):
        return u8(self.bit_value)


stm8_isa = Isa()


class Stm8Instruction(Instruction):
    isa = stm8_isa


class Nop(Stm8Instruction):
    tokens = [Stm8OpToken]
    syntax = Syntax(['nop'])
    patterns = [FixedPattern('op', 0x9D)]