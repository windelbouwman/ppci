from ..isa import Instruction, Isa, register_argument, Syntax
from ..isa import FixedPattern, SubPattern, VariablePattern
from ..token import Token, u16, bit_range, bit, bit_concat
from ...bitfun import wrap_negative
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


class AvrToken2(AvrToken):
    op = bit_range(9, 16)
    d = bit_range(4, 9)


class AvrToken3(AvrToken):
    op = bit_range(11, 16)
    d = bit_range(4, 9)
    a = bit_concat(bit_range(9, 11), bit_range(0, 4))


class AvrToken4(AvrToken):
    op = bit_range(12, 16)
    d = bit_range(4, 8)
    k = bit_concat(bit_range(8, 12), bit_range(0, 4))


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


#class Jmp(AvrInstruction):
#    lab = register_argument('lab', str)
#    syntax = Syntax(['jmp', lab])


@avr_isa.register_relocation
def relsigned12bit(sym_value, data, reloc_value):
    """ Apply 10 bit signed relocation """
    assert sym_value % 2 == 0
    assert reloc_value % 2 == 0
    offset = (sym_value - reloc_value - 2) // 2
    assert offset in range(-2047, 2048), str(offset)
    imm12 = wrap_negative(offset, 12)
    data[0] = imm12 & 0xff
    data[1] = (data[1] & 0xf0) | (imm12 >> 8)


class Rjmp(AvrInstruction):
    lab = register_argument('lab', str)
    syntax = Syntax(['rjmp', lab])
    patterns = [FixedPattern('n3', 0xc)]

    def relocations(self):
        return [(self.lab, relsigned12bit)]


class Mov(AvrInstruction):
    tokens = [AvrToken1]
    rd = register_argument('rd', AvrRegister, read=True, write=True)
    rr = register_argument('rr', AvrRegister, read=True)
    syntax = Syntax(['mov', rd, ',', rr])
    patterns = [
        FixedPattern('op', 0b1011),
        SubPattern('r', rr),
        SubPattern('d', rd)]


class Push(AvrInstruction):
    tokens = [AvrToken2]
    rd = register_argument('rd', AvrRegister, read=True)
    syntax = Syntax(['push', rd])
    patterns = [
        FixedPattern('op', 0b1001001),
        FixedPattern('n0', 0xf),
        SubPattern('d', rd)]


class Pop(AvrInstruction):
    tokens = [AvrToken2]
    rd = register_argument('rd', AvrRegister, write=True)
    syntax = Syntax(['pop', rd])
    patterns = [
        FixedPattern('op', 0b1001000),
        FixedPattern('n0', 0xf),
        SubPattern('d', rd)]


class Nop(AvrInstruction):
    syntax = Syntax(['nop'])
    patterns = [FixedPattern('w0', 0)]


class Ret(AvrInstruction):
    syntax = Syntax(['ret'])
    patterns = [FixedPattern('w0', 0b1001010100001000)]


class Reti(AvrInstruction):
    syntax = Syntax(['reti'])
    patterns = [FixedPattern('w0', 0b1001010100011000)]


class Ldi(AvrInstruction):
    tokens = [AvrToken4]
    rd = register_argument('rd', AvrRegister, write=True)
    nk = register_argument('nk', int)
    syntax = Syntax(['ldi', rd, ',', nk])

    @property
    def reg_num(self):
        n = self.rd.num
        assert n in range(16, 32)
        return n - 16

    patterns = [
        FixedPattern('op', 0b1110),
        VariablePattern('d', reg_num),
        VariablePattern('k', nk)]


class In(AvrInstruction):
    tokens = [AvrToken3]
    rd = register_argument('rd', AvrRegister, write=True)
    na = register_argument('na', int)
    syntax = Syntax(['in', rd, ',', na])
    patterns = [
        FixedPattern('op', 0b10110),
        SubPattern('d', rd),
        VariablePattern('a', na)]


class Out(AvrInstruction):
    tokens = [AvrToken3]
    rd = register_argument('rd', AvrRegister, read=True)
    na = register_argument('na', int)
    syntax = Syntax(['out', na, ',', rd])
    patterns = [
        FixedPattern('op', 0b10111),
        SubPattern('d', rd),
        VariablePattern('a', na)]


@avr_isa.pattern('stm', 'JMP', cost=1)
def _(context, tree):
    tgt = tree.value
    context.emit(Rjmp(tgt.name, jumps=[tgt]))
