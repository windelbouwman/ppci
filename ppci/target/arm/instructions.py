
from ..basetarget import Instruction, LabelAddress
from ...bitfun import encode_imm32

from .token import ArmToken
from .registers import R0, SP, ArmRegister



# Instructions:

class ArmInstruction(Instruction):
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
    def __init__(self, reg, imm):
        super().__init__()
        assert type(imm) is int
        self.reg = reg
        self.imm = imm

    def encode(self):
        self.token[0:12] = encode_imm32(self.imm)
        self.token.Rd = self.reg.num
        self.token[16:20] = 0
        self.token[20] = 0  # Set flags
        self.token[21:28] = 0b0011101
        self.token.cond = AL
        return self.token.encode()

    def __repr__(self):
        return 'Mov {}, {}'.format(self.reg, self.imm)


class Mov2(ArmInstruction):
    def __init__(self, rd, rm):
        super().__init__()
        self.rd = rd
        self.rm = rm

    def encode(self):
        self.token[0:4] = self.rm.num
        self.token[4:12] = 0
        self.token[12:16] = self.rd.num
        self.token[16:20] = 0
        self.token.S = 0
        self.token[21:28] = 0xD
        self.token.cond = AL
        return self.token.encode()

    def __repr__(self):
        return 'MOV {}, {}'.format(self.rd, self.rm)


def Cmp(*args):
    if len(args) == 2:
        if isinstance(args[1], int):
            return Cmp1(*args)
        elif isinstance(args[1], ArmRegister):
            return Cmp2(*args)
    raise Exception()


class Cmp1(ArmInstruction):
    """ CMP Rn, imm """
    def __init__(self, reg, imm):
        super().__init__()
        assert type(imm) is int
        self.reg = reg
        self.imm = imm

    def encode(self):
        self.token[0:12] = encode_imm32(self.imm)
        self.token.Rn = self.reg.num
        self.token[20:28] = 0b00110101
        self.token.cond = AL
        return self.token.encode()

    def __repr__(self):
        return 'CMP {}, {}'.format(self.reg, self.imm)


class Cmp2(ArmInstruction):
    """ CMP Rn, Rm """
    def __init__(self, rn, rm):
        super().__init__()
        self.rn = rn
        self.rm = rm

    def encode(self):
        self.token.Rn = self.rn.num
        self.token.Rm = self.rm.num
        self.token[7:16] = 0
        self.token[20:28] = 0b10101
        self.token.cond = AL
        return self.token.encode()

    def __repr__(self):
        return 'CMP {}, {}'.format(self.rn, self.rm)


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
    def __init__(self, rd, rn, rm):
        super().__init__()
        self.rd = rd
        self.rn = rn
        self.rm = rm

    def encode(self):
        self.token[0:4] = self.rn.num
        self.token[4:8] = 0b1001
        self.token[8:12] = self.rm.num
        self.token[16:20] = self.rd.num
        self.token.S = 0
        self.token.cond = AL
        return self.token.encode()


class OpRegRegReg(ArmInstruction):
    """ add rd, rn, rm """
    def __init__(self, rd, rn, rm, shift=0):
        super().__init__()
        self.rd = rd
        self.rn = rn
        self.rm = rm

    def encode(self):
        self.token[0:4] = self.rm.num
        self.token[4] = 0
        self.token[5:7] = 0
        self.token[7:12] = 0 # Shift
        self.token.Rd = self.rd.num
        self.token.Rn = self.rn.num
        self.token.S = 0 # Set flags
        self.token[21:28] = self.opcode
        self.token.cond = 0xE # Always!
        return self.token.encode()

    def __repr__(self):
        return '{} {}, {}, {}'.format(self.mnemonic, self.rd, self.rn, self.rm)


class Add1(OpRegRegReg):
    mnemonic = 'ADD'
    opcode = 0b0000100


class Sub1(OpRegRegReg):
    mnemonic = 'SUB'
    opcode = 0b0000010


class Orr1(OpRegRegReg):
    mnemonic = 'ORR'
    opcode = 0b0001100

Orr = Orr1

class And1(OpRegRegReg):
    mnemonic = 'AND'
    opcode = 0b0000000

And = And1

class ShiftBase(ArmInstruction):
    """ ? rd, rn, rm """
    def __init__(self, rd, rn, rm):
        super().__init__()
        self.rd = rd
        self.rn = rn
        self.rm = rm

    def encode(self):
        self.token[0:4] = self.rn.num
        self.token[4:8] = self.opcode
        self.token[8:12] = self.rm.num
        self.token[12:16] = self.rd.num
        self.token.S = 0 # Set flags
        self.token[21:28] = 0b1101
        self.token.cond = 0xE # Always!
        return self.token.encode()

    def __repr__(self):
        return '{} {}, {}, {}'.format(self.mnemonic, self.rd, self.rn, self.rm)


class Lsr1(ShiftBase):
    mnemonic = 'LSR'
    opcode = 0b0011

Lsr = Lsr1

class Lsl1(ShiftBase):
    mnemonic = 'LSL'
    opcode = 0b0001

Lsl = Lsl1

class OpRegRegImm(ArmInstruction):
    """ add rd, rn, imm12 """
    def __init__(self, rd, rn, imm):
        super().__init__()
        self.rd = rd
        self.rn = rn
        self.imm2 = encode_imm32(imm)
        self.imm = imm

    def encode(self):
        self.token[0:12] = self.imm2
        self.token.Rd = self.rd.num
        self.token.Rn = self.rn.num
        self.token.S = 0 # Set flags
        self.token[21:28] = self.opcode
        self.token.cond = 0xE # Always!
        return self.token.encode()

    def __repr__(self):
        return '{} {}, {}, {}'.format(self.mnemonic, self.rd, self.rn, self.imm)


class Add2(OpRegRegImm):
    mnemonic = 'ADD'
    opcode = 0b0010100


class Sub2(OpRegRegImm):
    mnemonic = 'SUB'
    opcode = 0b0010010



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


EQ, NE, CS, CC, MI, PL, VS, VC, HI, LS, GE, LT, GT, LE, AL = range(15)

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
    def __init__(self, rt, rn, offset):
        super().__init__()
        self.rt = rt
        self.rn = rn
        self.offset = offset

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


class Ldr1(LdrStrBase):
    opcode = 0b010
    bit20 = 1
    mnemonic = 'LDR'


class Adr(ArmInstruction):
    def __init__(self, rd, label):
        super().__init__()
        self.rd = rd
        self.label = label

    def __repr__(self):
        return 'ADR {}, {}'.format(self.rd, self.label)

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
    def __init__(self, rt, label):
        super().__init__()
        self.rt = rt
        self.label = label

    def __repr__(self):
        return 'LDR {}, {}'.format(self.rt, self.label)

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
