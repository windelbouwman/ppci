"""
    Definitions of arm instructions.
"""
from .. import Instruction, Isa
from .. import register_argument, value_argument
from ...bitfun import encode_imm32
from .registers import ArmRegister
from ..token import Token, u32, u8, bit_range
from ..instructionselector import InstructionSelector, pattern


class RegisterSet(set):
    pass


isa = Isa()
isa.typ2nt[ArmRegister] = 'reg'
isa.typ2nt[int] = 'imm32'
isa.typ2nt[str] = 'strrr'
isa.typ2nt[RegisterSet] = 'reg_list'


# Tokens:
class ArmToken(Token):
    def __init__(self):
        super().__init__(32)

    cond = bit_range(28, 32)
    S = bit_range(20, 21)
    Rd = bit_range(12, 16)
    Rn = bit_range(16, 20)
    Rm = bit_range(0, 4)

    def encode(self):
        return u32(self.bit_value)


class ByteToken(Token):
    def __init__(self):
        super().__init__(8)

    def encode(self):
        return u8(self.bit_value)

# Patterns:

# Condition patterns:
EQ, NE, CS, CC, MI, PL, VS, VC, HI, LS, GE, LT, GT, LE, AL = range(15)


# Instructions:

class ArmInstruction(Instruction):
    tokens = [ArmToken]
    isa = isa


def Dcd(v):
    if type(v) is int:
        return Dcd1(v)
    elif type(v) is str:
        return Dcd2(v)
    else:
        raise NotImplementedError()


class Dcd1(ArmInstruction):
    v = register_argument('v', int)
    syntax = ['dcd', v]

    def encode(self):
        self.token[0:32] = self.v
        return self.token.encode()


class Dcd2(ArmInstruction):
    v = register_argument('v', str)
    syntax = ['dcd', '=', v]

    def encode(self):
        self.token[0:32] = 0
        return self.token.encode()

    def relocations(self):
        return [(self.v, 'absaddr32')]


class Db(ArmInstruction):
    tokens = [ByteToken]
    v = register_argument('v', int)
    syntax = ['db', v]

    def encode(self):
        assert self.v < 256
        self.token[0:8] = self.v
        return self.token.encode()


class Ds(ArmInstruction):
    """ Reserve x amount of zero bytes (same as resb in nasm) """
    tokens = []
    v = register_argument('v', int)
    syntax = ['ds', v]

    def encode(self):
        return bytes([0] * self.v)


def Mov(*args):
    if len(args) == 2:
        if isinstance(args[1], int):
            return Mov1(*args)
        elif isinstance(args[1], ArmRegister):
            return Mov2(*args)
    raise Exception()


class Mov1(ArmInstruction):
    """ Mov Rd, imm16 """
    rd = register_argument('rd', ArmRegister, write=True)
    imm = register_argument('imm', int)
    syntax = ['mov', rd, ',', imm]

    def encode(self):
        self.token[0:12] = encode_imm32(self.imm)
        self.token.Rd = self.rd.num
        self.token[16:20] = 0
        self.token[20] = 0  # Set flags
        self.token[21:28] = 0b0011101
        self.token.cond = AL
        return self.token.encode()


class Mov2(ArmInstruction):
    rd = register_argument('rd', ArmRegister, write=True)
    rm = register_argument('rm', ArmRegister, read=True)
    syntax = ['mov', rd, ',', rm]

    def encode(self):
        self.token[0:4] = self.rm.num
        self.token[4:12] = 0
        self.token[12:16] = self.rd.num
        self.token[16:20] = 0
        self.token.S = 0
        self.token[21:28] = 0xD
        self.token.cond = AL
        return self.token.encode()


def Cmp(*args):
    if len(args) == 2:
        if isinstance(args[1], int):
            return Cmp1(*args)
        elif isinstance(args[1], ArmRegister):
            return Cmp2(*args)
    raise Exception()


class Cmp1(ArmInstruction):
    """ CMP Rn, imm """
    reg = register_argument('reg', ArmRegister, read=True)
    imm = value_argument('imm')
    syntax = ['cmp', reg, ',', imm]

    def encode(self):
        self.token[0:12] = encode_imm32(self.imm)
        self.token.Rn = self.reg.num
        self.token[20:28] = 0b00110101
        self.token.cond = AL
        return self.token.encode()


class Cmp2(ArmInstruction):
    """ CMP Rn, Rm """
    rn = register_argument('rn', ArmRegister, read=True)
    rm = register_argument('rm', ArmRegister, read=True)
    syntax = ['cmp', rn, ',', rm]

    def encode(self):
        self.token.Rn = self.rn.num
        self.token.Rm = self.rm.num
        self.token[7:16] = 0
        self.token[20:28] = 0b10101
        self.token.cond = AL
        return self.token.encode()


def Add(*args):
    if len(args) == 3 and isinstance(args[0], ArmRegister) and \
            isinstance(args[1], ArmRegister):
        if isinstance(args[2], ArmRegister):
            return Add1(args[0], args[1], args[2])
        elif isinstance(args[2], int):
            return Add2(args[0], args[1], args[2])
    raise Exception()


def Sub(*args):
    if len(args) == 3 and isinstance(args[0], ArmRegister) and \
            isinstance(args[1], ArmRegister):
        if isinstance(args[2], ArmRegister):
            return Sub1(args[0], args[1], args[2])
        elif isinstance(args[2], int):
            return Sub2(args[0], args[1], args[2])
    raise Exception()


def Mul(*args):
    return Mul1(args[0], args[1], args[2])


class Mul1(ArmInstruction):
    rd = register_argument('rd', ArmRegister, write=True)
    rn = register_argument('rn', ArmRegister, read=True)
    rm = register_argument('rm', ArmRegister, read=True)
    syntax = ['mul', rd, ',', rn, ',', rm]

    def encode(self):
        self.token[0:4] = self.rn.num
        self.token[4:8] = 0b1001
        self.token[8:12] = self.rm.num
        self.token[16:20] = self.rd.num
        self.token.S = 0
        self.token.cond = AL
        return self.token.encode()


class Sdiv(ArmInstruction):
    """ Encoding A1
        rd = rn / rm
    """
    rd = register_argument('rd', ArmRegister, write=True)
    rn = register_argument('rn', ArmRegister, read=True)
    rm = register_argument('rm', ArmRegister, read=True)
    syntax = ['sdiv', rd, ',', rn, ',', rm]

    def encode(self):
        self.token[0:4] = self.rn.num
        self.token[4:8] = 0b0001
        self.token[8:12] = self.rm.num
        self.token[12:16] = 0b1111
        self.token[16:20] = self.rd.num
        self.token[20:28] = 0b1110001
        self.token.cond = AL
        return self.token.encode()


class Udiv(ArmInstruction):
    """ Encoding A1
        rd = rn / rm
    """
    rd = register_argument('rd', ArmRegister, write=True)
    rn = register_argument('rn', ArmRegister, read=True)
    rm = register_argument('rm', ArmRegister, read=True)
    syntax = ['udiv', rd, ',', rn, ',', rm]

    def encode(self):
        self.token[0:4] = self.rn.num
        self.token[4:8] = 0b0001
        self.token[8:12] = self.rm.num
        self.token[12:16] = 0b1111
        self.token[16:20] = self.rd.num
        self.token[20:28] = 0b1110011
        self.token.cond = AL
        return self.token.encode()


class Mls(ArmInstruction):
    """ Multiply substract
        Semantics:
        rd = ra - rn * rm
    """
    rd = register_argument('rd', ArmRegister, write=True)
    rn = register_argument('rn', ArmRegister, read=True)
    rm = register_argument('rm', ArmRegister, read=True)
    ra = register_argument('ra', ArmRegister, read=True)
    syntax = ['mls', rd, ',', rn, ',', rm, ',', ra]

    def encode(self):
        self.token[0:4] = self.rn.num
        self.token[4:8] = 0b1001
        self.token[8:12] = self.rm.num
        self.token[12:16] = self.ra.num
        self.token[16:20] = self.rd.num
        self.token[20:28] = 0b00000110
        self.token.cond = AL
        return self.token.encode()


class OpRegRegReg(ArmInstruction):
    """ add rd, rn, rm """
    def encode(self):
        self.token[0:4] = self.rm.num
        self.token[4] = 0
        self.token[5:7] = 0
        self.token[7:12] = 0  # Shift
        self.token.Rd = self.rd.num
        self.token.Rn = self.rn.num
        self.token.S = 0  # Set flags
        self.token[21:28] = self.opcode
        self.token.cond = AL  # Always!
        return self.token.encode()


def make_regregreg(mnemonic, opcode):
    rd = register_argument('rd', ArmRegister, write=True)
    rn = register_argument('rn', ArmRegister, read=True)
    rm = register_argument('rm', ArmRegister, read=True)
    syntax = [mnemonic, rd, ',', rn, ',', rm]
    members = {
        'syntax': syntax, 'rd': rd, 'rn': rn, 'rm': rm, 'opcode': opcode}
    return type(mnemonic + '_ins', (OpRegRegReg,), members)

Add1 = make_regregreg('add', 0b0000100)
Sub1 = make_regregreg('sub', 0b0000010)
Orr1 = make_regregreg('orr', 0b0001100)
Orr = Orr1
And1 = make_regregreg('and', 0b0000000)
And = And1
Eor1 = make_regregreg('eor', 0b0000001)


class ShiftBase(ArmInstruction):
    """ ? rd, rn, rm """
    rd = register_argument('rd', ArmRegister, write=True)
    rn = register_argument('rn', ArmRegister, read=True)
    rm = register_argument('rm', ArmRegister, read=True)

    def encode(self):
        self.token[0:4] = self.rn.num
        self.token[4:8] = self.opcode
        self.token[8:12] = self.rm.num
        self.token[12:16] = self.rd.num
        self.token.S = 0  # Set flags
        self.token[21:28] = 0b1101
        self.token.cond = AL
        return self.token.encode()


class Lsr1(ShiftBase):
    opcode = 0b0011
    syntax = ['lsr', ShiftBase.rd, ',', ShiftBase.rn, ',', ShiftBase.rm]


Lsr = Lsr1


class Lsl1(ShiftBase):
    opcode = 0b0001
    syntax = ['lsl', ShiftBase.rd, ',', ShiftBase.rn, ',', ShiftBase.rm]


Lsl = Lsl1


class OpRegRegImm(ArmInstruction):
    """ add rd, rn, imm12 """
    def encode(self):
        self.token[0:12] = encode_imm32(self.imm)
        self.token.Rd = self.rd.num
        self.token.Rn = self.rn.num
        self.token.S = 0  # Set flags
        self.token[21:28] = self.opcode
        self.token.cond = AL
        return self.token.encode()


def make_regregimm(mnemonic, opcode):
    rd = register_argument('rd', ArmRegister, write=True)
    rn = register_argument('rn', ArmRegister, read=True)
    imm = register_argument('imm', int)
    syntax = [mnemonic, rd, ',', rn, ',', imm]
    members = {
        'syntax': syntax, 'rd': rd, 'rn': rn, 'imm': imm, 'opcode': opcode}
    return type(mnemonic + '_ins', (OpRegRegImm,), members)

Add2 = make_regregimm('add', 0b0010100)
Sub2 = make_regregimm('sub', 0b0010010)


# Branches:

class BranchBaseRoot(ArmInstruction):
    target = register_argument('target', str)

    def encode(self):
        self.token.cond = self.cond
        self.token[24:28] = self.opcode
        return self.token.encode()

    def relocations(self):
        return [(self.target, 'b_imm24')]


class BranchBase(BranchBaseRoot):
    opcode = 0b1010


class BranchLinkBase(BranchBaseRoot):
    opcode = 0b1011


class Bl(BranchLinkBase):
    cond = AL
    syntax = ['bl', BranchBaseRoot.target]


def make_branch(mnemonic, cond):
    target = register_argument('target', str)
    syntax = [mnemonic, target]
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


def reg_list_to_mask(reg_list):
    mask = 0
    for reg in reg_list:
        mask |= (1 << reg.num)
    return mask


class Push(ArmInstruction):
    reg_list = register_argument('reg_list', RegisterSet)
    syntax = ['push', reg_list]

    def encode(self):
        self.token.cond = AL
        self.token[16:28] = 0b100100101101
        self.token[0:16] = reg_list_to_mask(self.reg_list)
        return self.token.encode()


class Pop(ArmInstruction):
    reg_list = register_argument('reg_list', RegisterSet)
    syntax = ['pop', reg_list]

    def encode(self):
        self.token.cond = AL
        self.token[16:28] = 0b100010111101
        self.token[0:16] = reg_list_to_mask(self.reg_list)
        return self.token.encode()


def Ldr(*args):
    """ Convenience function that creates the correct instruction """
    if len(args) == 3:
        if isinstance(args[1], ArmRegister):
            return Ldr1(*args)
    elif len(args) == 2:
        if isinstance(args[1], ArmRegister):
            return Ldr1(args[0], args[1], 0)
        elif isinstance(args[1], str):
            return Ldr3(*args)
    raise Exception()


def LdrPseudo(rt, lab, add_lit):
    """ Ldr rt, =lab ==> ldr rt, [pc, offset in litpool] ... dcd lab """
    lit_lbl = add_lit(lab)
    return Ldr(rt, lit_lbl)


def Str(*args):
    if len(args) == 3 and isinstance(args[1], ArmRegister):
        return Str1(*args)
    elif len(args) == 2 and isinstance(args[1], ArmRegister):
        return Str1(args[0], args[1], 0)
    raise Exception()


class LdrStrBase(ArmInstruction):
    rn = register_argument('rn', ArmRegister, read=True)
    offset = register_argument('offset', int)

    def encode(self):
        self.token.cond = AL
        self.token.Rn = self.rn.num
        self.token[25:28] = self.opcode
        self.token[22] = self.bit22
        self.token[20] = self.bit20
        self.token[12:16] = self.rt.num
        self.token[24] = 1  # Index
        if self.offset >= 0:
            self.token[23] = 1  # U == 1 'add'
            self.token[0:12] = self.offset
        else:
            self.token[23] = 0
            self.token[0:12] = -self.offset
        return self.token.encode()


class Str1(LdrStrBase):
    rt = register_argument('rt', ArmRegister, read=True)
    opcode = 0b010
    bit20 = 0
    bit22 = 0
    syntax = [
        'str', rt, ',', '[', LdrStrBase.rn, ',',
        LdrStrBase.offset, ']']


class Ldr1(LdrStrBase):
    rt = register_argument('rt', ArmRegister, write=True)
    opcode = 0b010
    bit20 = 1
    bit22 = 0
    syntax = [
        'ldr', rt, ',', '[', LdrStrBase.rn, ',',
        LdrStrBase.offset, ']']


class Strb(LdrStrBase):
    """ ldrb rt, [rn, offset] # Store byte at address """
    rt = register_argument('rt', ArmRegister, read=True)
    opcode = 0b010
    bit20 = 0
    bit22 = 1
    syntax = [
        'strb', rt, ',', '[', LdrStrBase.rn, ',',
        LdrStrBase.offset, ']']


class Ldrb(LdrStrBase):
    """ ldrb rt, [rn, offset] """
    rt = register_argument('rt', ArmRegister, write=True)
    opcode = 0b010
    bit20 = 1
    bit22 = 1
    syntax = [
        'ldrb', rt, ',', '[', LdrStrBase.rn, ',',
        LdrStrBase.offset, ']']


class Adr(ArmInstruction):
    rd = register_argument('rd', ArmRegister, write=True)
    label = register_argument('label', str)
    syntax = ['adr', rd, ',', label]

    def relocations(self):
        return [(self.label, 'adr_imm12')]

    def encode(self):
        self.token.cond = AL
        self.token[0:12] = 0  # Filled by linker
        self.token[12:16] = self.rd.num
        self.token[16:20] = 0b1111
        self.token[25] = 1
        return self.token.encode()


class Ldr3(ArmInstruction):
    """ Load PC relative constant value
        LDR rt, label
        encoding A1
    """
    rt = register_argument('rt', ArmRegister, write=True)
    label = register_argument('label', str)
    syntax = ['ldr', rt, ',', label]

    def relocations(self):
        return [(self.label, 'ldr_imm12')]

    def encode(self):
        self.token.cond = AL
        self.token[0:12] = 0  # Filled by linker
        self.token[12:16] = self.rt.num
        self.token[16:23] = 0b0011111
        self.token[24:28] = 0b0101
        return self.token.encode()


class McrBase(ArmInstruction):
    """ Mov arm register to coprocessor register """
    def encode(self):
        self.token[0:4] = self.crm
        self.token[4] = 1
        self.token[5:8] = self.opc2
        self.token[8:12] = self.coproc
        self.token[12:16] = self.rt.num
        self.token[16:20] = self.crn
        self.token[20] = self.b20
        self.token[21:24] = self.opc1
        self.token[24:28] = 0b1110
        self.token.cond = AL
        return self.token.encode()


class Mcr(McrBase):
    coproc = register_argument('coproc', int)
    opc1 = register_argument('opc1', int)
    rt = register_argument('rt', ArmRegister, read=True)
    crn = register_argument('crn', int)
    crm = register_argument('crm', int)
    opc2 = register_argument('opc2', int)
    b20 = 0
    syntax = ['mcr', coproc, ',', opc1, ',', rt, ',', crn, ',', crm, ',', opc2]


class Mrc(McrBase):
    coproc = register_argument('coproc', int)
    opc1 = register_argument('opc1', int)
    rt = register_argument('rt', ArmRegister, write=True)
    crn = register_argument('crn', int)
    crm = register_argument('crm', int)
    opc2 = register_argument('opc2', int)
    b20 = 1
    syntax = ['mrc', coproc, ',', opc1, ',', rt, ',', crn, ',', crm, ',', opc2]


class ArmInstructionSelector(InstructionSelector):
    """ Instruction selector for the arm architecture """

    @pattern('stm', 'MOVI32(MEMI32(reg), reg)', cost=2)
    def P1(self, tree, c0, c1):
        self.emit(Str1(c1, c0, 0))

    @pattern(
        'stm', 'MOVI32(MEMI32(ADDI32(reg, CONSTI32)), reg)',
        cost=2,
        condition=lambda t: t.children[0].children[0].children[1].value < 256)
    def P1_b(self, tree, c0, c1):
        # TODO: something strange here: when enabeling this rule, programs
        # compile correctly...
        offset = tree.children[0].children[0].children[1].value
        self.emit(Str1(c1, c0, offset))

    @pattern('stm', 'MOVI8(MEMI8(reg), reg)', cost=2)
    def P2(self, tree, c0, c1):
        self.emit(Strb(c1, c0, 0))

    @pattern('stm', 'MOVI32(REGI32, reg)', cost=2)
    def P3(self, tree, c0):
        self.move(tree.children[0].value, c0)

    @pattern('stm', 'JMP', cost=2)
    def P5(self, tree):
        label, tgt = tree.value
        self.emit(B(label, jumps=[tgt]))

    @pattern('reg', 'REGI32', cost=0)
    def P6(self, tree):
        return tree.value

    @pattern('reg', 'CONSTI32', cost=4)
    def P7(self, tree):
        d = self.newTmp()
        ln = self.frame.add_constant(tree.value)
        self.emit(Ldr3(d, ln))
        return d

    @pattern('reg', 'CONSTI32', cost=2, condition=lambda t: t.value < 256)
    def P23(self, tree):
        d = self.newTmp()
        c0 = tree.value
        assert isinstance(c0, int)
        assert c0 < 256 and c0 >= 0
        self.emit(Mov1(d, c0))
        return d

    @pattern('stm', 'CJMP(reg, reg)', cost=2)
    def P8(self, tree, c0, c1):
        op, yes_label, yes_tgt, no_label, no_tgt = tree.value
        opnames = {"<": Blt, ">": Bgt, "==": Beq, "!=": Bne, ">=": Bge}
        Bop = opnames[op]
        self.emit(Cmp2(c0, c1))
        jmp_ins = B(no_label, jumps=[no_tgt])
        self.emit(Bop(yes_label, jumps=[yes_tgt, jmp_ins]))
        self.emit(jmp_ins)

    @pattern('reg', 'ADDI32(reg, reg)', cost=2)
    def P9(self, tree, c0, c1):
        d = self.newTmp()
        self.emit(Add1(d, c0, c1))
        return d

    @pattern('reg', 'ADDI8(reg, reg)', cost=2)
    def P9_2(self, tree, c0, c1):
        d = self.newTmp()
        self.emit(Add1(d, c0, c1))
        return d

    @pattern(
        'reg', 'ADDI32(reg, CONSTI32)', cost=2,
        condition=lambda t: t.children[1].value < 256)
    def P9_3a(self, tree, c0):
        d = self.newTmp()
        c1 = tree.children[1].value
        self.emit(Add2(d, c0, c1))
        return d

    @pattern(
        'reg', 'ADDI32(CONSTI32, reg)', cost=2,
        condition=lambda t: t.children[0].value < 256)
    def P9_3b(self, tree, c0):
        d = self.newTmp()
        c1 = tree.children[0].value
        self.emit(Add2(d, c0, c1))
        return d

    @pattern('reg', 'SUBI32(reg, reg)', cost=2)
    def P12(self, tree, c0, c1):
        d = self.newTmp()
        self.emit(Sub1(d, c0, c1))
        return d

    @pattern('reg', 'SUBI8(reg, reg)', cost=2)
    def P12_2(self, tree, c0, c1):
        # TODO: temporary fix this with an 32 bits sub
        d = self.newTmp()
        self.emit(Sub1(d, c0, c1))
        return d

    @pattern('reg', 'GLOBALADDRESS', cost=4)
    def P13(self, tree):
        d = self.newTmp()
        ln = self.frame.add_constant(tree.value)
        self.emit(Ldr3(d, ln))
        return d

    @pattern('reg', 'MEMI8(reg)', cost=2)
    def P14(self, tree, c0):
        d = self.newTmp()
        self.emit(Ldrb(d, c0, 0))
        return d

    @pattern('reg', 'MEMI32(reg)', cost=2)
    def P15(self, tree, c0):
        d = self.newTmp()
        self.emit(Ldr1(d, c0, 0))
        return d

    @pattern('reg', 'CALL', cost=2)
    def P16(self, tree):
        label, args, res_var = tree.value
        self.frame.gen_call(label, args, res_var)

    @pattern('stm', 'CALL', cost=2)
    def P17(self, tree):
        label, args, res_var = tree.value
        self.frame.gen_call(label, args, res_var)

    @pattern('reg', 'ADR(CONSTDATA)', cost=2)
    def P18(self, tree):
        d = self.newTmp()
        ln = self.frame.add_constant(tree.children[0].value)
        self.emit(Adr(d, ln))
        return d

    @pattern('reg', 'ANDI32(reg, reg)', cost=2)
    def P19(self, tree, c0, c1):
        d = self.newTmp()
        self.emit(And1(d, c0, c1))
        return d

    @pattern('reg', 'ORI32(reg, reg)', cost=2)
    def P19_b(self, tree, c0, c1):
        d = self.newTmp()
        self.emit(Orr1(d, c0, c1))
        return d

    @pattern('reg', 'SHRI32(reg, reg)', cost=2)
    def P20(self, tree, c0, c1):
        d = self.newTmp()
        self.emit(Lsr1(d, c0, c1))
        return d

    @pattern('reg', 'SHLI32(reg, reg)', cost=2)
    def P20_b(self, tree, c0, c1):
        d = self.newTmp()
        self.emit(Lsl1(d, c0, c1))
        return d

    @pattern('reg', 'MULI32(reg, reg)', cost=10)
    def P21(self, tree, c0, c1):
        d = self.newTmp()
        self.emit(Mul1(d, c0, c1))
        return d

    @pattern('reg', 'MEMI32(ADDI32(reg, CONSTI32))', cost=2)
    def P22(self, tree, c0):
        d = self.newTmp()
        c1 = tree.children[0].children[1].value
        assert isinstance(c1, int)
        self.emit(Ldr1(d, c0, c1))
        return d

    @pattern('reg', 'DIVI32(reg, reg)', cost=10)
    def P24_a(self, tree, c0, c1):
        d = self.newTmp()
        # Generate call into runtime lib function!
        self.frame.gen_call('__sdiv', [c0, c1], d)
        return d

    @pattern('reg', 'REMI32(reg, reg)', cost=10)
    def P24_b(self, tree, c0, c1):
        # Implement remainder as a combo of div and mls (multiply substract)
        d = self.newTmp()
        self.frame.gen_call('__sdiv', [c0, c1], d)
        d2 = self.newTmp()
        self.emit(Mls(d2, d, c1, c0))
        return d2

    @pattern('reg', 'XORI32(reg, reg)', cost=2)
    def P25(self, tree, c0, c1):
        d = self.newTmp()
        self.emit(Eor1(d, c0, c1))
        return d

# TODO: implement DIVI32 by library call.
# TODO: Do that here, or in irdag?


class MachineThatHasDivOps:
    @pattern('reg', 'DIVI32(reg, reg)', cost=10)
    def P23(self, tree, c0, c1):
        d = self.newTmp()
        self.emit(Udiv, dst=[d], src=[c0, c1])
        return d

    @pattern('reg', 'REMI32(reg, reg)', cost=10)
    def P24(self, tree, c0, c1):
        # Implement remainder as a combo of div and mls (multiply substract)
        d = self.newTmp()
        self.emit(Udiv, dst=[d], src=[c0, c1])
        d2 = self.newTmp()
        self.emit(Mls, dst=[d2], src=[d, c1, c0])
        return d2
