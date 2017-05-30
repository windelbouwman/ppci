
from ..isa import Isa
from ..token import Token, bit_range


orbis32 = Isa()


class Orbis32BaseToken(Token):
    class Info:
        size = 32
        endianness = 'big'

    opcode = bit_range(26, 32)
    rd = bit_range(21, 26)
    ra = bit_range(16, 21)
    rb = bit_range(11, 16)
    allbits = bit_range(0, 32)


class Orbis32Token(Orbis32BaseToken):
    opcode2 = bit_range(0, 11)
    imm = bit_range(0, 16)
    n = bit_range(0, 26)
    k = bit_range(0, 16)


class Orbis32StoreToken(Orbis32BaseToken):
    imm = bit_range(21, 26) + bit_range(0, 11)


class Orbis32ShiftImmediateToken(Orbis32BaseToken):
    opcode2 = bit_range(6, 8)
    l = bit_range(0, 6)
