
""" The xtensa instructions """

from ..token import Token, bit_range
from ..isa import Isa
from ..encoding import Instruction, Operand, Syntax, Transform
from ..encoding import Relocation
from ..arch import ArtificialInstruction
from .registers import AddressRegister, FloatRegister, a1
from ...utils.bitfun import wrap_negative
from ... import ir


core_isa = Isa()
narrow_isa = core_isa
floating_point_isa = core_isa
boolean_isa = core_isa


class RrrToken(Token):
    """ RRR format """
    class Info:
        size = 24

    op2 = bit_range(20, 24)
    op1 = bit_range(16, 20)
    r = bit_range(12, 16)
    s = bit_range(8, 12)
    t = bit_range(4, 8)
    op0 = bit_range(0, 4)


class Rri4Token(Token):
    class Info:
        size = 32


class Rri8Token(Token):
    class Info:
        size = 24

    imm8 = bit_range(16, 24)
    r = bit_range(12, 16)
    s = bit_range(8, 12)
    t = bit_range(4, 8)
    op0 = bit_range(0, 4)
    imm12 = s + imm8


class Ri16Token(Token):
    class Info:
        size = 24

    imm16 = bit_range(8, 24)
    t = bit_range(4, 8)
    op0 = bit_range(0, 4)


class RsrToken(Token):
    class Info:
        size = 24


class CallToken(Token):
    class Info:
        size = 24

    imm18 = bit_range(6, 24)
    n = bit_range(4, 6)
    op0 = bit_range(0, 4)


class CallxToken(Token):
    class Info:
        size = 24

    op2 = bit_range(20, 24)
    op1 = bit_range(16, 20)
    r = bit_range(12, 16)
    s = bit_range(8, 12)
    m = bit_range(6, 8)
    n = bit_range(4, 6)
    op0 = bit_range(0, 4)


class Bri8Token(Token):
    class Info:
        size = 24

    imm8 = bit_range(16, 24)
    r = bit_range(12, 16)
    s = bit_range(8, 12)
    m = bit_range(6, 8)
    n = bit_range(4, 6)
    op0 = bit_range(0, 4)


class Bri12Token(Token):
    class Info:
        size = 24

    imm12 = bit_range(12, 24)
    s = bit_range(8, 12)
    m = bit_range(6, 8)
    n = bit_range(4, 6)
    op0 = bit_range(0, 4)


class RrrnToken(Token):
    """ Narrow RRR format """
    class Info:
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


class XtensaMacroInstruction(ArtificialInstruction):
    isa = core_isa


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


@core_isa.register_relocation
class Ri16Relocation(Relocation):
    name = 'ri16'
    number = 3
    token = Ri16Token
    field = 'imm16'

    def calc(self, sym_value, reloc_value):
        assert sym_value & 3 == 0
        offset = (sym_value - ((reloc_value + 3) & 0xfffffffc))
        offset = offset >> 2
        # assert offset in range(-60000, 2095), str(offset)
        # TODO: this wrap_negative is somewhat weird
        return wrap_negative(offset, 16)


@core_isa.register_relocation
class Call0Relocation(Relocation):
    name = 'call0'
    number = 4
    token = CallToken
    field = 'imm18'

    def calc(self, sym_value, reloc_value):
        # Nice weird call0 encoding!
        assert sym_value % 4 == 0  # Assert 32 bit aligned!
        s = sym_value >> 2
        r = (reloc_value & 0xfffffffc) >> 2
        offset = s - (r + 1)
        # assert offset in range(-524284, 524288), str(offset)
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
        return [Call0Relocation(self.label)]


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


class L32r(XtensaCoreInstruction):
    """ Load 32-bit pc relative """
    tokens = [Ri16Token]
    t = Operand('t', AddressRegister, write=True)
    label = Operand('label', str)
    patterns = {'t': t, 'op0': 1}
    syntax = Syntax(['l32r', ' ', t, ',', ' ', label])

    def relocations(self):
        return [Ri16Relocation(self.label)]


class Mov(XtensaMacroInstruction):
    """ Move (actually a macro) """
    r = Operand('r', AddressRegister, write=True)
    s = Operand('s', AddressRegister, read=True)
    syntax = Syntax(['mov', ' ', r, ',', ' ', s])

    def render(self):
        yield Or(self.r, self.s, self.s)


class Movi(XtensaCoreInstruction):
    """ Move immediate """
    tokens = [Rri8Token]
    t = Operand('t', AddressRegister, write=True)
    imm = Operand('imm', int)
    patterns = {'imm12': imm, 'r': 10, 't': t, 'op0': 2}
    syntax = Syntax(['movi', ' ', t, ',', ' ', imm])


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


class Ret(XtensaCoreInstruction):
    """ Non-windowed return """
    tokens = [CallxToken]
    patterns = {'op2': 0, 'op1': 0, 'r': 0, 's': 0, 'm': 2, 'n': 0, 'op0': 0}
    syntax = Syntax(['ret'])


class S8i(XtensaCoreInstruction):
    """ Store 8-bit """
    tokens = [Rri8Token]
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, read=True)
    imm = Operand('imm', int)
    patterns = {'imm8': imm, 'r': 4, 's': s, 't': t, 'op0': 2}
    syntax = Syntax(['s8i', ' ', t, ',', ' ', s, ',', ' ', imm])


class S16i(XtensaCoreInstruction):
    """ Store 16-bit """
    tokens = [Rri8Token]
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, read=True)
    imm = Operand('imm', int)
    patterns = {'imm8': Shift1(imm), 'r': 5, 's': s, 't': t, 'op0': 2}
    syntax = Syntax(['s16i', ' ', t, ',', ' ', s, ',', ' ', imm])


class S32i(XtensaCoreInstruction):
    """ Store 32-bit """
    tokens = [Rri8Token]
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, read=True)
    imm = Operand('imm', int)
    patterns = {'imm8': Shift2(imm), 'r': 6, 's': s, 't': t, 'op0': 2}
    syntax = Syntax(['s32i', ' ', t, ',', ' ', s, ',', ' ', imm])


class Sll(XtensaCoreInstruction):
    """ Shift left logical """
    tokens = [RrrToken]
    r = Operand('r', AddressRegister, write=True)
    s = Operand('s', AddressRegister, read=True)
    patterns = {'op2': 10, 'op1': 1, 'r': r, 's': s, 't': 0, 'op0': 0}
    syntax = Syntax(['sll', ' ', r, ',', ' ', s])


class Sra(XtensaCoreInstruction):
    """ Shift right arithmatic """
    tokens = [RrrToken]
    r = Operand('r', AddressRegister, write=True)
    t = Operand('t', AddressRegister, read=True)
    patterns = {'op2': 11, 'op1': 1, 'r': r, 's': 0, 't': t, 'op0': 0}
    syntax = Syntax(['sra', ' ', r, ',', ' ', t])


class Srl(XtensaCoreInstruction):
    """ Shift right logical """
    tokens = [RrrToken]
    r = Operand('r', AddressRegister, write=True)
    t = Operand('t', AddressRegister, read=True)
    patterns = {'op2': 9, 'op1': 1, 'r': r, 's': 0, 't': t, 'op0': 0}
    syntax = Syntax(['srl', ' ', r, ',', ' ', t])


class Srli(XtensaCoreInstruction):
    """ Shift right logical immediate """
    tokens = [RrrToken]
    r = Operand('r', AddressRegister, write=True)
    t = Operand('t', AddressRegister, read=True)
    imm = Operand('imm', int)
    patterns = {'op2': 4, 'op1': 1, 'r': r, 's': imm, 't': t, 'op0': 0}
    syntax = Syntax(['srli', ' ', r, ',', ' ', t, ',', ' ', imm])


class Ssl(XtensaCoreInstruction):
    """ Set shift amount for left shift """
    tokens = [RrrToken]
    s = Operand('s', AddressRegister, read=True)
    patterns = {'op2': 4, 'op1': 0, 'r': 1, 's': s, 't': 0, 'op0': 0}
    syntax = Syntax(['ssl', ' ', s])


class Ssr(XtensaCoreInstruction):
    """ Set shift amount for right shift """
    tokens = [RrrToken]
    s = Operand('s', AddressRegister, read=True)
    patterns = {'op2': 4, 'op1': 0, 'r': 0, 's': s, 't': 0, 'op0': 0}
    syntax = Syntax(['ssr', ' ', s])


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


# Extra handy instructions:
class Push(XtensaMacroInstruction):
    """ Push a register on stack """
    r = Operand('r', AddressRegister, read=True)
    syntax = Syntax(['push', ' ', r])

    def render(self):
        yield Addi(a1, a1, -4)
        yield S32i(self.r, a1, 0)


class Pop(XtensaMacroInstruction):
    """ Pop a register from the stack """
    r = Operand('r', AddressRegister, write=True)
    syntax = Syntax(['pop', ' ', r])

    def render(self):
        yield L32i(self.r, a1, 0)
        yield Addi(a1, a1, 4)


@core_isa.pattern('stm', 'MOVU8(reg)')
def pattern_mov_u8(context, tree, c0):
    d = tree.value
    context.emit(Mov(d, c0, ismove=True))


@core_isa.pattern('stm', 'MOVI32(reg)')
def pattern_mov_i32(context, tree, c0):
    d = tree.value
    context.emit(Mov(d, c0, ismove=True))


@core_isa.pattern('reg', 'REGU8')
@core_isa.pattern('reg', 'REGI32')
def pattern_reg(context, tree):
    return tree.value


@core_isa.pattern('reg', 'LABEL')
def pattern_label(context, tree):
    # Load the address of a label
    # store the address label in the constant pool, and load this value
    ln = context.frame.add_constant(tree.value)
    d = context.new_reg(AddressRegister)
    context.emit(L32r(d, ln))
    return d


@core_isa.pattern(
    'reg', 'CONSTI32', size=3, cycles=1, energy=1,
    condition=lambda t: t.value in range(-2048, 2047))
def pattern_const_small_i32(context, tree, size=3, cycles=1, energy=1):
    d = context.new_reg(AddressRegister)
    context.emit(Movi(d, tree.value))
    return d


@core_isa.pattern('reg', 'CONSTI32', size=8, cycles=5, energy=5)
def pattern_const_i32(context, tree):
    # Load the address of a label
    # store the address label in the constant pool, and load this value
    ln = context.frame.add_constant(tree.value)
    d = context.new_reg(AddressRegister)
    context.emit(L32r(d, ln))
    return d


@core_isa.pattern('reg', 'CONSTI8')
@core_isa.pattern('reg', 'CONSTU8')
def pattern_const_8(context, tree):
    # Load the address of a label
    # store the address label in the constant pool, and load this value
    ln = context.frame.add_constant(tree.value)
    d = context.new_reg(AddressRegister)
    context.emit(L32r(d, ln))
    # TODO: movi maybe used here
    return d


@core_isa.pattern('reg', 'I32TOI32(reg)')
def pattern_i32_to_i32(context, tree, c0):
    return c0


@core_isa.pattern('reg', 'I32TOU8(reg)')
def pattern_i32_to_u8(context, tree, c0):
    return c0


@core_isa.pattern('reg', 'U8TOI32(reg)')
def pattern_u8_to_i32(context, tree, c0):
    return c0


@core_isa.pattern('reg', 'ADDI32(reg,reg)', size=3, cycles=1, energy=1)
def pattern_add_i32(context, tree, c0, c1):
    d = context.new_reg(AddressRegister)
    context.emit(Add(d, c0, c1))
    return d


@core_isa.pattern(
    'reg', 'ADDI32(reg,CONSTI32)', size=3, cycles=1, energy=1,
    condition=lambda t: t[1].value in range(-128, 127))
def pattern_add_i32_imm(context, tree, c0):
    d = context.new_reg(AddressRegister)
    context.emit(Addi(d, c0, tree[1].value))
    return d


@core_isa.pattern('reg', 'SUBI32(reg,reg)', size=3, cycles=1, energy=1)
def pattern_sub_i32(context, tree, c0, c1):
    d = context.new_reg(AddressRegister)
    context.emit(Sub(d, c0, c1))
    return d


@core_isa.pattern('reg', 'MULI32(reg, reg)', size=10, cycles=10, energy=10)
def pattern_mul32(context, tree, c0, c1):
    d = context.new_reg(AddressRegister)
    # Generate call into runtime lib function!
    context.gen_call(('swmuldiv_mul', [ir.i32, ir.i32], ir.i32, [c0, c1], d))
    return d


@core_isa.pattern('reg', 'DIVI32(reg, reg)')
def pattern_div32(context, tree, c0, c1):
    d = context.new_reg(AddressRegister)
    # Generate call into runtime lib function!
    context.gen_call(('swmuldiv_div', [ir.i32, ir.i32], ir.i32, [c0, c1], d))
    return d


@core_isa.pattern('reg', 'ANDI32(reg,reg)')
def pattern_and_i32(context, tree, c0, c1):
    d = context.new_reg(AddressRegister)
    context.emit(And(d, c0, c1))
    return d


@core_isa.pattern('reg', 'ORI32(reg,reg)')
def pattern_or_i32(context, tree, c0, c1):
    d = context.new_reg(AddressRegister)
    context.emit(Or(d, c0, c1))
    return d


@core_isa.pattern('reg', 'SHLI32(reg,reg)')
def pattern_shl_i32(context, tree, c0, c1):
    d = context.new_reg(AddressRegister)
    context.emit(Ssl(c1))
    context.emit(Sll(d, c0))
    return d


@core_isa.pattern('reg', 'SHRI32(reg,reg)')
def pattern_shr_i32(context, tree, c0, c1):
    d = context.new_reg(AddressRegister)
    context.emit(Ssr(c1))
    context.emit(Srl(d, c0))
    return d


@core_isa.pattern('reg', 'LDRU8(reg)')
def pattern_ldr_u8(context, tree, c0):
    d = context.new_reg(AddressRegister)
    context.emit(L8ui(d, c0, 0))
    return d


@core_isa.pattern('stm', 'STRU8(reg, reg)')
def pattern_str_u8(context, tree, c0, c1):
    context.emit(S8i(c1, c0, 0))


@core_isa.pattern('reg', 'LDRI32(reg)', size=3, cycles=2, energy=2)
def pattern_ldr_i32(context, tree, c0):
    d = context.new_reg(AddressRegister)
    context.emit(L32i(d, c0, 0))
    return d


@core_isa.pattern(
    'reg', 'LDRI32(ADDI32(reg, CONSTI32))', size=3, cycles=2, energy=2,
    condition=lambda t: t[0][1].value in range(0, 1020, 4))
def pattern_ldr_i32_add_const(context, tree, c0):
    d = context.new_reg(AddressRegister)
    context.emit(L32i(d, c0, tree[0][1].value))
    return d


@core_isa.pattern('stm', 'STRI32(reg, reg)', size=3, cycles=2, energy=2)
def pattern_str_i32(context, tree, c0, c1):
    context.emit(S32i(c1, c0, 0))


@core_isa.pattern(
    'stm', 'STRI32(ADDI32(reg, CONSTI32), reg)', size=3, cycles=2, energy=2,
    condition=lambda t: t[0][1].value in range(0, 1020, 4))
def pattern_str_i32_add_const(context, tree, c0, c1):
    context.emit(S32i(c1, c0, tree[0][1].value))


@core_isa.pattern('stm', 'JMP')
def pattern_jmp(context, tree):
    tgt = tree.value
    context.emit(J(tgt.name, jumps=[tgt]))


@core_isa.pattern('stm', 'CJMP(reg, reg)')
def pattern_cjmp(context, tree, c0, c1):
    op, yes_label, no_label = tree.value
    opnames = {
        "<": (Blt, False),
        ">": (Blt, True),
        "==": (Beq, False),
        "!=": (Bne, False),
        ">=": (Bge, False),
        "<=": (Bge, True),
        }
    jmp_ins = J(no_label.name, jumps=[no_label])
    tmp_label = context.new_label()
    Bop, swap = opnames[op]
    if swap:
        context.emit(Bop(c1, c0, tmp_label.name, jumps=[tmp_label, jmp_ins]))
    else:
        context.emit(Bop(c0, c1, tmp_label.name, jumps=[tmp_label, jmp_ins]))
    context.emit(jmp_ins)  # The false label
    context.emit(tmp_label)
    context.emit(J(yes_label.name, jumps=[yes_label]))


@core_isa.pattern('stm', 'CALL', size=10)
def pattern_call(context, tree):
    context.gen_call(tree.value)
