
""" Contains instruction set for creating binary data.

For example:

db 0 -> 00
dw 0 -> 0000
dd 2 -> 02000000

"""

from .isa import Isa
from .encoding import Instruction, Operand, Syntax, Relocation
from .token import Token, bit_range, u32

data_isa = Isa()


class ByteToken(Token):
    size = 8
    value = bit_range(0, 8)


class WordToken(Token):
    size = 16
    value = bit_range(0, 16)


class DwordToken(Token):
    size = 32
    value = bit_range(0, 32)


class DataInstruction(Instruction):
    isa = data_isa


class Db(DataInstruction):
    tokens = [ByteToken]
    v = Operand('v', int)
    syntax = Syntax(['db', ' ', v])
    patterns = {'value': v}


class Dw(DataInstruction):
    tokens = [WordToken]
    v = Operand('v', int)
    syntax = Syntax(['dw', ' ', v])
    patterns = {'value': v}


class Dw2(DataInstruction):
    tokens = [WordToken]
    v = Operand('v', str)
    syntax = Syntax(['dw', ' ', v])

    def relocations(self):
        return [U16DataRelocation(self.v)]


@data_isa.register_relocation
class U16DataRelocation(Relocation):
    name = 'absaddr16'
    token = WordToken
    field = 'value'

    def calc(self, sym_value, reloc_value):
        assert sym_value % 2 == 0
        assert reloc_value % 2 == 0
        return sym_value


class Dd(DataInstruction):
    tokens = [DwordToken]
    v = Operand('v', int)
    syntax = Syntax(['dd', ' ', v])
    patterns = {'value': v}


@data_isa.register_relocation
class U32DataRelocation(Relocation):
    name = 'absaddr32'
    token = DwordToken
    field = 'value'

    def calc(self, sym_value, reloc_value):
        assert sym_value % 4 == 0
        assert reloc_value % 4 == 0
        return sym_value


class Dcd2(DataInstruction):
    v = Operand('v', str)
    syntax = Syntax(['dcd', ' ', '=', v])

    def encode(self):
        return u32(0)

    def relocations(self):
        return [U32DataRelocation(self.v)]


class Ds(DataInstruction):
    """ Reserve an amount of space """
    tokens = []
    v = Operand('v', int)
    syntax = Syntax(['ds', ' ', v])

    def encode(self):
        return bytes([0] * self.v)
