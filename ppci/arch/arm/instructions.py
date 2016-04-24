"""
    Definitions of arm instructions.
"""

# pylint: disable=no-member,invalid-name

from ..isa import Instruction, Isa, Constructor, Syntax, FixedPattern
from ..isa import VariablePattern
from ..isa import register_argument, value_argument
from ...utils.bitfun import encode_imm32
from .registers import ArmRegister, Coreg, Coproc, RegisterSet
from ..token import Token, u32, bit_range
from .relocations import apply_b_imm24, apply_rel8
from .relocations import apply_ldr_imm12, apply_adr_imm12

# TODO: do not use ir stuff here!
from ...ir import i32


arm_isa = Isa()

arm_isa.register_relocation(apply_adr_imm12)
arm_isa.register_relocation(apply_b_imm24)
arm_isa.register_relocation(apply_ldr_imm12)
arm_isa.register_relocation(apply_rel8)


# Tokens:
class ArmToken(Token):
    def __init__(self):
        super().__init__(32)

    cond = bit_range(28, 32)
    S = bit_range(20, 21)
    Rd = bit_range(12, 16)
    Rn = bit_range(16, 20)
    Rm = bit_range(0, 4)
    shift_typ = bit_range(5, 7)
    shift_imm = bit_range(7, 12)

    def encode(self):
        return u32(self.bit_value)


# Patterns:

# Condition patterns:
EQ, NE, CS, CC, MI, PL, VS, VC, HI, LS, GE, LT, GT, LE, AL = range(15)
COND_MAP = {
    'EQ': EQ,
    'NE': NE,
    'CS': CS,
    'CC': CC,
    'MI': MI,
    'PL': PL,
    'VS': VS,
    'VC': VC,
    'HI': HI,
    'LS': LS,
    'GE': GE,
    'LT': LT,
    'GT': GT,
    'LE': LE,
    'AL': AL}


# Shift suffix:
class ShiftModifier(Constructor):
    """ Shift modifier that can be appended to shift Rm """
    syntaxi = 'shift'


class NoShift(ShiftModifier):
    """ No shift """
    patterns = (
        FixedPattern('shift_typ', 0),
        FixedPattern('shift_imm', 0),
        )
    syntax = Syntax([])


class ShiftLsl(ShiftModifier):
    """ Logical shift left n bits """
    n = register_argument('n', int)
    patterns = (
        FixedPattern('shift_typ', 0),
        VariablePattern('shift_imm', n),
        )
    syntax = Syntax([',', 'lsl', n])


class ShiftLsr(ShiftModifier):
    """ Logical shift right n bits """
    n = register_argument('n', int)
    patterns = (
        FixedPattern('shift_typ', 1),
        VariablePattern('shift_imm', n),
        )
    syntax = Syntax([',', 'lsr', n])


class ShiftAsr(ShiftModifier):
    """ Arithmetic shift right n bits """
    n = register_argument('n', int)
    patterns = (
        FixedPattern('shift_typ', 2),
        VariablePattern('shift_imm', n),
        )
    syntax = Syntax([',', 'asr', n])


# Instructions:

def inter_twine(a, cond):
    """ Create a permutation for a instruction class """
    # TODO: give this function the right name
    stx = list(a.syntax.syntax)
    mnemonic = stx[0] + cond
    stx[0] = mnemonic
    syntax = Syntax(stx)
    ccode = COND_MAP[cond.upper()]
    patterns = (FixedPattern('cond', ccode), )
    members = {'syntax': syntax, 'patterns': patterns}
    return type(mnemonic, (a, ), members)


class ArmInstruction(Instruction):
    tokens = [ArmToken]
    isa = arm_isa


class Mov1(ArmInstruction):
    """ Mov Rd, imm16 """
    rd = register_argument('rd', ArmRegister, write=True)
    imm = register_argument('imm', int)
    syntax = Syntax(['mov', rd, ',', imm])

    def encode(self):
        self.token1[0:12] = encode_imm32(self.imm)
        self.token1.Rd = self.rd.num
        self.token1[16:20] = 0
        self.token1[20] = 0  # Set flags
        self.token1[21:28] = 0b0011101
        self.token1.cond = AL
        return self.token1.encode()


class Mov2(ArmInstruction):
    """ Mov register to register """
    rd = register_argument('rd', ArmRegister, write=True)
    rm = register_argument('rm', ArmRegister, read=True)
    shift = register_argument('shift', ShiftModifier)
    syntax = Syntax(['mov', rd, ',', rm, shift])
    patterns = (
        FixedPattern('cond', AL),
        )

    def encode(self):
        self.set_all_patterns()
        self.token1[0:4] = self.rm.num
        self.token1[4] = 0
        self.token1[12:16] = self.rd.num
        self.token1[16:20] = 0
        self.token1.S = 0
        self.token1[21:28] = 0xD
        return self.token1.encode()

Mov2LS = inter_twine(Mov2, 'ls')


class Cmp1(ArmInstruction):
    """ CMP Rn, imm """
    reg = register_argument('reg', ArmRegister, read=True)
    imm = value_argument('imm')
    syntax = Syntax(['cmp', reg, ',', imm])

    def encode(self):
        self.token1[0:12] = encode_imm32(self.imm)
        self.token1.Rn = self.reg.num
        self.token1[20:28] = 0b00110101
        self.token1.cond = AL
        return self.token1.encode()


class Cmp2(ArmInstruction):
    """ CMP Rn, Rm """
    rn = register_argument('rn', ArmRegister, read=True)
    rm = register_argument('rm', ArmRegister, read=True)
    shift = register_argument('shift', ShiftModifier)
    syntax = Syntax(['cmp', rn, ',', rm, shift])
    patterns = (
        FixedPattern('cond', AL),
        )

    def encode(self):
        self.set_all_patterns()
        self.token1.Rn = self.rn.num
        self.token1.Rm = self.rm.num
        self.token1[4] = 0
        self.token1[12:16] = 0
        self.token1[20:28] = 0b10101
        return self.token1.encode()


class Mul1(ArmInstruction):
    rd = register_argument('rd', ArmRegister, write=True)
    rn = register_argument('rn', ArmRegister, read=True)
    rm = register_argument('rm', ArmRegister, read=True)
    syntax = Syntax(['mul', rd, ',', rn, ',', rm])

    def encode(self):
        self.token1[0:4] = self.rn.num
        self.token1[4:8] = 0b1001
        self.token1[8:12] = self.rm.num
        self.token1[16:20] = self.rd.num
        self.token1.S = 0
        self.token1.cond = AL
        return self.token1.encode()


class Sdiv(ArmInstruction):
    """ Encoding A1
        rd = rn / rm

        This instruction is not always present
    """
    rd = register_argument('rd', ArmRegister, write=True)
    rn = register_argument('rn', ArmRegister, read=True)
    rm = register_argument('rm', ArmRegister, read=True)
    syntax = Syntax(['sdiv', rd, ',', rn, ',', rm])

    def encode(self):
        self.token1[0:4] = self.rn.num
        self.token1[4:8] = 0b0001
        self.token1[8:12] = self.rm.num
        self.token1[12:16] = 0b1111
        self.token1[16:20] = self.rd.num
        self.token1[20:28] = 0b1110001
        self.token1.cond = AL
        return self.token1.encode()


class Udiv(ArmInstruction):
    """ Encoding A1
        rd = rn / rm
    """
    rd = register_argument('rd', ArmRegister, write=True)
    rn = register_argument('rn', ArmRegister, read=True)
    rm = register_argument('rm', ArmRegister, read=True)
    syntax = Syntax(['udiv', rd, ',', rn, ',', rm])

    def encode(self):
        self.token1[0:4] = self.rn.num
        self.token1[4:8] = 0b0001
        self.token1[8:12] = self.rm.num
        self.token1[12:16] = 0b1111
        self.token1[16:20] = self.rd.num
        self.token1[20:28] = 0b1110011
        self.token1.cond = AL
        return self.token1.encode()


class Mls(ArmInstruction):
    """ Multiply substract
        Semantics:
        rd = ra - rn * rm
    """
    rd = register_argument('rd', ArmRegister, write=True)
    rn = register_argument('rn', ArmRegister, read=True)
    rm = register_argument('rm', ArmRegister, read=True)
    ra = register_argument('ra', ArmRegister, read=True)
    syntax = Syntax(['mls', rd, ',', rn, ',', rm, ',', ra])

    def encode(self):
        self.token1[0:4] = self.rn.num
        self.token1[4:8] = 0b1001
        self.token1[8:12] = self.rm.num
        self.token1[12:16] = self.ra.num
        self.token1[16:20] = self.rd.num
        self.token1[20:28] = 0b00000110
        self.token1.cond = AL
        return self.token1.encode()


class OpRegRegReg(ArmInstruction):
    """ add rd, rn, rm """
    patterns = (
        FixedPattern('cond', AL),
        FixedPattern('S', 0),
        )

    def encode(self):
        self.set_all_patterns()
        self.token1[0:4] = self.rm.num
        self.token1[4] = 0
        self.token1[5:7] = 0   # Shift type
        self.token1[7:12] = 0  # Shift
        self.token1.Rd = self.rd.num
        self.token1.Rn = self.rn.num
        self.token1[21:28] = self.opcode
        return self.token1.encode()


def make_regregreg(mnemonic, opcode):
    """ Create a new instruction class with three registers as operands """
    rd = register_argument('rd', ArmRegister, write=True)
    rn = register_argument('rn', ArmRegister, read=True)
    rm = register_argument('rm', ArmRegister, read=True)
    syntax = Syntax([mnemonic, rd, ',', rn, ',', rm])
    members = {
        'syntax': syntax, 'rd': rd, 'rn': rn, 'rm': rm, 'opcode': opcode}
    return type(mnemonic + '_ins', (OpRegRegReg,), members)


Add1 = make_regregreg('add', 0b0000100)
Adc1 = make_regregreg('adc', 0b0000101)
Sub1 = make_regregreg('sub', 0b0000010)
Orr1 = make_regregreg('orr', 0b0001100)
Orr = Orr1
And1 = make_regregreg('and', 0b0000000)
And = And1
Eor1 = make_regregreg('eor', 0b0000001)


Sub1CC = inter_twine(Sub1, 'cc')
Sub1cs = inter_twine(Sub1, 'cs')
Sub1NE = inter_twine(Sub1, 'ne')


class ShiftBase(ArmInstruction):
    """ ? rd, rn, rm """
    rd = register_argument('rd', ArmRegister, write=True)
    rn = register_argument('rn', ArmRegister, read=True)
    rm = register_argument('rm', ArmRegister, read=True)

    def encode(self):
        self.token1[0:4] = self.rn.num
        self.token1[4:8] = self.opcode
        self.token1[8:12] = self.rm.num
        self.token1[12:16] = self.rd.num
        self.token1.S = 0  # Set flags
        self.token1[21:28] = 0b1101
        self.token1.cond = AL
        return self.token1.encode()


class Lsr1(ShiftBase):
    opcode = 0b0011
    syntax = Syntax(
        ['lsr', ShiftBase.rd, ',', ShiftBase.rn, ',', ShiftBase.rm])


Lsr = Lsr1


class Lsl1(ShiftBase):
    opcode = 0b0001
    syntax = Syntax(
        ['lsl', ShiftBase.rd, ',', ShiftBase.rn, ',', ShiftBase.rm])


Lsl = Lsl1


class OpRegRegImm(ArmInstruction):
    """ add rd, rn, imm12 """
    def encode(self):
        self.token1[0:12] = encode_imm32(self.imm)
        self.token1.Rd = self.rd.num
        self.token1.Rn = self.rn.num
        self.token1.S = 0  # Set flags
        self.token1[21:28] = self.opcode
        self.token1.cond = AL
        return self.token1.encode()


def make_regregimm(mnemonic, opcode):
    rd = register_argument('rd', ArmRegister, write=True)
    rn = register_argument('rn', ArmRegister, read=True)
    imm = register_argument('imm', int)
    syntax = Syntax([mnemonic, rd, ',', rn, ',', imm])
    members = {
        'syntax': syntax, 'rd': rd, 'rn': rn, 'imm': imm, 'opcode': opcode}
    return type(mnemonic + '_ins', (OpRegRegImm,), members)

Add2 = make_regregimm('add', 0b0010100)
Sub2 = make_regregimm('sub', 0b0010010)


# Branches:

class BranchBaseRoot(ArmInstruction):
    target = register_argument('target', str)

    def encode(self):
        self.token1.cond = self.cond
        self.token1[24:28] = self.opcode
        return self.token1.encode()

    def relocations(self):
        return [(self.target, apply_b_imm24)]


class BranchBase(BranchBaseRoot):
    opcode = 0b1010


class BranchLinkBase(BranchBaseRoot):
    opcode = 0b1011


class Bl(BranchLinkBase):
    cond = AL
    syntax = Syntax(['bl', BranchBaseRoot.target])


def make_branch(mnemonic, cond):
    target = register_argument('target', str)
    syntax = Syntax([mnemonic, target])
    members = {
        'syntax': syntax, 'target': target, 'cond': cond}
    return type(mnemonic + '_ins', (BranchBase,), members)

B = make_branch('b', AL)
Beq = make_branch('beq', EQ)
Bgt = make_branch('bgt', GT)
Bge = make_branch('bge', GE)
Bls = make_branch('bls', LS)
Ble = make_branch('ble', LE)
Blt = make_branch('blt', LT)
Bne = make_branch('bne', NE)
Bhs = make_branch('bhs', CS)  # Hs (higher or same) is synonim for CS
Blo = make_branch('blo', CC)  # Lo (unsigned lower) is synonim for CC


def reg_list_to_mask(reg_list):
    mask = 0
    for reg in reg_list:
        mask |= (1 << reg.num)
    return mask


class Push(ArmInstruction):
    reg_list = register_argument('reg_list', RegisterSet)
    syntax = Syntax(['push', reg_list])

    def encode(self):
        self.token1.cond = AL
        self.token1[16:28] = 0b100100101101
        self.token1[0:16] = reg_list_to_mask(self.reg_list)
        return self.token1.encode()


class Pop(ArmInstruction):
    reg_list = register_argument('reg_list', RegisterSet)
    syntax = Syntax(['pop', reg_list])

    def encode(self):
        self.token1.cond = AL
        self.token1[16:28] = 0b100010111101
        self.token1[0:16] = reg_list_to_mask(self.reg_list)
        return self.token1.encode()


def LdrPseudo(rt, lab, add_lit):
    """ Ldr rt, =lab ==> ldr rt, [pc, offset in litpool] ... dcd lab """
    lit_lbl = add_lit(lab)
    return Ldr3(rt, lit_lbl)


class LdrStrBase(ArmInstruction):
    rn = register_argument('rn', ArmRegister, read=True)
    offset = register_argument('offset', int)

    def encode(self):
        self.token1.cond = AL
        self.token1.Rn = self.rn.num
        self.token1[25:28] = self.opcode
        self.token1[22] = self.bit22
        self.token1[20] = self.bit20
        self.token1[12:16] = self.rt.num
        self.token1[24] = 1  # Index
        if self.offset >= 0:
            self.token1[23] = 1  # U == 1 'add'
            self.token1[0:12] = self.offset
        else:
            self.token1[23] = 0
            self.token1[0:12] = -self.offset
        return self.token1.encode()


class Str1(LdrStrBase):
    rt = register_argument('rt', ArmRegister, read=True)
    opcode = 0b010
    bit20 = 0
    bit22 = 0
    syntax = Syntax([
        'str', rt, ',', '[', LdrStrBase.rn, ',', LdrStrBase.offset, ']'])


class Ldr1(LdrStrBase):
    rt = register_argument('rt', ArmRegister, write=True)
    opcode = 0b010
    bit20 = 1
    bit22 = 0
    syntax = Syntax([
        'ldr', rt, ',', '[', LdrStrBase.rn, ',', LdrStrBase.offset, ']'])


class Strb(LdrStrBase):
    """ ldrb rt, [rn, offset] # Store byte at address """
    rt = register_argument('rt', ArmRegister, read=True)
    opcode = 0b010
    bit20 = 0
    bit22 = 1
    syntax = Syntax([
        'strb', rt, ',', '[', LdrStrBase.rn, ',',
        LdrStrBase.offset, ']'])


class Ldrb(LdrStrBase):
    """ ldrb rt, [rn, offset] """
    rt = register_argument('rt', ArmRegister, write=True)
    opcode = 0b010
    bit20 = 1
    bit22 = 1
    syntax = Syntax([
        'ldrb', rt, ',', '[', LdrStrBase.rn, ',',
        LdrStrBase.offset, ']'])


class Adr(ArmInstruction):
    rd = register_argument('rd', ArmRegister, write=True)
    label = register_argument('label', str)
    syntax = Syntax(['adr', rd, ',', label])

    def relocations(self):
        return [(self.label, apply_adr_imm12)]

    def encode(self):
        self.token1.cond = AL
        self.token1[0:12] = 0  # Filled by linker
        self.token1[12:16] = self.rd.num
        self.token1[16:20] = 0b1111
        self.token1[25] = 1
        return self.token1.encode()


class Ldr3(ArmInstruction):
    """ Load PC relative constant value
        LDR rt, label
        encoding A1
    """
    rt = register_argument('rt', ArmRegister, write=True)
    label = register_argument('label', str)
    syntax = Syntax(['ldr', rt, ',', label])

    def relocations(self):
        return [(self.label, apply_ldr_imm12)]

    def encode(self):
        self.token1.cond = AL
        self.token1[0:12] = 0  # Filled by linker
        self.token1[12:16] = self.rt.num
        self.token1[16:23] = 0b0011111
        self.token1[24:28] = 0b0101
        return self.token1.encode()


class McrBase(ArmInstruction):
    """ Mov arm register to coprocessor register """
    def encode(self):
        self.token1[0:4] = self.crm.num
        self.token1[4] = 1
        self.token1[5:8] = self.opc2
        self.token1[8:12] = self.coproc.num
        self.token1[12:16] = self.rt.num
        self.token1[16:20] = self.crn.num
        self.token1[20] = self.b20
        self.token1[21:24] = self.opc1
        self.token1[24:28] = 0b1110
        self.token1.cond = AL
        return self.token1.encode()


class Mcr(McrBase):
    """ Move from register to co processor register """
    coproc = register_argument('coproc', Coproc)
    opc1 = register_argument('opc1', int)
    rt = register_argument('rt', ArmRegister, read=True)
    crn = register_argument('crn', Coreg, read=True)
    crm = register_argument('crm', Coreg, read=True)
    opc2 = register_argument('opc2', int)
    b20 = 0
    syntax = Syntax(
        ['mcr', coproc, ',', opc1, ',', rt, ',', crn, ',', crm, ',', opc2])


class Mrc(McrBase):
    coproc = register_argument('coproc', Coproc)
    opc1 = register_argument('opc1', int)
    rt = register_argument('rt', ArmRegister, write=True)
    crn = register_argument('crn', Coreg, read=True)
    crm = register_argument('crm', Coreg, read=True)
    opc2 = register_argument('opc2', int)
    b20 = 1
    syntax = Syntax(
        ['mrc', coproc, ',', opc1, ',', rt, ',', crn, ',', crm, ',', opc2])


# Instruction selection patterns:
@arm_isa.pattern('stm', 'STRI32(reg, reg)', size=4)
def pattern_str32(self, tree, c0, c1):
    self.emit(Str1(c1, c0, 0))


@arm_isa.pattern(
    'stm', 'STRI32(ADDI32(reg, CONSTI32), reg)',
    size=4,
    condition=lambda t: t.children[0].children[1].value < 256)
def pattern_str32_1(context, tree, c0, c1):
    # TODO: something strange here: when enabeling this rule, programs
    # compile correctly...
    offset = tree.children[0].children[1].value
    context.emit(Str1(c1, c0, offset))


@arm_isa.pattern('stm', 'STRI8(reg, reg)', size=4)
def pattern_str8(context, tree, c0, c1):
    context.emit(Strb(c1, c0, 0))


@arm_isa.pattern('reg', 'MOVI32(reg)', size=4)
def pattern_mov32(context, tree, c0):
    context.move(tree.value, c0)
    return tree.value


@arm_isa.pattern('reg', 'MOVI8(reg)', size=4)
def pattern_mov8(context, tree, c0):
    context.move(tree.value, c0)
    return tree.value


@arm_isa.pattern('stm', 'JMP', cost=2)
def pattern_jmp(context, tree):
    tgt = tree.value
    context.emit(B(tgt.name, jumps=[tgt]))


@arm_isa.pattern('reg', 'REGI32', size=0, cycles=0, energy=0)
def pattern_reg32(context, tree):
    return tree.value


@arm_isa.pattern('reg', 'REGI8', size=0, cycles=0, energy=0)
def pattern_reg8(context, tree):
    return tree.value


@arm_isa.pattern('reg', 'CONSTI32', size=8)
def pattern_const32(context, tree):
    d = context.new_reg(ArmRegister)
    ln = context.frame.add_constant(tree.value)
    context.emit(Ldr3(d, ln))
    return d


@arm_isa.pattern('reg', 'CONSTI32', size=4, condition=lambda t: t.value < 256)
def pattern_const32_1(context, tree):
    d = context.new_reg(ArmRegister)
    c0 = tree.value
    assert isinstance(c0, int)
    assert c0 < 256 and c0 >= 0
    context.emit(Mov1(d, c0))
    return d


@arm_isa.pattern('reg', 'CONSTI8', size=4, condition=lambda t: t.value < 256)
def pattern_const8_1(context, tree):
    d = context.new_reg(ArmRegister)
    c0 = tree.value
    assert isinstance(c0, int)
    assert c0 < 256 and c0 >= 0
    context.emit(Mov1(d, c0))
    return d


@arm_isa.pattern('stm', 'CJMP(reg, reg)', cost=2)
def pattern_cjmp(context, tree, c0, c1):
    op, yes_label, no_label = tree.value
    opnames = {"<": Blt, ">": Bgt, "==": Beq, "!=": Bne, ">=": Bge}
    Bop = opnames[op]
    context.emit(Cmp2(c0, c1, NoShift()))
    jmp_ins = B(no_label.name, jumps=[no_label])
    context.emit(Bop(yes_label.name, jumps=[yes_label, jmp_ins]))
    context.emit(jmp_ins)


@arm_isa.pattern('reg', 'ADDI32(reg, reg)', cost=2)
def pattern_add32(context, tree, c0, c1):
    d = context.new_reg(ArmRegister)
    context.emit(Add1(d, c0, c1))
    return d


@arm_isa.pattern('reg', 'ADDI8(reg, reg)', size=4)
def pattern_add8(context, tree, c0, c1):
    d = context.new_reg(ArmRegister)
    context.emit(Add1(d, c0, c1))
    return d


@arm_isa.pattern(
    'reg', 'ADDI32(reg, CONSTI32)', size=4,
    condition=lambda t: t.children[1].value < 256)
def pattern_add32_1(context, tree, c0):
    d = context.new_reg(ArmRegister)
    c1 = tree.children[1].value
    context.emit(Add2(d, c0, c1))
    return d


@arm_isa.pattern(
    'reg', 'ADDI32(CONSTI32, reg)', size=4,
    condition=lambda t: t.children[0].value < 256)
def pattern_add32_2(context, tree, c0):
    d = context.new_reg(ArmRegister)
    c1 = tree.children[0].value
    context.emit(Add2(d, c0, c1))
    return d


@arm_isa.pattern('reg', 'SUBI32(reg, reg)', size=4)
def pattern_sub32(context, tree, c0, c1):
    d = context.new_reg(ArmRegister)
    context.emit(Sub1(d, c0, c1))
    return d


@arm_isa.pattern('reg', 'SUBI8(reg, reg)', size=4)
def pattern_sub8(context, tree, c0, c1):
    # TODO: temporary fix this with an 32 bits sub
    d = context.new_reg(ArmRegister)
    context.emit(Sub1(d, c0, c1))
    return d


@arm_isa.pattern('reg', 'LABEL', size=8)
def pattern_label(context, tree):
    d = context.new_reg(ArmRegister)
    ln = context.frame.add_constant(tree.value)
    context.emit(Ldr3(d, ln))
    return d


@arm_isa.pattern('reg', 'LDRI8(reg)', size=4)
def pattern_ld8(context, tree, c0):
    d = context.new_reg(ArmRegister)
    context.emit(Ldrb(d, c0, 0))
    return d


@arm_isa.pattern('reg', 'LDRI32(reg)', size=4)
def pattern_ld32(context, tree, c0):
    d = context.new_reg(ArmRegister)
    context.emit(Ldr1(d, c0, 0))
    return d


@arm_isa.pattern('reg', 'CALL')
def pattern_call(context, tree):
    label, arg_types, ret_type, args, res_var = tree.value
    context.gen_call(label, arg_types, ret_type, args, res_var)
    return res_var


@arm_isa.pattern('reg', 'ANDI32(reg, reg)', size=4)
def pattern_and(context, tree, c0, c1):
    d = context.new_reg(ArmRegister)
    context.emit(And1(d, c0, c1))
    return d


@arm_isa.pattern('reg', 'ORI32(reg, reg)', size=4)
def pattern_or32(context, tree, c0, c1):
    d = context.new_reg(ArmRegister)
    context.emit(Orr1(d, c0, c1))
    return d


@arm_isa.pattern('reg', 'SHRI32(reg, reg)', size=4)
def pattern_shr32(context, tree, c0, c1):
    d = context.new_reg(ArmRegister)
    context.emit(Lsr1(d, c0, c1))
    return d


@arm_isa.pattern('reg', 'SHLI32(reg, reg)', size=4)
def pattern_shl32(context, tree, c0, c1):
    d = context.new_reg(ArmRegister)
    context.emit(Lsl1(d, c0, c1))
    return d


@arm_isa.pattern('reg', 'MULI32(reg, reg)', size=4)
def pattern_mul32(context, tree, c0, c1):
    d = context.new_reg(ArmRegister)
    context.emit(Mul1(d, c0, c1))
    return d


@arm_isa.pattern('reg', 'LDRI32(ADDI32(reg, CONSTI32))', size=4)
def pattern_ldr32(context, tree, c0):
    d = context.new_reg(ArmRegister)
    c1 = tree.children[0].children[1].value
    assert isinstance(c1, int)
    context.emit(Ldr1(d, c0, c1))
    return d


@arm_isa.pattern('reg', 'DIVI32(reg, reg)')
def pattern_div32(context, tree, c0, c1):
    d = context.new_reg(ArmRegister)
    # Generate call into runtime lib function!
    context.gen_call('__sdiv', [i32, i32], i32, [c0, c1], d)
    return d


@arm_isa.pattern('reg', 'REMI32(reg, reg)')
def pattern_rem32(context, tree, c0, c1):
    # Implement remainder as a combo of div and mls (multiply substract)
    d = context.new_reg(ArmRegister)
    context.gen_call('__sdiv', [i32, i32], i32, [c0, c1], d)
    d2 = context.new_reg(ArmRegister)
    context.emit(Mls(d2, d, c1, c0))
    return d2


@arm_isa.pattern('reg', 'XORI32(reg, reg)', size=4)
def pattern_xor32(context, tree, c0, c1):
    d = context.new_reg(ArmRegister)
    context.emit(Eor1(d, c0, c1))
    return d

# TODO: implement DIVI32 by library call.
# TODO: Do that here, or in irdag?

isa_with_div = Isa()


@isa_with_div.pattern('reg', 'DIVI32(reg, reg)', size=4)
def pattern_23(self, tree, c0, c1):
    d = self.new_reg(ArmRegister)
    self.emit(Udiv, dst=[d], src=[c0, c1])
    return d


@isa_with_div.pattern('reg', 'REMI32(reg, reg)', size=4)
def pattern_24(self, tree, c0, c1):
    # Implement remainder as a combo of div and mls (multiply substract)
    d = self.new_reg(ArmRegister)
    self.emit(Udiv, dst=[d], src=[c0, c1])
    d2 = self.new_reg(ArmRegister)
    self.emit(Mls, dst=[d2], src=[d, c1, c0])
    return d2
