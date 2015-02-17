from ..basetarget import Instruction, Isa
from ..token import u16, u32
from ..arm.registers import ArmRegister, SP
from ..instructionselector import InstructionSelector, pattern
from ...irmach import AbstractInstruction

from ..token import Token, bit_range


class ThumbToken(Token):
    def __init__(self):
        super().__init__(16)

    rd = bit_range(0, 3)

    def encode(self):
        return u16(self.bit_value)


# Instructions:
isa = Isa()
isa.typ2nt[ArmRegister] = 'reg'
isa.typ2nt[int] = 'imm32'
isa.typ2nt[str] = 'strrr'
isa.typ2nt[set] = 'reg_list'


class ThumbInstruction(Instruction):
    """ Base of all thumb instructions.
    """
    tokens = [ThumbToken]
    isa = isa


class LongThumbInstruction(ThumbInstruction):
    tokens = [ThumbToken, ThumbToken]


def Dcd(v):
    if type(v) is str:
        return Dcd2(v)
    elif type(v) is int:
        return Dcd1(v)
    else:
        raise NotImplementedError()


class Dcd1(ThumbInstruction):
    args = [('v', int)]
    syntax = ['dcd', 0]

    def encode(self):
        return u32(self.v)


class Dcd2(ThumbInstruction):
    args = [('v', str)]
    syntax = ['dcd', '=', 0]

    def encode(self):
        return u32(0)

    def relocations(self):
        return [(self.v, 'absaddr32')]


class ConstantData():
    def __init__(self, v):
        super().__init__()
        assert isinstance(v, int)
        self.v = v


class Db(ThumbInstruction):
    args = [('v', int)]
    syntax = ['db', 0]

    def encode(self):
        assert self.v < 256
        return bytes([self.v])


class Ds(ThumbInstruction):
    tokens = []
    args = [('v', int)]
    syntax = ['ds', 0]

    def encode(self):
        return bytes([0] * self.v)


class nop_ins(ThumbInstruction):
    def encode(self):
        return bytes()

    def __repr__(self):
        return 'NOP'


# Memory related

class LS_imm5_base(ThumbInstruction):
    """ ??? Rt, [Rn, imm5] """
    args = [('rt', ArmRegister), ('rn', ArmRegister), ('imm5', int)]

    def encode(self):
        assert self.imm5 % 4 == 0
        assert self.rn.num < 8
        assert self.rt.num < 8
        Rn = self.rn.num
        Rt = self.rt.num
        imm5 = self.imm5 >> 2
        self.token[0:3] = Rt
        self.token[3:6] = Rn
        self.token[6:11] = imm5
        self.token[11:16] = self.opcode
        return self.token.encode()


class Str2(LS_imm5_base):
    syntax = ['str', 0, ',', '[', 1, ',', 2, ']']
    opcode = 0xC

    @staticmethod
    def from_im(im):
        return Str2(im.src[1], im.src[0], im.others[0])


#############3
# Experiments:
# stm: MOVI32(MEMI32(reg), reg) 2 'self.emit(Str2, others=[0], src=[c0, c1])'
#def pattern(*args, **kwargs):
#    return lambda f: f
#
#pattern(
#    'stm: MOVI32(MEMI32(reg), reg)',
#    cost=2,
#    f=lambda c0, c1: emit(Str2, others=[0], src=[c0, c1])
#    )
#
#class Matcher:
#    @pattern('a', cost=2)
#    def P1(self):
#        self.emit()
#
#
## stm: MOVI32(MEMI32(reg), reg) 2 
## 'self.emit(Str2, others=[0], src=[c0, c1])'
#class Str2Pattern:
#    cost = 2
#    pattern = 'stm: MOVI32(MEMI32(reg), reg)'
#
###############

class Ldr2(LS_imm5_base):
    syntax = ['ldr', 0, ',', '[', 1, ',', 2, ']']
    opcode = 0xD

    @staticmethod
    def from_im(im):
        return Ldr2(im.dst[0], im.src[0], im.others[0])


class LS_byte_imm5_base(ThumbInstruction):
    """ ??? Rt, [Rn, imm5] """
    args = [('rt', ArmRegister), ('rn', ArmRegister), ('imm5', int)]

    def encode(self):
        assert self.rn.num < 8
        assert self.rt.num < 8
        Rn = self.rn.num
        Rt = self.rt.num
        imm5 = self.imm5
        self.token[0:3] = Rt
        self.token[3:6] = Rn
        self.token[6:11] = imm5
        self.token[11:16] = self.opcode
        return self.token.encode()


class Strb(LS_byte_imm5_base):
    syntax = ['strb', 0, ',', '[', 1, ',', 2, ']']
    opcode = 0xE

    @staticmethod
    def from_im(im):
        return Strb(im.src[1], im.src[0], im.others[0])


class Ldrb(LS_byte_imm5_base):
    syntax = ['ldrb', 0, ',', '[', 1, ',', 2, ']']
    opcode = 0b01111

    @staticmethod
    def from_im(im):
        return Ldrb(im.dst[0], im.src[0], im.others[0])


class ls_sp_base_imm8(ThumbInstruction):
    args = [('rt', ArmRegister), ('offset', int)]

    def encode(self):
        rt = self.rt.num
        assert rt < 8
        imm8 = self.offset >> 2
        assert imm8 < 256
        h = (self.opcode << 8) | (rt << 8) | imm8
        return u16(h)


def Ldr(*args):
    if len(args) == 2 and isinstance(args[0], ArmRegister) \
            and isinstance(args[1], str):
        return Ldr3(*args)
    else:
        raise Exception()


class Ldr3(ThumbInstruction):
    """ ldr Rt, LABEL, load value from pc relative position """
    args = [('rt', ArmRegister), ('label', str)]
    syntax = ['ldr', 0, ',', 1]

    def relocations(self):
        return [(self.label, 'lit_add_8')]

    def encode(self):
        rt = self.rt.num
        assert rt < 8
        imm8 = 0
        h = (0x9 << 11) | (rt << 8) | imm8
        return u16(h)

    @staticmethod
    def from_im(im):
        return Ldr3(im.dst[0],  im.others[0])


class Ldr1(ls_sp_base_imm8):
    """ ldr Rt, [SP, imm8] """
    opcode = 0x98
    syntax = ['ldr', 0, ',', '[', 'sp', ',', 1, ']']


class Str1(ls_sp_base_imm8):
    """ str Rt, [SP, imm8] """
    opcode = 0x90
    syntax = ['str', 0, ',', '[', 'sp', ',', 1, ']']


class Adr(ThumbInstruction):
    args = [('rd', ArmRegister), ('label', str)]
    syntax = ['adr', 0, ',', 1]

    def relocations(self):
        return [(self.label, 'lit_add_8')]

    def encode(self):
        self.token[0:8] = 0  # Filled by linker
        self.token[8:11] = self.rd.num
        self.token[11:16] = 0b10100
        return self.token.encode()

    @staticmethod
    def from_im(im):
        return Adr(im.dst[0], im.others[0])


class Mov3(ThumbInstruction):
    """ mov Rd, imm8, move immediate value into register """
    opcode = 4   # 00100 Rd(3) imm8
    args = [('rd', ArmRegister), ('imm', int)]
    syntax = ['mov', 0, ',', 1]

    def encode(self):
        rd = self.rd.num
        self.token[8:11] = rd
        self.token[0:8] = self.imm
        self.token[11:16] = self.opcode
        return self.token.encode()

    @staticmethod
    def from_im(im):
        return Mov3(im.dst[0], im.others[0])

# Arithmatics:


class regregimm3_base(ThumbInstruction):
    args = [('rd', ArmRegister), ('rn', ArmRegister), ('imm3', int)]

    def encode(self):
        assert self.imm3 < 8
        rd = self.rd.num
        self.token[0:3] = rd
        self.token[3:6] = self.rn.num
        self.token[6:9] = self.imm3
        self.token[9:16] = self.opcode
        return self.token.encode()


class Add2(regregimm3_base):
    """ add Rd, Rn, imm3 """
    syntax = ['add', 0, ',', 1, ',', 2]
    opcode = 0b0001110

    @staticmethod
    def from_im(im):
        return Add2(im.dst[0], im.src[0], im.others[0])


class Sub2(regregimm3_base):
    """ sub Rd, Rn, imm3 """
    syntax = ['sub', 0, ',', 1, ',', 2]
    opcode = 0b0001111

    @staticmethod
    def from_im(im):
        return Sub2(im.dst[0], im.src[0], im.others[0])


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
    args = [('rd', ArmRegister), ('rn', ArmRegister), ('rm', ArmRegister)]

    def encode(self):
        at = ThumbToken()
        at.rd = self.rd.num
        rn = self.rn.num
        rm = self.rm.num
        at[3:6] = rn
        at[6:9] = rm
        at[9:16] = self.opcode
        return at.encode()


class Add3(regregreg_base):
    syntax = ['add', 0, ',', 1, ',', 2]
    opcode = 0b0001100

    @staticmethod
    def from_im(im):
        return Add3(im.dst[0], im.src[0], im.src[1])


class Sub3(regregreg_base):
    syntax = ['sub', 0, ',', 1, ',', 2]
    opcode = 0b0001101

    @staticmethod
    def from_im(im):
        return Sub3(im.dst[0], im.src[0], im.src[1])


class Mov2(ThumbInstruction):
    """ mov rd, rm (all registers, also > r7 """
    args = [('rd', ArmRegister), ('rm', ArmRegister)]
    syntax = ['mov', 0, ',', 1]

    def encode(self):
        self.token.rd = self.rd.num & 0x7
        D = (self.rd.num >> 3) & 0x1
        Rm = self.rm.num
        opcode = 0b01000110
        self.token[8:16] = opcode
        self.token[3:7] = Rm
        self.token[7] = D
        return self.token.encode()

    @staticmethod
    def from_im(im):
        return Mov2(im.dst[0], im.src[0])


class Mul(ThumbInstruction):
    """
        mul Rn, Rdm

        multiply Rn and Rm and store the result in Rd
        Rd and Rm are the same register.
    """
    args = [('rn', ArmRegister), ('rdm', ArmRegister)]
    syntax = ['mul', 0, ',', 1]

    def encode(self):
        rn = self.rn.num
        self.token.rd = self.rdm.num
        opcode = 0b0100001101
        self.token[6:16] = opcode
        self.token[3:6] = rn
        return self.token.encode()

    @staticmethod
    def from_im(im):
        return Mul(im.src[0], im.dst[0])


class Rsb_imm_t1(ThumbInstruction):
    """ rsbs rd, rn, #0 """
    args = [('rd', ArmRegister), ('rn', ArmRegister)]
    # TODO: what is the syntax for constant 0?
    syntax = ['rsb', 0, ',', 1, ',']

    def encode(self):
        raise NotImplementedError()
        return self.token.encode()


class regreg_base(ThumbInstruction):
    """ ??? Rdn, Rm """
    args = [('rdn', ArmRegister), ('rm', ArmRegister)]

    def encode(self):
        self.token.rd = self.rdn.num
        rm = self.rm.num
        self.token[3:6] = rm
        self.token[6:16] = self.opcode
        return self.token.encode()


class And(regreg_base):
    syntax = ['and', 0, ',', 1]
    opcode = 0b0100000000

    @staticmethod
    def from_im(im):
        return And(im.src[0], im.src[1])


class Orr(regreg_base):
    syntax = ['orr', 0, ',', 1]
    opcode = 0b0100001100

    @staticmethod
    def from_im(im):
        return Orr(im.src[0], im.src[1])


class Cmp(regreg_base):
    syntax = ['cmp', 0, ',', 1]
    opcode = 0b0100001010

    @staticmethod
    def from_im(im):
        return Cmp(im.src[0], im.src[1])


class Lsl(regreg_base):
    syntax = ['lsl', 0, ',', 1]
    opcode = 0b0100000010

    @staticmethod
    def from_im(im):
        return Lsl(im.src[0], im.src[1])


class Lsr(regreg_base):
    syntax = ['lsr', 0, ',', 1]
    opcode = 0b0100000011

    @staticmethod
    def from_im(im):
        return Lsr(im.src[0], im.src[1])


class Cmp2(ThumbInstruction):
    """ cmp Rn, imm8 """
    opcode = 5   # 00101
    args = [('rn', ArmRegister), ('imm', int)]
    syntax = ['cmp', 0, ',', 1]

    def encode(self):
        self.token[0:8] = self.imm
        self.token[8:11] = self.rn.num
        self.token[11:16] = self.opcode
        return self.token.encode()


# Jumping:

class jumpBase_ins(ThumbInstruction):
    args = [('target', str)]


class B(jumpBase_ins):
    syntax = ['b', 0]

    def encode(self):
        h = (0b11100 << 11) | 0
        # | 1 # 1 to enable thumb mode
        return u16(h)

    def relocations(self):
        return [(self.target, 'wrap_new11')]


class Bw(LongThumbInstruction):
    """ Encoding T4
        Same encoding as Bl, longer jumps are possible with this function!
    """
    syntax = ['bw', 0]
    args = [('target', str)]

    def encode(self):
        j1 = 1
        j2 = 1
        self.token[11:16] = 0b11110
        self.token2[13] = j1
        self.token2[11] = j2
        self.token2[12] = 1
        self.token2[15] = 1
        return self.token.encode() + self.token2.encode()

    def relocations(self):
        return [(self.target, 'bl_imm11_imm10')]


class Bl(LongThumbInstruction):
    """ Branch with link """
    syntax = ['bl', 0]
    args = [('target', str)]

    def encode(self):
        j1 = 1  # TODO: what do these mean?
        j2 = 1
        self.token[11:16] = 0b11110
        self.token2[13] = j1
        self.token2[11] = j2
        self.token2[12] = 1
        self.token2[14] = 1
        self.token2[15] = 1
        return self.token.encode() + self.token2.encode()

    def relocations(self):
        return [(self.target, 'bl_imm11_imm10')]


class cond_base_ins(jumpBase_ins):
    def encode(self):
        imm8 = 0
        h = (0b1101 << 12) | (self.cond << 8) | imm8
        return u16(h)

    def relocations(self):
        return [(self.target, 'rel8')]


class Beq(cond_base_ins):
    syntax = ['beq', 0]
    cond = 0


class Bne(cond_base_ins):
    syntax = ['bne', 0]
    cond = 1


class Blt(cond_base_ins):
    syntax = ['blt', 0]
    cond = 0b1011


class Ble(cond_base_ins):
    syntax = ['ble', 0]
    cond = 0b1101


class Bgt(cond_base_ins):
    syntax = ['bgt', 0]
    cond = 0b1100


class Bge(cond_base_ins):
    syntax = ['bge', 0]
    cond = 0b1010


# Long conditional jumps:
class cond_base_ins_long(jumpBase_ins):
    """ Encoding T3 """
    def encode(self):
        j1 = 0  # TODO: what do these mean?
        j2 = 0
        h1 = (0b11110 << 11) | (self.cond << 6)
        h2 = (0b1000 << 12) | (j1 << 13) | (j2 << 11)
        return u16(h1) + u16(h2)

    def relocations(self):
        return [(self.target, 'b_imm11_imm6')]


class Beqw(cond_base_ins_long):
    syntax = ['beqw', 0]
    cond = 0


class Bnew(cond_base_ins_long):
    syntax = ['bnew', 0]
    cond = 1


class Bltw(cond_base_ins_long):
    syntax = ['bltw', 0]
    cond = 0b1011


class Blew(cond_base_ins_long):
    syntax = ['blew', 0]
    cond = 0b1101


class Bgtw(cond_base_ins_long):
    syntax = ['bgtw', 0]
    cond = 0b1100


class Bgew(cond_base_ins_long):
    syntax = ['bgew', 0]
    cond = 0b1010


class Push(ThumbInstruction):
    args = [('regs', set)]
    syntax = ['push', 0]

    def __repr__(self):
        return 'Push {{{}}}'.format(self.regs)

    def encode(self):
        for n in register_numbers(self.regs):
            if n < 8:
                self.token[n] = 1
            elif n == 14:
                self.token[8] = 1
            else:
                raise NotImplementedError('not implemented for {}'.format(n))
        self.token[9:16] = 0x5a
        return self.token.encode()


def register_numbers(regs):
    for r in regs:
        yield r.num


class Pop(ThumbInstruction):
    args = [('regs', set)]
    syntax = ['pop', 0]

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
    syntax = ['yield']

    def encode(self):
        return u16(0xbf10)


class addspsp_base(ThumbInstruction):
    """ add/sub SP with imm7 << 2 """
    args = [('imm7', int)]

    def encode(self):
        assert self.imm7 < 512
        assert self.imm7 % 4 == 0
        return u16((self.opcode << 7) | self.imm7 >> 2)


class AddSp(addspsp_base):
    syntax = ['add', 'sp', ',', 'sp', ',', 0]
    opcode = 0b101100000


class SubSp(addspsp_base):
    syntax = ['sub', 'sp', ',', 'sp', ',', 0]
    opcode = 0b101100001


# Define instruction selector:

class ThumbInstructionSelector(InstructionSelector):
    """ Instruction selector for the thumb architecture """

    @pattern('stm', 'MOVI32(MEMI32(reg), reg)', cost=1)
    def P1(self, tree, c0, c1):
        self.emit(Str2, others=[0], src=[c0, c1])

    @pattern('stm', 'JMP', cost=2)
    def P3(self, tree):
        label, tgt = tree.value
        self.emit(Bw(label), jumps=[tgt])

    @pattern('reg', 'REGI32', cost=0)
    def P4(self, tree):
        return tree.value

    @pattern('reg', 'ADDI32(reg,reg)', cost=1)
    def P5(self, tree, c0, c1):
        d = self.newTmp()
        self.emit(Add3, dst=[d], src=[c0, c1])
        return d

    @pattern('reg', 'ADDI8(reg,reg)', cost=1)
    def P5_2(self, tree, c0, c1):
        d = self.newTmp()
        self.emit(Add3, dst=[d], src=[c0, c1])
        return d

    @pattern('stm', 'MOVI32(REGI32,cn)', cost=2)
    def P7(self, tree, c0):
        ln = self.frame.addConstant(c0)
        r = tree.children[0].value
        self.emit(Ldr3, dst=[r], others=[ln])

    @pattern('cn', 'CONSTI32', cost=0)
    def P8(self, tree):
        return tree.value

    @pattern('reg', 'GLOBALADDRESS', cost=2)
    def P9(self, tree):
        d = self.newTmp()
        ln = self.frame.addConstant(tree.value)
        self.emit(Ldr3, dst=[d], others=[ln])
        return d

    @pattern('reg', 'CONSTI32', cost=3)
    def P10(self, tree):
        d = self.newTmp()
        ln = self.frame.addConstant(tree.value)
        self.emit(Ldr3, dst=[d], others=[ln])
        return d

    @pattern('stm', 'MOVI32(REGI32,reg)', cost=1)
    def P11(self, tree, c0):
        r = tree.children[0].value
        self.move(r, c0)

    @pattern('stm', 'CJMP(reg,reg)', cost=3)
    def P12(self, tree, c0, c1):
        op, yes_label, yes_tgt, no_label, no_tgt = tree.value
        opnames = {"<": Bltw, ">": Bgtw, "==": Beqw, "!=": Bnew, ">=": Bgew}
        Bop = opnames[op]
        jmp_ins = AbstractInstruction(Bw(no_label), jumps=[no_tgt])
        self.emit(Cmp, src=[c0, c1])
        self.emit(Bop(yes_label), jumps=[yes_tgt, jmp_ins])
        self.emit(jmp_ins)

    @pattern('stm', 'MOVI8(MEMI8(reg),reg)', cost=1)
    def P13(self, tree, c0, c1):
        self.emit(Strb, others=[0], src=[c0, c1])

    @pattern('reg', 'MEMI8(reg)', cost=1)
    def P14(self, tree, c0):
        d = self.newTmp()
        self.emit(Ldrb, dst=[d], src=[c0], others=[0])
        return d

    @pattern('reg', 'MEMI32(reg)', cost=1)
    def P15(self, tree, c0):
        d = self.newTmp()
        self.emit(Ldr2, dst=[d], src=[c0], others=[0])
        return d

    @pattern('reg', 'CALL', cost=1)
    def P16(self, tree):
        return self.munchCall(tree.value)

    # TODO: fix this double otherwise, by extra token kind IGNR(CALL(..))
    @pattern('stm', 'CALL', cost=1)
    def P17(self, tree):
        return self.munchCall(tree.value)

    @pattern('reg', 'SUBI32(reg,reg)', cost=1)
    def P18(self, tree, c0, c1):
        d = self.newTmp()
        self.emit(Sub3, dst=[d], src=[c0, c1])
        return d

    @pattern('reg', 'SUBI8(reg,reg)', cost=1)
    def P18_2(self, tree, c0, c1):
        d = self.newTmp()
        self.emit(Sub3, dst=[d], src=[c0, c1])
        return d

    @pattern('reg', 'ADR(CONSTDATA)', cost=2)
    def P19(self, tree):
        d = self.newTmp()
        ln = self.frame.addConstant(tree.children[0].value)
        self.emit(Adr, dst=[d], others=[ln])
        return d

    @pattern('reg', 'SHRI32(reg, reg)', cost=1)
    def P20(self, tree, c0, c1):
        d = self.newTmp()
        self.move(d, c0)
        self.emit(Lsr, dst=[], src=[d, c1])
        return d

    @pattern('reg', 'ORI32(reg, reg)', cost=1)
    def P21(self, tree, c0, c1):
        d = self.newTmp()
        self.move(d, c0)
        self.emit(Orr, dst=[], src=[d, c1])
        return d

    @pattern('reg', 'ANDI32(reg, reg)', cost=1)
    def P22(self, tree, c0, c1):
        d = self.newTmp()
        self.move(d, c0)
        self.emit(And, dst=[], src=[d, c1])
        return d

    @pattern('reg', 'SHLI32(reg, reg)', cost=1)
    def P23(self, tree, c0, c1):
        d = self.newTmp()
        self.move(d, c0)
        self.emit(Lsl, dst=[], src=[d, c1])
        return d

    @pattern('reg', 'MULI32(reg, reg)', cost=5)
    def P24(self, tree, c0, c1):
        d = self.newTmp()
        self.move(d, c0)
        self.emit(Mul, dst=[d], src=[c1, d])
        return d

#reg: MEMI32(ADDI32(reg, cn))  1 'return tree.children[0].children[1].value < 32' 'd = self.newTmp(); self.emit(Ldr2, dst=[d], src=[c0], others=[c1]); return d'
#addr: reg 0 ''
