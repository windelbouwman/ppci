
""" Contains instruction set for creating binary data.

For example:

dw 0 -> 00
db 0 -> 0000
dd 2 -> 02000000

"""

from .isa import Instruction, Isa, register_argument, Syntax
from .token import Token, u16, bit_range, bit, u8, u32

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
    syntax = ['db', v]

    def encode(self):
        self.token.value = self.v
        return self.token.encode()


class Dw(DataInstruction):
    tokens = [WordToken]
    v = register_argument('v', int)
    syntax = ['dw', v]

    def encode(self):
        self.token.value = self.v
        return self.token.encode()


class Dd(DataInstruction):
    tokens = [DwordToken]
    v = register_argument('v', int)
    syntax = ['dd', v]

    def encode(self):
        self.token.value = self.v
        return self.token.encode()


class Ds(DataInstruction):
    """ Reserve an amount of space """
    tokens = []
    v = register_argument('v', int)
    syntax = ['ds', v]

    def encode(self):
        return bytes([0] * self.v)
