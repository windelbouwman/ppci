
""" The xtensa instructions """

from ..token import Token, bit_range
from ..isa import Isa
from ..encoding import Instruction, Operand, Syntax, Transform
from ..encoding import Relocation
from .registers import AddressRegister, FloatRegister
from ...utils.bitfun import wrap_negative


core_isa = Isa()
narrow_isa = core_isa
floating_point_isa = core_isa
boolean_isa = core_isa


class RrrToken(Token):
    """ RRR format """
    size = 24
    op2 = bit_range(20, 24)
    op1 = bit_range(16, 20)
    r = bit_range(12, 16)
    s = bit_range(8, 12)
    t = bit_range(4, 8)
    op0 = bit_range(0, 4)


class Rri4Token(Token):
    size = 32


class Rri8Token(Token):
    size = 24
    imm8 = bit_range(16, 24)
    r = bit_range(12, 16)
    s = bit_range(8, 12)
    t = bit_range(4, 8)
    op0 = bit_range(0, 4)


class Ri16Token(Token):
    size = 24
    imm16 = bit_range(8, 24)
    t = bit_range(4, 8)
    op0 = bit_range(0, 4)


class RsrToken(Token):
    size = 24


class CallToken(Token):
    size = 24
    imm18 = bit_range(6, 24)
    n = bit_range(4, 6)
    op0 = bit_range(0, 4)


class Bri8Token(Token):
    size = 24
    imm8 = bit_range(16, 24)
    r = bit_range(12, 16)
    s = bit_range(8, 12)
    m = bit_range(6, 8)
    n = bit_range(4, 6)
    op0 = bit_range(0, 4)


class Bri12Token(Token):
    size = 24
    imm12 = bit_range(12, 24)
    s = bit_range(8, 12)
    m = bit_range(6, 8)
    n = bit_range(4, 6)
    op0 = bit_range(0, 4)


class RrrnToken(Token):
    """ Narrow RRR format """
    size = 16
    r = bit_range(12, 16)
    s = bit_range(8, 12)
    t = bit_range(4, 8)
    op0 = bit_range(0, 4)


class Shift1(Transform):
    def forwards(self, val):
        return val >> 1

    def backwards(self, val):
        return val << 1


class Shift2(Transform):
    def forwards(self, val):
        return val >> 2

    def backwards(self, val):
        return val << 2


class XtensaCoreInstruction(Instruction):
    isa = core_isa


class XtensaNarrowInstruction(Instruction):
    isa = narrow_isa


class XtensaFloatingPointInstruction(Instruction):
    isa = floating_point_isa


class XtensaBooleanInstruction(Instruction):
    isa = boolean_isa


class Abs(XtensaCoreInstruction):
    """ Calculate absolute value """
    tokens = [RrrToken]
    r = Operand('r', AddressRegister, write=True)
    t = Operand('t', AddressRegister, read=True)
    patterns = {'op2': 6, 'op1': 0, 'r': r, 's': 1, 't': t, 'op0': 0}
    syntax = Syntax(['abs', ' ', r, ',', ' ', t])


class Abss(XtensaFloatingPointInstruction):
    """ Calculate absolute value single precision float """
    tokens = [RrrToken]
    fr = Operand('fr', FloatRegister, write=True)
    fs = Operand('fs', FloatRegister, read=True)
    patterns = {'op2': 15, 'op1': 10, 'r': fr, 's': fs, 't': 1, 'op0': 0}
    syntax = Syntax(['abs', '.', 's', ' ', fr, ',', ' ', fs])


class Add(XtensaCoreInstruction):
    """ Add """
    tokens = [RrrToken]
    r = Operand('r', AddressRegister, write=True)
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, read=True)
    patterns = {'op2': 8, 'op1': 0, 'r': r, 's': s, 't': t, 'op0': 0}
    syntax = Syntax(['add', ' ', r, ',', ' ', s, ',', ' ', t])


class Addn(XtensaNarrowInstruction):
    """ Narrow add """
    tokens = [RrrnToken]
    r = Operand('r', AddressRegister, write=True)
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, read=True)
    patterns = {'r': r, 's': s, 't': t, 'op0': 0b1010}
    syntax = Syntax(['add', '.', 'n', ' ', r, ',', ' ', s, ',', ' ', t])


class Adds(XtensaFloatingPointInstruction):
    """ Add.s """
    tokens = [RrrToken]
    fr = Operand('fr', FloatRegister, write=True)
    fs = Operand('fs', FloatRegister, read=True)
    ft = Operand('ft', FloatRegister, read=True)
    patterns = {'op2': 0, 'op1': 10, 'r': fr, 's': fs, 't': ft, 'op0': 0}
    syntax = Syntax(['add', '.', 's', ' ', fr, ',', ' ', fs, ',', ' ', ft])


class Addi(XtensaCoreInstruction):
    """ Add immediate """
    tokens = [Rri8Token]
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, write=True)
    imm = Operand('imm', int)
    patterns = {'imm8': imm, 'r': 0xc, 's': s, 't': t, 'op0': 2}
    syntax = Syntax(['addi', ' ', t, ',', ' ', s, ',', ' ', imm])


# TODO: addi.n


class Addmi(XtensaCoreInstruction):
    """ Add immediate with shift by 8 """
    tokens = [Rri8Token]
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, write=True)
    imm = Operand('imm', int)
    patterns = {'imm8': imm, 'r': 0xd, 's': s, 't': t, 'op0': 2}
    syntax = Syntax(['addmi', ' ', t, ',', ' ', s, ',', ' ', imm])


class Addx2(XtensaCoreInstruction):
    """ Addx2 """
    tokens = [RrrToken]
    r = Operand('r', AddressRegister, write=True)
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, read=True)
    patterns = {'op2': 9, 'op1': 0, 'r': r, 's': s, 't': t, 'op0': 0}
    syntax = Syntax(['addx2', ' ', r, ',', ' ', s, ',', ' ', t])


class Addx4(XtensaCoreInstruction):
    """ Addx4 """
    tokens = [RrrToken]
    r = Operand('r', AddressRegister, write=True)
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, read=True)
    patterns = {'op2': 10, 'op1': 0, 'r': r, 's': s, 't': t, 'op0': 0}
    syntax = Syntax(['addx4', ' ', r, ',', ' ', s, ',', ' ', t])


class Addx8(XtensaCoreInstruction):
    """ Addx8 """
    tokens = [RrrToken]
    r = Operand('r', AddressRegister, write=True)
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, read=True)
    patterns = {'op2': 0b1011, 'op1': 0, 'r': r, 's': s, 't': t, 'op0': 0}
    syntax = Syntax(['addx8', ' ', r, ',', ' ', s, ',', ' ', t])

# TODO: All4


class And(XtensaCoreInstruction):
    """ And """
    tokens = [RrrToken]
    r = Operand('r', AddressRegister, write=True)
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, read=True)
    patterns = {'op2': 1, 'op1': 0, 'r': r, 's': s, 't': t, 'op0': 0}
    syntax = Syntax(['and', ' ', r, ',', ' ', s, ',', ' ', t])


class Andb(XtensaBooleanInstruction):
    """ Boolean and """
    tokens = [RrrToken]
    r = Operand('r', AddressRegister, write=True)
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, read=True)
    patterns = {'op2': 0, 'op1': 2, 'r': r, 's': s, 't': t, 'op0': 0}
    syntax = Syntax(['andb', ' ', r, ',', ' ', s, ',', ' ', t])


class Andbc(XtensaBooleanInstruction):
    """ Boolean and with complement """
    tokens = [RrrToken]
    r = Operand('r', AddressRegister, write=True)
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, read=True)
    patterns = {'op2': 1, 'op1': 2, 'r': r, 's': s, 't': t, 'op0': 0}
    syntax = Syntax(['andbc', ' ', r, ',', ' ', s, ',', ' ', t])


# TODO: any4

# TODO: any8

# TODO: ball

@core_isa.register_relocation
class Imm8Relocation(Relocation):
    name = 'imm8'
    number = 0
    token = Rri8Token
    field = 'imm8'

    def calc(self, sym_value, reloc_value):
        offset = (sym_value - reloc_value - 4)
        assert offset in range(-128, 127), str(offset)
        # TODO: this wrap_negative is somewhat weird
        return wrap_negative(offset, 8)


@core_isa.register_relocation
class Imm12Relocation(Relocation):
    name = 'bri12'
    number = 1
    token = Bri12Token
    field = 'imm12'

    def calc(self, sym_value, reloc_value):
        offset = (sym_value - reloc_value - 4)
        assert offset in range(-2096, 2095), str(offset)
        # TODO: this wrap_negative is somewhat weird
        return wrap_negative(offset, 12)


@core_isa.register_relocation
class Imm18Relocation(Relocation):
    name = 'call18'
    number = 2
    token = CallToken
    field = 'imm18'

    def calc(self, sym_value, reloc_value):
        offset = (sym_value - reloc_value - 4)
        assert offset in range(-131068, 131075), str(offset)
        # TODO: this wrap_negative is somewhat weird
        return wrap_negative(offset, 18)


class Bany(XtensaCoreInstruction):
    """ Branch if any bit set """
    tokens = [Rri8Token]
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, read=True)
    label = Operand('label', str)
    patterns = {'r': 8, 's': s, 't': t, 'op0': 7}
    syntax = Syntax(['bany', ' ', s, ',', ' ', t, ',', ' ', label])

    def relocations(self):
        return [Imm8Relocation(self.label)]


class Bbc(XtensaCoreInstruction):
    """ Branch if bit clear """
    tokens = [Rri8Token]
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, read=True)
    label = Operand('label', str)
    patterns = {'r': 5, 's': s, 't': t, 'op0': 7}
    syntax = Syntax(['bbc', ' ', s, ',', ' ', t, ',', ' ', label])

    def relocations(self):
        return [Imm8Relocation(self.label)]


class Beq(XtensaCoreInstruction):
    """ Branch if equal """
    tokens = [Rri8Token]
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, read=True)
    label = Operand('label', str)
    patterns = {'r': 1, 's': s, 't': t, 'op0': 7}
    syntax = Syntax(['beq', ' ', s, ',', ' ', t, ',', ' ', label])

    def relocations(self):
        return [Imm8Relocation(self.label)]


class Beqz(XtensaCoreInstruction):
    """ Branch if equal to zero """
    tokens = [Bri12Token]
    s = Operand('s', AddressRegister, read=True)
    label = Operand('label', str)
    patterns = {'s': s, 'm': 0, 'n': 1, 'op0': 6}
    syntax = Syntax(['beqz', ' ', s, ',', ' ', label])

    def relocations(self):
        return [Imm12Relocation(self.label)]


class Bge(XtensaCoreInstruction):
    """ Branch if greater than or equal """
    tokens = [Rri8Token]
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, read=True)
    label = Operand('label', str)
    patterns = {'r': 10, 's': s, 't': t, 'op0': 7}
    syntax = Syntax(['bge', ' ', s, ',', ' ', t, ',', ' ', label])

    def relocations(self):
        return [Imm8Relocation(self.label)]


class Bgeu(XtensaCoreInstruction):
    """ Branch if greater than or equal unsigned """
    tokens = [Rri8Token]
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, read=True)
    label = Operand('label', str)
    patterns = {'r': 11, 's': s, 't': t, 'op0': 7}
    syntax = Syntax(['bgeu', ' ', s, ',', ' ', t, ',', ' ', label])

    def relocations(self):
        return [Imm8Relocation(self.label)]


class Blt(XtensaCoreInstruction):
    """ Branch if less than """
    tokens = [Rri8Token]
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, read=True)
    label = Operand('label', str)
    patterns = {'r': 2, 's': s, 't': t, 'op0': 7}
    syntax = Syntax(['blt', ' ', s, ',', ' ', t, ',', ' ', label])

    def relocations(self):
        return [Imm8Relocation(self.label)]


class Bltu(XtensaCoreInstruction):
    """ Branch if less than unsigned """
    tokens = [Rri8Token]
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, read=True)
    label = Operand('label', str)
    patterns = {'r': 3, 's': s, 't': t, 'op0': 7}
    syntax = Syntax(['bltu', ' ', s, ',', ' ', t, ',', ' ', label])

    def relocations(self):
        return [Imm8Relocation(self.label)]


class Bne(XtensaCoreInstruction):
    """ Branch if not equal """
    tokens = [Rri8Token]
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, read=True)
    label = Operand('label', str)
    patterns = {'r': 9, 's': s, 't': t, 'op0': 7}
    syntax = Syntax(['bne', ' ', s, ',', ' ', t, ',', ' ', label])

    def relocations(self):
        return [Imm8Relocation(self.label)]


class Bnez(XtensaCoreInstruction):
    """ Branch if not equal to zero """
    tokens = [Bri12Token]
    s = Operand('s', AddressRegister, read=True)
    label = Operand('label', str)
    patterns = {'s': s, 'm': 1, 'n': 1, 'op0': 6}
    syntax = Syntax(['bnez', ' ', s, ',', ' ', label])

    def relocations(self):
        return [Imm12Relocation(self.label)]


class Call0(XtensaCoreInstruction):
    """ Non windowed call """
    tokens = [CallToken]
    label = Operand('label', str)
    patterns = {'n': 0, 'op0': 5}
    syntax = Syntax(['call0', ' ', label])

    def relocations(self):
        return [Imm18Relocation(self.label)]


class J(XtensaCoreInstruction):
    """ Unconditional jump """
    tokens = [CallToken]
    label = Operand('label', str)
    patterns = {'n': 0, 'op0': 6}
    syntax = Syntax(['j', ' ', label])

    def relocations(self):
        return [Imm18Relocation(self.label)]


class L8ui(XtensaCoreInstruction):
    """ Load 8-bit unsigned """
    tokens = [Rri8Token]
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, write=True)
    imm = Operand('imm', int)
    patterns = {'imm8': imm, 'r': 0, 's': s, 't': t, 'op0': 2}
    syntax = Syntax(['l8ui', ' ', t, ',', ' ', s, ',', ' ', imm])


class L16si(XtensaCoreInstruction):
    """ Load 16-bit signed """
    tokens = [Rri8Token]
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, write=True)
    imm = Operand('imm', int)
    patterns = {'imm8': Shift1(imm), 'r': 9, 's': s, 't': t, 'op0': 2}
    syntax = Syntax(['l16si', ' ', t, ',', ' ', s, ',', ' ', imm])


class L16ui(XtensaCoreInstruction):
    """ Load 16-bit unsigned """
    tokens = [Rri8Token]
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, write=True)
    imm = Operand('imm', int)
    patterns = {'imm8': Shift1(imm), 'r': 1, 's': s, 't': t, 'op0': 2}
    syntax = Syntax(['l16ui', ' ', t, ',', ' ', s, ',', ' ', imm])


class L32i(XtensaCoreInstruction):
    """ Load 32-bit """
    tokens = [Rri8Token]
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, write=True)
    imm = Operand('imm', int)
    patterns = {'imm8': Shift2(imm), 'r': 2, 's': s, 't': t, 'op0': 2}
    syntax = Syntax(['l32i', ' ', t, ',', ' ', s, ',', ' ', imm])


class L32in(XtensaNarrowInstruction):
    """ Narrow load 32-bit """
    tokens = [RrrnToken]
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, write=True)
    imm = Operand('imm', int)
    patterns = {'r': Shift2(imm), 's': s, 't': t, 'op0': 8}
    syntax = Syntax(['l32i', '.', 'n', ' ', t, ',', ' ', s, ',', ' ', imm])


class Neg(XtensaCoreInstruction):
    """ Negate """
    tokens = [RrrToken]
    r = Operand('r', AddressRegister, write=True)
    t = Operand('t', AddressRegister, read=True)
    patterns = {'op2': 6, 'op1': 0, 'r': r, 's': 0, 't': t, 'op0': 0}
    syntax = Syntax(['neg', ' ', r, ',', ' ', t])


class Nop(XtensaCoreInstruction):
    """ No operation """
    tokens = [RrrToken]
    patterns = {'op2': 0, 'op1': 0, 'r': 2, 's': 0, 't': 15, 'op0': 0}
    syntax = Syntax(['nop'])


class Or(XtensaCoreInstruction):
    """ Bitwise logical or """
    tokens = [RrrToken]
    r = Operand('r', AddressRegister, write=True)
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, read=True)
    patterns = {'op2': 2, 'op1': 0, 'r': r, 's': s, 't': t, 'op0': 0}
    syntax = Syntax(['or', ' ', r, ',', ' ', s, ',', ' ', t])


class Srli(XtensaCoreInstruction):
    """ Shift right logical immediate """
    tokens = [RrrToken]
    r = Operand('r', AddressRegister, write=True)
    t = Operand('t', AddressRegister, read=True)
    imm = Operand('imm', int)
    patterns = {'op2': 4, 'op1': 1, 'r': r, 's': imm, 't': t, 'op0': 0}
    syntax = Syntax(['srli', ' ', r, ',', ' ', t, ',', ' ', imm])


class Sub(XtensaCoreInstruction):
    """ Substract """
    tokens = [RrrToken]
    r = Operand('r', AddressRegister, write=True)
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, read=True)
    patterns = {'op2': 12, 'op1': 0, 'r': r, 's': s, 't': t, 'op0': 0}
    syntax = Syntax(['sub', ' ', r, ',', ' ', s, ',', ' ', t])


class Subx2(XtensaCoreInstruction):
    """ Substract with shift by 1 """
    tokens = [RrrToken]
    r = Operand('r', AddressRegister, write=True)
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, read=True)
    patterns = {'op2': 13, 'op1': 0, 'r': r, 's': s, 't': t, 'op0': 0}
    syntax = Syntax(['subx2', ' ', r, ',', ' ', s, ',', ' ', t])


class Subx4(XtensaCoreInstruction):
    """ Substract with shift by 2 """
    tokens = [RrrToken]
    r = Operand('r', AddressRegister, write=True)
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, read=True)
    patterns = {'op2': 14, 'op1': 0, 'r': r, 's': s, 't': t, 'op0': 0}
    syntax = Syntax(['subx4', ' ', r, ',', ' ', s, ',', ' ', t])


class Subx8(XtensaCoreInstruction):
    """ Substract with shift by 3 """
    tokens = [RrrToken]
    r = Operand('r', AddressRegister, write=True)
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, read=True)
    patterns = {'op2': 15, 'op1': 0, 'r': r, 's': s, 't': t, 'op0': 0}
    syntax = Syntax(['subx8', ' ', r, ',', ' ', s, ',', ' ', t])


class Xor(XtensaCoreInstruction):
    """ Bitwise logical exclusive or """
    tokens = [RrrToken]
    r = Operand('r', AddressRegister, write=True)
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, read=True)
    patterns = {'op2': 3, 'op1': 0, 'r': r, 's': s, 't': t, 'op0': 0}
    syntax = Syntax(['xor', ' ', r, ',', ' ', s, ',', ' ', t])


@core_isa.pattern('reg', 'ADDI32(reg,reg)')
def pattern_add_i32(context, tree, c0, c1):
    d = context.new_reg(AddressRegister)
    context.emit(Add(d, c0, c1))
    return d


@core_isa.pattern('reg', 'ANDI32(reg,reg)')
def pattern_and_i32(context, tree, c0, c1):
    d = context.new_reg(AddressRegister)
    context.emit(And(d, c0, c1))
    return d


@core_isa.pattern('reg', 'LDRU8(reg)')
def pattern_ldr_u8(context, tree, c0):
    d = context.new_reg(AddressRegister)
    context.emit(L8ui(d, c0, 0))
    return d


@core_isa.pattern('reg', 'LDRI32(reg)')
def pattern_ldr_i32(context, tree, c0):
    d = context.new_reg(AddressRegister)
    context.emit(L32i(d, c0, 0))
    return d
