from ..isa import Instruction, Isa, register_argument, Syntax
from ..isa import FixedPattern, SubPattern, VariablePattern
from ..token import Token, u16, bit_range, bit, bit_concat
from ...utils.bitfun import wrap_negative
from ...ir import i16
from .registers import AvrRegister, r16, AvrPseudo16Register, X


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


class Imm16Token(Token):
    def __init__(self):
        super().__init__(16)
    imm = bit_range(0, 16)

    def encode(self):
        return u16(self.bit_value)


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


class And(AvrInstruction):
    tokens = [AvrArithmaticToken]
    rd = register_argument('rd', AvrRegister, read=True, write=True)
    rr = register_argument('rr', AvrRegister, read=True)
    syntax = Syntax(['and', rd, ',', rr])
    patterns = [
        FixedPattern('op', 0b1000),
        SubPattern('r', rr),
        SubPattern('d', rd)]


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


@avr_isa.register_relocation
def rel_ldilo(sym_value, data, reloc_value):
    imm8 = wrap_negative(sym_value, 16) & 0xff
    data[0] = (data[0] & 0xf0) | imm8 & 0xf
    data[1] = (data[1] & 0xf0) | ((imm8 >> 4) & 0xf)


class LdiLoAddr(AvrInstruction):
    tokens = [AvrToken4]
    rd = register_argument('rd', AvrRegister, write=True)
    lab = register_argument('lab', str)
    syntax = Syntax(['ldi', rd, ',', 'lo', '(', lab, ')'])

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
    rd = register_argument('rd', AvrRegister, write=True)
    lab = register_argument('lab', str)
    syntax = Syntax(['ldi', rd, ',', 'hi', '(', lab, ')'])

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
def _(context, tree):
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
    context.emit(Cp(c0.lo, c1.lo))
    context.emit(Cpc(c0.lo, c1.lo))
    jmp_ins = Rjmp(no_label.name, jumps=[no_label])
    context.emit(Bop(yes_label.name, jumps=[yes_label, jmp_ins]))
    context.emit(jmp_ins)


@avr_isa.pattern('reg16', 'CALL', size=2)
def pattern_call(context, tree):
    label, arg_types, ret_type, args, res_var = tree.value
    context.gen_call(label, arg_types, ret_type, args, res_var)
    return res_var


@avr_isa.pattern('reg', 'REGI8', size=0, cycles=0, energy=0)
def pattern_reg8(context, tree):
    return tree.value


@avr_isa.pattern('reg16', 'REGI16', size=0, cycles=0, energy=0)
def pattern_reg16(context, tree):
    assert isinstance(tree.value, AvrPseudo16Register)
    return tree.value


@avr_isa.pattern('reg', 'MOVI8(reg)', size=2)
def pattern_mov8(context, tree, c0):
    context.move(tree.value, c0)
    return tree.value


@avr_isa.pattern('reg', 'MOVI8(reg16)', size=2)
def pattern_mov8_16(context, tree, c0):
    context.move(tree.value, c0.lo)
    return tree.value


@avr_isa.pattern('stm', 'MOVI16(reg16)', size=4)
def pattern_mov16(context, tree, c0):
    context.move(tree.value.lo, c0.lo)
    context.move(tree.value.hi, c0.hi)
    return tree.value


@avr_isa.pattern('reg', 'ADDI8(reg, reg)', size=4)
def pattern_add8(context, tree, c0, c1):
    d = context.new_reg(AvrRegister)
    context.move(d, c0)
    context.emit(Add(d, c1))
    return d


@avr_isa.pattern('reg16', 'ADDI16(reg16, reg16)', size=8)
def pattern_add16(context, tree, c0, c1):
    d = context.new_reg(AvrPseudo16Register)
    context.move(d.lo, c0.lo)
    context.move(d.hi, c0.hi)
    context.emit(Add(d.lo, c1.lo))
    context.emit(Adc(d.hi, c1.hi))
    return d


@avr_isa.pattern('reg16', 'SUBI16(reg16, reg16)', size=8)
def pattern_sub16(context, tree, c0, c1):
    d = context.new_reg(AvrPseudo16Register)
    context.move(d.lo, c0.lo)
    context.move(d.hi, c0.hi)
    context.emit(Sub(d.lo, c1.lo))
    context.emit(Sbc(d.hi, c1.hi))
    return d


@avr_isa.pattern('reg16', 'ANDI16(reg16, reg16)', size=8)
def pattern_and16(context, tree, c0, c1):
    d = context.new_reg(AvrPseudo16Register)
    context.move(d.lo, c0.lo)
    context.move(d.hi, c0.hi)
    context.emit(And(d.lo, c1.lo))
    context.emit(And(d.hi, c1.hi))
    return d


@avr_isa.pattern('reg16', 'ORI16(reg16, reg16)', size=8)
def pattern_or16(context, tree, c0, c1):
    d = context.new_reg(AvrPseudo16Register)
    context.move(d.lo, c0.lo)
    context.move(d.hi, c0.hi)
    context.emit(Or(d.lo, c1.lo))
    context.emit(Or(d.hi, c1.hi))
    return d


@avr_isa.pattern('reg16', 'DIVI16(reg16, reg16)', size=8)
def pattern_div16(context, tree, c0, c1):
    d = context.new_reg(AvrPseudo16Register)
    # TODO
    return d


@avr_isa.pattern('reg16', 'MULI16(reg16, reg16)', size=8)
def pattern_mul16(context, tree, c0, c1):
    d = context.new_reg(AvrPseudo16Register)
    # TODO
    return d


@avr_isa.pattern('reg16', 'SHRI16(reg16, reg16)', size=8)
def pattern_shr16(context, tree, c0, c1):
    """ invoke runtime """
    d = context.new_reg(AvrPseudo16Register)
    # cntr = context.new_reg(AvrRegister)
    context.gen_call('__shr16', [i16, i16], i16, [c0, c1], d)
    #context.move(d.lo, c0.lo)
    #context.move(d.hi, c0.hi)
    #context.move(cntr, c1.lo)
    # context.emit(Label('a'))
    #context.emit(Lsr(d.hi))
    #context.emit(Ror(d.lo))
    #context.emit(Dec(cntr))

    # TODO: fix this!
    # context.emit(Brne('a'))
    return d


@avr_isa.pattern('reg16', 'SHLI16(reg16, reg16)', size=8)
def pattern_shl16(context, tree, c0, c1):
    """ invoke runtime """
    d = context.new_reg(AvrPseudo16Register)
    context.gen_call('__shl16', [i16, i16], i16, [c0, c1], d)
    return d


@avr_isa.pattern('reg', 'LDRI8(reg16)', size=2)
def pattern_ldr8(context, tree, c0):
    context.move(X.hi, c0.hi)
    context.move(X.lo, c0.lo)
    d = context.new_reg(AvrRegister)
    context.emit(Ld(d))
    return d


@avr_isa.pattern('reg16', 'LDRI16(reg16)', size=8)
def pattern_ldr16(context, tree, c0):
    d = context.new_reg(AvrPseudo16Register)
    context.move(X.hi, c0.hi)
    context.move(X.lo, c0.lo)
    context.emit(LdPostInc(d.lo))
    context.emit(Ld(d.hi))
    return d


@avr_isa.pattern('stm', 'STRI16(reg16, reg16)', size=8)
def pattern_str16(context, tree, c0, c1):
    context.move(X.hi, c0.hi)
    context.move(X.lo, c0.lo)
    context.emit(StPostInc(c1.lo))
    context.emit(St(c1.hi))


@avr_isa.pattern('reg', 'CONSTI8', size=2)
def _(context, tree):
    d = context.new_reg(AvrRegister)
    context.emit(Ldi(r16, tree.value))
    context.move(d, r16)
    return d


@avr_isa.pattern('reg16', 'CONSTI16', size=4)
def _(context, tree):
    d = context.new_reg(AvrPseudo16Register)
    lb = tree.value & 0xff
    hb = (tree.value >> 8) & 0xff
    context.emit(Ldi(r16, lb))
    context.move(d.lo, r16)
    context.emit(Ldi(r16, hb))
    context.move(d.hi, r16)
    return d


@avr_isa.pattern('reg16', 'LABEL', size=4)
def _(context, tree):
    """ Determine the label address and yield its result """
    d = context.new_reg(AvrPseudo16Register)
    context.emit(LdiLoAddr(r16, tree.value))
    context.move(d.lo, r16)
    context.emit(LdiHiAddr(r16, tree.value))
    context.move(d.hi, r16)
    return d
