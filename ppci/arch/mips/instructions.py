""" Mips instruction definitions.

See also: https://en.wikipedia.org/wiki/MIPS_architecture
"""

from ..encoding import Instruction, Operand, Syntax
from ..generic_instructions import ArtificialInstruction
from ..isa import Relocation, Isa
from ..token import Token, bit_range
from .registers import MipsRegister
from . import registers

isa = Isa()


class MipsToken(Token):
    class Info:
        size = 32

    opcode = bit_range(26, 32)


class MipsRToken(MipsToken):
    rs = bit_range(21, 26)
    rt = bit_range(16, 21)
    rd = bit_range(11, 16)
    shamt = bit_range(6, 11)
    funct = bit_range(0, 6)


class MipsIToken(MipsToken):
    rs = bit_range(21, 26)
    rt = bit_range(16, 21)
    imm = bit_range(0, 16)


class MipsJToken(MipsToken):
    address = bit_range(0, 26)


class MipsInstruction(Instruction):
    isa = isa


def make_r(mnemonic, opcode, funct, shamt=0):
    rs = Operand('rs', MipsRegister, read=True)
    rt = Operand('rt', MipsRegister, read=True)
    rd = Operand('rd', MipsRegister, write=True)
    syntax = Syntax([mnemonic, ' ', rd, ',', ' ', rs, ',', ' ', rt])
    patterns = {
        'opcode': opcode,
        'rs': rs, 'rt': rt, 'rd': rd,
        'shamt': shamt, 'funct': funct,
    }
    members = {
        'tokens': [MipsRToken],
        'rs': rs, 'rt': rt, 'rd': rd,
        'syntax': syntax,
        'patterns': patterns,
    }
    return type(mnemonic.title(), (MipsInstruction,), members)


def make_i(mnemonic, opcode):
    """ Factory function to create an I-format instruction """
    rs = Operand('rs', MipsRegister, read=True)
    rt = Operand('rt', MipsRegister, write=True)
    imm = Operand('imm', int)
    syntax = Syntax([mnemonic, ' ', rt, ',', ' ', rs, ',', ' ', imm])
    patterns = {'opcode': opcode, 'rs': rs, 'rt': rt, 'imm': imm}
    members = {
        'tokens': [MipsIToken],
        'rs': rs, 'rt': rt, 'imm': imm,
        'syntax': syntax, 'patterns': patterns,
    }
    return type(mnemonic.title(), (MipsInstruction,), members)


def make_mem(mnemonic, opcode, is_load=False):
    """ Factory function to create an load or store instruction """
    rs = Operand('rs', MipsRegister, read=True)
    rt = Operand('rt', MipsRegister, read=not is_load, write=is_load)
    imm = Operand('imm', int)
    syntax = Syntax([mnemonic, ' ', rt, ',', ' ', imm, '(', rs, ')'])
    patterns = {'opcode': opcode, 'rs': rs, 'rt': rt, 'imm': imm}
    members = {
        'tokens': [MipsIToken],
        'rs': rs, 'rt': rt, 'imm': imm,
        'syntax': syntax, 'patterns': patterns,
    }
    return type(mnemonic.title(), (MipsInstruction,), members)


@isa.register_relocation
class Abs26Relocation(Relocation):
    """ Apply 26 bit relocation """
    name = 'abs26'
    token = MipsJToken
    field = 'address'

    def calc(self, sym_value, reloc_value):
        assert sym_value % 4 == 0
        return sym_value >> 2


# Memory instructions:
Lb = make_mem('lb', 32, is_load=True)
Lh = make_mem('lh', 33, is_load=True)
Lwl = make_mem('lwl', 34, is_load=True)
Lw = make_mem('lw', 35, is_load=True)
Lbu = make_mem('lbu', 36, is_load=True)
Lhu = make_mem('lhu', 37, is_load=True)
Lwr = make_mem('lwr', 38, is_load=True)
Sb = make_mem('sb', 40, is_load=False)
Sh = make_mem('sh', 41, is_load=False)
Swl = make_mem('swl', 42, is_load=False)
Sw = make_mem('sw', 43, is_load=False)
Swr = make_mem('swr', 44, is_load=False)

# Arithmatic instructions:
Add = make_r('add', 0, 32)
Addu = make_r('addu', 0, 33)
Sub = make_r('sub', 0, 34)
Subu = make_r('subu', 0, 35)
And = make_r('and', 0, 36)
Or = make_r('or', 0, 37)
Xor = make_r('xor', 0, 38)
Nor = make_r('nor', 0, 39)
Slt = make_r('slt', 0, 42)
Sltu = make_r('sltu', 0, 43)

Addi = make_i('addi', 8)
Addiu = make_i('addiu', 9)
Slti = make_i('slti', 10)
Sltiu = make_i('sltiu', 11)
Andi = make_i('andi', 12)
Ori = make_i('ori', 13)
Xori = make_i('xori', 14)
Lui = make_i('lui', 15)

Sllv = make_r('sllv', 0, 4)
Srlv = make_r('srlv', 0, 6)
Srav = make_r('srav', 0, 7)


class Jr(MipsInstruction):
    """ Jump register """
    tokens = [MipsRToken]
    rs = Operand('rs', MipsRegister, read=True)
    syntax = Syntax(['jr', ' ', rs])
    patters = {
        'opcode': 0, 'rs': rs, 'rt': 0, 'rd': 0, 'shamt': 0, 'funct': 8
    }


class Jalr(MipsInstruction):
    """ Jump and link register """
    tokens = [MipsRToken]
    rs = Operand('rs', MipsRegister, read=True)
    syntax = Syntax(['jalr', ' ', rs])
    patters = {
        'opcode': 0, 'rs': rs, 'rt': 0, 'rd': 0, 'shamt': 0, 'funct': 9
    }


class J(MipsInstruction):
    """ Jump """
    tokens = [MipsJToken]
    label = Operand('label', str)
    syntax = Syntax(['j', ' ', label])
    patterns = {'opcode': 2}

    def gen_relocations(self):
        yield Abs26Relocation(self.label)


class Jal(MipsInstruction):
    """ Jump and link """
    tokens = [MipsJToken]
    label = Operand('label', str)
    syntax = Syntax(['jal', ' ', label])
    patterns = {'opcode': 3}

    def gen_relocations(self):
        yield Abs26Relocation(self.label)


# Pseudo instructions:

class PseudoMipsInstruction(ArtificialInstruction):
    """ Base class for all pseudo instructions """
    isa = isa


class Nop(PseudoMipsInstruction):
    """ No-operation """
    syntax = Syntax(['nop'])

    def render(self):
        yield Add(registers.r0, registers.r0, registers.r0)


def mov(dst, src):
    """ Move src into dst register """
    return Addi(dst, src, 0, ismove=True)


# Pattern matching:


# Arithmatic patterns:
@isa.pattern('reg', 'ADDI32(reg, reg)', size=4, cycles=1, energy=1)
def pattern_addi32(context, tree, c0, c1):
    d = context.new_reg(MipsRegister)
    context.emit(Add(d, c1, c0))
    return d


@isa.pattern('reg', 'ADDU32(reg, reg)', size=4, cycles=1, energy=1)
def pattern_addu32(context, tree, c0, c1):
    d = context.new_reg(MipsRegister)
    context.emit(Addu(d, c1, c0))
    return d


@isa.pattern('reg', 'SUBI32(reg, reg)', size=4, cycles=1, energy=1)
def pattern_subi32(context, tree, c0, c1):
    d = context.new_reg(MipsRegister)
    context.emit(Sub(d, c1, c0))
    return d


@isa.pattern('reg', 'SUBU32(reg, reg)', size=4, cycles=1, energy=1)
def pattern_subu32(context, tree, c0, c1):
    d = context.new_reg(MipsRegister)
    context.emit(Subu(d, c1, c0))
    return d


@isa.pattern('reg', 'NEGI32(reg)', size=4, cycles=1, energy=1)
def pattern_neg_i32(context, tree, c0):
    d = context.new_reg(MipsRegister)
    context.emit(Subu(d, registers.r0, c0))
    return d


@isa.pattern('reg', 'ANDI8(reg, reg)', size=4, cycles=1, energy=1)
@isa.pattern('reg', 'ANDU8(reg, reg)', size=4, cycles=1, energy=1)
@isa.pattern('reg', 'ANDI16(reg, reg)', size=4, cycles=1, energy=1)
@isa.pattern('reg', 'ANDU16(reg, reg)', size=4, cycles=1, energy=1)
@isa.pattern('reg', 'ANDI32(reg, reg)', size=4, cycles=1, energy=1)
@isa.pattern('reg', 'ANDU32(reg, reg)', size=4, cycles=1, energy=1)
def pattern_and32(context, tree, c0, c1):
    d = context.new_reg(MipsRegister)
    context.emit(And(d, c1, c0))
    return d


@isa.pattern('reg', 'ORI8(reg, reg)', size=4, cycles=1, energy=1)
@isa.pattern('reg', 'ORU8(reg, reg)', size=4, cycles=1, energy=1)
@isa.pattern('reg', 'ORI16(reg, reg)', size=4, cycles=1, energy=1)
@isa.pattern('reg', 'ORU16(reg, reg)', size=4, cycles=1, energy=1)
@isa.pattern('reg', 'ORI32(reg, reg)', size=4, cycles=1, energy=1)
@isa.pattern('reg', 'ORU32(reg, reg)', size=4, cycles=1, energy=1)
def pattern_or32(context, tree, c0, c1):
    d = context.new_reg(MipsRegister)
    context.emit(Or(d, c1, c0))
    return d


@isa.pattern('reg', 'XORI32(reg, reg)', size=4, cycles=1, energy=1)
@isa.pattern('reg', 'XORU32(reg, reg)', size=4, cycles=1, energy=1)
def pattern_xor32(context, tree, c0, c1):
    d = context.new_reg(MipsRegister)
    context.emit(Xor(d, c1, c0))
    return d


@isa.pattern('reg', 'SHLI32(reg, reg)', size=4, cycles=1, energy=1)
@isa.pattern('reg', 'SHLU32(reg, reg)', size=4, cycles=1, energy=1)
def pattern_shl(context, tree, c0, c1):
    d = context.new_reg(MipsRegister)
    context.emit(Sllv(d, c1, c0))
    return d


@isa.pattern('reg', 'SHRI32(reg, reg)', size=4, cycles=1, energy=1)
@isa.pattern('reg', 'SHRU32(reg, reg)', size=4, cycles=1, energy=1)
def pattern_shr(context, tree, c0, c1):
    d = context.new_reg(MipsRegister)
    context.emit(Srlv(d, c1, c0))
    return d


def call_internal(context, name, a, b):
    d = context.new_reg(MipsRegister)
    context.move(registers.a0, a)
    context.move(registers.a1, b)
    context.emit(Jal(name, clobbers=()))
    context.emit(Nop())
    context.move(d, registers.v0)
    return d


@isa.pattern('reg', 'MULI32(reg, reg)', size=4, cycles=1, energy=1)
def pattern_mul_i32(context, tree, c0, c1):
    return call_internal(context, 'runtime_mulsi3', c0, c1)


@isa.pattern('reg', 'MULU32(reg, reg)', size=4, cycles=1, energy=1)
def pattern_mul_u32(context, tree, c0, c1):
    return call_internal(context, 'runtime_umulsi3', c0, c1)


@isa.pattern('reg', 'DIVI32(reg, reg)', size=4, cycles=1, energy=1)
def pattern_div_i32(context, tree, c0, c1):
    return call_internal(context, 'runtime_divsi3', c0, c1)


@isa.pattern('reg', 'DIVU32(reg, reg)', size=4, cycles=1, energy=1)
def pattern_div_u32(context, tree, c0, c1):
    return call_internal(context, 'runtime_udivsi3', c0, c1)


# Memory patterns:
@isa.pattern('mem', 'reg', size=0, cycles=0, energy=0)
def pattern_reg_as_mem(context, tree, c0):
    return c0, 0


@isa.pattern('mem', 'FPRELU32', size=0, cycles=0, energy=0)
def pattern_fprel32(context, tree):
    offset = tree.value.offset
    base = registers.fp
    return base, offset


@isa.pattern('stm', 'STRI32(mem, reg)', size=4, cycles=2, energy=2)
@isa.pattern('stm', 'STRU32(mem, reg)', size=4, cycles=2, energy=2)
def pattern_str_32(context, tree, c0, c1):
    base, offset = c0
    context.emit(Sw(c1, offset, base))
    context.emit(Nop())


@isa.pattern('reg', 'LDRI32(mem)', size=4, cycles=2, energy=2)
@isa.pattern('reg', 'LDRU32(mem)', size=4, cycles=2, energy=2)
def pattern_ldr_32(context, tree, c0):
    d = context.new_reg(MipsRegister)
    base, offset = c0
    context.emit(Lw(d, offset, base))
    context.emit(Nop())
    return d


@isa.pattern('stm', 'STRI16(mem, reg)', size=4, cycles=2, energy=2)
@isa.pattern('stm', 'STRU16(mem, reg)', size=4, cycles=2, energy=2)
def pattern_str_16(context, tree, c0, c1):
    base, offset = c0
    context.emit(Sw(c1, offset, base))
    context.emit(Nop())


@isa.pattern('reg', 'LDRI16(mem)', size=4, cycles=2, energy=2)
def pattern_ldr_i16(context, tree, c0):
    d = context.new_reg(MipsRegister)
    base, offset = c0
    context.emit(Lh(d, offset, base))
    context.emit(Nop())
    return d


@isa.pattern('reg', 'LDRU16(mem)', size=4, cycles=2, energy=2)
def pattern_ldr_u16(context, tree, c0):
    d = context.new_reg(MipsRegister)
    base, offset = c0
    context.emit(Lhu(d, offset, base))
    context.emit(Nop())
    return d


@isa.pattern('stm', 'STRI8(mem, reg)', size=4, cycles=2, energy=2)
@isa.pattern('stm', 'STRU8(mem, reg)', size=4, cycles=2, energy=2)
def pattern_str_8(context, tree, c0, c1):
    base, offset = c0
    context.emit(Sb(c1, offset, base))
    context.emit(Nop())


@isa.pattern('reg', 'LDRI8(mem)', size=4, cycles=2, energy=2)
def pattern_ldr_i8(context, tree, c0):
    d = context.new_reg(MipsRegister)
    base, offset = c0
    context.emit(Lb(d, offset, base))
    context.emit(Nop())  # Load delay slot
    return d


@isa.pattern('reg', 'LDRU8(mem)', size=4, cycles=2, energy=2)
def pattern_ldr_u8(context, tree, c0):
    d = context.new_reg(MipsRegister)
    base, offset = c0
    context.emit(Lbu(d, offset, base))
    context.emit(Nop())
    return d


# Misc patterns:
@isa.pattern('stm', 'MOVI32(reg)', size=4, cycles=1, energy=1)
@isa.pattern('stm', 'MOVU32(reg)', size=4, cycles=1, energy=1)
@isa.pattern('stm', 'MOVI16(reg)', size=4, cycles=1, energy=1)
@isa.pattern('stm', 'MOVU16(reg)', size=4, cycles=1, energy=1)
@isa.pattern('stm', 'MOVI8(reg)', size=4, cycles=1, energy=1)
@isa.pattern('stm', 'MOVU8(reg)', size=4, cycles=1, energy=1)
def pattern_mov32(context, tree, c0):
    d = tree.value
    context.emit(mov(d, c0))


@isa.pattern('reg', 'CONSTI32', size=8, cycles=2, energy=2)
@isa.pattern('reg', 'CONSTU32', size=8, cycles=2, energy=2)
def pattern_const32(context, tree):
    value = tree.value
    upper = (value >> 16) & 0xffff
    lower = value & 0xffff
    d = context.new_reg(MipsRegister)
    context.emit(Lui(d, registers.r0, upper))
    context.emit(Ori(d, d, lower))
    return d


@isa.pattern('reg', 'CONSTI16', size=4, cycles=1, energy=1)
@isa.pattern('reg', 'CONSTU16', size=4, cycles=1, energy=1)
@isa.pattern('reg', 'CONSTI8', size=4, cycles=1, energy=1)
@isa.pattern('reg', 'CONSTU8', size=4, cycles=1, energy=1)
def pattern_const16(context, tree):
    value = tree.value & 0xffff
    d = context.new_reg(MipsRegister)
    context.emit(Addi(d, registers.r0, value))
    return d


@isa.pattern('reg', 'REGI32', size=0, cycles=0, energy=0)
@isa.pattern('reg', 'REGU32', size=0, cycles=0, energy=0)
@isa.pattern('reg', 'REGI16', size=0, cycles=0, energy=0)
@isa.pattern('reg', 'REGU16', size=0, cycles=0, energy=0)
@isa.pattern('reg', 'REGI8', size=0, cycles=0, energy=0)
@isa.pattern('reg', 'REGU8', size=0, cycles=0, energy=0)
def pattern_reg(context, tree):
    return tree.value


@isa.pattern('reg', 'I32TOI32(reg)', size=0, cycles=0, energy=0)
@isa.pattern('reg', 'I32TOU32(reg)', size=0, cycles=0, energy=0)
@isa.pattern('reg', 'U32TOI32(reg)', size=0, cycles=0, energy=0)
@isa.pattern('reg', 'U32TOU32(reg)', size=0, cycles=0, energy=0)
@isa.pattern('reg', 'I32TOI8(reg)', size=0, cycles=0, energy=0)
@isa.pattern('reg', 'I32TOU8(reg)', size=0, cycles=0, energy=0)
@isa.pattern('reg', 'U32TOI8(reg)', size=0, cycles=0, energy=0)
@isa.pattern('reg', 'U32TOU8(reg)', size=0, cycles=0, energy=0)
@isa.pattern('reg', 'I8TOI32(reg)', size=0, cycles=0, energy=0)
@isa.pattern('reg', 'I8TOU32(reg)', size=0, cycles=0, energy=0)
@isa.pattern('reg', 'U8TOI32(reg)', size=0, cycles=0, energy=0)
@isa.pattern('reg', 'U8TOU32(reg)', size=0, cycles=0, energy=0)
def pattern_cast(context, tree, c0):
    return c0


@isa.pattern('reg', 'LABEL', size=8, cycles=2, energy=2)
def pattern_label(context, tree):
    label = tree.value
    d = context.new_reg(MipsRegister)
    # TODO!
    return d


# Jumping around:
@isa.pattern('stm', 'JMP')
def pattern_jmp(context, tree):
    tgt = tree.value
    context.emit(J(tgt.name, jumps=[tgt]))


@isa.pattern('stm', 'CJMPI32(reg, reg)')
@isa.pattern('stm', 'CJMPI8(reg, reg)')
@isa.pattern('stm', 'CJMPU8(reg, reg)')
def pattern_cjmp(context, tree, c0, c1):
    op, yes_label, no_label = tree.value
    # TODO
    return
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
