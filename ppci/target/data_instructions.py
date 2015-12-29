
""" Contains instruction set for creating binary data.

For example:

db 0 -> 00
dw 0 -> 0000
dd 2 -> 02000000

"""

from .isa import Instruction, Isa, register_argument, Syntax, VariablePattern
from .token import Token, u16, bit_range, u8, u32

data_isa = Isa()


class ByteToken(Token):
    value = bit_range(0, 8)

    def __init__(self):
        super().__init__(8)

    def encode(self):
        return u8(self.bit_value)


class WordToken(Token):
    value = bit_range(0, 16)

    def __init__(self):
        super().__init__(16)

    def encode(self):
        return u16(self.bit_value)


class DwordToken(Token):
    value = bit_range(0, 32)

    def __init__(self):
        super().__init__(32)

    def encode(self):
        return u32(self.bit_value)


class DataInstruction(Instruction):
    isa = data_isa


class Db(DataInstruction):
    tokens = [ByteToken]
    v = register_argument('v', int)
    syntax = Syntax(['db', v])
    patterns = [VariablePattern('value', v)]


class Dw(DataInstruction):
    tokens = [WordToken]
    v = register_argument('v', int)
    syntax = Syntax(['dw', v])
    patterns = [VariablePattern('value', v)]


class Dd(DataInstruction):
    tokens = [DwordToken]
    v = register_argument('v', int)
    syntax = Syntax(['dd', v])
    patterns = [VariablePattern('value', v)]


class Ds(DataInstruction):
    """ Reserve an amount of space """
    tokens = []
    v = register_argument('v', int)
    syntax = Syntax(['ds', v])

    def encode(self):
        return bytes([0] * self.v)
