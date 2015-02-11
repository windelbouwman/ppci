
from ..basetarget import Instruction, Isa
from ...bitfun import encode_imm32
from .registers import ArmRegister
from ..token import Token, u32, u8, bit_range
from ..instructionselector import InstructionSelector, pattern
from ...irmach import AbstractInstruction


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
    args = [('v', int)]
    syntax = ['dcd', 0]

    def encode(self):
        self.token[0:32] = self.v
        return self.token.encode()


class Dcd2(ArmInstruction):
    args = [('v', str)]
    syntax = ['dcd', '=', 0]

    def encode(self):
        self.token[0:32] = 0
        return self.token.encode()

    def relocations(self):
        return [(self.v, 'absaddr32')]


class Db(ArmInstruction):
    tokens = [ByteToken]
    args = [('v', int)]
    syntax = ['db', 0]

    def encode(self):
        assert self.v < 256
        self.token[0:8] = self.v
        return self.token.encode()


class Ds(ArmInstruction):
    tokens = []
    args = [('v', int)]
    syntax = ['ds', 0]

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
    args = [('reg', ArmRegister), ('imm', int)]
    syntax = ['mov', 0, ',', 1]

    def encode(self):
        self.token[0:12] = encode_imm32(self.imm)
        self.token.Rd = self.reg.num
        self.token[16:20] = 0
        self.token[20] = 0  # Set flags
        self.token[21:28] = 0b0011101
        self.token.cond = AL
        return self.token.encode()

    @staticmethod
    def from_im(im):
        return Mov1(im.dst[0], im.others[0])


class Mov2(ArmInstruction):
    args = [('rd', ArmRegister), ('rm', ArmRegister)]
    syntax = ['mov', 0, ',', 1]
    # bindings = [Binding(0:4, Arg), ()]

    def encode(self):
        self.token[0:4] = self.rm.num
        self.token[4:12] = 0
        self.token[12:16] = self.rd.num
        self.token[16:20] = 0
        self.token.S = 0
        self.token[21:28] = 0xD
        self.token.cond = AL
        return self.token.encode()

    @staticmethod
    def from_im(im):
        return Mov2(im.dst[0], im.src[0])


def Cmp(*args):
    if len(args) == 2:
        if isinstance(args[1], int):
            return Cmp1(*args)
        elif isinstance(args[1], ArmRegister):
            return Cmp2(*args)
    raise Exception()


class Cmp1(ArmInstruction):
    """ CMP Rn, imm """
    args = [('reg', ArmRegister), ('imm', int)]
    syntax = ['cmp', 0, ',', 1]

    def encode(self):
        self.token[0:12] = encode_imm32(self.imm)
        self.token.Rn = self.reg.num
        self.token[20:28] = 0b00110101
        self.token.cond = AL
        return self.token.encode()


class Cmp2(ArmInstruction):
    """ CMP Rn, Rm """
    args = [('rn', ArmRegister), ('rm', ArmRegister)]
    syntax = ['cmp', 0, ',', 1]

    def encode(self):
        self.token.Rn = self.rn.num
        self.token.Rm = self.rm.num
        self.token[7:16] = 0
        self.token[20:28] = 0b10101
        self.token.cond = AL
        return self.token.encode()

    @staticmethod
    def from_im(im):
        return Cmp2(im.src[0], im.src[1])


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
    args = [('rd', ArmRegister), ('rn', ArmRegister), ('rm', ArmRegister)]
    syntax = ['mul', 0, ',', 1, ',', 2]

    def encode(self):
        self.token[0:4] = self.rn.num
        self.token[4:8] = 0b1001
        self.token[8:12] = self.rm.num
        self.token[16:20] = self.rd.num
        self.token.S = 0
        self.token.cond = AL
        return self.token.encode()

    @staticmethod
    def from_im(im):
        return Mul1(im.dst[0], im.src[0], im.src[1])


class OpRegRegReg(ArmInstruction):
    """ add rd, rn, rm """
    args = [('rd', ArmRegister), ('rn', ArmRegister), ('rm', ArmRegister)]

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


class Add1(OpRegRegReg):
    syntax = ['add', 0, ',', 1, ',', 2]
    opcode = 0b0000100

    @staticmethod
    def from_im(im):
        return Add1(im.dst[0], im.src[0], im.src[1])


class Sub1(OpRegRegReg):
    syntax = ['sub', 0, ',', 1, ',', 2]
    opcode = 0b0000010

    @staticmethod
    def from_im(im):
        return Sub1(im.dst[0], im.src[0], im.src[1])


class Orr1(OpRegRegReg):
    syntax = ['orr', 0, ',', 1, ',', 2]
    opcode = 0b0001100

Orr = Orr1


class And1(OpRegRegReg):
    syntax = ['and', 0, ',', 1, ',', 2]
    opcode = 0b0000000

    @staticmethod
    def from_im(im):
        return And1(im.dst[0], im.src[0], im.src[1])

And = And1


class ShiftBase(ArmInstruction):
    """ ? rd, rn, rm """
    args = [('rd', ArmRegister), ('rn', ArmRegister), ('rm', ArmRegister)]

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
    syntax = ['lsr', 0, ',', 1, ',', 2]

    @staticmethod
    def from_im(im):
        return Lsr1(im.dst[0], im.src[0], im.src[1])


Lsr = Lsr1


class Lsl1(ShiftBase):
    opcode = 0b0001
    syntax = ['lsl', 0, ',', 1, ',', 2]

Lsl = Lsl1


class OpRegRegImm(ArmInstruction):
    """ add rd, rn, imm12 """
    args = [('rd', ArmRegister), ('rn', ArmRegister), ('imm', int)]

    def encode(self):
        self.token[0:12] = encode_imm32(self.imm)
        self.token.Rd = self.rd.num
        self.token.Rn = self.rn.num
        self.token.S = 0  # Set flags
        self.token[21:28] = self.opcode
        self.token.cond = AL
        return self.token.encode()


class Add2(OpRegRegImm):
    opcode = 0b0010100
    syntax = ['add', 0, ',', 1, ',', 2]

    @staticmethod
    def from_im(im):
        return Add2(im.dst[0], im.src[0], im.others[0])


class Sub2(OpRegRegImm):
    opcode = 0b0010010
    syntax = ['sub', 0, ',', 1, ',', 2]


# Branches:

class BranchBaseRoot(ArmInstruction):
    args = [('target', str)]

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
    syntax = ['bl', 0]


class B(BranchBase):
    cond = AL
    syntax = ['b', 0]


class Beq(BranchBase):
    cond = EQ
    syntax = ['beq', 0]


class Bgt(BranchBase):
    cond = GT
    syntax = ['bgt', 0]


class Bge(BranchBase):
    cond = GE
    syntax = ['bge', 0]


class Ble(BranchBase):
    cond = LE
    syntax = ['ble', 0]


class Blt(BranchBase):
    cond = LT
    syntax = ['blt', 0]


class Bne(BranchBase):
    cond = NE
    syntax = ['bne', 0]


def reg_list_to_mask(reg_list):
    mask = 0
    for reg in reg_list:
        mask |= (1 << reg.num)
    return mask


class Push(ArmInstruction):
    args = [('reg_list', RegisterSet)]
    syntax = ['push', 0]

    def encode(self):
        self.token.cond = AL
        self.token[16:28] = 0b100100101101
        self.token[0:16] = reg_list_to_mask(self.reg_list)
        return self.token.encode()


class Pop(ArmInstruction):
    args = [('reg_list', RegisterSet)]
    syntax = ['pop', 0]

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
    args = [('rt', ArmRegister), ('rn', ArmRegister), ('offset', int)]

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
    opcode = 0b010
    bit20 = 0
    bit22 = 0
    syntax = ['str', 0, ',', '[', 1, ',', 2, ']']

    @staticmethod
    def from_im(im):
        return Str1(im.src[1], im.src[0], im.others[0])


class Ldr1(LdrStrBase):
    opcode = 0b010
    bit20 = 1
    bit22 = 0
    syntax = ['ldr', 0, ',', '[', 1, ',', 2, ']']

    @staticmethod
    def from_im(im):
        return Ldr1(im.dst[0], im.src[0], im.others[0])


class Strb(LdrStrBase):
    """ ldrb rt, [rn, offset] # Store byte at address """
    opcode = 0b010
    bit20 = 0
    bit22 = 1
    syntax = ['strb', 0, ',', '[', 1, ',', 2, ']']

    @staticmethod
    def from_im(im):
        return Strb(im.src[1], im.src[0], im.others[0])


class Ldrb(LdrStrBase):
    """ ldrb rt, [rn, offset] """
    opcode = 0b010
    bit20 = 1
    bit22 = 1
    syntax = ['ldrb', 0, ',', '[', 1, ',', 2, ']']

    @staticmethod
    def from_im(im):
        return Ldrb(im.dst[0], im.src[0], im.others[0])


class Adr(ArmInstruction):
    args = [('rd', ArmRegister), ('label', str)]
    syntax = ['adr', 0, ',', 1]

    def relocations(self):
        return [(self.label, 'adr_imm12')]

    def encode(self):
        self.token.cond = AL
        self.token[0:12] = 0  # Filled by linker
        self.token[12:16] = self.rd.num
        self.token[16:20] = 0b1111
        self.token[25] = 1
        return self.token.encode()

    @staticmethod
    def from_im(im):
        return Adr(im.dst[0], im.others[0])


class Ldr3(ArmInstruction):
    """ Load PC relative constant value
        LDR rt, label
        encoding A1
    """
    args = [('rt', ArmRegister), ('label', str)]
    syntax = ['ldr', 0, ',', 1]

    def relocations(self):
        return [(self.label, 'ldr_imm12')]

    def encode(self):
        self.token.cond = AL
        self.token[0:12] = 0  # Filled by linker
        self.token[12:16] = self.rt.num
        self.token[16:23] = 0b0011111
        self.token[24:28] = 0b0101
        return self.token.encode()

    @staticmethod
    def from_im(im):
        return Ldr3(im.dst[0], im.others[0])


class McrBase(ArmInstruction):
    """ Mov arm register to coprocessor register """
    args = [('coproc', int), ('opc1', int), ('rt', ArmRegister), ('crn', int),
            ('crm', int), ('opc2', int)]

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
    b20 = 0
    syntax = ['mcr', 0, ',', 1, ',', 2, ',', 3, ',', 4, ',', 5]


class Mrc(McrBase):
    b20 = 1
    syntax = ['mrc', 0, ',', 1, ',', 2, ',', 3, ',', 4, ',', 5]


class ArmInstructionSelector(InstructionSelector):
    """ Instruction selector for the arm architecture """

    @pattern('stm', 'MOVI32(MEMI32(reg), reg)', cost=2)
    def P1(self, tree, c0, c1):
        self.emit(Str1, others=[0], src=[c0, c1])

    @pattern('stm', 'MOVI8(MEMI8(reg), reg)', cost=2)
    def P2(self, tree, c0, c1):
        self.emit(Strb, others=[0], src=[c0, c1])

    @pattern('stm', 'MOVI32(REGI32, reg)', cost=2)
    def P3(self, tree, c0):
        self.move(tree.children[0].value, c0)

    # stm: MOVI32(MEMI32(ADDI32(reg, cn)), reg) 2 'self.emit(Str1, others=[c1], src=[c0, c2])'

    @pattern('stm', 'JMP', cost=2)
    def P5(self, tree):
        label, tgt = tree.value
        self.emit(B(label), jumps=[tgt])

    @pattern('reg', 'REGI32', cost=0)
    def P6(self, tree):
        return tree.value

    @pattern('reg', 'CONSTI32', cost=4)
    def P7(self, tree):
        d = self.newTmp()
        ln = self.frame.add_constant(tree.value)
        self.emit(Ldr3, dst=[d], others=[ln])
        return d

    @pattern('stm', 'CJMP(reg, reg)', cost=2)
    def P8(self, tree, c0, c1):
        op, yes_label, yes_tgt, no_label, no_tgt = tree.value
        opnames = {"<": Blt, ">": Bgt, "==": Beq, "!=": Bne, ">=": Bge}
        Bop = opnames[op]
        self.emit(Cmp2, src=[c0, c1])
        jmp_ins = AbstractInstruction(B(no_label), jumps=[no_tgt])
        self.emit(Bop(yes_label), jumps=[yes_tgt, jmp_ins])
        self.emit(jmp_ins)

    @pattern('reg', 'ADDI32(reg, reg)', cost=2)
    def P9(self, tree, c0, c1):
        d = self.newTmp()
        self.emit(Add1, dst=[d], src=[c0, c1])
        return d

    @pattern('reg', 'ADDI8(reg, reg)', cost=2)
    def P9_2(self, tree, c0, c1):
        d = self.newTmp()
        self.emit(Add1, dst=[d], src=[c0, c1])
        return d

    #reg: ADDI32(reg, cn)          2 'return tree.children[1].value < 256' 'd = self.newTmp(); self.emit(Add2, dst=[d], src=[c0], others=[c1]); return d'
    #reg: ADDI32(cn, reg)          2 'return tree.children[0].value < 256' 'd = self.newTmp(); self.emit(Add2, dst=[d], src=[c1], others=[c0]); return d'

    @pattern('reg', 'SUBI32(reg, reg)', cost=2)
    def P12(self, tree, c0, c1):
        d = self.newTmp()
        self.emit(Sub1, dst=[d], src=[c0, c1])
        return d

    @pattern('reg', 'SUBI8(reg, reg)', cost=2)
    def P12_2(self, tree, c0, c1):
        # TODO: temporary fix this with an 32 bits sub
        d = self.newTmp()
        self.emit(Sub1, dst=[d], src=[c0, c1])
        return d

    @pattern('reg', 'GLOBALADDRESS', cost=4)
    def P13(self, tree):
        d = self.newTmp()
        ln = self.frame.add_constant(tree.value)
        self.emit(Ldr3, dst=[d], others=[ln])
        return d

    @pattern('reg', 'MEMI8(reg)', cost=2)
    def P14(self, tree, c0):
        d = self.newTmp()
        self.emit(Ldrb, dst=[d], src=[c0], others=[0])
        return d

    @pattern('reg', 'MEMI32(reg)', cost=2)
    def P15(self, tree, c0):
        d = self.newTmp()
        self.emit(Ldr1, dst=[d], src=[c0], others=[0])
        return d

    @pattern('reg', 'CALL', cost=2)
    def P16(self, tree):
        return self.munchCall(tree.value)

    @pattern('stm', 'CALL', cost=2)
    def P17(self, tree):
        self.munchCall(tree.value)

    @pattern('reg', 'ADR(CONSTDATA)', cost=2)
    def P18(self, tree):
        d = self.newTmp()
        ln = self.frame.add_constant(tree.children[0].value)
        self.emit(Adr, dst=[d], others=[ln])
        return d

    @pattern('reg', 'ANDI32(reg, reg)', cost=2)
    def P19(self, tree, c0, c1):
        d = self.newTmp()
        self.emit(And1, dst=[d], src=[c0, c1])
        return d

    @pattern('reg', 'SHRI32(reg, reg)', cost=2)
    def P20(self, tree, c0, c1):
        d = self.newTmp()
        self.emit(Lsr1, dst=[d], src=[c0, c1])
        return d

    @pattern('reg', 'MULI32(reg, reg)', cost=10)
    def P21(self, tree, c0, c1):
        d = self.newTmp()
        self.emit(Mul1, dst=[d], src=[c0, c1])
        return d

# reg: MEMI32(ADDI32(reg, cn))  2 'd = self.newTmp(); self.emit(Ldr1, dst=[d], src=[c0], others=[c1]); return d'
# cn: CONSTI32                  0 'return tree.value'
# reg: CONSTI32                 2 'return (type(tree.value) is int) and (tree.value < 256)' 'd = self.newTmp(); self.emit(Mov1, dst=[d], others=[tree.value]); return d'
