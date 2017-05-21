
from .isa import orbis32, Orbis32Token, Orbis32StoreToken
from .registers import Or1kRegister
from ..encoding import Instruction, Syntax, Operand
from ..encoding import Relocation
from ...utils.bitfun import wrap_negative
from . import registers


# basic 32 bit integers
class Orbis32Instruction(Instruction):
    isa = orbis32
    tokens = [Orbis32Token]


@orbis32.register_relocation
class JumpRelocation(Relocation):
    name = 'jump'
    token = Orbis32Token
    field = 'n'

    def calc(self, sym_value, reloc_value):
        assert sym_value % 4 == 0
        assert reloc_value % 4 == 0
        offset = sym_value - reloc_value
        # assert offset in range(-256, 254, 4), str(offset)
        return wrap_negative(offset // 4, 26)


# Utility functions:
def regregreg(mnemonic, opcode, opcode2):
    rd = Operand('rd', Or1kRegister, write=True)
    ra = Operand('ra', Or1kRegister, read=True)
    rb = Operand('rb', Or1kRegister, read=True)
    syntax = Syntax(['l', '.', mnemonic, ' ', rd, ',', ' ', ra, ',', ' ', rb])
    patterns = {
        'opcode': opcode, 'rd': rd, 'ra': ra, 'rb': rb, 'opcode2': opcode2}
    members = {
        'rd': rd, 'ra': ra, 'rb': rb, 'syntax': syntax, 'patterns': patterns}
    class_name = mnemonic.title()
    return type(class_name, (Orbis32Instruction,), members)


def regreg(mnemonic, opcode, opcode2):
    rd = Operand('rd', Or1kRegister, write=True)
    ra = Operand('ra', Or1kRegister, read=True)
    syntax = Syntax(['l', '.', mnemonic, ' ', rd, ',', ' ', ra])
    patterns = {
        'opcode': opcode, 'rd': rd, 'ra': ra, 'rb': 0, 'opcode2': opcode2}
    members = {'rd': rd, 'ra': ra, 'syntax': syntax, 'patterns': patterns}
    class_name = mnemonic.title()
    return type(class_name, (Orbis32Instruction,), members)


def regregimm(mnemonic, opcode):
    rd = Operand('rd', Or1kRegister, write=True)
    ra = Operand('ra', Or1kRegister, read=True)
    imm = Operand('imm', int)
    syntax = Syntax(['l', '.', mnemonic, ' ', rd, ',', ' ', ra, ',', ' ', imm])
    patterns = {
        'opcode': opcode, 'rd': rd, 'ra': ra, 'imm': imm}
    members = {
        'rd': rd, 'ra': ra, 'imm': imm, 'syntax': syntax, 'patterns': patterns}
    class_name = mnemonic.title()
    return type(class_name, (Orbis32Instruction,), members)


def regb(mnemonic, opcode):
    rb = Operand('rb', Or1kRegister, read=True)
    syntax = Syntax(['l', '.', mnemonic, ' ', rb])
    patterns = {'opcode': opcode, 'rb': rb}
    members = {'rb': rb, 'syntax': syntax, 'patterns': patterns}
    class_name = mnemonic.title()
    return type(class_name, (Orbis32Instruction,), members)


class JumpInstruction(Orbis32Instruction):
    label = Operand('label', str)

    def relocations(self):
        yield JumpRelocation(self.label)


def jump(mnemonic, opcode):
    syntax = Syntax(['l', '.', mnemonic, ' ', JumpInstruction.label])
    patterns = {'opcode': opcode}
    members = {'syntax': syntax, 'patterns': patterns}
    class_name = mnemonic.title()
    return type(class_name, (JumpInstruction,), members)


def fixed(mnemonic, opcode):
    syntax = Syntax(['l', '.', mnemonic])
    patterns = {'allbits': opcode}
    members = {'syntax': syntax, 'patterns': patterns}
    class_name = mnemonic.title()
    return type(class_name, (Orbis32Instruction,), members)


def load(mnemonic, opcode):
    """ Create a load instruction """
    rd = Operand('rd', Or1kRegister, write=True)
    ra = Operand('ra', Or1kRegister, read=True)
    imm = Operand('imm', int)
    syntax = Syntax(['l', '.', mnemonic, ' ', rd, ',', ' ', imm, '(', ra, ')'])
    patterns = {
        'opcode': opcode, 'rd': rd, 'ra': ra, 'imm': imm}
    members = {
        'rd': rd, 'ra': ra, 'imm': imm, 'syntax': syntax, 'patterns': patterns}
    class_name = mnemonic.title()
    return type(class_name, (Orbis32Instruction,), members)


def store(mnemonic, opcode):
    """ Create a store instruction """
    ra = Operand('ra', Or1kRegister, read=True)
    rb = Operand('rb', Or1kRegister, read=True)
    imm = Operand('imm', int)
    syntax = Syntax(['l', '.', mnemonic, ' ', imm, '(', ra, ')', ',', ' ', rb])
    patterns = {
        'opcode': opcode, 'ra': ra, 'rb': rb, 'imm': imm}
    members = {
        'ra': ra, 'rb': rb, 'imm': imm, 'syntax': syntax,
        'patterns': patterns, 'tokens': [Orbis32StoreToken]}
    class_name = mnemonic.title()
    return type(class_name, (Orbis32Instruction,), members)


def setflag(mnemonic, opcode):
    """ Create an instruction setting the flag bit """
    ra = Operand('ra', Or1kRegister, read=True)
    rb = Operand('rb', Or1kRegister, read=True)
    syntax = Syntax(['l', '.', mnemonic, ' ', ra, ',', ' ', rb])
    patterns = {
        'opcode': 0b111001, 'rd': opcode, 'ra': ra, 'rb': rb}
    members = {'ra': ra, 'rb': rb, 'syntax': syntax, 'patterns': patterns}
    class_name = mnemonic.title()
    return type(class_name, (Orbis32Instruction,), members)


# Instructions:
Add = regregreg('add', 0b111000, 0b0000000)
Addc = regregreg('addc', 0b111000, 0b0000001)
Addi = regregimm('addi', 0b100111)
Addic = regregimm('addic', 0b101000)
And = regregreg('and', 0b111000, 0b0000011)
Andi = regregimm('andi', 0b101001)
Bf = jump('bf', 0b000100)
Bnf = jump('bnf', 0b000011)
Cmov = regregreg('cmov', 0b111000, 0b0001110)
Csync = fixed('csync', 0x23000000)
Div = regregreg('div', 0b111000, 0b1100001001)
Divu = regregreg('divu', 0b111000, 0b1100001010)
Extbs = regreg('extbs', 0b111000, 0b0001001100)
Extbz = regreg('extbz', 0b111000, 0b0011001100)
Exths = regreg('exths', 0b111000, 0b0000001100)
Exthz = regreg('exthz', 0b111000, 0b0010001100)
J = jump('j', 0b000000)
Jal = jump('jal', 0b000001)
Jalr = regb('jalr', 0b010010)
Jr = regb('jr', 0b010001)
Lbs = load('lbs', 0b100100)
Lbz = load('lbz', 0b100011)
Lhs = load('lhs', 0b100110)
Lhz = load('lhz', 0b100101)
Lwa = load('lwa', 0b011011)
Lws = load('lws', 0b100010)
Lwz = load('lwz', 0b100001)


class Movhi(Orbis32Instruction):
    """ Mov immediate high """
    rd = Operand('rd', Or1kRegister, write=True)
    imm = Operand('imm', int)
    syntax = Syntax(['l', '.', 'movhi', ' ', rd, ',', ' ', imm])
    patterns = {'opcode': 0b000110, 'rd': rd, 'ra': 0, 'k': imm}


class Macrc(Orbis32Instruction):
    """ Mac read and clear """
    rd = Operand('rd', Or1kRegister, write=True)
    syntax = Syntax(['l', '.', 'macrc', ' ', rd])
    patterns = {'opcode': 0b000110, 'rd': rd, 'ra': 1, 'k': 0}


Mul = regregreg('mul', 0b111000, 0b01100000110)
Mulu = regregreg('mulu', 0b111000, 0b01100001011)
Or = regregreg('or', 0b111000, 0b0000100)
Ori = regregimm('ori', 0b101010)
Sb = store('sb', 0b110110)
Sfeq = setflag('sfeq', 0b00000)
Sfne = setflag('sfne', 0b00001)
Sfgeu = setflag('sfgeu', 0b00011)
Sfgtu = setflag('sfgtu', 0b00010)
Sfltu = setflag('sfltu', 0b00100)
Sfleu = setflag('sfleu', 0b00101)
Sfgts = setflag('sfgts', 0b01010)
Sfges = setflag('sfges', 0b01011)
Sflts = setflag('sflts', 0b01100)
Sfles = setflag('sfles', 0b01101)
Sh = store('sh', 0b110111)
Sll = regregreg('sll', 0b111000, 0b0001000)
Srl = regregreg('srl', 0b111000, 0b0011000)
Sra = regregreg('sra', 0b111000, 0b0101000)
Sub = regregreg('sub', 0b111000, 0b0000010)
Sw = store('sw', 0b110101)
Swa = store('swa', 0b110011)
Xor = regregreg('xor', 0b111000, 0b0000101)
Xori = regregimm('xori', 0b101011)


# Helpers:
def mov(dst, src):
    return Addi(dst, src, 0, ismove=True)


# Arithmatic patterns:
@orbis32.pattern('reg', 'ADDI8(reg, reg)', size=8, cycles=2, energy=2)
def pattern_addi8(context, tree, c0, c1):
    d = context.new_reg(Or1kRegister)
    context.emit(Add(d, c0, c1))
    # TODO: or use sign extend here?
    context.emit(Andi(d, d, 0xff))
    return d


@orbis32.pattern('reg', 'ADDI32(reg, reg)', size=4, cycles=1, energy=1)
def pattern_addi32(context, tree, c0, c1):
    d = context.new_reg(Or1kRegister)
    context.emit(Add(d, c0, c1))
    return d


@orbis32.pattern('reg', 'ANDI8(reg, reg)', size=4, cycles=1, energy=1)
@orbis32.pattern('reg', 'ANDI32(reg, reg)', size=4, cycles=1, energy=1)
def pattern_andi32(context, tree, c0, c1):
    d = context.new_reg(Or1kRegister)
    context.emit(And(d, c0, c1))
    return d


@orbis32.pattern('reg', 'SHRI32(reg, reg)', size=4, cycles=1, energy=1)
def pattern_shri32(context, tree, c0, c1):
    d = context.new_reg(Or1kRegister)
    context.emit(Srl(d, c0, c1))
    return d


@orbis32.pattern('reg', 'SHLI32(reg, reg)', size=4, cycles=1, energy=1)
def pattern_shli32(context, tree, c0, c1):
    d = context.new_reg(Or1kRegister)
    context.emit(Sll(d, c0, c1))
    return d


@orbis32.pattern('reg', 'DIVI32(reg, reg)', size=4, cycles=1, energy=1)
def pattern_divi32(context, tree, c0, c1):
    d = context.new_reg(Or1kRegister)
    context.emit(Div(d, c0, c1))
    return d


@orbis32.pattern('reg', 'DIVU32(reg, reg)', size=4, cycles=1, energy=1)
def pattern_divu32(context, tree, c0, c1):
    d = context.new_reg(Or1kRegister)
    context.emit(Divu(d, c0, c1))
    return d


@orbis32.pattern('reg', 'ORI8(reg, reg)', size=4, cycles=1, energy=1)
@orbis32.pattern('reg', 'ORI32(reg, reg)', size=4, cycles=1, energy=1)
def pattern_ori32(context, tree, c0, c1):
    d = context.new_reg(Or1kRegister)
    context.emit(Or(d, c0, c1))
    return d


@orbis32.pattern('reg', 'MULI32(reg, reg)', size=4, cycles=1, energy=1)
def pattern_muli32(context, tree, c0, c1):
    d = context.new_reg(Or1kRegister)
    context.emit(Mul(d, c0, c1))
    return d


@orbis32.pattern('reg', 'MULU32(reg, reg)', size=4, cycles=1, energy=1)
def pattern_mulu32(context, tree, c0, c1):
    d = context.new_reg(Or1kRegister)
    context.emit(Mulu(d, c0, c1))
    return d


@orbis32.pattern('reg', 'SUBI8(reg, reg)', size=4, cycles=1, energy=1)
def pattern_subi8(context, tree, c0, c1):
    d = context.new_reg(Or1kRegister)
    context.emit(Sub(d, c0, c1))
    # TODO: or use sign extend here?
    context.emit(Andi(d, d, 0xff))
    return d


@orbis32.pattern('reg', 'SUBI32(reg, reg)', size=4, cycles=1, energy=1)
def pattern_subi32(context, tree, c0, c1):
    d = context.new_reg(Or1kRegister)
    context.emit(Sub(d, c0, c1))
    return d


@orbis32.pattern('reg', 'XORI8(reg, reg)', size=4, cycles=1, energy=1)
@orbis32.pattern('reg', 'XORI32(reg, reg)', size=4, cycles=1, energy=1)
def pattern_xori32(context, tree, c0, c1):
    d = context.new_reg(Or1kRegister)
    context.emit(Xor(d, c0, c1))
    return d


# Memory patterns:
@orbis32.pattern('stm', 'STRI8(reg, reg)', size=4, cycles=1, energy=1)
@orbis32.pattern('stm', 'STRU8(reg, reg)', size=4, cycles=1, energy=1)
def pattern_str8(context, tree, c0, c1):
    context.emit(Sb(0, c0, c1))


@orbis32.pattern('stm', 'STRI8(FPRELI32, reg)', size=4, cycles=1, energy=1)
@orbis32.pattern('stm', 'STRU8(FPRELI32, reg)', size=4, cycles=1, energy=1)
def pattern_str8_fprel(context, tree, c0):
    offset = tree[0].value
    context.emit(Sb(offset, registers.r2, c0))


@orbis32.pattern('reg', 'LDRU8(reg)', size=4)
def pattern_ldru8(context, tree, c0):
    d = context.new_reg(Or1kRegister)
    context.emit(Lbz(d, 0, c0))
    return d


@orbis32.pattern('reg', 'LDRU8(FPRELI32)', size=4)
def pattern_ldru8_fprel(context, tree):
    offset = tree[0].value
    d = context.new_reg(Or1kRegister)
    context.emit(Lbz(d, offset, registers.r2))
    return d


@orbis32.pattern('reg', 'LDRI8(reg)', size=4)
def pattern_ldri8(context, tree, c0):
    d = context.new_reg(Or1kRegister)
    context.emit(Lbs(d, 0, c0))
    return d


@orbis32.pattern('reg', 'LDRI8(FPRELI32)', size=4)
def pattern_ldri8_fprel(context, tree):
    offset = tree[0].value
    d = context.new_reg(Or1kRegister)
    context.emit(Lbs(d, offset, registers.r2))
    return d


@orbis32.pattern('stm', 'STRI32(reg, reg)', size=4, cycles=1, energy=1)
@orbis32.pattern('stm', 'STRU32(reg, reg)', size=4, cycles=1, energy=1)
def pattern_str32(context, tree, c0, c1):
    context.emit(Sw(0, c0, c1))


@orbis32.pattern('stm', 'STRI32(FPRELI32, reg)', size=4, cycles=1, energy=1)
@orbis32.pattern('stm', 'STRU32(FPRELI32, reg)', size=4, cycles=1, energy=1)
def pattern_str32_fprel(context, tree, c0):
    offset = tree[0].value
    context.emit(Sw(offset, registers.r2, c0))


@orbis32.pattern('reg', 'LDRU32(reg)', size=4, cycles=1, energy=1)
def pattern_ldru32(context, tree, c0):
    d = context.new_reg(Or1kRegister)
    context.emit(Lwz(d, 0, c0))
    return d


@orbis32.pattern('reg', 'LDRI32(reg)', size=4, cycles=1, energy=1)
def pattern_ldri32(context, tree, c0):
    d = context.new_reg(Or1kRegister)
    context.emit(Lws(d, 0, c0))
    return d


@orbis32.pattern('reg', 'LDRI32(FPRELI32)', size=4, cycles=1, energy=1)
def pattern_ldri32_fprel(context, tree):
    d = context.new_reg(Or1kRegister)
    offset = tree[0].value
    context.emit(Lws(d, offset, registers.r2))
    return d


@orbis32.pattern('reg', 'FPRELI32', size=4, cycles=1, energy=1)
def pattern_fprel(context, tree):
    offset = tree.value
    d = context.new_reg(Or1kRegister)
    context.emit(Addi(d, registers.r2, offset))
    return d


# Control flow patterns:
@orbis32.pattern('reg', 'CALL')
def pattern_call(context, tree):
    return context.gen_call(tree.value)


@orbis32.pattern('stm', 'JMP', size=4)
def pattern_jmp(context, tree):
    tgt = tree.value
    context.emit(J(tgt.name, jumps=[tgt]))


@orbis32.pattern('stm', 'CJMP(reg, reg)', size=10)
def pattern_cjmp(context, tree, lhs, rhs):
    op, true_tgt, false_tgt = tree.value
    opnames = {
        "<": Sflts, ">": Sfgts, "==": Sfeq, "!=": Sfne,
        ">=": Sfges, '<=': Sfles}
    op_ins = opnames[op]
    context.emit(op_ins(lhs, rhs))
    jmp_ins = J(false_tgt.name, jumps=[false_tgt])
    context.emit(Bf(true_tgt.name, jumps=[true_tgt, jmp_ins]))
    context.emit(jmp_ins)


# Other patterns:
@orbis32.pattern('reg', 'LABEL', size=2)
def pattern_label(context, tree):
    d = context.new_reg(Or1kRegister)
    # ln = context.frame.add_constant(tree.value)
    # TODO!
    # context.emit(Mov(AdrSrc(ln), RegDst(d)))
    return d


@orbis32.pattern('reg', 'CONSTU32', size=8, cycles=2, energy=2)
@orbis32.pattern('reg', 'CONSTI32', size=8, cycles=2, energy=2)
def pattern_const32(context, tree):
    d = context.new_reg(Or1kRegister)
    cnst = tree.value
    context.emit(Movhi(d, cnst >> 16))
    context.emit(Ori(d, d, cnst & 0xffff))
    return d


@orbis32.pattern('reg', 'MOVI8(reg)', size=4, cycles=1, energy=1)
@orbis32.pattern('reg', 'MOVU8(reg)', size=4, cycles=1, energy=1)
@orbis32.pattern('reg', 'MOVI32(reg)', size=4, cycles=1, energy=1)
@orbis32.pattern('reg', 'MOVU32(reg)', size=4, cycles=1, energy=1)
def pattern_mov(context, tree, c0):
    dst = tree.value
    context.emit(Addi(dst, c0, 0))
    return dst


@orbis32.pattern('reg', 'REGI32', size=0, cycles=0, energy=0)
@orbis32.pattern('reg', 'REGU32', size=0, cycles=0, energy=0)
@orbis32.pattern('reg', 'REGI8', size=0, cycles=0, energy=0)
@orbis32.pattern('reg', 'REGU8', size=0, cycles=0, energy=0)
def pattern_reg(context, tree):
    return tree.value


# Data conversion patterns:
@orbis32.pattern('reg', 'U32TOI32(reg)', size=0, cycles=0, energy=0)
@orbis32.pattern('reg', 'I32TOI32(reg)', size=0, cycles=0, energy=0)
@orbis32.pattern('reg', 'U32TOU32(reg)', size=0, cycles=0, energy=0)
@orbis32.pattern('reg', 'I32TOU32(reg)', size=0, cycles=0, energy=0)
def pattern_i32toi32(context, tree, c0):
    return c0


@orbis32.pattern('reg', 'I8TOI32(reg)', size=4, cycles=1, energy=1)
def pattern_i8toi32(context, tree, c0):
    d = context.new_reg(Or1kRegister)
    context.emit(Extbs(d, c0))
    return d


@orbis32.pattern('reg', 'U8TOU32(reg)', size=4, cycles=1, energy=1)
@orbis32.pattern('reg', 'U8TOI32(reg)', size=4, cycles=1, energy=1)
def pattern_u8tou32(context, tree, c0):
    d = context.new_reg(Or1kRegister)
    context.emit(Extbz(d, c0))
    return d


@orbis32.pattern('reg', 'U32TOU8(reg)', size=4, cycles=1, energy=1)
@orbis32.pattern('reg', 'I32TOU8(reg)', size=4, cycles=1, energy=1)
def pattern_i32tou8(context, tree, c0):
    d = context.new_reg(Or1kRegister)
    context.emit(Extbz(d, c0))
    return c0
