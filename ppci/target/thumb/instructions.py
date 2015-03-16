from .. import Instruction, Isa, register_argument
from ..token import u16, u32
from ..arm.registers import ArmRegister, SP
from ..instructionselector import InstructionSelector, pattern
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
    v = register_argument('v', int)
    syntax = ['dcd', v]

    def encode(self):
        return u32(self.v)


class Dcd2(ThumbInstruction):
    v = register_argument('v', str)
    syntax = ['dcd', '=', v]

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
    v = register_argument('v', int)
    syntax = ['db', v]

    def encode(self):
        assert self.v < 256
        return bytes([self.v])


class Ds(ThumbInstruction):
    tokens = []
    v = register_argument('v', int)
    syntax = ['ds', v]

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
    rn = register_argument('rn', ArmRegister, read=True)
    imm5 = register_argument('imm5', int)

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
    rt = register_argument('rt', ArmRegister, read=True)
    syntax = [
        'str', rt, ',', '[', LS_imm5_base.rn, ',', LS_imm5_base.imm5, ']']
    opcode = 0xC


#############
# Experiments:
# stm: MOVI32(MEMI32(reg), reg) 2 'self.emit(Str2, others=[0], src=[c0, c1])'
# def pattern(*args, **kwargs):
#    return lambda f: f
#
# pattern(
#    'stm: MOVI32(MEMI32(reg), reg)',
#    cost=2,
#    f=lambda c0, c1: emit(Str2, others=[0], src=[c0, c1])
#    )
#
# class Matcher:
#    @pattern('a', cost=2)
#    def P1(self):
#        self.emit()
#
#
# # stm: MOVI32(MEMI32(reg), reg) 2
# # 'self.emit(Str2, others=[0], src=[c0, c1])'
# class Str2Pattern:
#    cost = 2
#    pattern = 'stm: MOVI32(MEMI32(reg), reg)'
#
###############

class Ldr2(LS_imm5_base):
    rt = register_argument('rt', ArmRegister, write=True)
    syntax = [
        'ldr', rt, ',', '[', LS_imm5_base.rn, ',', LS_imm5_base.imm5, ']']
    opcode = 0xD


class LS_byte_imm5_base(ThumbInstruction):
    """ ??? Rt, [Rn, imm5] """
    rn = register_argument('rn', ArmRegister, read=True)
    imm5 = register_argument('imm5', int)

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
    rt = register_argument('rt', ArmRegister, read=True)
    syntax = [
        'strb', rt, ',', '[', LS_byte_imm5_base.rn, ',',
        LS_byte_imm5_base.imm5, ']']
    opcode = 0xE


class Ldrb(LS_byte_imm5_base):
    rt = register_argument('rt', ArmRegister, write=True)
    syntax = [
        'ldrb', rt, ',', '[', LS_byte_imm5_base.rn, ',',
        LS_byte_imm5_base.imm5, ']']
    opcode = 0b01111


class ls_sp_base_imm8(ThumbInstruction):
    offset = register_argument('offset', int)

    def encode(self):
        rt = self.rt.num
        assert rt < 8
        imm8 = self.offset >> 2
        assert imm8 < 256
        h = (self.opcode << 8) | (rt << 8) | imm8
        return u16(h)


class Ldr3(ThumbInstruction):
    """ ldr Rt, LABEL, load value from pc relative position """
    rt = register_argument('rt', ArmRegister, write=True)
    label = register_argument('label', str)
    syntax = ['ldr', rt, ',', label]

    def relocations(self):
        return [(self.label, 'lit_add_8')]

    def encode(self):
        rt = self.rt.num
        assert rt < 8
        imm8 = 0
        h = (0x9 << 11) | (rt << 8) | imm8
        return u16(h)


class Ldr1(ls_sp_base_imm8):
    """ ldr Rt, [SP, imm8] """
    rt = register_argument('rt', ArmRegister, write=True)
    opcode = 0x98
    syntax = ['ldr', rt, ',', '[', 'sp', ',', ls_sp_base_imm8.offset, ']']


class Str1(ls_sp_base_imm8):
    """ str Rt, [SP, imm8] """
    rt = register_argument('rt', ArmRegister, read=True)
    opcode = 0x90
    syntax = ['str', rt, ',', '[', 'sp', ',', ls_sp_base_imm8.offset, ']']


class Adr(ThumbInstruction):
    rd = register_argument('rd', ArmRegister, write=True)
    label = register_argument('label', str)
    syntax = ['adr', rd, ',', label]

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
    rd = register_argument('rd', ArmRegister, write=True)
    imm = register_argument('imm', int)
    syntax = ['mov', rd, ',', imm]

    def encode(self):
        rd = self.rd.num
        self.token[8:11] = rd
        self.token[0:8] = self.imm
        self.token[11:16] = self.opcode
        return self.token.encode()

# Arithmatics:


class regregimm3_base(ThumbInstruction):
    rd = register_argument('rd', ArmRegister, write=True)
    rn = register_argument('rn', ArmRegister, read=True)
    imm3 = register_argument('imm3', int)

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
    syntax = [
        'add', regregimm3_base.rd, ',', regregimm3_base.rn, ',',
        regregimm3_base.imm3]
    opcode = 0b0001110


class Sub2(regregimm3_base):
    """ sub Rd, Rn, imm3 """
    syntax = [
        'sub', regregimm3_base.rd, ',', regregimm3_base.rn, ',',
        regregimm3_base.imm3]
    opcode = 0b0001111


class regregreg_base(ThumbInstruction):
    """ ??? Rd, Rn, Rm """
    rd = register_argument('rd', ArmRegister, write=True)
    rn = register_argument('rn', ArmRegister, read=True)
    rm = register_argument('rm', ArmRegister, read=True)

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
    syntax = [
        'add', regregreg_base.rd, ',', regregreg_base.rn, ',',
        regregreg_base.rm]
    opcode = 0b0001100


class Sub3(regregreg_base):
    syntax = [
        'sub', regregreg_base.rd, ',', regregreg_base.rn, ',',
        regregreg_base.rm]
    opcode = 0b0001101


class Mov2(ThumbInstruction):
    """ mov rd, rm (all registers, also > r7 """
    rd = register_argument('rd', ArmRegister, write=True)
    rm = register_argument('rm', ArmRegister, read=True)
    syntax = ['mov', rd, ',', rm]

    def encode(self):
        self.token.rd = self.rd.num & 0x7
        D = (self.rd.num >> 3) & 0x1
        Rm = self.rm.num
        opcode = 0b01000110
        self.token[8:16] = opcode
        self.token[3:7] = Rm
        self.token[7] = D
        return self.token.encode()


class Mul(ThumbInstruction):
    """
        mul Rn, Rdm

        multiply Rn and Rm and store the result in Rd
        Rd and Rm are the same register.
    """
    rn = register_argument('rn', ArmRegister, read=True)
    rdm = register_argument('rdm', ArmRegister, read=True, write=True)
    syntax = ['mul', rn, ',', rdm]

    def encode(self):
        rn = self.rn.num
        self.token.rd = self.rdm.num
        opcode = 0b0100001101
        self.token[6:16] = opcode
        self.token[3:6] = rn
        return self.token.encode()


class Sdiv(LongThumbInstruction):
    """ Signed division.
        Encoding T1
    """
    rd = register_argument('rd', ArmRegister, write=True)
    rn = register_argument('rn', ArmRegister, read=True)
    rm = register_argument('rm', ArmRegister, read=True)
    syntax = ['sdiv', rd, ',', rn, ',', rm]

    def encode(self):
        self.token[11:16] = 0b11111
        self.token[4:11] = 0b0111001
        self.token[0:4] = self.rn.num
        self.token2[12:16] = 0b1111
        self.token2[8:12] = self.rd.num
        self.token2[4:8] = 0b1111
        self.token2[0:4] = self.rm.num
        return self.token.encode() + self.token2.encode()


class regreg_base(ThumbInstruction):
    """ ??? Rdn, Rm """
    def encode(self):
        self.token.rd = self.rdn.num
        rm = self.rm.num
        self.token[3:6] = rm
        self.token[6:16] = self.opcode
        return self.token.encode()


def make_regreg(mnemonic, opcode):
    rdn = register_argument('rdn', ArmRegister, write=True, read=True)
    rm = register_argument('rm', ArmRegister, read=True)
    syntax = [mnemonic, rdn, ',', rm]
    members = {'syntax': syntax, 'rdn': rdn, 'rm': rm, 'opcode': opcode}
    return type(mnemonic + '_ins', (regreg_base,), members)


And = make_regreg('and', 0b0100000000)
Orr = make_regreg('orr', 0b0100001100)
Eor = make_regreg('eor', 0b0100000001)
Cmp = make_regreg('cmp', 0b0100001010)
Lsl = make_regreg('lsl', 0b0100000010)
Lsr = make_regreg('lsr', 0b0100000011)


class Cmp2(ThumbInstruction):
    """ cmp Rn, imm8 """
    opcode = 5   # 00101
    rn = register_argument('rn', ArmRegister, read=True)
    imm = register_argument('imm', int)
    syntax = ['cmp', rn, ',', imm]

    def encode(self):
        self.token[0:8] = self.imm
        self.token[8:11] = self.rn.num
        self.token[11:16] = self.opcode
        return self.token.encode()


# Jumping:


class B(ThumbInstruction):
    target = register_argument('target', str)
    syntax = ['b', target]

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
    target = register_argument('target', str)
    syntax = ['bw', target]

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
    target = register_argument('target', str)
    syntax = ['bl', target]

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


class cond_base_ins(ThumbInstruction):
    def encode(self):
        imm8 = 0
        h = (0b1101 << 12) | (self.cond << 8) | imm8
        return u16(h)

    def relocations(self):
        return [(self.target, 'rel8')]


def make_cond_branch(mnemonic, cond):
    target = register_argument('target', str)
    syntax = [mnemonic, target]
    members = {
        'syntax': syntax, 'target': target, 'cond': cond}
    return type(mnemonic + '_ins', (cond_base_ins,), members)


Beq = make_cond_branch('beq', 0)
Bne = make_cond_branch('bne', 1)
Blt = make_cond_branch('blt', 0b1011)
Ble = make_cond_branch('ble', 0b1101)
Bgt = make_cond_branch('bgt', 0b1100)
Bge = make_cond_branch('bge', 0b1010)


# Long conditional jumps:
class cond_base_ins_long(LongThumbInstruction):
    """ Encoding T3 """
    def encode(self):
        j1 = 0  # TODO: what do these mean?
        j2 = 0
        h1 = (0b11110 << 11) | (self.cond << 6)
        h2 = (0b1000 << 12) | (j1 << 13) | (j2 << 11)
        return u16(h1) + u16(h2)

    def relocations(self):
        return [(self.target, 'b_imm11_imm6')]


def make_long_cond_branch(mnemonic, cond):
    target = register_argument('target', str)
    syntax = [mnemonic, target]
    members = {
        'syntax': syntax, 'target': target, 'cond': cond}
    return type(mnemonic + '_ins', (cond_base_ins_long,), members)


Beqw = make_long_cond_branch('beqw', 0)
Bnew = make_long_cond_branch('bnew', 1)
Bltw = make_long_cond_branch('bltw', 0b1011)
Blew = make_long_cond_branch('blew', 0b1101)
Bgtw = make_long_cond_branch('bgtw', 0b1100)
Bgew = make_long_cond_branch('bgew', 0b1010)


class Push(ThumbInstruction):
    regs = register_argument('regs', set)
    syntax = ['push', regs]

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
    regs = register_argument('regs', set)
    syntax = ['pop', regs]

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
    imm7 = register_argument('imm7', int)

    def encode(self):
        assert self.imm7 < 512
        assert self.imm7 % 4 == 0
        return u16((self.opcode << 7) | self.imm7 >> 2)


class AddSp(addspsp_base):
    syntax = ['add', 'sp', ',', 'sp', ',', addspsp_base.imm7]
    opcode = 0b101100000


class SubSp(addspsp_base):
    syntax = ['sub', 'sp', ',', 'sp', ',', addspsp_base.imm7]
    opcode = 0b101100001


# Define instruction selector:

class ThumbInstructionSelector(InstructionSelector):
    """ Instruction selector for the thumb architecture """

    @pattern('stm', 'MOVI32(MEMI32(reg), reg)', cost=1)
    def P1(self, tree, c0, c1):
        self.emit(Str2(c1, c0, 0))

    @pattern('stm', 'JMP', cost=2)
    def P3(self, tree):
        label, tgt = tree.value
        self.emit(Bw(label, jumps=[tgt]))

    @pattern('reg', 'REGI32', cost=0)
    def P4(self, tree):
        return tree.value

    @pattern('reg', 'ADDI32(reg,reg)', cost=1)
    def P5(self, tree, c0, c1):
        d = self.newTmp()
        self.emit(Add3(d, c0, c1))
        return d

    @pattern('reg', 'ADDI8(reg,reg)', cost=1)
    def P5_2(self, tree, c0, c1):
        d = self.newTmp()
        self.emit(Add3(d, c0, c1))
        return d

    @pattern('stm', 'MOVI32(REGI32,cn)', cost=2)
    def P7(self, tree, c0):
        ln = self.frame.addConstant(c0)
        r = tree.children[0].value
        self.emit(Ldr3(r, ln))

    @pattern('cn', 'CONSTI32', cost=0)
    def P8(self, tree):
        return tree.value

    @pattern('reg', 'GLOBALADDRESS', cost=2)
    def P9(self, tree):
        d = self.newTmp()
        ln = self.frame.addConstant(tree.value)
        self.emit(Ldr3(d, ln))
        return d

    @pattern('reg', 'CONSTI32', cost=3)
    def P10(self, tree):
        d = self.newTmp()
        ln = self.frame.addConstant(tree.value)
        self.emit(Ldr3(d, ln))
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
        jmp_ins = Bw(no_label, jumps=[no_tgt])
        self.emit(Cmp(c0, c1))
        self.emit(Bop(yes_label, jumps=[yes_tgt, jmp_ins]))
        self.emit(jmp_ins)

    @pattern('stm', 'MOVI8(MEMI8(reg),reg)', cost=1)
    def P13(self, tree, c0, c1):
        self.emit(Strb(c1, c0, 0))

    @pattern('reg', 'MEMI8(reg)', cost=1)
    def P14(self, tree, c0):
        d = self.newTmp()
        self.emit(Ldrb(d, c0, 0))
        return d

    @pattern('reg', 'MEMI32(reg)', cost=1)
    def P15(self, tree, c0):
        d = self.newTmp()
        self.emit(Ldr2(d, c0, 0))
        return d

    @pattern('reg', 'CALL', cost=1)
    def P16(self, tree):
        label, args, res_var = tree.value
        self.frame.gen_call(label, args, res_var)

    # TODO: fix this double otherwise, by extra token kind IGNR(CALL(..))
    @pattern('stm', 'CALL', cost=1)
    def P17(self, tree):
        label, args, res_var = tree.value
        self.frame.gen_call(label, args, res_var)

    @pattern('reg', 'SUBI32(reg,reg)', cost=1)
    def P18(self, tree, c0, c1):
        d = self.newTmp()
        self.emit(Sub3(d, c0, c1))
        return d

    @pattern('reg', 'SUBI8(reg,reg)', cost=1)
    def P18_2(self, tree, c0, c1):
        d = self.newTmp()
        self.emit(Sub3(d, c0, c1))
        return d

    @pattern('reg', 'ADR(CONSTDATA)', cost=2)
    def P19(self, tree):
        d = self.newTmp()
        ln = self.frame.addConstant(tree.children[0].value)
        self.emit(Adr(d, ln))
        return d

    @pattern('reg', 'SHRI32(reg, reg)', cost=1)
    def P20(self, tree, c0, c1):
        d = self.newTmp()
        self.move(d, c0)
        self.emit(Lsr(d, c1))
        return d

    @pattern('reg', 'ORI32(reg, reg)', cost=1)
    def P21(self, tree, c0, c1):
        d = self.newTmp()
        self.move(d, c0)
        self.emit(Orr(d, c1))
        return d

    @pattern('reg', 'ANDI32(reg, reg)', cost=1)
    def P22(self, tree, c0, c1):
        d = self.newTmp()
        self.move(d, c0)
        self.emit(And(d, c1))
        return d

    @pattern('reg', 'SHLI32(reg, reg)', cost=1)
    def P23(self, tree, c0, c1):
        d = self.newTmp()
        self.move(d, c0)
        self.emit(Lsl(d, c1))
        return d

    @pattern('reg', 'MULI32(reg, reg)', cost=5)
    def P24(self, tree, c0, c1):
        d = self.newTmp()
        self.move(d, c0)
        # Attention: multiply takes the second argument as use and def:
        self.emit(Mul(c1, d))
        return d

    @pattern('reg', 'DIVI32(reg, reg)', cost=10)
    def P25(self, tree, c0, c1):
        d = self.newTmp()
        self.emit(Sdiv(d, c0, c1))
        return d

    @pattern('reg', 'REMI32(reg, reg)', cost=10)
    def P26(self, tree, c0, c1):
        d2 = self.newTmp()
        self.emit(Sdiv(d2, c0, c1))
        # Multiply result by divider:
        self.emit(Mul(c1, d2))

        # Substract from divident:
        d = self.newTmp()
        self.emit(Sub3(d, c0, d2))
        return d

    @pattern('reg', 'XORI32(reg, reg)', cost=10)
    def P27(self, tree, c0, c1):
        d = self.newTmp()
        self.move(d, c0)
        self.emit(Eor(d, c1))
        return d

# reg: MEMI32(ADDI32(reg, cn))  1 'return tree.children[0].children[1].value < 32' 'd = self.newTmp(); self.emit(Ldr2, dst=[d], src=[c0], others=[c1]); return d'
# addr: reg 0 ''
