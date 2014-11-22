
from ..basetarget import Instruction, LabelAddress
from ...bitfun import encode_imm32
from .registers import R0, SP, ArmRegister
from ..token import Token, u32, bit_range


class Isa:
    def __init__(self):
        self.lower_funcs = {}

isa = Isa()

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

# Patterns:

# Condition patterns:
EQ, NE, CS, CC, MI, PL, VS, VC, HI, LS, GE, LT, GT, LE, AL = range(15)


# Instructions:

class ArmInstruction(Instruction):
    tokens = [ArmToken]
    isa = isa

    def __init__(self):
        self.token = ArmToken()


class ConstantData(ArmInstruction):
    def __init__(self, v):
        super().__init__()
        assert isinstance(v, int)
        self.v = v


class Dcd(ArmInstruction):
    def __init__(self, v):
        super().__init__()
        assert isinstance(v, int) or isinstance(v, LabelAddress)
        self.v = v

    def encode(self):
        if type(self.v) is int:
            self.token[0:32] = self.v
        else:
            self.token[0:32] = 0
        return self.token.encode()

    def relocations(self):
        if type(self.v) is LabelAddress:
            return [(self.v.name, 'absaddr32')]
        return []

    def __repr__(self):
        if type(self.v) is int:
            return 'DCD {}'.format(hex(self.v))
        else:
            return 'DCD ={}'.format(self.v.name)


class Db(ConstantData):
    def encode(self):
        assert self.v < 256
        return bytes([self.v])

    def __repr__(self):
        return 'DB {}'.format(hex(self.v))


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
        self.token.cond = 0xE  # Always!
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
        self.token.S = 0 # Set flags
        self.token[21:28] = self.opcode
        self.token.cond = 0xE # Always!
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
    def __init__(self, target):
        super().__init__()
        self.target = target

    def encode(self):
        self.token.cond = self.cond
        self.token[24:28] = self.opcode
        return self.token.encode()

    def relocations(self):
        return [(self.target, 'b_imm24')]

    def __repr__(self):
        mnemonic = self.__class__.__name__
        return '{} {}'.format(mnemonic, self.target)


class BranchBase(BranchBaseRoot):
    opcode = 0b1010


class BranchLinkBase(BranchBaseRoot):
    opcode = 0b1011


class Bl(BranchLinkBase):
    cond = AL


class B(BranchBase):
    cond = AL


class Beq(BranchBase):
    cond = EQ


class Bgt(BranchBase):
    cond = GT


class Bge(BranchBase):
    cond = GE


class Ble(BranchBase):
    cond = LE


class Blt(BranchBase):
    cond = LT


class Bne(BranchBase):
    cond = NE

# Memory:

def reg_list_to_mask(reg_list):
    mask = 0
    for reg in reg_list:
        mask |= (1 << reg.num)
    return mask


class Push(ArmInstruction):
    def __init__(self, register_set):
        super().__init__()
        self.reg_list = register_set

    def encode(self):
        self.token.cond = AL
        self.token[16:28] = 0b100100101101
        reg_list = 0
        self.token[0:16] = reg_list_to_mask(self.reg_list)
        return self.token.encode()

    def __repr__(self):
        return 'PUSH {}'.format(self.reg_list)


class Pop(ArmInstruction):
    def __init__(self, register_set):
        super().__init__()
        self.reg_list = register_set

    def encode(self):
        self.token.cond = AL
        self.token[16:28] = 0b100010111101
        self.token[0:16] = reg_list_to_mask(self.reg_list)
        return self.token.encode()

    def __repr__(self):
        return 'POP {}'.format(self.reg_list)


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
    lit_lbl = add_lit(LabelAddress(lab))
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

    def __repr__(self):
        return '{} {}, [{}, {}]'.format(self.mnemonic, self.rt, self.rn,
                hex(self.offset))


class Str1(LdrStrBase):
    opcode = 0b010
    bit20 = 0
    mnemonic = 'STR'

    @staticmethod
    def from_im(im):
        return Str1(im.src[1], im.src[0], im.others[0])


class Ldr1(LdrStrBase):
    opcode = 0b010
    bit20 = 1
    mnemonic = 'LDR'

    @staticmethod
    def from_im(im):
        return Ldr1(im.dst[0], im.src[0], im.others[0])


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
    def __init__(self, coproc, opc1, rt, crn, crm, opc2):
        super().__init__()
        self.coproc = coproc
        self.opc1 = opc1
        self.rt = rt
        self.crn = crn
        self.crm = crm
        self.opc2 = opc2

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


class Mrc(McrBase):
    b20 = 1
