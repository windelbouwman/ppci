""" Microblaze instructions """

from ..encoding import Instruction, Syntax, Operand

from ..isa import Isa
from ..token import Token, bit_range
from .registers import MicroBlazeRegister


isa = Isa()


# The microblaze has two instruction formats named A and B:
class TypeAToken(Token):
    class Info:
        size = 32

    opcode = bit_range(0, 6)
    rd = bit_range(6, 11)
    ra = bit_range(11, 16)
    rb = bit_range(16, 21)
    opcode2 = bit_range(21, 32)


class TypeBToken(Token):
    class Info:
        size = 32

    opcode = bit_range(0, 6)
    rd = bit_range(6, 11)
    ra = bit_range(11, 16)
    imm = bit_range(16, 32)


class MicroBlazeInstruction(Instruction):
    isa = isa


def type_a(mnemonic: str, opcode1, opcode2, rd=None, ra=None, rb=None):
    """ Create a type a instruction """
    operands = []
    if rd is None:
        rd = Operand('rd', MicroBlazeRegister, write=True)
        operands.append(rd)
    if ra is None:
        ra = Operand('ra', MicroBlazeRegister, read=True)
        operands.append(ra)
    if rb is None:
        rb = Operand('rb', MicroBlazeRegister, read=True)
        operands.append(rb)

    syntax = [mnemonic]
    if operands:
        for operand in operands[:-1]:
            syntax.extend([' ', operand, ','])
        syntax.extend([' ', operands[-1]])
    syntax = Syntax(syntax)

    patterns = {
        'opcode': opcode1, 'opcode2': opcode2,
        'rd': rd, 'ra': ra, 'rb': rb,
    }
    members = {
        'tokens': [TypeAToken],
        'rd': rd, 'ra': ra,
        'rb': rb,
        'syntax': syntax, 'patterns': patterns,
    }

    name = mnemonic.title()
    return type(name, (MicroBlazeInstruction,), members)


def type_b(mnemonic, opcode, rd=None, ra=None, imm=None):
    """ Create an instruction class for a type B instruction """
    rd = Operand('rd', MicroBlazeRegister, write=True)
    ra = Operand('ra', MicroBlazeRegister, read=True)
    syntax = [mnemonic, ' ', rd, ',', ' ', ra]
    if imm is None:
        imm = Operand('imm', int)
        syntax.extend([',', ' ', imm])
    syntax = Syntax(syntax)

    patterns = {'opcode': opcode, 'rd': rd, 'ra': ra, 'imm': imm}
    members = {
        'tokens': [TypeBToken],
        'rd': rd, 'ra': ra,
        'imm': imm,
        'syntax': syntax, 'patterns': patterns,
    }

    name = mnemonic.title()
    return type(name, (MicroBlazeInstruction,), members)


# See table 1-6 in the microblaze reference manual:

Add = type_a('add', 0, 0)
Rsub = type_a('rsub', 1, 0)
Addc = type_a('addc', 2, 0)
Rsubc = type_a('rsubc', 3, 0)
Addk = type_a('addk', 4, 0)
Rsubk = type_a('rsubk', 5, 0)
Addkc = type_a('addkc', 6, 0)
Rsubkc = type_a('rsubkc', 7, 0)

Cmp = type_a('cmp', 5, 1)
Cmp = type_a('cmp', 5, 3)

Addi = type_b('addi', 8)
Rsubi = type_b('rsubi', 9)
Addic = type_b('addic', 10)
Rsubic = type_b('rsubic', 11)
Addik = type_b('addik', 12)
Rsubik = type_b('rsubik', 13)
Addikc = type_b('addikc', 14)
Rsubikc = type_b('rsubikc', 15)

Mul = type_a('mul', 0x10, 0)
Mulh = type_a('mulh', 0x10, 1)
Mulhu = type_a('mulhu', 0x10, 3)
Mulhsu = type_a('mulhsu', 0x10, 2)

Bsra = type_a('bsra', 0x11, 0x200)
Bsll = type_a('bsll', 0x11, 0x400)

Muli = type_b('muli', 0x18)

Bsrli = 0
Bsrai = 0
Bslli = 0

Idiv = type_a('idiv', 0x12, 0)
Idivu = type_a('idiv', 0x12, 2)


# Floating point instructions:
def type_float(mnemonic, opcode, rb=None):
    return type_a(mnemonic, 0x16, opcode, rb=rb)


Fadd = type_float('fadd', 0)
Frsub = type_float('frsub', 0x80)
Fmul = type_float('fmul', 0x100)
Fdiv = type_float('fdiv', 0x180)
# TODO:
# Fcmp_un = type_float('fcmp.un', 0x200)
# Fcmp_lt = type_float('fcmp.lt', 0x210)
# Fcmp_eq = type_float('fcmp.eq', 0x220)
# Fcmp_le = type_float('fcmp.le', 0x230)
# Fcmp_gt = type_float('fcmp.gt', 0x240)
# Fcmp_ne = type_float('fcmp.ne', 0x250)
# Fcmp_ge = type_float('fcmp.ge', 0x260)
Flt = type_float('flt', 0x280, rb=0)
Fint = type_float('fint', 0x300, rb=0)
Fsqrt = type_float('fsqrt', 0x380, rb=0)

Or = type_a('or', 0x20, 0)
And = type_a('and', 0x21, 0)
Xor = type_a('xor', 0x22, 0)
Andn = type_a('andn', 0x23, 0)
Pcmpbf = type_a('pcmpbf', 0x20, 0x400)
Pcmpeq = type_a('pcmpeq', 0x22, 0x400)
Pcmpne = type_a('pcmpeq', 0x23, 0x400)

Sra = type_b('sra', 0x24, imm=0x1)
Src = type_b('sra', 0x24, imm=0x21)
Srl = type_b('sra', 0x24, imm=0x41)
Sext8 = type_b('sext8', 0x24, imm=0x60)
Sext16 = type_b('sext16', 0x24, imm=0x61)
Wic = type_a('wic', 0x24, 0x68, rd=0)
Wdc = type_a('wic', 0x24, 0x64, rd=0)

Br = type_a('br', 0x26, 0, rd=0, ra=0x0)
Brd = type_a('brd', 0x26, 0, rd=0, ra=0x10)
Brld = type_a('brld', 0x26, 0, ra=0x14)
Bra = type_a('bra', 0x26, 0, rd=0, ra=0x8)
Brad = type_a('brad', 0x26, 0, rd=0, ra=0x18)
Brald = type_a('brald', 0x26, 0, ra=0x1c)
Brk = type_a('brk', 0x26, 0, ra=0xc)

Beq = type_a('beq', 0x27, 0, rd=0x0)
Bne = type_a('bne', 0x27, 0, rd=0x1)
Blt = type_a('blt', 0x27, 0, rd=0x2)
Ble = type_a('ble', 0x27, 0, rd=0x3)
Bgt = type_a('bgt', 0x27, 0, rd=0x4)
Bge = type_a('bge', 0x27, 0, rd=0x5)

Beqd = type_a('beqd', 0x27, 0, rd=0x10)
Bned = type_a('bned', 0x27, 0, rd=0x11)
Bltd = type_a('bltd', 0x27, 0, rd=0x12)
Bled = type_a('bled', 0x27, 0, rd=0x13)
Bgtd = type_a('bgtd', 0x27, 0, rd=0x14)
Bged = type_a('bged', 0x27, 0, rd=0x15)

Ori = type_b('ori', 0x28)
Andi = type_b('andi', 0x29)
Xori = type_b('xori', 0x2a)
Andni = type_b('xori', 0x2b)
Imm = type_b('xori', 0x2c, rd=0, ra=0)

Rtsd = type_b('rtsd', 0x2d, rd=0x10)
Rtid = type_b('rtsd', 0x2d, rd=0x11)
Rtbd = type_b('rtbd', 0x2d, rd=0x12)
Rted = type_b('rted', 0x2d, rd=0x14)

Bri = type_b('bri', 0x2e, rd=0, ra=0)
Brid = type_b('brid', 0x2e, rd=0, ra=0x10)
Brlid = type_b('brlid', 0x2e, ra=0x14)
Brai = type_b('brai', 0x2e, rd=0, ra=0x8)
Braid = type_b('braid', 0x2e, rd=0, ra=0x18)
Bralid = type_b('bralid', 0x2e, ra=0x1c)
Brki = type_b('brki', 0x2e, ra=0xc)

Beqi = type_b('beqi', 0x2f, rd=0x0)
Bnei = type_b('bnei', 0x2f, rd=0x1)
Blti = type_b('blti', 0x2f, rd=0x2)
Blei = type_b('blei', 0x2f, rd=0x3)
Bgti = type_b('bgti', 0x2f, rd=0x4)
Bgei = type_b('bgei', 0x2f, rd=0x5)
Beqid = type_b('beqid', 0x2f, rd=0x10)
Bneid = type_b('bneid', 0x2f, rd=0x11)
Bltid = type_b('bltid', 0x2f, rd=0x12)
Bleid = type_b('bleid', 0x2f, rd=0x13)
Bgtid = type_b('bgtid', 0x2f, rd=0x14)
Bgeid = type_b('bgeid', 0x2f, rd=0x15)

# Memory:
Lbu = type_a('lbu', 0x30, 0)
Lhu = type_a('lhu', 0x31, 0)
Lw = type_a('lw', 0x32, 0)
Sb = type_a('sb', 0x34, 0)
Sh = type_a('sh', 0x35, 0)
Sw = type_a('sw', 0x36, 0)


# Instruction selection:

@isa.pattern('reg', 'ADDI8(reg, reg)', size=4)
@isa.pattern('reg', 'ADDU8(reg, reg)', size=4)
@isa.pattern('reg', 'ADDI16(reg, reg)', size=4)
@isa.pattern('reg', 'ADDU16(reg, reg)', size=4)
@isa.pattern('reg', 'ADDI32(reg, reg)', size=4)
@isa.pattern('reg', 'ADDU32(reg, reg)', size=4)
def pattern_add(context, tree, c0, c1):
    d = context.new_reg(MicroBlazeRegister)
    context.emit(Add(d, c0, c1))
    return d


@isa.pattern('reg', 'SUBI8(reg, reg)', size=4)
@isa.pattern('reg', 'SUBU8(reg, reg)', size=4)
@isa.pattern('reg', 'SUBI16(reg, reg)', size=4)
@isa.pattern('reg', 'SUBU16(reg, reg)', size=4)
@isa.pattern('reg', 'SUBI32(reg, reg)', size=4)
@isa.pattern('reg', 'SUBU32(reg, reg)', size=4)
def pattern_sub(context, tree, c0, c1):
    d = context.new_reg(MicroBlazeRegister)
    context.emit(Rsub(d, c1, c0))
    return d


# Bitwise instruction matching:
@isa.pattern('reg', 'ANDI8(reg, reg)', size=4)
@isa.pattern('reg', 'ANDU8(reg, reg)', size=4)
@isa.pattern('reg', 'ANDI16(reg, reg)', size=4)
@isa.pattern('reg', 'ANDU16(reg, reg)', size=4)
@isa.pattern('reg', 'ANDI32(reg, reg)', size=4)
@isa.pattern('reg', 'ANDU32(reg, reg)', size=4)
def pattern_and(context, tree, c0, c1):
    d = context.new_reg(MicroBlazeRegister)
    context.emit(And(d, c0, c1))
    return d


@isa.pattern('reg', 'ORI8(reg, reg)', size=4)
@isa.pattern('reg', 'ORU8(reg, reg)', size=4)
@isa.pattern('reg', 'ORI16(reg, reg)', size=4)
@isa.pattern('reg', 'ORU16(reg, reg)', size=4)
@isa.pattern('reg', 'ORI32(reg, reg)', size=4)
@isa.pattern('reg', 'ORU32(reg, reg)', size=4)
def pattern_or(context, tree, c0, c1):
    d = context.new_reg(MicroBlazeRegister)
    context.emit(Or(d, c0, c1))
    return d


@isa.pattern('reg', 'XORI8(reg, reg)', size=4)
@isa.pattern('reg', 'XORU8(reg, reg)', size=4)
@isa.pattern('reg', 'XORI16(reg, reg)', size=4)
@isa.pattern('reg', 'XORU16(reg, reg)', size=4)
@isa.pattern('reg', 'XORI32(reg, reg)', size=4)
@isa.pattern('reg', 'XORU32(reg, reg)', size=4)
def pattern_xor(context, tree, c0, c1):
    d = context.new_reg(MicroBlazeRegister)
    context.emit(Xor(d, c0, c1))
    return d
