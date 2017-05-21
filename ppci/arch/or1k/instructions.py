
from .isa import orbis32, Orbis32Token
from .registers import Or1kRegister
from ..encoding import Instruction, Syntax, Operand
from ..encoding import Relocation
from ...utils.bitfun import wrap_negative


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
Mul = regregreg('mul', 0b111000, 0b1100000110)
Or = regregreg('or', 0b111000, 0b0000100)
Ori = regregimm('ori', 0b101010)
Sub = regregreg('sub', 0b111000, 0b0000010)
Xor = regregreg('xor', 0b111000, 0b0000101)
Xori = regregimm('xori', 0b101011)


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


@orbis32.pattern('reg', 'DIVI32(reg, reg)', size=4, cycles=1, energy=1)
def pattern_divi32(context, tree, c0, c1):
    d = context.new_reg(Or1kRegister)
    context.emit(Div(d, c0, c1))
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
