
""" The xtensa instructions """

from ..token import Token, bit_range
from ..arch import Isa
from ..encoding import Instruction, Operand, Syntax
from .registers import AddressRegister, XRegf


core_isa = Isa()


class RrrToken(Token):
    size = 24
    op2 = bit_range(20, 24)
    op1 = bit_range(16, 20)
    r = bit_range(12, 16)
    s = bit_range(8, 12)
    t = bit_range(4, 8)
    op0 = bit_range(0, 4)


class RrrnToken(Token):
    """ Narrow variant """
    size = 16
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


class XtensaInstruction(Instruction):
    isa = core_isa


class Abs(XtensaInstruction):
    """ Calculate absolute value """
    tokens = [RrrToken]
    r = Operand('r', AddressRegister, write=True)
    t = Operand('t', AddressRegister, read=True)
    patterns = {'op2': 6, 'op1': 0, 'r': r, 's': 1, 't': t, 'op0': 0}
    syntax = Syntax(['abs', ' ', r, ',', ' ', t])


class Abss(XtensaInstruction):
    """ Calculate absolute value single precision float """
    tokens = [RrrToken]
    fr = Operand('fr', XRegf, write=True)
    fs = Operand('fs', XRegf, read=True)
    patterns = {'op2': 15, 'op1': 10, 'r': fr, 's': fs, 't': 1, 'op0': 0}
    syntax = Syntax(['abs', '.', 's', ' ', fr, ',', ' ', fs])


class Add(XtensaInstruction):
    """ Add """
    tokens = [RrrToken]
    r = Operand('r', AddressRegister, write=True)
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, read=True)
    patterns = {'op2': 8, 'op1': 0, 'r': r, 's': s, 't': t, 'op0': 0}
    syntax = Syntax(['add', ' ', r, ',', ' ', s, ',', ' ', t])


class Addn(XtensaInstruction):
    """ Narrow add """
    tokens = [RrrnToken]
    r = Operand('r', AddressRegister, write=True)
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, read=True)
    patterns = {'r': r, 's': s, 't': t, 'op0': 0b1010}
    syntax = Syntax(['add', '.', 'n', ' ', r, ',', ' ', s, ',', ' ', t])


class Adds(XtensaInstruction):
    """ Add.s """
    tokens = [RrrToken]
    fr = Operand('fr', XRegf, write=True)
    fs = Operand('fs', XRegf, read=True)
    ft = Operand('ft', XRegf, read=True)
    patterns = {'op2': 0, 'op1': 10, 'r': fr, 's': fs, 't': ft, 'op0': 0}
    syntax = Syntax(['add', '.', 's', ' ', fr, ',', ' ', fs, ',', ' ', ft])


class Addi(XtensaInstruction):
    """ Add immediate """
    tokens = [Rri8Token]
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, write=True)
    imm = Operand('imm', int)
    patterns = {'imm8': imm, 'r': 0xc, 's': s, 't': t, 'op0': 2}
    syntax = Syntax(['addi', ' ', t, ',', ' ', s, ',', ' ', imm])


# TODO: addi.n


class Addmi(XtensaInstruction):
    """ Add immediate with shift by 8 """
    tokens = [Rri8Token]
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, write=True)
    imm = Operand('imm', int)
    patterns = {'imm8': imm, 'r': 0xd, 's': s, 't': t, 'op0': 2}
    syntax = Syntax(['addmi', ' ', t, ',', ' ', s, ',', ' ', imm])


class Addx2(XtensaInstruction):
    """ Addx2 """
    tokens = [RrrToken]
    r = Operand('r', AddressRegister, write=True)
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, read=True)
    patterns = {'op2': 9, 'op1': 0, 'r': r, 's': s, 't': t, 'op0': 0}
    syntax = Syntax(['addx2', ' ', r, ',', ' ', s, ',', ' ', t])


class Addx4(XtensaInstruction):
    """ Addx4 """
    tokens = [RrrToken]
    r = Operand('r', AddressRegister, write=True)
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, read=True)
    patterns = {'op2': 10, 'op1': 0, 'r': r, 's': s, 't': t, 'op0': 0}
    syntax = Syntax(['addx4', ' ', r, ',', ' ', s, ',', ' ', t])


class Addx8(XtensaInstruction):
    """ Addx8 """
    tokens = [RrrToken]
    r = Operand('r', AddressRegister, write=True)
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, read=True)
    patterns = {'op2': 0b1011, 'op1': 0, 'r': r, 's': s, 't': t, 'op0': 0}
    syntax = Syntax(['addx8', ' ', r, ',', ' ', s, ',', ' ', t])

# TODO: All4


class And(XtensaInstruction):
    """ And """
    tokens = [RrrToken]
    r = Operand('r', AddressRegister, write=True)
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, read=True)
    patterns = {'op2': 1, 'op1': 0, 'r': r, 's': s, 't': t, 'op0': 0}
    syntax = Syntax(['and', ' ', r, ',', ' ', s, ',', ' ', t])


class Andb(XtensaInstruction):
    """ Boolean and """
    tokens = [RrrToken]
    r = Operand('r', AddressRegister, write=True)
    s = Operand('s', AddressRegister, read=True)
    t = Operand('t', AddressRegister, read=True)
    patterns = {'op2': 0, 'op1': 2, 'r': r, 's': s, 't': t, 'op0': 0}
    syntax = Syntax(['andb', ' ', r, ',', ' ', s, ',', ' ', t])


class Andbc(XtensaInstruction):
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




@core_isa.pattern('reg', 'ADDI32(reg,reg)')
def pattern_add(context):
    context.new_register(AddressRegister)
