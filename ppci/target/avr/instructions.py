
from ..isa import Instruction, Isa, register_argument, Syntax
from ..isa import FixedPattern, SubPattern
from ..token import Token, u16, bit_range, bit, bit_concat, u8
from .registers import AvrRegister


class AvrToken(Token):
    def __init__(self):
        super().__init__(16)
    w0 = bit_range(0, 16)
    b0 = bit_range(0, 8)
    b1 = bit_range(8, 16)
    n0 = bit_range(0, 4)
    n1 = bit_range(4, 8)
    n2 = bit_range(8, 12)
    n3 = bit_range(12, 16)

    def encode(self):
        return u16(self.bit_value)


class AvrToken1(AvrToken):
    op = bit_range(10, 16)
    r = bit_concat(bit(9), bit_range(0, 4))
    d = bit_range(4, 9)


avr_isa = Isa()


class AvrInstruction(Instruction):
    isa = avr_isa
    tokens = [AvrToken]


class Add(AvrInstruction):
    tokens = [AvrToken1]
    rd = register_argument('rd', AvrRegister, read=True, write=True)
    rr = register_argument('rr', AvrRegister, read=True)
    syntax = Syntax(['add', rd, ',', rr])
    patterns = [
        FixedPattern('op', 3),
        SubPattern('r', rr),
        SubPattern('d', rd)]


class Sub(AvrInstruction):
    tokens = [AvrToken1]
    rd = register_argument('rd', AvrRegister, read=True, write=True)
    rr = register_argument('rr', AvrRegister, read=True)
    syntax = Syntax(['sub', rd, ',', rr])
    patterns = [
        FixedPattern('op', 0b110),
        SubPattern('r', rr),
        SubPattern('d', rd)]


class And(AvrInstruction):
    rd = register_argument('rd', AvrRegister, read=True, write=True)
    rr = register_argument('rr', AvrRegister, read=True)
    syntax = Syntax(['and', rd, ',', rr])
    patterns = [
        FixedPattern('mod', 0),
        FixedPattern('mod', 0)]


class Jmp(AvrInstruction):
    lab = register_argument('lab', str)
    syntax = Syntax(['jmp', lab])


class Mov(AvrInstruction):
    tokens = [AvrToken1]
    rd = register_argument('rd', AvrRegister, read=True, write=True)
    rr = register_argument('rr', AvrRegister, read=True)
    syntax = Syntax(['mov', rd, ',', rr])
    patterns = [
        FixedPattern('op', 0b1011),
        SubPattern('r', rr),
        SubPattern('d', rd)]


class Nop(AvrInstruction):
    syntax = Syntax(['nop'])
    patterns = [FixedPattern('w0', 0)]


class Ret(AvrInstruction):
    syntax = Syntax(['ret'])
    patterns = [FixedPattern('w0', 0b1001010100001000)]
