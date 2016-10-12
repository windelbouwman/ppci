"""
    Definitions of arm instructions.
"""

# pylint: disable=no-member,invalid-name

from .isa import arm_isa, ArmToken, Isa
from ..encoding import Instruction, Constructor, Syntax, Operand
from ...utils.bitfun import encode_imm32
from .registers import ArmRegister, Coreg, Coproc, RegisterSet
from .arm_relocations import Imm24Relocation
from .arm_relocations import LdrImm12Relocation, AdrImm12Relocation
from ...ir import i32


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


class NoShift(Constructor):
    """ No shift """
    syntax = Syntax([])
    patterns = {'shift_typ': 0, 'shift_imm': 0}


class ShiftLsl(Constructor):
    """ Logical shift left n bits """
    n = Operand('n', int)
    syntax = Syntax([',', ' ', 'lsl', ' ', n])
    patterns = {'shift_typ': 0, 'shift_imm': n}


class ShiftLsr(Constructor):
    """ Logical shift right n bits """
    n = Operand('n', int)
    syntax = Syntax([',', ' ', 'lsr', ' ', n])
    patterns = {'shift_typ': 1, 'shift_imm': n}


class ShiftAsr(Constructor):
    """ Arithmetic shift right n bits """
    n = Operand('n', int)
    syntax = Syntax([',', ' ', 'asr', ' ', n])
    patterns = {'shift_typ': 2, 'shift_imm': n}


# Shift suffix:
shift_modes = (NoShift, ShiftLsl, ShiftLsr, ShiftAsr)


# Instructions:

def inter_twine(a, cond):
    """ Create a permutation for a instruction class """
    # TODO: give this function the right name
    stx = list(a.syntax.syntax)
    ccode = COND_MAP[cond.upper()]
    mnemonic = stx[0] + cond
    stx[0] = mnemonic
    syntax = Syntax(stx)
    patterns = dict(a.patterns)
    patterns['cond'] = ccode
    members = {'syntax': syntax, 'patterns': patterns}
    return type(mnemonic, (a, ), members)


class ArmInstruction(Instruction):
    tokens = [ArmToken]
    isa = arm_isa


class Mov1(ArmInstruction):
    """ Mov Rd, imm16 """
    rd = Operand('rd', ArmRegister, write=True)
    imm = Operand('imm', int)
    syntax = Syntax(['mov', ' ', rd, ',', ' ', imm])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:12] = encode_imm32(self.imm)
        tokens[0].Rd = self.rd.num
        tokens[0][16:20] = 0
        tokens[0][20] = 0  # Set flags
        tokens[0][21:28] = 0b0011101
        tokens[0].cond = AL
        return tokens[0].encode()


class Mov2(ArmInstruction):
    """ Mov register to register """
    rd = Operand('rd', ArmRegister, write=True)
    rm = Operand('rm', ArmRegister, read=True)
    shift = Operand('shift', shift_modes)
    syntax = Syntax(['mov', ' ', rd, ',', ' ', rm, shift])
    patterns = {'cond': AL, 'S': 0}

    def encode(self):
        tokens = self.get_tokens()
        self.set_all_patterns(tokens)
        tokens[0][4] = 0
        tokens[0].Rm = self.rm.num
        tokens[0][12:16] = self.rd.num
        tokens[0][16:20] = 0
        tokens[0][21:28] = 0xD
        return tokens[0].encode()


Mov2LS = inter_twine(Mov2, 'ls')


class Cmp1(ArmInstruction):
    """ CMP Rn, imm """
    reg = Operand('reg', ArmRegister, read=True)
    imm = Operand('imm', int)
    syntax = Syntax(['cmp', reg, ',', imm])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:12] = encode_imm32(self.imm)
        tokens[0].Rn = self.reg.num
        tokens[0][20:28] = 0b00110101
        tokens[0].cond = AL
        return tokens[0].encode()


class Cmp2(ArmInstruction):
    """ CMP Rn, Rm """
    rn = Operand('rn', ArmRegister, read=True)
    rm = Operand('rm', ArmRegister, read=True)
    shift = Operand('shift', shift_modes)
    syntax = Syntax(['cmp', ' ', rn, ',', ' ', rm, shift])
    patterns = {'cond': AL, 'Rm': rm, 'Rn': rn}

    def encode(self):
        tokens = self.get_tokens()
        self.set_all_patterns(tokens)
        tokens[0][4] = 0
        tokens[0][12:16] = 0
        tokens[0][20:28] = 0b10101
        return tokens[0].encode()


class Mul1(ArmInstruction):
    rd = Operand('rd', ArmRegister, write=True)
    rn = Operand('rn', ArmRegister, read=True)
    rm = Operand('rm', ArmRegister, read=True)
    syntax = Syntax(['mul', rd, ',', rn, ',', rm])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:4] = self.rn.num
        tokens[0][4:8] = 0b1001
        tokens[0][8:12] = self.rm.num
        tokens[0][16:20] = self.rd.num
        tokens[0].S = 0
        tokens[0].cond = AL
        return tokens[0].encode()


class Sdiv(ArmInstruction):
    """ Encoding A1
        rd = rn / rm

        This instruction is not always present
    """
    rd = Operand('rd', ArmRegister, write=True)
    rn = Operand('rn', ArmRegister, read=True)
    rm = Operand('rm', ArmRegister, read=True)
    syntax = Syntax(['sdiv', rd, ',', rn, ',', rm])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:4] = self.rn.num
        tokens[0][4:8] = 0b0001
        tokens[0][8:12] = self.rm.num
        tokens[0][12:16] = 0b1111
        tokens[0][16:20] = self.rd.num
        tokens[0][20:28] = 0b1110001
        tokens[0].cond = AL
        return tokens[0].encode()


class Udiv(ArmInstruction):
    """ Encoding A1
        rd = rn / rm
    """
    rd = Operand('rd', ArmRegister, write=True)
    rn = Operand('rn', ArmRegister, read=True)
    rm = Operand('rm', ArmRegister, read=True)
    syntax = Syntax(['udiv', rd, ',', rn, ',', rm])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:4] = self.rn.num
        tokens[0][4:8] = 0b0001
        tokens[0][8:12] = self.rm.num
        tokens[0][12:16] = 0b1111
        tokens[0][16:20] = self.rd.num
        tokens[0][20:28] = 0b1110011
        tokens[0].cond = AL
        return tokens[0].encode()


class Mls(ArmInstruction):
    """ Multiply substract
        Semantics:
        rd = ra - rn * rm
    """
    rd = Operand('rd', ArmRegister, write=True)
    rn = Operand('rn', ArmRegister, read=True)
    rm = Operand('rm', ArmRegister, read=True)
    ra = Operand('ra', ArmRegister, read=True)
    syntax = Syntax(['mls', rd, ',', rn, ',', rm, ',', ra])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:4] = self.rn.num
        tokens[0][4:8] = 0b1001
        tokens[0][8:12] = self.rm.num
        tokens[0][12:16] = self.ra.num
        tokens[0][16:20] = self.rd.num
        tokens[0][20:28] = 0b00000110
        tokens[0].cond = AL
        return tokens[0].encode()


class OpRegRegReg(ArmInstruction):
    """ add rd, rn, rm """
    patterns = {'cond': AL, 'S': 0}

    def encode(self):
        tokens = self.get_tokens()
        self.set_all_patterns(tokens)
        tokens[0][0:4] = self.rm.num
        tokens[0][4] = 0
        tokens[0].Rd = self.rd.num
        tokens[0].Rn = self.rn.num
        tokens[0][21:28] = self.opcode
        return tokens[0].encode()


def make_regregreg(mnemonic, opcode):
    """ Create a new instruction class with three registers as operands """
    rd = Operand('rd', ArmRegister, write=True)
    rn = Operand('rn', ArmRegister, read=True)
    rm = Operand('rm', ArmRegister, read=True)
    shift = Operand('shift', shift_modes)
    syntax = Syntax([mnemonic, ' ', rd, ',', ' ', rn, ',', ' ', rm, shift])
    members = {
        'syntax': syntax, 'rd': rd, 'rn': rn, 'rm': rm, 'opcode': opcode,
        'shift': shift,
        }
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
    rd = Operand('rd', ArmRegister, write=True)
    rn = Operand('rn', ArmRegister, read=True)
    rm = Operand('rm', ArmRegister, read=True)
    patterns = {'cond': AL, 'S': 0}

    def encode(self):
        tokens = self.get_tokens()
        self.set_all_patterns(tokens)
        tokens[0][0:4] = self.rn.num
        tokens[0][4:8] = self.opcode
        tokens[0][8:12] = self.rm.num
        tokens[0][12:16] = self.rd.num
        tokens[0][21:28] = 0b1101
        return tokens[0].encode()


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
        tokens = self.get_tokens()
        tokens[0][0:12] = encode_imm32(self.imm)
        tokens[0].Rd = self.rd.num
        tokens[0].Rn = self.rn.num
        tokens[0].S = 0  # Set flags
        tokens[0][21:28] = self.opcode
        tokens[0].cond = AL
        return tokens[0].encode()


def make_regregimm(mnemonic, opcode):
    rd = Operand('rd', ArmRegister, write=True)
    rn = Operand('rn', ArmRegister, read=True)
    imm = Operand('imm', int)
    syntax = Syntax([mnemonic, rd, ',', rn, ',', imm])
    members = {
        'syntax': syntax, 'rd': rd, 'rn': rn, 'imm': imm, 'opcode': opcode}
    return type(mnemonic + '_ins', (OpRegRegImm,), members)

Add2 = make_regregimm('add', 0b0010100)
Sub2 = make_regregimm('sub', 0b0010010)


# Branches:

class BranchBaseRoot(ArmInstruction):
    target = Operand('target', str)

    def encode(self):
        tokens = self.get_tokens()
        tokens[0].cond = self.cond
        tokens[0][24:28] = self.opcode
        return tokens[0].encode()

    def relocations(self):
        return [Imm24Relocation(self.target)]


class BranchBase(BranchBaseRoot):
    opcode = 0b1010


class BranchLinkBase(BranchBaseRoot):
    opcode = 0b1011


class Bl(BranchLinkBase):
    cond = AL
    syntax = Syntax(['bl', BranchBaseRoot.target])


def make_branch(mnemonic, cond):
    target = Operand('target', str)
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
    reg_list = Operand('reg_list', RegisterSet)
    syntax = Syntax(['push', reg_list])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0].cond = AL
        tokens[0][16:28] = 0b100100101101
        tokens[0][0:16] = reg_list_to_mask(self.reg_list)
        return tokens[0].encode()


class Pop(ArmInstruction):
    reg_list = Operand('reg_list', RegisterSet)
    syntax = Syntax(['pop', reg_list])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0].cond = AL
        tokens[0][16:28] = 0b100010111101
        tokens[0][0:16] = reg_list_to_mask(self.reg_list)
        return tokens[0].encode()


def LdrPseudo(rt, lab, add_lit):
    """ Ldr rt, =lab ==> ldr rt, [pc, offset in litpool] ... dcd lab """
    lit_lbl = add_lit(lab)
    return Ldr3(rt, lit_lbl)


class LdrStrBase(ArmInstruction):
    rn = Operand('rn', ArmRegister, read=True)
    offset = Operand('offset', int)

    def encode(self):
        tokens = self.get_tokens()
        tokens[0].cond = AL
        tokens[0].Rn = self.rn.num
        tokens[0][25:28] = self.opcode
        tokens[0][22] = self.bit22
        tokens[0][20] = self.bit20
        tokens[0][12:16] = self.rt.num
        tokens[0][24] = 1  # Index
        if self.offset >= 0:
            tokens[0][23] = 1  # U == 1 'add'
            tokens[0][0:12] = self.offset
        else:
            tokens[0][23] = 0
            tokens[0][0:12] = -self.offset
        return tokens[0].encode()


class Str1(LdrStrBase):
    rt = Operand('rt', ArmRegister, read=True)
    opcode = 0b010
    bit20 = 0
    bit22 = 0
    syntax = Syntax([
        'str', ' ', rt, ',', ' ', '[', LdrStrBase.rn, ',', ' ',
        LdrStrBase.offset, ']'])


class Ldr1(LdrStrBase):
    rt = Operand('rt', ArmRegister, write=True)
    opcode = 0b010
    bit20 = 1
    bit22 = 0
    syntax = Syntax([
        'ldr', ' ', rt, ',', ' ', '[', LdrStrBase.rn, ',', ' ',
        LdrStrBase.offset, ']'])


class Strb(LdrStrBase):
    """ ldrb rt, [rn, offset] # Store byte at address """
    rt = Operand('rt', ArmRegister, read=True)
    opcode = 0b010
    bit20 = 0
    bit22 = 1
    syntax = Syntax([
        'strb', ' ', rt, ',', ' ', '[', LdrStrBase.rn, ',', ' ',
        LdrStrBase.offset, ']'])


class Ldrb(LdrStrBase):
    """ ldrb rt, [rn, offset] """
    rt = Operand('rt', ArmRegister, write=True)
    opcode = 0b010
    bit20 = 1
    bit22 = 1
    syntax = Syntax([
        'ldrb', ' ', rt, ',', ' ', '[', LdrStrBase.rn, ',', ' ',
        LdrStrBase.offset, ']'])


class Adr(ArmInstruction):
    rd = Operand('rd', ArmRegister, write=True)
    label = Operand('label', str)
    syntax = Syntax(['adr', rd, ',', label])

    def relocations(self):
        return [AdrImm12Relocation(self.label)]

    def encode(self):
        tokens = self.get_tokens()
        tokens[0].cond = AL
        tokens[0][0:12] = 0  # Filled by linker
        tokens[0][12:16] = self.rd.num
        tokens[0][16:20] = 0b1111
        tokens[0][25] = 1
        return tokens[0].encode()


class Ldr3(ArmInstruction):
    """ Load PC relative constant value
        LDR rt, label
        encoding A1
    """
    rt = Operand('rt', ArmRegister, write=True)
    label = Operand('label', str)
    syntax = Syntax(['ldr', rt, ',', label])

    def relocations(self):
        return [LdrImm12Relocation(self.label)]

    def encode(self):
        tokens = self.get_tokens()
        tokens[0].cond = AL
        tokens[0][0:12] = 0  # Filled by linker
        tokens[0][12:16] = self.rt.num
        tokens[0][16:23] = 0b0011111
        tokens[0][24:28] = 0b0101
        return tokens[0].encode()


class McrBase(ArmInstruction):
    """ Mov arm register to coprocessor register """
    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:4] = self.crm.num
        tokens[0][4] = 1
        tokens[0][5:8] = self.opc2
        tokens[0][8:12] = self.coproc.num
        tokens[0][12:16] = self.rt.num
        tokens[0][16:20] = self.crn.num
        tokens[0][20] = self.b20
        tokens[0][21:24] = self.opc1
        tokens[0][24:28] = 0b1110
        tokens[0].cond = AL
        return tokens[0].encode()


class Mcr(McrBase):
    """ Move from register to co processor register """
    coproc = Operand('coproc', Coproc, read=True)
    opc1 = Operand('opc1', int)
    rt = Operand('rt', ArmRegister, read=True)
    crn = Operand('crn', Coreg, read=True)
    crm = Operand('crm', Coreg, read=True)
    opc2 = Operand('opc2', int)
    b20 = 0
    syntax = Syntax(
        ['mcr', coproc, ',', opc1, ',', rt, ',', crn, ',', crm, ',', opc2])


class Mrc(McrBase):
    coproc = Operand('coproc', Coproc, read=True)
    opc1 = Operand('opc1', int)
    rt = Operand('rt', ArmRegister, write=True)
    crn = Operand('crn', Coreg, read=True)
    crm = Operand('crm', Coreg, read=True)
    opc2 = Operand('opc2', int)
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


@arm_isa.pattern('stm', 'JMP', size=2)
def pattern_jmp(context, tree):
    tgt = tree.value
    context.emit(B(tgt.name, jumps=[tgt]))


@arm_isa.pattern('reg', 'REGI32', size=0, cycles=0, energy=0)
def pattern_reg32(context, tree):
    return tree.value


@arm_isa.pattern('reg', 'REGI8', size=0, cycles=0, energy=0)
def pattern_reg8(context, tree):
    return tree.value


@arm_isa.pattern('reg', 'I32TOI32(reg)', size=0)
def pattern_i32toi32(self, tree, c0):
    return c0


@arm_isa.pattern('reg', 'I8TOI32(reg)', size=0)
def pattern_i8toi32(self, tree, c0):
    # TODO: do something?
    return c0


@arm_isa.pattern('reg', 'I32TOI8(reg)', size=0)
def pattern_i32toi8(self, tree, c0):
    # TODO: do something?
    return c0


@arm_isa.pattern('reg', 'CONSTI32', size=8)
def pattern_const32(context, tree):
    d = context.new_reg(ArmRegister)
    ln = context.frame.add_constant(tree.value)
    context.emit(Ldr3(d, ln))
    return d


@arm_isa.pattern(
    'reg', 'CONSTI32', size=4, condition=lambda t: t.value in range(256))
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


@arm_isa.pattern('stm', 'CJMP(reg, reg)', size=2)
def pattern_cjmp(context, tree, c0, c1):
    op, yes_label, no_label = tree.value
    opnames = {"<": Blt, ">": Bgt, "==": Beq, "!=": Bne, ">=": Bge}
    Bop = opnames[op]
    context.emit(Cmp2(c0, c1, NoShift()))
    jmp_ins = B(no_label.name, jumps=[no_label])
    context.emit(Bop(yes_label.name, jumps=[yes_label, jmp_ins]))
    context.emit(jmp_ins)


@arm_isa.pattern('reg', 'ADDI32(reg, reg)', size=2)
def pattern_add32(context, tree, c0, c1):
    d = context.new_reg(ArmRegister)
    context.emit(Add1(d, c0, c1, NoShift()))
    return d


@arm_isa.pattern('reg', 'ADDI8(reg, reg)', size=4)
def pattern_add8(context, tree, c0, c1):
    d = context.new_reg(ArmRegister)
    context.emit(Add1(d, c0, c1, NoShift()))
    return d


@arm_isa.pattern(
    'reg', 'ADDI32(reg, CONSTI32)', size=4,
    condition=lambda t: t.children[1].value in range(256))
def pattern_add32_1(context, tree, c0):
    d = context.new_reg(ArmRegister)
    c1 = tree.children[1].value
    context.emit(Add2(d, c0, c1))
    return d


@arm_isa.pattern(
    'reg', 'ADDI32(CONSTI32, reg)', size=4,
    condition=lambda t: t.children[0].value in range(256))
def pattern_add32_2(context, tree, c0):
    d = context.new_reg(ArmRegister)
    c1 = tree.children[0].value
    context.emit(Add2(d, c0, c1))
    return d


@arm_isa.pattern('reg', 'SUBI32(reg, reg)', size=4)
def pattern_sub32(context, tree, c0, c1):
    d = context.new_reg(ArmRegister)
    context.emit(Sub1(d, c0, c1, NoShift()))
    return d


@arm_isa.pattern('reg', 'SUBI8(reg, reg)', size=4)
def pattern_sub8(context, tree, c0, c1):
    # TODO: temporary fix this with an 32 bits sub
    d = context.new_reg(ArmRegister)
    context.emit(Sub1(d, c0, c1, NoShift()))
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


@arm_isa.pattern('reg', 'CALL', size=10)
def pattern_call(context, tree):
    return context.gen_call(tree.value)


@arm_isa.pattern('reg', 'ANDI32(reg, reg)', size=4)
def pattern_and(context, tree, c0, c1):
    d = context.new_reg(ArmRegister)
    context.emit(And1(d, c0, c1, NoShift()))
    return d


@arm_isa.pattern('reg', 'ORI32(reg, reg)', size=4)
def pattern_or32(context, tree, c0, c1):
    d = context.new_reg(ArmRegister)
    context.emit(Orr1(d, c0, c1, NoShift()))
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
    context.gen_call(('__sdiv', [i32, i32], i32, [c0, c1], d))
    return d


@arm_isa.pattern('reg', 'REMI32(reg, reg)')
def pattern_rem32(context, tree, c0, c1):
    # Implement remainder as a combo of div and mls (multiply substract)
    d = context.new_reg(ArmRegister)
    context.gen_call(('__sdiv', [i32, i32], i32, [c0, c1], d))
    d2 = context.new_reg(ArmRegister)
    context.emit(Mls(d2, d, c1, c0))
    return d2


@arm_isa.pattern('reg', 'XORI32(reg, reg)', size=4)
def pattern_xor32(context, tree, c0, c1):
    d = context.new_reg(ArmRegister)
    context.emit(Eor1(d, c0, c1, NoShift()))
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
