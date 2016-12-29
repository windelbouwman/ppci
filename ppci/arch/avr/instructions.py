from ..isa import Isa
from ..encoding import Instruction, Operand, Syntax, Relocation, Transform
from ..arch import RegisterUseDef, ArtificialInstruction
from ..token import Token, bit_range, bit
from ...utils.bitfun import wrap_negative
from ...ir import i16
from .registers import AvrRegister, Z, AvrYRegister, AvrZRegister
from .registers import HighAvrRegister, AvrWordRegister
from .registers import HighAvrWordRegister, SuperHighAvrWordRegister
from .registers import r0, r1, r1r0


class AvrToken(Token):
    class Info:
        size = 16

    w0 = bit_range(0, 16)
    b0 = bit_range(0, 8)
    b1 = bit_range(8, 16)
    n0 = bit_range(0, 4)
    n1 = bit_range(4, 8)
    n2 = bit_range(8, 12)
    n3 = bit_range(12, 16)
    n210 = bit_range(0, 12)


class Imm16Token(Token):
    class Info:
        size = 16

    imm = bit_range(0, 16)


class AvrArithmaticToken(AvrToken):
    op = bit_range(10, 16)
    r = bit(9) + bit_range(0, 4)
    d = bit_range(4, 9)


class AvrToken2(AvrToken):
    op = bit_range(9, 16)
    op2 = bit_range(0, 4)
    d = bit_range(4, 9)


class AvrToken3(AvrToken):
    op = bit_range(11, 16)
    d = bit_range(4, 9)
    a = bit_range(9, 11) + bit_range(0, 4)


class AdiwToken(AvrToken):
    op = bit_range(8, 16)
    p = bit_range(4, 6)
    k = bit_range(6, 8) + bit_range(0, 4)


class AvrToken4(AvrToken):
    op = bit_range(12, 16)
    d = bit_range(4, 8)
    k = bit_range(8, 12) + bit_range(0, 4)


class ConditionalBranchToken(AvrToken):
    op = bit_range(11, 16)
    b = bit(10) + bit_range(0, 3)
    offset = bit_range(3, 10)


class AvrToken99(AvrToken):
    op = bit_range(14, 16) + bit(12)
    k = bit(13) + bit_range(10, 12) + bit_range(0, 3)
    y = bit(3)
    d = bit_range(4, 9)
    s = bit(9)


avr_isa = Isa()


class AvrInstruction(Instruction):
    isa = avr_isa


class Nop(AvrInstruction):
    tokens = [AvrToken]
    syntax = Syntax(['nop'])
    patterns = {'w0': 0}


# Arithmatic instructions:

class Add(AvrInstruction):
    tokens = [AvrArithmaticToken]
    rd = Operand('rd', AvrRegister, read=True, write=True)
    rr = Operand('rr', AvrRegister, read=True)
    syntax = Syntax(['add', ' ', rd, ',', ' ', rr])
    patterns = {'op': 0b11, 'r': rr, 'd': rd}


class Patch0r(Transform):
    def forwards(self, val):
        return (val // 2) - 12

    def backwards(self, val):
        return (val + 12) * 2


class Adiw(AvrInstruction):
    """ Add immediate to word (W, X, Y or Z) """
    tokens = [AdiwToken]
    rd = Operand('rd', SuperHighAvrWordRegister, read=True, write=True)
    imm = Operand('imm', int)
    syntax = Syntax(['adiw', ' ', rd, ',', ' ', imm])
    patterns = {'op': 0b10010110, 'k': imm, 'p': Patch0r(rd)}


class Sbiw(AvrInstruction):
    """ Substract immediate to word (W, X, Y or Z) """
    tokens = [AdiwToken]
    rd = Operand('rd', SuperHighAvrWordRegister, read=True, write=True)
    imm = Operand('imm', int)
    syntax = Syntax(['sbiw', ' ', rd, ',', ' ', imm])
    patterns = {'op': 0b10010111, 'k': imm, 'p': Patch0r(rd)}


class Adc(AvrInstruction):
    tokens = [AvrArithmaticToken]
    rd = Operand('rd', AvrRegister, read=True, write=True)
    rr = Operand('rr', AvrRegister, read=True)
    syntax = Syntax(['adc', ' ', rd, ',', ' ', rr])
    patterns = {'op': 0b111, 'r': rr, 'd': rd}


class Cp(AvrInstruction):
    """ Compare """
    tokens = [AvrArithmaticToken]
    rd = Operand('rd', AvrRegister, read=True)
    rr = Operand('rr', AvrRegister, read=True)
    syntax = Syntax(['cp', ' ', rd, ',', ' ', rr])
    patterns = {'op': 0b101, 'r': rr, 'd': rd}


class Cpc(AvrInstruction):
    """ Compare with carry """
    tokens = [AvrArithmaticToken]
    rd = Operand('rd', AvrRegister, read=True)
    rr = Operand('rr', AvrRegister, read=True)
    syntax = Syntax(['cpc', ' ', rd, ',', ' ', rr])
    patterns = {'op': 0b1, 'r': rr, 'd': rd}


class Sub(AvrInstruction):
    tokens = [AvrArithmaticToken]
    rd = Operand('rd', AvrRegister, read=True, write=True)
    rr = Operand('rr', AvrRegister, read=True)
    syntax = Syntax(['sub', ' ', rd, ',', ' ', rr])
    patterns = {'op': 0b110, 'r': rr, 'd': rd}


class Sbc(AvrInstruction):
    tokens = [AvrArithmaticToken]
    rd = Operand('rd', AvrRegister, read=True, write=True)
    rr = Operand('rr', AvrRegister, read=True)
    syntax = Syntax(['sbc', ' ', rd, ',', ' ', rr])
    patterns = {'op': 0b10, 'r': rr, 'd': rd}


class And(AvrInstruction):
    tokens = [AvrArithmaticToken]
    rd = Operand('rd', AvrRegister, read=True, write=True)
    rr = Operand('rr', AvrRegister, read=True)
    syntax = Syntax(['and', ' ', rd, ',', ' ', rr])
    patterns = {'op': 0b1000, 'r': rr, 'd': rd}


class Eor(AvrInstruction):
    tokens = [AvrArithmaticToken]
    rd = Operand('rd', AvrRegister, read=True, write=True)
    rr = Operand('rr', AvrRegister, read=True)
    syntax = Syntax(['eor', ' ', rd, ',', ' ', rr])
    patterns = {'op': 0b1001, 'r': rr, 'd': rd}


class Or(AvrInstruction):
    tokens = [AvrArithmaticToken]
    rd = Operand('rd', AvrRegister, read=True, write=True)
    rr = Operand('rr', AvrRegister, read=True)
    syntax = Syntax(['or', ' ', rd, ',', ' ', rr])
    patterns = {'op': 0b1010, 'r': rr, 'd': rd}


def make_one_op(mnemonic, opcode):
    tokens = [AvrToken2]
    rd = Operand('rd', AvrRegister, write=True, read=True)
    syntax = Syntax([mnemonic, ' ', rd])
    patterns = {'op': 0b1001010, 'n0': opcode, 'd': rd}
    members = {
        'syntax': syntax, 'tokens': tokens, 'patterns': patterns, 'rd': rd,
        }
    return type(mnemonic.title(), (AvrInstruction,), members)


Inc = make_one_op('inc', 0b0011)
Asr = make_one_op('asr', 0b0101)
Lsr = make_one_op('lsr', 0b0110)
Ror = make_one_op('ror', 0b0111)
Dec = make_one_op('dec', 0b1010)


def lsl(rd):
    return Add(rd, rd)


@avr_isa.register_relocation
class TwelveBitAvrRelocation(Relocation):
    name = '12bit'
    number = 0
    token = AvrToken
    field = 'n210'

    def calc(self, sym_value, reloc_value):
        assert sym_value % 2 == 0
        assert reloc_value % 2 == 0
        offset = (sym_value - reloc_value - 2) // 2
        assert offset in range(-2047, 2048), str(offset)
        return wrap_negative(offset, 12)


class Rjmp(AvrInstruction):
    tokens = [AvrToken]
    lab = Operand('lab', str)
    syntax = Syntax(['rjmp', ' ', lab])
    patterns = {'n3': 0xc}

    def relocations(self):
        return [TwelveBitAvrRelocation(self.lab, offset=0)]


class Call(AvrInstruction):
    tokens = [AvrToken]
    lab = Operand('lab', str)
    syntax = Syntax(['call', ' ', lab])
    patterns = {'n3': 0xd}

    def relocations(self):
        return [TwelveBitAvrRelocation(self.lab, offset=0)]


@avr_isa.register_relocation
class SevenBitAvrRelocation(Relocation):
    """ 7 bit signed relocation """
    name = '7bit'
    number = 1
    token = ConditionalBranchToken
    field = 'offset'

    def calc(self, sym_value, reloc_value):
        assert sym_value % 2 == 0
        assert reloc_value % 2 == 0
        offset = (sym_value - reloc_value - 2) // 2
        assert offset in range(-63, 64), str(offset)
        return wrap_negative(offset, 7)


class AvrConditionalJumpInstruction(AvrInstruction):
    tokens = [ConditionalBranchToken]
    lab = Operand('lab', str)

    def relocations(self):
        return [SevenBitAvrRelocation(self.lab)]


class Brne(AvrConditionalJumpInstruction):
    """ Branch when not equal (Z flag is cleared) """
    syntax = Syntax(['brne', ' ', AvrConditionalJumpInstruction.lab])
    patterns = {'op': 0b11110, 'b': 0b1001}


class Breq(AvrConditionalJumpInstruction):
    syntax = Syntax(['breq', ' ', AvrConditionalJumpInstruction.lab])
    patterns = {'op': 0b11110, 'b': 0b0001}


class Brlt(AvrConditionalJumpInstruction):
    """ Branch if less than (signed) """
    syntax = Syntax(['brlt', ' ', AvrConditionalJumpInstruction.lab])
    patterns = {'op': 0b11110, 'b': 0b0100}


class Brge(AvrConditionalJumpInstruction):
    """ Branch if greater or equal (signed) """
    syntax = Syntax(['brge', ' ', AvrConditionalJumpInstruction.lab])
    patterns = {'op': 0b11110, 'b': 0b1100}


class Mov(AvrInstruction):
    tokens = [AvrArithmaticToken]
    rd = Operand('rd', AvrRegister, write=True)
    rr = Operand('rr', AvrRegister, read=True)
    syntax = Syntax(['mov', ' ', rd, ',', ' ', rr])
    patterns = {'op': 0b1011, 'r': rr, 'd': rd}


class PatchDiv2(Transform):
    def forwards(self, val):
        assert val in range(0, 32, 2)
        return val >> 1


class Movw(AvrInstruction):
    tokens = [AvrToken]
    rd = Operand('rd', AvrWordRegister, write=True)
    rr = Operand('rr', AvrWordRegister, read=True)
    syntax = Syntax(['movw', ' ', rd, ',', ' ', rr])
    patterns = {'b1': 0b1, 'n0': PatchDiv2(rr), 'n1': PatchDiv2(rd)}


class Push(AvrInstruction):
    tokens = [AvrToken2]
    rd = Operand('rd', AvrRegister, read=True)
    syntax = Syntax(['push', ' ', rd])
    patterns = {'op': 0b1001001, 'n0': 0xf, 'd': rd}


class Pop(AvrInstruction):
    tokens = [AvrToken2]
    rd = Operand('rd', AvrRegister, write=True)
    syntax = Syntax(['pop', ' ', rd])
    patterns = {'op': 0b1001000, 'n0': 0xf, 'd': rd}


class Ld(AvrInstruction):
    tokens = [AvrToken2]
    rd = Operand('rd', AvrRegister, write=True)
    syntax = Syntax(['ld', ' ', rd, ',', ' ', 'x'])
    patterns = {'op': 0b1001000, 'op2': 0b1100, 'd': rd}


class Ldd_y(AvrInstruction):
    """ Load with offset """
    tokens = [AvrToken99]
    rd = Operand('rd', AvrRegister, write=True)
    y = Operand('y', AvrYRegister, read=True)
    imm = Operand('imm', int)
    syntax = Syntax(['ldd', ' ', rd, ',', ' ', y, '+', imm])
    patterns = {'op': 0b100, 's': 0, 'y': 1, 'd': rd, 'k': imm}


class Std_y(AvrInstruction):
    """ Store with offset """
    tokens = [AvrToken99]
    rd = Operand('rd', AvrRegister, read=True)
    y = Operand('y', AvrYRegister, read=True)
    imm = Operand('imm', int)
    syntax = Syntax(['std', ' ', y, '+', imm, ',', ' ', rd])
    patterns = {'op': 0b100, 's': 1, 'y': 1, 'd': rd, 'k': imm}


class Ldd_z(AvrInstruction):
    """ Load with offset """
    tokens = [AvrToken99]
    rd = Operand('rd', AvrRegister, write=True)
    z = Operand('z', AvrZRegister, read=True)
    imm = Operand('imm', int)
    syntax = Syntax(['ldd', ' ', rd, ',', ' ', z, '+', imm])
    patterns = {'op': 0b100, 's': 0, 'y': 0, 'd': rd, 'k': imm}


class Std_z(AvrInstruction):
    """ Store with offset """
    tokens = [AvrToken99]
    rd = Operand('rd', AvrRegister, read=True)
    z = Operand('z', AvrZRegister, read=True)
    imm = Operand('imm', int)
    syntax = Syntax(['std', ' ', z, '+', imm, ',', ' ', rd])
    patterns = {'op': 0b100, 's': 1, 'y': 0, 'd': rd, 'k': imm}


class LdPostInc(AvrInstruction):
    tokens = [AvrToken2]
    rd = Operand('rd', AvrRegister, write=True)
    syntax = Syntax(['ld', ' ', rd, ',', ' ', 'x', '+'])
    patterns = {'op': 0b1001000, 'op2': 0b1101, 'd': rd}


class LdPreDec(AvrInstruction):
    tokens = [AvrToken2]
    rd = Operand('rd', AvrRegister, write=True)
    syntax = Syntax(['ld', ' ', rd, ',', ' ', '-', 'x'])
    patterns = {'op': 0b1001000, 'op2': 0b1110, 'd': rd}


class LpmPostInc(AvrInstruction):
    """ Load from program memory """
    tokens = [AvrToken2]
    rd = Operand('rd', AvrRegister, write=True)
    syntax = Syntax(['lpm', ' ', rd, ',', ' ', 'z', '+'])
    patterns = {'op': 0b1001000, 'op2': 0b0101, 'd': rd}


class St(AvrInstruction):
    """ Store register a X pointer location """
    tokens = [AvrToken2]
    rd = Operand('rd', AvrRegister, read=True)
    syntax = Syntax(['st', ' ', 'x', ',', ' ', rd])
    patterns = {'op': 0b1001001, 'op2': 0b1100, 'd': rd}


class StPostInc(AvrInstruction):
    """ Store register value at memory X location and post increment X """
    tokens = [AvrToken2]
    rd = Operand('rd', AvrRegister, read=True)
    syntax = Syntax(['st', ' ', 'x', '+', ',', ' ', rd])
    patterns = {'op': 0b1001001, 'op2': 0b1101, 'd': rd}


class StPreDec(AvrInstruction):
    tokens = [AvrToken2]
    rd = Operand('rd', AvrRegister, read=True)
    syntax = Syntax(['st', ' ', '-', 'x', ',', ' ', rd])
    patterns = {'op': 0b1001001, 'op2': 0b1110, 'd': rd}


class Sts(AvrInstruction):
    tokens = [AvrToken2, Imm16Token]
    rd = Operand('rd', AvrRegister, read=True)
    imm = Operand('imm', int)
    syntax = Syntax(['sts', ' ', imm, ',', ' ', rd])
    patterns = {'op': 0b1001001, 'n0': 0x0, 'd': rd, 'imm': imm}


class Lds(AvrInstruction):
    tokens = [AvrToken2, Imm16Token]
    rd = Operand('rd', AvrRegister, read=True)
    imm = Operand('imm', int)
    syntax = Syntax(['lds', ' ', rd, ',', ' ', imm])
    patterns = {'op': 0b1001000, 'n0': 0x0, 'd': rd, 'imm': imm}


class Ret(AvrInstruction):
    tokens = [AvrToken]
    syntax = Syntax(['ret'])
    patterns = {'w0': 0b1001010100001000}


class Reti(AvrInstruction):
    tokens = [AvrToken]
    syntax = Syntax(['reti'])
    patterns = {'w0': 0b1001010100011000}


class PatchedBy16(Transform):
    def forwards(self, val):
        return val - 16


def make_i(mnemonic, opcode, read=False, write=False):
    tokens = [AvrToken4]
    rd = Operand('rd', HighAvrRegister, read=read, write=write)
    nk = Operand('nk', int)
    syntax = Syntax([mnemonic, ' ', rd, ',', ' ', nk])
    patterns = {'op': opcode, 'd': PatchedBy16(rd), 'k': nk}
    members = {
        'syntax': syntax, 'tokens': tokens, 'patterns': patterns,
        'rd': rd, 'nk': nk
        }
    return type(mnemonic.title(), (AvrInstruction,), members)


Cpi = make_i('cpi', 0b0011, read=True, write=False)
Sbci = make_i('sbci', 0b0100, read=True, write=True)
Subi = make_i('sbci', 0b0101, read=True, write=True)
Ori = make_i('ori', 0b0110, read=True, write=True)
Andi = make_i('andi', 0b0111, read=True, write=True)
Ldi = make_i('ldi', 0b1110, read=False, write=True)


@avr_isa.register_relocation
class LdiLoAvrRelocation(Relocation):
    name = 'ldilo'
    number = 2
    token = AvrToken4
    field = 'k'

    def calc(self, sym_value, reloc_value):
        imm8 = wrap_negative(sym_value, 16) & 0xff
        return imm8


class LdiLoAddr(AvrInstruction):
    tokens = [AvrToken4]
    rd = Operand('rd', HighAvrRegister, write=True)
    lab = Operand('lab', str)
    syntax = Syntax(['ldi', ' ', rd, ',', ' ', 'low', '(', lab, ')'])
    patterns = {'op': 0b1110, 'd': PatchedBy16(rd)}

    def relocations(self):
        return [LdiLoAvrRelocation(self.lab)]


@avr_isa.register_relocation
class LdiHiAvrRelocation(Relocation):
    name = 'ldihi'
    number = 3
    token = AvrToken4
    field = 'k'

    def calc(self, sym_value, reloc_value):
        imm8 = (wrap_negative(sym_value, 16) >> 8) & 0xff
        return imm8


class LdiHiAddr(AvrInstruction):
    tokens = [AvrToken4]
    rd = Operand('rd', HighAvrRegister, write=True)
    lab = Operand('lab', str)
    syntax = Syntax(['ldi', ' ', rd, ',', ' ', 'high', '(', lab, ')'])
    patterns = {'op': 0b1110, 'd': PatchedBy16(rd)}

    def relocations(self):
        return [LdiHiAvrRelocation(self.lab)]


class In(AvrInstruction):
    tokens = [AvrToken3]
    rd = Operand('rd', AvrRegister, write=True)
    na = Operand('na', int)
    syntax = Syntax(['in', ' ', rd, ',', ' ', na])
    patterns = {'op': 0b10110, 'd': rd, 'a': na}


class Out(AvrInstruction):
    tokens = [AvrToken3]
    rd = Operand('rd', AvrRegister, read=True)
    na = Operand('na', int)
    syntax = Syntax(['out', ' ', na, ',', ' ', rd])
    patterns = {'op': 0b10111, 'd': rd, 'a': na}


class PseudoAvrInstruction(ArtificialInstruction):
    """ These instructions are used to implement word arithmatic that is
        actually implemented by two 8-bit registers """
    pass


class Addw(PseudoAvrInstruction):
    rd = Operand('rd', AvrWordRegister, read=True, write=True)
    rr = Operand('rr', AvrWordRegister, read=True)
    syntax = Syntax(['addw', ' ', rd, ',', ' ', rr])

    def render(self):
        yield Add(self.rd.lo, self.rr.lo)
        yield Adc(self.rd.hi, self.rr.hi)


class Cpw(PseudoAvrInstruction):
    rd = Operand('rd', AvrWordRegister, read=True)
    rr = Operand('rr', AvrWordRegister, read=True)
    syntax = Syntax(['cpw', ' ', rd, ',', ' ', rr])

    def render(self):
        yield Cp(self.rd.lo, self.rr.lo)
        yield Cpc(self.rd.hi, self.rr.hi)


class Subw(PseudoAvrInstruction):
    rd = Operand('rd', AvrWordRegister, read=True, write=True)
    rr = Operand('rr', AvrWordRegister, read=True)
    syntax = Syntax(['subw', ' ', rd, ',', ' ', rr])

    def render(self):
        yield Sub(self.rd.lo, self.rr.lo)
        yield Sbc(self.rd.hi, self.rr.hi)


class Andw(PseudoAvrInstruction):
    rd = Operand('rd', AvrWordRegister, read=True, write=True)
    rr = Operand('rr', AvrWordRegister, read=True)
    syntax = Syntax(['andw', ' ', rd, ',', ' ', rr])

    def render(self):
        yield And(self.rd.lo, self.rr.lo)
        yield And(self.rd.hi, self.rr.hi)


class Orw(PseudoAvrInstruction):
    rd = Operand('rd', AvrWordRegister, read=True, write=True)
    rr = Operand('rr', AvrWordRegister, read=True)
    syntax = Syntax(['orw', ' ', rd, ',', ' ', rr])

    def render(self):
        yield Or(self.rd.lo, self.rr.lo)
        yield Or(self.rd.hi, self.rr.hi)


class Ldiw(PseudoAvrInstruction):
    rd = Operand('rd', HighAvrWordRegister, write=True)
    nk = Operand('nk', int)
    syntax = Syntax(['ldiw', ' ', rd, ',', ' ', nk])

    def render(self):
        lb = self.nk & 0xff
        hb = (self.nk >> 8) & 0xff
        yield Ldi(self.rd.lo, lb)
        yield Ldi(self.rd.hi, hb)


class LdiwAddr(PseudoAvrInstruction):
    rd = Operand('rd', HighAvrWordRegister, write=True)
    lab = Operand('lab', str)
    syntax = Syntax(['ldiw', ' ', rd, ',', ' ', '@', '(', lab, ')'])

    def render(self):
        yield LdiLoAddr(self.rd.lo, self.lab)
        yield LdiHiAddr(self.rd.hi, self.lab)


class StWord(PseudoAvrInstruction):
    """ Store a word by using st X+ and st X """
    rd = Operand('rd', AvrWordRegister, read=True)
    syntax = Syntax(['stw', ' ', 'x', '+', ',', ' ', rd])

    def render(self):
        yield StPostInc(self.rd.lo)
        yield StPostInc(self.rd.hi)


class LddWord_z(PseudoAvrInstruction):
    """ Pseudo instruction for loading a word from z + offset """
    rd = Operand('rd', AvrWordRegister, write=True)
    z = Operand('z', AvrZRegister, read=True)
    imm = Operand('imm', int)
    syntax = Syntax(['ldd_word', ' ', rd, ',', ' ', z, '+', imm])

    def render(self):
        yield Ldd_z(self.rd.lo, self.z, self.imm)
        yield Ldd_z(self.rd.hi, self.z, self.imm + 1)


class StdWord_z(PseudoAvrInstruction):
    """ Pseudo instruction for storing a word at z + offset """
    z = Operand('z', AvrZRegister, read=True)
    imm = Operand('imm', int)
    rd = Operand('rd', AvrWordRegister, read=True)
    syntax = Syntax(['std_word', ' ', z, '+', imm, ',', ' ', rd])

    def render(self):
        yield Std_z(self.z, self.imm, self.rd.lo)
        yield Std_z(self.z, self.imm + 1, self.rd.hi)


@avr_isa.pattern('stm', 'JMP', size=2)
def pattern_jmp(context, tree):
    tgt = tree.value
    context.emit(Rjmp(tgt.name, jumps=[tgt]))


@avr_isa.pattern('stm', 'CJMP(reg16, reg16)', size=10)
def pattern_cjmp(context, tree, c0, c1):
    op, yes_label, no_label = tree.value
    opnames = {
        "==": (Breq, False),
        "!=": (Brne, False),
        '<': (Brlt, False),
        '>': (Brlt, True),
        '>=': (Brge, False),
        '<=': (Brge, True)}
    Bop, swap = opnames[op]

    if swap:
        context.emit(Cpw(c1, c0))
    else:
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
@avr_isa.pattern('reg', 'REGU8', size=0, cycles=0, energy=0)
def pattern_reg8(context, tree):
    return tree.value


@avr_isa.pattern('reg16', 'REGI16', size=0, cycles=0, energy=0)
def pattern_reg16(context, tree):
    assert isinstance(tree.value, AvrWordRegister)
    return tree.value


@avr_isa.pattern('stm', 'MOVI8(reg)', size=2)
@avr_isa.pattern('stm', 'MOVU8(reg)', size=2)
def pattern_mov8(context, tree, c0):
    context.move(tree.value, c0)


@avr_isa.pattern('stm', 'MOVI16(reg16)', size=2)
def pattern_mov16(context, tree, c0):
    context.move(tree.value, c0)


@avr_isa.pattern('reg16', 'I16TOI16(reg16)', size=0)
def pattern_i16toi16(context, tree, c0):
    return c0


@avr_isa.pattern('reg16', 'U8TOI16(reg)', size=0)
def pattern_u8toi16(context, tree, c0):
    context.move(r0, c0)
    context.emit(Eor(r1, r1))

    ud1 = RegisterUseDef()
    ud1.add_defs([r1r0])
    ud1.add_uses([r0, r1])
    context.emit(ud1)

    d = context.new_reg(AvrWordRegister)
    context.move(d, r1r0)
    return d


@avr_isa.pattern('reg', 'I16TOI8(reg16)', size=0)
@avr_isa.pattern('reg', 'I16TOU8(reg16)', size=0)
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
    context.gen_call(('swmuldiv_div', [i16, i16], i16, [c0, c1], d))
    return d


@avr_isa.pattern('reg16', 'MULI16(reg16, reg16)', size=8)
def pattern_mul16(context, tree, c0, c1):
    d = context.new_reg(AvrWordRegister)
    context.gen_call(('swmuldiv_mul', [i16, i16], i16, [c0, c1], d))
    return d


@avr_isa.pattern('reg16', 'SHRI16(reg16, reg16)', size=8)
def pattern_shr16(context, tree, c0, c1):
    """ invoke runtime """
    d = context.new_reg(AvrWordRegister)
    context.gen_call(('__shr16', [i16, i16], i16, [c0, c1], d))
    return d


@avr_isa.pattern('reg16', 'SHLI16(reg16, reg16)', size=8)
def pattern_shl16(context, tree, c0, c1):
    """ invoke runtime """
    d = context.new_reg(AvrWordRegister)
    context.gen_call(('__shl16', [i16, i16], i16, [c0, c1], d))
    return d


@avr_isa.pattern('reg', 'LDRI8(reg16)', size=4, cycles=2)
@avr_isa.pattern('reg', 'LDRU8(reg16)', size=4, cycles=2)
def pattern_ldr8(context, tree, c0):
    # z = context.new_reg(AvrZRegister)
    d = context.new_reg(AvrRegister)
    context.move(Z, c0)
    context.emit(Ldd_z(d, Z, 0))
    return d


@avr_isa.pattern(
    'reg', 'LDRI8(ADDI16(reg16, CONSTI16))', size=4, cycles=2,
    condition=lambda t: t.children[0].children[1].value < 64)
@avr_isa.pattern(
    'reg', 'LDRU8(ADDI16(reg16, CONSTI16))', size=4, cycles=2,
    condition=lambda t: t.children[0].children[1].value < 64)
def pattern_ldr8_offset(context, tree, c0):
    # z = context.new_reg(AvrZRegister)
    d = context.new_reg(AvrRegister)
    offset = tree.children[0].children[1].value
    context.move(Z, c0)
    context.emit(Ldd_z(d, Z, offset))
    return d


@avr_isa.pattern('reg16', 'LDRI16(reg16)', size=4)
def pattern_ldr16(context, tree, c0):
    # z = context.new_reg(AvrZRegister)
    d = context.new_reg(AvrWordRegister)
    context.move(Z, c0)
    context.emit(LddWord_z(d, Z, 0))
    stub = RegisterUseDef()
    stub.add_use(Z)
    context.emit(stub)
    return d


@avr_isa.pattern(
    'reg16', 'LDRI16(ADDI16(reg16, CONSTI16))', size=4, cycles=4,
    condition=lambda t: t.children[0].children[1].value < 63)
def pattern_ldr16_offset(context, tree, c0):
    # z = context.new_reg(AvrZRegister)
    d = context.new_reg(AvrWordRegister)
    offset = tree[0][1].value
    context.move(Z, c0)
    context.emit(LddWord_z(d, Z, offset))
    stub = RegisterUseDef()
    stub.add_use(Z)
    context.emit(stub)
    return d


@avr_isa.pattern('stm', 'STRI8(reg16, reg)', size=2)
@avr_isa.pattern('stm', 'STRU8(reg16, reg)', size=2)
def pattern_str8(context, tree, c0, c1):
    # z = context.new_reg(AvrZRegister)
    context.move(Z, c0)
    context.emit(Std_z(Z, 0, c1))


@avr_isa.pattern(
    'stm', 'STRI8(ADDI16(reg16, CONSTI16), reg)', size=2,
    condition=lambda t: t[0][1].value < 64)
@avr_isa.pattern(
    'stm', 'STRU8(ADDI16(reg16, CONSTI16), reg)', size=2,
    condition=lambda t: t[0][1].value < 64)
def pattern_str8_offset(context, tree, c0, c1):
    # z = context.new_reg(AvrZRegister)
    offset = tree[0][1].value
    context.move(Z, c0)
    context.emit(Std_z(Z, offset, c1))


@avr_isa.pattern('stm', 'STRI16(reg16, reg16)', size=8)
def pattern_str16(context, tree, c0, c1):
    # z = context.new_reg(AvrZRegister)
    context.move(Z, c0)
    context.emit(StdWord_z(Z, 0, c1))


@avr_isa.pattern(
    'stm', 'STRI16(ADDI16(reg16, CONSTI16), reg16)', size=6,
    condition=lambda t: t[0][1].value < 63)
def pattern_str16_offset(context, tree, c0, c1):
    # z = context.new_reg(AvrZRegister)
    offset = tree[0][1].value
    context.move(Z, c0)
    context.emit(StdWord_z(Z, offset, c1))


@avr_isa.pattern('reg', 'CONSTI8', size=2)
@avr_isa.pattern('reg', 'CONSTU8', size=2)
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
