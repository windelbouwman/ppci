import struct
from ..isa import Instruction, Isa, register_argument, Syntax
from ..isa import FixedPattern, SubPattern, VariablePattern
from ..arch import RegisterUseDef, ArtificialInstruction
from ..token import Token, u16, bit_range, bit, bit_concat
from ...utils.bitfun import wrap_negative
from ...ir import i16
from .registers import AvrRegister, X
from .registers import HighAvrRegister, AvrWordRegister
from .registers import HighAvrWordRegister
from .registers import r0, r1, r1r0


class AvrToken(Token):
    def __init__(self):
        super().__init__(16, fmt='<H')
    w0 = bit_range(0, 16)
    b0 = bit_range(0, 8)
    b1 = bit_range(8, 16)
    n0 = bit_range(0, 4)
    n1 = bit_range(4, 8)
    n2 = bit_range(8, 12)
    n3 = bit_range(12, 16)


class Imm16Token(Token):
    def __init__(self):
        super().__init__(16, fmt='<H')
    imm = bit_range(0, 16)


class AvrArithmaticToken(AvrToken):
    op = bit_range(10, 16)
    r = bit_concat(bit(9), bit_range(0, 4))
    d = bit_range(4, 9)


class AvrToken2(AvrToken):
    op = bit_range(9, 16)
    op2 = bit_range(0, 4)
    d = bit_range(4, 9)


class AvrToken3(AvrToken):
    op = bit_range(11, 16)
    d = bit_range(4, 9)
    a = bit_concat(bit_range(9, 11), bit_range(0, 4))


class AvrToken4(AvrToken):
    op = bit_range(12, 16)
    d = bit_range(4, 8)
    k = bit_concat(bit_range(8, 12), bit_range(0, 4))


class AvrToken5(AvrToken):
    op = bit_range(11, 16)
    b = bit_concat(bit(10), bit_range(0, 3))

avr_isa = Isa()


class AvrInstruction(Instruction):
    isa = avr_isa


class PseudoAvrInstruction(ArtificialInstruction):
    """ These instructions are used to implement word arithmatic that is
        actually implemented by two 8-bit registers """
    pass


class Nop(AvrInstruction):
    tokens = [AvrToken]
    syntax = Syntax(['nop'])
    patterns = [FixedPattern('w0', 0)]


# Arithmatic instructions:

class Add(AvrInstruction):
    tokens = [AvrArithmaticToken]
    rd = register_argument('rd', AvrRegister, read=True, write=True)
    rr = register_argument('rr', AvrRegister, read=True)
    syntax = Syntax(['add', rd, ',', rr])
    patterns = [
        FixedPattern('op', 0b11),
        SubPattern('r', rr),
        SubPattern('d', rd)]


class Adc(AvrInstruction):
    tokens = [AvrArithmaticToken]
    rd = register_argument('rd', AvrRegister, read=True, write=True)
    rr = register_argument('rr', AvrRegister, read=True)
    syntax = Syntax(['adc', rd, ',', rr])
    patterns = [
        FixedPattern('op', 0b111),
        SubPattern('r', rr),
        SubPattern('d', rd)]


class Addw(PseudoAvrInstruction):
    tokens = [AvrArithmaticToken]
    rd = register_argument('rd', AvrWordRegister, read=True, write=True)
    rr = register_argument('rr', AvrWordRegister, read=True)
    syntax = Syntax(['addw', rd, ',', rr])

    def render(self):
        yield Add(self.rd.lo, self.rr.lo)
        yield Adc(self.rd.hi, self.rr.hi)


class Cp(AvrInstruction):
    """ Compare """
    tokens = [AvrArithmaticToken]
    rd = register_argument('rd', AvrRegister, read=True)
    rr = register_argument('rr', AvrRegister, read=True)
    syntax = Syntax(['cp', rd, ',', rr])
    patterns = [
        FixedPattern('op', 0b101),
        SubPattern('r', rr),
        SubPattern('d', rd)]


class Cpc(AvrInstruction):
    """ Compare with carry """
    tokens = [AvrArithmaticToken]
    rd = register_argument('rd', AvrRegister, read=True)
    rr = register_argument('rr', AvrRegister, read=True)
    syntax = Syntax(['cpc', rd, ',', rr])
    patterns = [
        FixedPattern('op', 0b1),
        SubPattern('r', rr),
        SubPattern('d', rd)]


class Cpw(PseudoAvrInstruction):
    rd = register_argument('rd', AvrWordRegister, read=True)
    rr = register_argument('rr', AvrWordRegister, read=True)
    syntax = Syntax(['cpw', rd, ',', rr])

    def render(self):
        yield Cp(self.rd.lo, self.rr.lo)
        yield Cpc(self.rd.hi, self.rr.hi)


class Sub(AvrInstruction):
    tokens = [AvrArithmaticToken]
    rd = register_argument('rd', AvrRegister, read=True, write=True)
    rr = register_argument('rr', AvrRegister, read=True)
    syntax = Syntax(['sub', rd, ',', rr])
    patterns = [
        FixedPattern('op', 0b110),
        SubPattern('r', rr),
        SubPattern('d', rd)]


class Sbc(AvrInstruction):
    tokens = [AvrArithmaticToken]
    rd = register_argument('rd', AvrRegister, read=True, write=True)
    rr = register_argument('rr', AvrRegister, read=True)
    syntax = Syntax(['sbc', rd, ',', rr])
    patterns = [
        FixedPattern('op', 0b10),
        SubPattern('r', rr),
        SubPattern('d', rd)]


class Subw(PseudoAvrInstruction):
    rd = register_argument('rd', AvrWordRegister, read=True, write=True)
    rr = register_argument('rr', AvrWordRegister, read=True)
    syntax = Syntax(['subw', rd, ',', rr])

    def render(self):
        yield Sub(self.rd.lo, self.rr.lo)
        yield Sbc(self.rd.hi, self.rr.hi)


class And(AvrInstruction):
    tokens = [AvrArithmaticToken]
    rd = register_argument('rd', AvrRegister, read=True, write=True)
    rr = register_argument('rr', AvrRegister, read=True)
    syntax = Syntax(['and', rd, ',', rr])
    patterns = [
        FixedPattern('op', 0b1000),
        SubPattern('r', rr),
        SubPattern('d', rd)]


class Andw(PseudoAvrInstruction):
    rd = register_argument('rd', AvrWordRegister, read=True, write=True)
    rr = register_argument('rr', AvrWordRegister, read=True)
    syntax = Syntax(['andw', rd, ',', rr])

    def render(self):
        yield And(self.rd.lo, self.rr.lo)
        yield And(self.rd.hi, self.rr.hi)


class Eor(AvrInstruction):
    tokens = [AvrArithmaticToken]
    rd = register_argument('rd', AvrRegister, read=True, write=True)
    rr = register_argument('rr', AvrRegister, read=True)
    syntax = Syntax(['eor', rd, ',', rr])
    patterns = [
        FixedPattern('op', 0b1001),
        SubPattern('r', rr),
        SubPattern('d', rd)]


class Or(AvrInstruction):
    tokens = [AvrArithmaticToken]
    rd = register_argument('rd', AvrRegister, read=True, write=True)
    rr = register_argument('rr', AvrRegister, read=True)
    syntax = Syntax(['or', rd, ',', rr])
    patterns = [
        FixedPattern('op', 0b1010),
        SubPattern('r', rr),
        SubPattern('d', rd)]


class Orw(PseudoAvrInstruction):
    rd = register_argument('rd', AvrWordRegister, read=True, write=True)
    rr = register_argument('rr', AvrWordRegister, read=True)
    syntax = Syntax(['orw', rd, ',', rr])

    def render(self):
        yield Or(self.rd.lo, self.rr.lo)
        yield Or(self.rd.hi, self.rr.hi)


class Inc(AvrInstruction):
    tokens = [AvrToken2]
    rd = register_argument('rd', AvrRegister, write=True, read=True)
    syntax = Syntax(['inc', rd])
    patterns = [
        FixedPattern('op', 0b1001010),
        FixedPattern('n0', 0b0011),
        SubPattern('d', rd)]


class Dec(AvrInstruction):
    tokens = [AvrToken2]
    rd = register_argument('rd', AvrRegister, write=True, read=True)
    syntax = Syntax(['dec', rd])
    patterns = [
        FixedPattern('op', 0b1001010),
        FixedPattern('n0', 0b1010),
        SubPattern('d', rd)]


class Lsr(AvrInstruction):
    tokens = [AvrToken2]
    rd = register_argument('rd', AvrRegister, write=True, read=True)
    syntax = Syntax(['lsr', rd])
    patterns = [
        FixedPattern('op', 0b1001010),
        FixedPattern('n0', 0b0110),
        SubPattern('d', rd)]


class Asr(AvrInstruction):
    tokens = [AvrToken2]
    rd = register_argument('rd', AvrRegister, write=True, read=True)
    syntax = Syntax(['asr', rd])
    patterns = [
        FixedPattern('op', 0b1001010),
        FixedPattern('n0', 0b0101),
        SubPattern('d', rd)]


def lsl(rd):
    return Add(rd, rd)


class Ror(AvrInstruction):
    tokens = [AvrToken2]
    rd = register_argument('rd', AvrRegister, write=True, read=True)
    syntax = Syntax(['ror', rd])
    patterns = [
        FixedPattern('op', 0b1001010),
        FixedPattern('n0', 0b0111),
        SubPattern('d', rd)]


@avr_isa.register_relocation
def relsigned12bit(sym_value, data, reloc_value):
    assert sym_value % 2 == 0
    assert reloc_value % 2 == 0
    offset = (sym_value - reloc_value - 2) // 2
    assert offset in range(-2047, 2048), str(offset)
    imm12 = wrap_negative(offset, 12)
    data[0] = imm12 & 0xff
    data[1] = (data[1] & 0xf0) | (imm12 >> 8)


class Rjmp(AvrInstruction):
    tokens = [AvrToken]
    lab = register_argument('lab', str)
    syntax = Syntax(['rjmp', lab])
    patterns = [FixedPattern('n3', 0xc)]

    def relocations(self):
        return [(self.lab, relsigned12bit)]


class Call(AvrInstruction):
    tokens = [AvrToken]
    lab = register_argument('lab', str)
    syntax = Syntax(['call', lab])
    patterns = [FixedPattern('n3', 0xd)]

    def relocations(self):
        return [(self.lab, relsigned12bit)]


@avr_isa.register_relocation
def relsigned7bit(sym_value, data, reloc_value):
    """ Apply 7 bit signed relocation """
    assert sym_value % 2 == 0
    assert reloc_value % 2 == 0
    offset = (sym_value - reloc_value - 2) // 2
    assert offset in range(-63, 64), str(offset)
    imm7 = wrap_negative(offset, 7)
    data[0] = (data[0] & 0x7) | ((imm7 & 0x1f) << 3)
    data[1] = (data[1] & 0xfc) | ((imm7 >> 5) & 0x3)


class Brne(AvrInstruction):
    """ Branch when not equal (Z flag is cleared) """
    tokens = [AvrToken5]
    lab = register_argument('lab', str)
    syntax = Syntax(['brne', lab])
    patterns = [
        FixedPattern('op', 0b11110),
        FixedPattern('b', 0b1001),
        ]

    def relocations(self):
        return [(self.lab, relsigned7bit)]


class Breq(AvrInstruction):
    tokens = [AvrToken5]
    lab = register_argument('lab', str)
    syntax = Syntax(['breq', lab])
    patterns = [
        FixedPattern('op', 0b11110),
        FixedPattern('b', 0b0001),
        ]

    def relocations(self):
        return [(self.lab, relsigned7bit)]


class Brlt(AvrInstruction):
    tokens = [AvrToken5]
    lab = register_argument('lab', str)
    syntax = Syntax(['brlt', lab])
    patterns = [
        FixedPattern('op', 0b11110),
        FixedPattern('b', 0b0100),
        ]

    def relocations(self):
        return [(self.lab, relsigned7bit)]


class Brge(AvrInstruction):
    tokens = [AvrToken5]
    lab = register_argument('lab', str)
    syntax = Syntax(['brge', lab])
    patterns = [
        FixedPattern('op', 0b11110),
        FixedPattern('b', 0b1100),
        ]

    def relocations(self):
        return [(self.lab, relsigned7bit)]


class Mov(AvrInstruction):
    tokens = [AvrArithmaticToken]
    rd = register_argument('rd', AvrRegister, write=True)
    rr = register_argument('rr', AvrRegister, read=True)
    syntax = Syntax(['mov', rd, ',', rr])
    patterns = [
        FixedPattern('op', 0b1011),
        SubPattern('r', rr),
        SubPattern('d', rd)]


class Movw(AvrInstruction):
    tokens = [AvrToken]
    rd = register_argument('rd', AvrWordRegister, write=True)
    rr = register_argument('rr', AvrWordRegister, read=True)
    syntax = Syntax(['movw', rd, ',', rr])

    @property
    def rd_num(self):
        n = self.rd.num
        assert n in range(0, 32, 2)
        return n >> 1

    @property
    def rr_num(self):
        n = self.rr.num
        assert n in range(0, 32, 2)
        return n >> 1

    patterns = [
        FixedPattern('b1', 0b1),
        VariablePattern('n0', rr_num),
        VariablePattern('n1', rd_num)]


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


class Ld(AvrInstruction):
    tokens = [AvrToken2]
    rd = register_argument('rd', AvrRegister, write=True)
    syntax = Syntax(['ld', rd, ',', 'x'])
    patterns = [
        FixedPattern('op', 0b1001000),
        FixedPattern('op2', 0b1100),
        SubPattern('d', rd)]


class LdPostInc(AvrInstruction):
    tokens = [AvrToken2]
    rd = register_argument('rd', AvrRegister, write=True)
    syntax = Syntax(['ld', rd, ',', 'x', '+'])
    patterns = [
        FixedPattern('op', 0b1001000),
        FixedPattern('op2', 0b1101),
        SubPattern('d', rd)]


class LdPreDec(AvrInstruction):
    tokens = [AvrToken2]
    rd = register_argument('rd', AvrRegister, write=True)
    syntax = Syntax(['ld', rd, ',', '-', 'x'])
    patterns = [
        FixedPattern('op', 0b1001000),
        FixedPattern('op2', 0b1110),
        SubPattern('d', rd)]


class LpmPostInc(AvrInstruction):
    """ Load from program memory """
    tokens = [AvrToken2]
    rd = register_argument('rd', AvrRegister, write=True)
    syntax = Syntax(['lpm', rd, ',', 'z', '+'])
    patterns = [
        FixedPattern('op', 0b1001000),
        FixedPattern('op2', 0b0101),
        SubPattern('d', rd)]


class St(AvrInstruction):
    """ Store register a X pointer location """
    tokens = [AvrToken2]
    rd = register_argument('rd', AvrRegister, read=True)
    syntax = Syntax(['st', 'x', ',', rd])
    patterns = [
        FixedPattern('op', 0b1001001),
        FixedPattern('op2', 0b1100),
        SubPattern('d', rd)]


class StPostInc(AvrInstruction):
    """ Store register value at memory X location and post increment X """
    tokens = [AvrToken2]
    rd = register_argument('rd', AvrRegister, read=True)
    syntax = Syntax(['st', 'x', '+', ',', rd])
    patterns = [
        FixedPattern('op', 0b1001001),
        FixedPattern('op2', 0b1101),
        SubPattern('d', rd)]


class StPreDec(AvrInstruction):
    tokens = [AvrToken2]
    rd = register_argument('rd', AvrRegister, read=True)
    syntax = Syntax(['st', '-', 'x', ',', rd])
    patterns = [
        FixedPattern('op', 0b1001001),
        FixedPattern('op2', 0b1110),
        SubPattern('d', rd)]


class StWord(PseudoAvrInstruction):
    """ Store a word by using st X+ and st X """
    rd = register_argument('rd', AvrWordRegister, read=True)
    syntax = Syntax(['stw', 'x', '+', ',', rd])

    def render(self):
        yield StPostInc(self.rd.lo)
        yield StPostInc(self.rd.hi)


class Sts(AvrInstruction):
    tokens = [AvrToken2, Imm16Token]
    rd = register_argument('rd', AvrRegister, read=True)
    imm = register_argument('imm', int)
    syntax = Syntax(['sts', imm, ',', rd])
    patterns = [
        FixedPattern('op', 0b1001001),
        FixedPattern('n0', 0x0),
        SubPattern('d', rd),
        VariablePattern('imm', imm)]


class Lds(AvrInstruction):
    tokens = [AvrToken2, Imm16Token]
    rd = register_argument('rd', AvrRegister, read=True)
    imm = register_argument('imm', int)
    syntax = Syntax(['lds', rd, ',', imm])
    patterns = [
        FixedPattern('op', 0b1001000),
        FixedPattern('n0', 0x0),
        SubPattern('d', rd),
        VariablePattern('imm', imm)]


class Ret(AvrInstruction):
    tokens = [AvrToken]
    syntax = Syntax(['ret'])
    patterns = [FixedPattern('w0', 0b1001010100001000)]


class Reti(AvrInstruction):
    tokens = [AvrToken]
    syntax = Syntax(['reti'])
    patterns = [FixedPattern('w0', 0b1001010100011000)]


class Ldi(AvrInstruction):
    tokens = [AvrToken4]
    rd = register_argument('rd', HighAvrRegister, write=True)
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


class Ldiw(PseudoAvrInstruction):
    rd = register_argument('rd', HighAvrWordRegister, write=True)
    nk = register_argument('nk', int)
    syntax = Syntax(['ldiw', rd, ',', nk])

    def render(self):
        lb = self.nk & 0xff
        hb = (self.nk >> 8) & 0xff
        yield Ldi(self.rd.lo, lb)
        yield Ldi(self.rd.hi, hb)


@avr_isa.register_relocation
def rel_ldilo(sym_value, data, reloc_value):
    imm8 = wrap_negative(sym_value, 16) & 0xff
    data[0] = (data[0] & 0xf0) | imm8 & 0xf
    data[1] = (data[1] & 0xf0) | ((imm8 >> 4) & 0xf)


class LdiLoAddr(AvrInstruction):
    tokens = [AvrToken4]
    rd = register_argument('rd', HighAvrRegister, write=True)
    lab = register_argument('lab', str)
    syntax = Syntax(['ldi', rd, ',', 'low', '(', lab, ')'])

    @property
    def reg_num(self):
        n = self.rd.num
        assert n in range(16, 32)
        return n - 16

    patterns = [
        FixedPattern('op', 0b1110),
        VariablePattern('d', reg_num)]

    def relocations(self):
        return [(self.lab, rel_ldilo)]


@avr_isa.register_relocation
def rel_ldihi(sym_value, data, reloc_value):
    imm8 = (wrap_negative(sym_value, 16) >> 8) & 0xff
    data[0] = (data[0] & 0xf0) | imm8 & 0xf
    data[1] = (data[1] & 0xf0) | ((imm8 >> 4) & 0xf)


class LdiHiAddr(AvrInstruction):
    tokens = [AvrToken4]
    rd = register_argument('rd', HighAvrRegister, write=True)
    lab = register_argument('lab', str)
    syntax = Syntax(['ldi', rd, ',', 'high', '(', lab, ')'])

    @property
    def reg_num(self):
        n = self.rd.num
        assert n in range(16, 32)
        return n - 16

    patterns = [
        FixedPattern('op', 0b1110),
        VariablePattern('d', reg_num)]

    def relocations(self):
        return [(self.lab, rel_ldihi)]


class LdiwAddr(PseudoAvrInstruction):
    rd = register_argument('rd', HighAvrWordRegister, write=True)
    lab = register_argument('lab', str)
    syntax = Syntax(['ldiw', rd, ',', '@', '(', lab, ')'])

    def render(self):
        yield LdiLoAddr(self.rd.lo, self.lab)
        yield LdiHiAddr(self.rd.hi, self.lab)


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


@avr_isa.pattern('stm', 'JMP', size=2)
def pattern_jmp(context, tree):
    tgt = tree.value
    context.emit(Rjmp(tgt.name, jumps=[tgt]))


@avr_isa.pattern('stm', 'CJMP(reg16, reg16)', size=10)
def pattern_cjmp(context, tree, c0, c1):
    op, yes_label, no_label = tree.value
    opnames = {
        "==": Breq,
        "!=": Brne,
        '<': Brlt,
        '>': Brge,  # TODO: fix this!
        '>=': Brge}
    Bop = opnames[op]

    context.emit(Cpw(c0, c1))

    jmp_ins_no = Rjmp(no_label.name, jumps=[no_label])
    jmp_ins_yes = Rjmp(yes_label.name, jumps=[yes_label])
    yes_label2 = context.new_label()
    context.emit(Bop(yes_label2.name, jumps=[yes_label2, jmp_ins_no]))
    context.emit(jmp_ins_no)
    context.emit(yes_label2)
    context.emit(jmp_ins_yes)


@avr_isa.pattern('reg16', 'CALL', size=2)
def pattern_call(context, tree):
    return context.gen_call(tree.value)


@avr_isa.pattern('reg', 'REGI8', size=0, cycles=0, energy=0)
def pattern_reg8(context, tree):
    return tree.value


@avr_isa.pattern('reg16', 'REGI16', size=0, cycles=0, energy=0)
def pattern_reg16(context, tree):
    assert isinstance(tree.value, AvrWordRegister)
    return tree.value


@avr_isa.pattern('stm', 'MOVI8(reg)', size=2)
def pattern_mov8(context, tree, c0):
    context.move(tree.value, c0)


#@avr_isa.pattern('stm', 'MOVI8(reg16)', size=2)
#def pattern_mov8_16(context, tree, c0):
#    context.move(tree.value, c0.lo)


@avr_isa.pattern('stm', 'MOVI16(reg16)', size=2)
def pattern_mov16(context, tree, c0):
    context.move(tree.value, c0)


@avr_isa.pattern('reg16', 'I16TOI16(reg16)', size=0)
def pattern_i16toi16(context, tree, c0):
    return c0


@avr_isa.pattern('reg', 'I16TOI8(reg16)', size=0)
def pattern_i16toi8(context, tree, c0):
    context.move(r1r0, c0)

    ud1 = RegisterUseDef()
    ud1.add_uses([r1r0])
    ud1.add_defs([r0, r1])
    context.emit(ud1)

    d = context.new_reg(AvrRegister)
    context.move(d, r0)
    return d


@avr_isa.pattern('reg', 'ADDI8(reg, reg)', size=4)
def pattern_add8(context, tree, c0, c1):
    d = context.new_reg(AvrRegister)
    context.move(d, c0)
    context.emit(Add(d, c1))
    return d


@avr_isa.pattern('reg16', 'ADDI16(reg16, reg16)', size=6)
def pattern_add16(context, tree, c0, c1):
    d = context.new_reg(AvrWordRegister)
    context.move(d, c0)
    context.emit(Addw(d, c1))
    return d


@avr_isa.pattern('reg16', 'SUBI16(reg16, reg16)', size=6)
def pattern_sub16(context, tree, c0, c1):
    d = context.new_reg(AvrWordRegister)
    context.move(d, c0)
    context.emit(Subw(d, c1))
    return d


@avr_isa.pattern('reg16', 'ANDI16(reg16, reg16)', size=6)
def pattern_and16(context, tree, c0, c1):
    d = context.new_reg(AvrWordRegister)
    context.move(d, c0)
    context.emit(Andw(d, c1))
    return d


@avr_isa.pattern('reg16', 'ORI16(reg16, reg16)', size=6)
def pattern_or16(context, tree, c0, c1):
    d = context.new_reg(AvrWordRegister)
    context.move(d, c0)
    context.emit(Orw(d, c1))
    return d


@avr_isa.pattern('reg16', 'DIVI16(reg16, reg16)', size=8)
def pattern_div16(context, tree, c0, c1):
    d = context.new_reg(AvrWordRegister)
    context.move(d, c0)
    context.move(d, c1)
    # TODO
    # raise NotImplementedError('idiv')
    return d


@avr_isa.pattern('reg16', 'MULI16(reg16, reg16)', size=8)
def pattern_mul16(context, tree, c0, c1):
    d = context.new_reg(AvrWordRegister)
    # TODO
    # raise NotImplementedError('imul')
    context.move(d, c0)
    context.move(d, c1)
    return d


@avr_isa.pattern('reg16', 'SHRI16(reg16, reg16)', size=8)
def pattern_shr16(context, tree, c0, c1):
    """ invoke runtime """
    d = context.new_reg(AvrWordRegister)
    # cntr = context.new_reg(AvrRegister)
    context.gen_call(('__shr16', [i16, i16], i16, [c0, c1], d))
    #context.move(d.lo, c0.lo)
    #context.move(d.hi, c0.hi)
    #context.move(cntr, c1.lo)
    # context.emit(Label('a'))
    #context.emit(Lsr(d.hi))
    #context.emit(Ror(d.lo))
    #context.emit(Dec(cntr))
    # raise NotImplementedError('shr')

    # TODO: fix this!
    # context.emit(Brne('a'))
    return d


@avr_isa.pattern('reg16', 'SHLI16(reg16, reg16)', size=8)
def pattern_shl16(context, tree, c0, c1):
    """ invoke runtime """
    d = context.new_reg(AvrWordRegister)
    context.gen_call(('__shl16', [i16, i16], i16, [c0, c1], d))
    return d


@avr_isa.pattern('reg', 'LDRI8(reg16)', size=2)
def pattern_ldr8(context, tree, c0):
    context.move(X, c0)
    d = context.new_reg(AvrRegister)
    context.emit(Ld(d))
    return d


@avr_isa.pattern('reg16', 'LDRI16(reg16)', size=8)
def pattern_ldr16(context, tree, c0):
    context.move(X, c0)
    context.emit(LdPostInc(r0))
    context.emit(Ld(r1))

    ud2 = RegisterUseDef()
    ud2.add_uses([r0, r1, X])
    ud2.add_def(r1r0)
    context.emit(ud2)

    d = context.new_reg(AvrWordRegister)
    context.move(d, r1r0)
    return d


@avr_isa.pattern('stm', 'STRI16(reg16, reg16)', size=8)
def pattern_str16(context, tree, c0, c1):
    context.move(X, c0)
    context.emit(StWord(c1))
    ud2 = RegisterUseDef()
    ud2.add_uses([X])
    context.emit(ud2)


@avr_isa.pattern('stm', 'STRI8(reg16, reg)', size=2)
def pattern_str8(context, tree, c0, c1):
    context.move(X, c0)
    context.emit(St(c1))
    ud2 = RegisterUseDef()
    ud2.add_uses([X])
    context.emit(ud2)


@avr_isa.pattern('reg', 'CONSTI8', size=2)
def pattern_const8(context, tree):
    d = context.new_reg(HighAvrRegister)
    context.emit(Ldi(d, tree.value))
    return d


@avr_isa.pattern('reg16', 'CONSTI16', size=4)
def pattern_const16(context, tree):
    d = context.new_reg(HighAvrWordRegister)
    context.emit(Ldiw(d, tree.value))
    return d


@avr_isa.pattern('reg16', 'LABEL', size=4)
def pattern_label(context, tree):
    """ Determine the label address and yield its result """
    d = context.new_reg(HighAvrWordRegister)
    context.emit(LdiwAddr(d, tree.value))
    return d
