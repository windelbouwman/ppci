from ..basetarget import Register, Instruction, LabelAddress
from ..token import u16, u32
from .armtoken import ThumbToken
from ..arm.registers import R0, ArmRegister, SP


# Instructions:

class ThumbInstruction(Instruction):
    pass


class Dcd(ThumbInstruction):
    def __init__(self, expr):
        if isinstance(expr, int) or isinstance(expr, LabelAddress):
            self.expr = expr
        else:
            raise NotImplementedError('{}'.format(expr))

    def encode(self):
        if type(self.expr) is int:
            return u32(self.expr)
        else:
            return u32(0)

    def relocations(self):
        if type(self.expr) is LabelAddress:
            return [(self.expr.name, 'absaddr32')]
        else:
            return []

    def __repr__(self):
        if type(self.expr) is int:
            return 'DCD 0x{0:X}'.format(self.expr)
        else:
            return 'DCD ={}'.format(self.expr.name)


class ConstantData(ThumbInstruction):
    def __init__(self, v):
        super().__init__()
        assert isinstance(v, int)
        self.v = v


class Db(ConstantData):
    def encode(self):
        assert self.v < 256
        return bytes([self.v])

    def __repr__(self):
        return 'DB {}'.format(hex(self.v))


class nop_ins(ThumbInstruction):
    def encode(self):
        return bytes()

    def __repr__(self):
        return 'NOP'


# Memory related

class LS_imm5_base(ThumbInstruction):
    """ ??? Rt, [Rn, imm5] """
    def __init__(self, rt, rn, imm5):
        assert imm5 % 4 == 0
        self.imm5 = imm5 >> 2
        self.rn = rn
        self.rt = rt
        assert self.rn.num < 8
        assert self.rt.num < 8
        self.token = ThumbToken()

    def encode(self):
        Rn = self.rn.num
        Rt = self.rt.num
        imm5 = self.imm5
        self.token[0:3] = Rt
        self.token[3:6] = Rn
        self.token[6:11] = imm5
        self.token[11:16] = self.opcode
        return self.token.encode()

    def __repr__(self):
        return '{} {}, [{}, {}]'.format(self.mnemonic, self.rt, self.rn,
                                        self.imm5)


class Str2(LS_imm5_base):
    mnemonic = "STR"
    opcode = 0xC


class Ldr2(LS_imm5_base):
    mnemonic = "LDR"
    opcode = 0xD


class ls_sp_base_imm8(ThumbInstruction):
    def __init__(self, rt, offset):
        self.rt = rt
        self.offset = offset

    def encode(self):
        rt = self.rt.num
        assert rt < 8
        imm8 = self.offset >> 2
        assert imm8 < 256
        h = (self.opcode << 8) | (rt << 8) | imm8
        return u16(h)

    def __repr__(self):
        mnemonic = self.__class__.__name__
        return '{} {}, [sp,#{}]'.format(mnemonic, self.rt, self.offset)


def Ldr(*args):
    if len(args) == 2 and isinstance(args[0], ArmRegister) \
            and isinstance(args[1], str):
        return Ldr3(*args)
    else:
        raise Exception()


class Ldr3(ThumbInstruction):
    """ ldr Rt, LABEL, load value from pc relative position """
    def __init__(self, rt, label):
        self.rt = rt
        self.label = label

    def relocations(self):
        return [(self.label, 'lit_add_8')]

    def encode(self):
        rt = self.rt.num
        assert rt < 8
        imm8 = 0
        h = (0x9 << 11) | (rt << 8) | imm8
        return u16(h)

    def __repr__(self):
        return 'LDR {}, {}'.format(self.rt, self.label)


class Ldr1(ls_sp_base_imm8):
    """ ldr Rt, [SP, imm8] """
    opcode = 0x98


class Str1(ls_sp_base_imm8):
    """ str Rt, [SP, imm8] """
    opcode = 0x90


class Adr(ThumbInstruction):
    def __init__(self, rd, label):
        super().__init__()
        self.rd = rd
        self.label = label
        self.token = ThumbToken()

    def __repr__(self):
        return 'ADR {}, {}'.format(self.rd, self.label)

    def relocations(self):
        return [(self.label, 'lit_add_8')]

    def encode(self):
        self.token[0:8] = 0  # Filled by linker
        self.token[8:11] = self.rd.num
        self.token[11:16] = 0b10100
        return self.token.encode()


class Mov3(ThumbInstruction):
    """ mov Rd, imm8, move immediate value into register """
    opcode = 4   # 00100 Rd(3) imm8
    def __init__(self, rd, imm):
        assert imm < 256
        self.imm = imm
        self.rd = rd
        self.token = ThumbToken()

    def encode(self):
        rd = self.rd.num
        self.token[8:11] = rd
        self.token[0:8] = self.imm
        self.token[11:16] = self.opcode
        return self.token.encode()

    def __repr__(self):
        return 'MOV {}, {}'.format(self.rd, self.imm)


# Arithmatics:


class regregimm3_base(ThumbInstruction):
    def __init__(self, rd, rn, imm3):
        self.rd = rd
        self.rn = rn
        assert imm3 < 8
        self.imm3 = imm3
        self.token = ThumbToken()

    def encode(self):
        rd = self.rd.num
        self.token[0:3] = rd
        self.token[3:6] = self.rn.num
        self.token[6:9] = self.imm3
        self.token[9:16] = self.opcode
        return self.token.encode()

    def __repr__(self):
        mnemonic = self.__class__.__name__
        return '{} {}, {}, {}'.format(mnemonic, self.rd, self.rn, self.imm3)



class Add2(regregimm3_base):
    """ add Rd, Rn, imm3 """
    opcode = 0b0001110


class Sub2(regregimm3_base):
    """ sub Rd, Rn, imm3 """
    opcode = 0b0001111


def Sub(*args):
    if len(args) == 3 and args[0] is SP and args[1] is SP and \
            isinstance(args[2], int) and args[2] < 256:
        return SubSp(args[2])
    elif len(args) == 3 and isinstance(args[0], ArmRegister) and \
            isinstance(args[1], ArmRegister) and isinstance(args[2], int) and \
            args[2] < 8:
        return Sub2(args[0], args[1], args[2])
    else:
        raise Exception()


def Add(*args):
    if len(args) == 3 and args[0] is SP and args[1] is SP and \
            isinstance(args[2], int) and args[2] < 256:
        return AddSp(args[2])
    elif len(args) == 3 and isinstance(args[0], ArmRegister) and \
            isinstance(args[1], ArmRegister) and isinstance(args[2], int) and \
            args[2] < 8:
        return Add2(args[0], args[1], args[2])
    else:
        raise Exception()


class regregreg_base(ThumbInstruction):
    """ ??? Rd, Rn, Rm """
    def __init__(self, rd, rn, rm):
        self.rd = rd
        self.rn = rn
        self.rm = rm

    def encode(self):
        at = ThumbToken()
        at.rd = self.rd.num
        rn = self.rn.num
        rm = self.rm.num
        at[3:6] = rn
        at[6:9] = rm
        at[9:16] = self.opcode
        return at.encode()

    def __repr__(self):
        return '{} {}, {}, {}'.format(self.mnemonic, self.rd, self.rn, self.rm)


class Add3(regregreg_base):
    mnemonic = 'ADD'
    opcode = 0b0001100


class Sub3(regregreg_base):
    mnemonic = 'SUB'
    opcode = 0b0001101


class Mov2(ThumbInstruction):
    """ mov rd, rm """
    mnemonic = 'MOV'
    def __init__(self, rd, rm):
        self.rd = rd
        self.rm = rm

    def encode(self):
        at = ThumbToken()
        at.rd = self.rd.num & 0x7
        D = (self.rd.num >> 3) & 0x1
        Rm = self.rm.num
        opcode = 0b01000110
        at[8:16] = opcode
        at[3:7] = Rm
        at[7] = D
        return at.encode()

    def __repr__(self):
        return '{} {}, {}'.format(self.mnemonic, self.rd, self.rm)


class Mul(ThumbInstruction):
    """ mul Rn, Rdm """
    mnemonic = 'MUL'
    def __init__(self, rn, rdm):
        self.rn = rn
        self.rdm = rdm

    def encode(self):
        at = ThumbToken()
        rn = self.rn.num
        at.rd = self.rdm.num
        opcode = 0b0100001101
        #h = (opcode << 6) | (rn << 3) | rdm
        at[6:16] = opcode
        at[3:6] = rn
        return at.encode()

    def __repr__(self):
        return '{} {}, {}'.format(self.mnemonic, self.rn, self.rdm)


class regreg_base(ThumbInstruction):
    """ ??? Rdn, Rm """
    def __init__(self, rdn, rm):
        self.rdn = rdn
        self.rm = rm

    def encode(self):
        at = ThumbToken()
        at.rd = self.rdn.num
        rm = self.rm.num
        at[3:6] = rm
        at[6:16] = self.opcode
        return at.encode()

    def __repr__(self):
        mnemonic = self.__class__.__name__
        return '{} {}, {}'.format(mnemonic, self.rdn, self.rm)


class movregreg_ins(regreg_base):
    """ mov Rd, Rm (reg8 operands) """
    opcode = 0


class And(regreg_base):
    opcode = 0b0100000000


class Orr(regreg_base):
    opcode = 0b0100001100


class Cmp(regreg_base):
    opcode = 0b0100001010


class Lsl(regreg_base):
    opcode = 0b0100000010


class Lsr(regreg_base):
    opcode = 0b0100000011


class Cmp2(ThumbInstruction):
    """ cmp Rn, imm8 """
    opcode = 5 # 00101
    def __init__(self, rn, imm):
        self.rn = rn
        self.imm = imm

    def encode(self):
        at = ThumbToken()
        at[0:8] = self.imm
        at[8:11] = self.rn.num
        at[11:16] = self.opcode
        return at.encode()


# Jumping:

class jumpBase_ins(ThumbInstruction):
    def __init__(self, target_label):
        assert type(target_label) is str
        self.target = target_label
        self.offset = 0

    def __repr__(self):
        mnemonic = self.__class__.__name__
        return '{} {}'.format(mnemonic, self.target)


class B(jumpBase_ins):
    def encode(self):
        h = (0b11100 << 11) | 0
        # | 1 # 1 to enable thumb mode
        return u16(h)

    def relocations(self):
        return [(self.target, 'wrap_new11')]


class Bw(jumpBase_ins):
    # Same encoding as Bl, longer jumps are possible with this function!
    def encode(self):
        imm11 = 0
        imm10 = 0
        j1 = 1
        j2 = 1
        s = 0
        h1 = (0b11110 << 11) | (s << 10) | imm10
        h2 = (0b1001 << 12) | (j1 << 13) | (j2 << 11) | imm11
        return u16(h1) + u16(h2)

    def relocations(self):
        return [(self.target, 'bl_imm11_imm10')]


class Bl(jumpBase_ins):
    def encode(self):
        imm11 = 0
        imm10 = 0
        j1 = 1  # TODO: what do these mean?
        j2 = 1
        s = 0
        h1 = (0b11110 << 11) | (s << 10) | imm10
        h2 = (0b1101 << 12) | (j1 << 13) | (j2 << 11) | imm11
        return u16(h1) + u16(h2)

    def relocations(self):
        return [(self.target, 'bl_imm11_imm10')]


class cond_base_ins(jumpBase_ins):
    def encode(self):
        imm8 = 0
        h = (0b1101 << 12) | (self.cond << 8) | imm8
        return u16(h)

    def relocations(self):
        return [(self.target, 'rel8')]


class cond_base_ins_long(jumpBase_ins):
    """ Encoding T3 """
    def encode(self):
        j1 = 1 # TODO: what do these mean?
        j2 = 1
        h1 = (0b11110 << 11) | (self.cond << 6)
        h2 = (0b1101 << 12) | (j1 << 13) | (j2 << 11)
        return u16(h1) + u16(h2)

    def relocations(self):
        return [(self.target, 'b_imm11_imm6')]


class Beq(cond_base_ins):
    cond = 0


class Bne(cond_base_ins):
    cond = 1


class Blt(cond_base_ins):
    cond = 0b1011


class Ble(cond_base_ins):
    cond = 0b1101


class Bgt(cond_base_ins):
    cond = 0b1100


class Bge(cond_base_ins):
    cond = 0b1010


class Push(ThumbInstruction):
    def __init__(self, regs):
        assert type(regs) is set
        self.regs = regs

    def __repr__(self):
        return 'Push {{{}}}'.format(self.regs)

    def encode(self):
        at = ThumbToken()
        for n in register_numbers(self.regs):
            if n < 8:
                at[n] = 1
            elif n == 14:
                at[8] = 1
            else:
                raise NotImplementedError('not implemented for {}'.format(n))
        at[9:16] = 0x5a
        return at.encode()


def register_numbers(regs):
    for r in regs:
        yield r.num

class Pop(ThumbInstruction):
    def __init__(self, regs):
        assert type(regs) is set
        self.regs = regs
        self.token = ThumbToken()

    def __repr__(self):
        return 'Pop {{{}}}'.format(self.regs)

    def encode(self):
        for n in register_numbers(self.regs):
            if n < 8:
                self.token[n] = 1
            elif n == 15:
                self.token[8] = 1
            else:
                raise NotImplementedError('not implemented for this register')
        self.token[9:16] = 0x5E
        return self.token.encode()



class Yield(ThumbInstruction):
    def encode(self):
        return u16(0xbf10)

# misc:

# add/sub SP:
class addspsp_base(ThumbInstruction):
    def __init__(self, imm7):
        assert imm7 < 512
        self.imm7 = imm7
        assert self.imm7 % 4 == 0
        self.imm7 >>= 2

    def encode(self):
        return u16((self.opcode << 7) | self.imm7)

    def __repr__(self):
        mnemonic = self.__class__.__name__
        return '{} sp, sp, {}'.format(mnemonic, self.imm7 << 2)


class AddSp(addspsp_base):
    opcode = 0b101100000


class SubSp(addspsp_base):
    opcode = 0b101100001
