""" Thumb instruction definitions """

from ..encoding import Instruction, Operand, Syntax
from ..token import u16
from .registers import ArmRegister, LowArmRegister, R7
from .thumb_relocations import Lit8Relocation, WrapNew11Relocation
from .thumb_relocations import BImm11Imm6Relocation
from .thumb_relocations import Rel8Relocation, BlImm11Relocation
from .isa import thumb_isa, ThumbToken

# pylint: disable=no-member,invalid-name


# Instructions:

class ThumbInstruction(Instruction):
    """ Base of all thumb instructions.
    """
    tokens = [ThumbToken]
    isa = thumb_isa


class LongThumbInstruction(ThumbInstruction):
    tokens = [ThumbToken, ThumbToken]


class nop_ins(ThumbInstruction):
    syntax = Syntax(['nop'])

    def encode(self):
        return bytes()


# Memory related

class LS_imm5_base(ThumbInstruction):
    """ ??? Rt, [Rn, imm5] """
    rn = Operand('rn', LowArmRegister, read=True)
    imm5 = Operand('imm5', int)

    def encode(self):
        assert self.imm5 % 4 == 0
        assert self.rn.num < 8
        assert self.rt.num < 8
        Rn = self.rn.num
        Rt = self.rt.num
        imm5 = self.imm5 >> 2
        tokens = self.get_tokens()
        tokens[0][0:3] = Rt
        tokens[0][3:6] = Rn
        tokens[0][6:11] = imm5
        tokens[0][11:16] = self.opcode
        return tokens[0].encode()


class Str2(LS_imm5_base):
    rt = Operand('rt', LowArmRegister, read=True)
    syntax = Syntax([
        'str', ' ', rt, ',', '[', LS_imm5_base.rn,
        ',', ' ', LS_imm5_base.imm5, ']'])
    opcode = 0xC


class Ldr2(LS_imm5_base):
    rt = Operand('rt', LowArmRegister, write=True)
    syntax = Syntax([
        'ldr', ' ', rt, ',', ' ', '[', LS_imm5_base.rn,
        ',', ' ', LS_imm5_base.imm5, ']'])
    opcode = 0xD


class LS_byte_imm5_base(ThumbInstruction):
    """ ??? Rt, [Rn, imm5] """
    rn = Operand('rn', LowArmRegister, read=True)
    imm5 = Operand('imm5', int)

    def encode(self):
        assert self.rn.num < 8
        assert self.rt.num < 8
        Rn = self.rn.num
        Rt = self.rt.num
        imm5 = self.imm5
        tokens = self.get_tokens()
        tokens[0][0:3] = Rt
        tokens[0][3:6] = Rn
        tokens[0][6:11] = imm5
        tokens[0][11:16] = self.opcode
        return tokens[0].encode()


class Strb(LS_byte_imm5_base):
    rt = Operand('rt', LowArmRegister, read=True)
    syntax = Syntax([
        'strb', ' ', rt, ',', ' ', '[', LS_byte_imm5_base.rn, ',', ' ',
        LS_byte_imm5_base.imm5, ']'])
    opcode = 0xE


class Ldrb(LS_byte_imm5_base):
    rt = Operand('rt', LowArmRegister, write=True)
    syntax = Syntax([
        'ldrb', ' ', rt, ',', ' ', '[', LS_byte_imm5_base.rn, ',', ' ',
        LS_byte_imm5_base.imm5, ']'])
    opcode = 0b01111


class Strh(ThumbInstruction):
    """ Strh Rt, [Rn, imm5] """
    rt = Operand('rt', LowArmRegister, read=True)
    rn = Operand('rn', LowArmRegister, read=True)
    imm5 = Operand('imm5', int)
    syntax = Syntax([
        'strh', ' ', rt, ',', ' ', '[', rn, ',', ' ', imm5, ']'])

    def encode(self):
        opcode = 0x10
        assert self.rn.num < 8
        assert self.rt.num < 8
        rn = self.rn.num
        rt = self.rt.num
        imm5 = self.imm5 << 1
        tokens = self.get_tokens()
        tokens[0][0:3] = rt
        tokens[0][3:6] = rn
        tokens[0][6:11] = imm5
        tokens[0][11:16] = opcode
        return tokens[0].encode()


class Ldrh(ThumbInstruction):
    """ Ldrh Rt, [Rn, imm5] """
    rt = Operand('rt', LowArmRegister, write=True)
    rn = Operand('rn', LowArmRegister, read=True)
    imm5 = Operand('imm5', int)
    syntax = Syntax([
        'ldrh', ' ', rt, ',', ' ', '[', rn, ',', ' ', imm5, ']'])

    def encode(self):
        opcode = 0x11
        assert self.rn.num < 8
        assert self.rt.num < 8
        rn = self.rn.num
        rt = self.rt.num
        imm5 = self.imm5
        tokens = self.get_tokens()
        tokens[0][0:3] = rt
        tokens[0][3:6] = rn
        tokens[0][6:11] = imm5
        tokens[0][11:16] = opcode
        return tokens[0].encode()


class ls_sp_base_imm8(ThumbInstruction):
    offset = Operand('offset', int)

    def encode(self):
        rt = self.rt.num
        assert rt < 8
        imm8 = self.offset >> 2
        assert imm8 < 256
        h = (self.opcode << 8) | (rt << 8) | imm8
        return u16(h)


class Ldr3(ThumbInstruction):
    """ ldr Rt, LABEL, load value from pc relative position """
    rt = Operand('rt', LowArmRegister, write=True)
    label = Operand('label', str)
    syntax = Syntax(['ldr', ' ', rt, ',', ' ', label])

    def relocations(self):
        return [Lit8Relocation(self.label)]

    def encode(self):
        rt = self.rt.num
        assert rt < 8
        imm8 = 0
        h = (0x9 << 11) | (rt << 8) | imm8
        return u16(h)


class Ldr1(ls_sp_base_imm8):
    """ ldr Rt, [SP, imm8] """
    rt = Operand('rt', LowArmRegister, write=True)
    opcode = 0x98
    syntax = Syntax(
        ['ldr', ' ', rt, ',', ' ', '[', 'sp', ',',
         ' ', ls_sp_base_imm8.offset, ']'])


class Str1(ls_sp_base_imm8):
    """ str Rt, [SP, imm8] """
    rt = Operand('rt', LowArmRegister, read=True)
    opcode = 0x90
    syntax = Syntax(
        ['str', ' ', rt, ',', ' ', '[', 'sp', ',', ' ',
         ls_sp_base_imm8.offset, ']'])


class Adr(ThumbInstruction):
    rd = Operand('rd', LowArmRegister, write=True)
    label = Operand('label', str)
    syntax = Syntax(['adr', rd, ',', label])

    def relocations(self):
        return [Lit8Relocation(self.label)]

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:8] = 0  # Filled by linker
        tokens[0][8:11] = self.rd.num
        tokens[0][11:16] = 0b10100
        return tokens[0].encode()


class Mov3(ThumbInstruction):
    """ mov Rd, imm8, move immediate value into register """
    opcode = 4   # 00100 Rd(3) imm8
    rd = Operand('rd', LowArmRegister, write=True)
    imm = Operand('imm', int)
    syntax = Syntax(['mov', ' ', rd, ',', ' ', imm])

    def encode(self):
        tokens = self.get_tokens()
        rd = self.rd.num
        tokens[0][8:11] = rd
        tokens[0][0:8] = self.imm
        tokens[0][11:16] = self.opcode
        return tokens[0].encode()

# Arithmatics:


class regregimm3_base(ThumbInstruction):
    rd = Operand('rd', LowArmRegister, write=True)
    rn = Operand('rn', LowArmRegister, read=True)
    imm3 = Operand('imm3', int)

    def encode(self):
        assert self.imm3 < 8
        rd = self.rd.num
        tokens = self.get_tokens()
        tokens[0][0:3] = rd
        tokens[0][3:6] = self.rn.num
        tokens[0][6:9] = self.imm3
        tokens[0][9:16] = self.opcode
        return tokens[0].encode()


class AddImm(regregimm3_base):
    """ add Rd, Rn, imm3 """
    syntax = Syntax([
        'add', ' ', regregimm3_base.rd, ',', ' ', regregimm3_base.rn, ',',
        regregimm3_base.imm3])
    opcode = 0b0001110


class SubImm(regregimm3_base):
    """ sub Rd, Rn, imm3 """
    syntax = Syntax([
        'sub', ' ', regregimm3_base.rd, ',', ' ', regregimm3_base.rn, ',',
        regregimm3_base.imm3])
    opcode = 0b0001111


class regregreg_base(ThumbInstruction):
    """ ??? Rd, Rn, Rm """
    rd = Operand('rd', LowArmRegister, write=True)
    rn = Operand('rn', LowArmRegister, read=True)
    rm = Operand('rm', LowArmRegister, read=True)

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
    syntax = Syntax([
        'add', ' ', regregreg_base.rd, ',', ' ', regregreg_base.rn, ',', ' ',
        regregreg_base.rm])
    opcode = 0b0001100


class Sub3(regregreg_base):
    syntax = Syntax([
        'sub', ' ', regregreg_base.rd, ',', ' ', regregreg_base.rn, ',', ' ',
        regregreg_base.rm])
    opcode = 0b0001101


class Mov2(ThumbInstruction):
    """ mov rd, rm (all registers, also > r7 """
    rd = Operand('rd', ArmRegister, write=True)
    rm = Operand('rm', ArmRegister, read=True)
    syntax = Syntax(['mov', ' ', rd, ',', ' ', rm])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0].rd = self.rd.num & 0x7
        D = (self.rd.num >> 3) & 0x1
        Rm = self.rm.num
        opcode = 0b01000110
        tokens[0][8:16] = opcode
        tokens[0][3:7] = Rm
        tokens[0][7] = D
        return tokens[0].encode()


class Mul(ThumbInstruction):
    """
        mul Rn, Rdm

        multiply Rn and Rm and store the result in Rd
        Rd and Rm are the same register.
    """
    rn = Operand('rn', LowArmRegister, read=True)
    rdm = Operand('rdm', LowArmRegister, read=True, write=True)
    syntax = Syntax(['mul', ' ', rn, ',', ' ', rdm])

    def encode(self):
        tokens = self.get_tokens()
        rn = self.rn.num
        tokens[0].rd = self.rdm.num
        opcode = 0b0100001101
        tokens[0][6:16] = opcode
        tokens[0][3:6] = rn
        return tokens[0].encode()


class Sdiv(LongThumbInstruction):
    """ Signed division.
        Encoding T1
    """
    rd = Operand('rd', ArmRegister, write=True)
    rn = Operand('rn', ArmRegister, read=True)
    rm = Operand('rm', ArmRegister, read=True)
    syntax = Syntax(['sdiv', ' ', rd, ',', ' ', rn, ',', ' ', rm])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][11:16] = 0b11111
        tokens[0][4:11] = 0b0111001
        tokens[0][0:4] = self.rn.num
        tokens[1][12:16] = 0b1111
        tokens[1][8:12] = self.rd.num
        tokens[1][4:8] = 0b1111
        tokens[1][0:4] = self.rm.num
        return tokens[0].encode() + tokens[1].encode()


class regreg_base(ThumbInstruction):
    """ ??? Rdn, Rm """
    def encode(self):
        tokens = self.get_tokens()
        tokens[0].rd = self.rdn.num
        rm = self.rm.num
        tokens[0][3:6] = rm
        tokens[0][6:16] = self.opcode
        return tokens[0].encode()


def make_regreg(mnemonic, opcode):
    rdn = Operand('rdn', LowArmRegister, write=True, read=True)
    rm = Operand('rm', LowArmRegister, read=True)
    syntax = Syntax([mnemonic, rdn, ',', rm])
    members = {'syntax': syntax, 'rdn': rdn, 'rm': rm, 'opcode': opcode}
    return type(mnemonic + '_ins', (regreg_base,), members)


And = make_regreg('and', 0b0100000000)
Orr = make_regreg('orr', 0b0100001100)
Eor = make_regreg('eor', 0b0100000001)
Cmp = make_regreg('cmp', 0b0100001010)
Lsl = make_regreg('lsl', 0b0100000010)
Lsr = make_regreg('lsr', 0b0100000011)
Asr = make_regreg('lsr', 0b0100000100)
Rsb = make_regreg('rsb', 0b0100001001)


class Cmp2(ThumbInstruction):
    """ cmp Rn, imm8 """
    opcode = 5   # 00101
    rn = Operand('rn', LowArmRegister, read=True)
    imm = Operand('imm', int)
    syntax = Syntax(['cmp', rn, ',', imm])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:8] = self.imm
        tokens[0][8:11] = self.rn.num
        tokens[0][11:16] = self.opcode
        return tokens[0].encode()


# Jumping:


class B(ThumbInstruction):
    target = Operand('target', str)
    syntax = Syntax(['b', ' ', target])

    def encode(self):
        h = (0b11100 << 11) | 0
        # | 1 # 1 to enable thumb mode
        return u16(h)

    def relocations(self):
        return [WrapNew11Relocation(self.target)]


class Bw(LongThumbInstruction):
    """ Encoding T4
        Same encoding as Bl, longer jumps are possible with this function!
    """
    target = Operand('target', str)
    syntax = Syntax(['bw', ' ', target])

    def encode(self):
        j1 = 1
        j2 = 1
        tokens = self.get_tokens()
        tokens[0][11:16] = 0b11110
        tokens[1][13] = j1
        tokens[1][11] = j2
        tokens[1][12] = 1
        tokens[1][15] = 1
        return tokens[0].encode() + tokens[1].encode()

    def relocations(self):
        return [BlImm11Relocation(self.target)]


class Bl(LongThumbInstruction):
    """ Branch with link """
    target = Operand('target', str)
    syntax = Syntax(['bl', ' ', target])

    def encode(self):
        j1 = 1  # TODO: what do these mean?
        j2 = 1
        tokens = self.get_tokens()
        tokens[0][11:16] = 0b11110
        tokens[1][13] = j1
        tokens[1][11] = j2
        tokens[1][12] = 1
        tokens[1][14] = 1
        tokens[1][15] = 1
        return tokens[0].encode() + tokens[1].encode()

    def relocations(self):
        return [BlImm11Relocation(self.target)]


class Blx(ThumbInstruction):
    """ Branch with link with target in a register """
    rm = Operand('rm', ArmRegister, read=True)
    syntax = Syntax(['blx', ' ', rm])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][7:16] = 0b010001111
        tokens[0][3:7] = self.rm.num
        tokens[0][0:3] = 0
        return tokens.encode()


class cond_base_ins(ThumbInstruction):
    def encode(self):
        imm8 = 0
        h = (0b1101 << 12) | (self.cond << 8) | imm8
        return u16(h)

    def relocations(self):
        return [Rel8Relocation(self.target)]


def make_cond_branch(mnemonic, cond):
    target = Operand('target', str)
    syntax = Syntax([mnemonic, target])
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
        return [BImm11Imm6Relocation(self.target)]


def make_long_cond_branch(mnemonic, cond):
    target = Operand('target', str)
    syntax = Syntax([mnemonic, target])
    members = {
        'syntax': syntax, 'target': target, 'cond': cond}
    return type(mnemonic + '_ins', (cond_base_ins_long,), members)


Beqw = make_long_cond_branch('beqw', 0)
Bnew = make_long_cond_branch('bnew', 1)
Bhsw = make_long_cond_branch('bhsw', 0b0010)  # unsigned higher or same
Blow = make_long_cond_branch('blow', 0b0011)  # unsigned lower
Bhiw = make_long_cond_branch('bhiw', 0b1000)  # unsigned higher
Blsw = make_long_cond_branch('blsw', 0b1001)  # unsigned lower or same
Bltw = make_long_cond_branch('bltw', 0b1011)  # signed less than
Blew = make_long_cond_branch('blew', 0b1101)  # signed less than or equal
Bgtw = make_long_cond_branch('bgtw', 0b1100)  # signed greater than
Bgew = make_long_cond_branch('bgew', 0b1010)  # signed greater than or equal


def push_bit_pos(n):
    if n < 8:
        return n
    elif n == 14:
        return 8
    else:  # pragma: no cover
        raise NotImplementedError('not implemented for {}'.format(n))


def pop_bit_pos(n):
    if n < 8:
        return n
    elif n == 15:
        return 8
    else:  # pragma: no cover
        raise NotImplementedError('not implemented for {}'.format(n))


class Push(ThumbInstruction):
    regs = Operand('regs', set)
    syntax = Syntax(['push', ' ', regs])

    def __repr__(self):
        return 'Push {{{}}}'.format(self.regs)

    def encode(self):
        tokens = self.get_tokens()
        for n in register_numbers(self.regs):
            tokens[0][push_bit_pos(n)] = 1
        tokens[0][9:16] = 0x5a
        return tokens[0].encode()


def register_numbers(regs):
    for r in regs:
        yield r.num


class Pop(ThumbInstruction):
    regs = Operand('regs', set)
    syntax = Syntax(['pop', ' ', regs])

    def __repr__(self):
        return 'Pop {{{}}}'.format(self.regs)

    def encode(self):
        tokens = self.get_tokens()
        for n in register_numbers(self.regs):
            tokens[0][pop_bit_pos(n)] = 1
        tokens[0][9:16] = 0x5E
        return tokens[0].encode()


class Yield(ThumbInstruction):
    syntax = Syntax(['yield'])

    def encode(self):
        return u16(0xbf10)


class addspsp_base(ThumbInstruction):
    """ add/sub SP with imm7 << 2 """
    imm7 = Operand('imm7', int)

    def encode(self):
        assert self.imm7 < 512
        assert self.imm7 % 4 == 0
        return u16((self.opcode << 7) | self.imm7 >> 2)


class AddSp(addspsp_base):
    syntax = Syntax(
        ['add', ' ', 'sp', ',', ' ', 'sp', ',', ' ', addspsp_base.imm7])
    opcode = 0b101100000


class SubSp(addspsp_base):
    syntax = Syntax(
        ['sub', ' ', 'sp', ',', ' ', 'sp', ',', ' ', addspsp_base.imm7])
    opcode = 0b101100001


# instruction selector:


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

@thumb_isa.pattern('stm', 'JMP', size=2)
def pattern_jmp(context, tree):
    label = tree.value
    context.emit(Bw(label.name, jumps=[label]))


@thumb_isa.pattern('reg', 'REGI32', size=0)
@thumb_isa.pattern('reg', 'REGU32', size=0)
@thumb_isa.pattern('reg', 'REGI16', size=0)
@thumb_isa.pattern('reg', 'REGU16', size=0)
@thumb_isa.pattern('reg', 'REGI8', size=0)
@thumb_isa.pattern('reg', 'REGU8', size=0)
def pattern_reg32(context, tree):
    return tree.value


@thumb_isa.pattern('reg', 'I32TOU32(reg)', size=0)
@thumb_isa.pattern('reg', 'U32TOI32(reg)', size=0)
@thumb_isa.pattern('reg', 'I32TOI32(reg)', size=0)
@thumb_isa.pattern('reg', 'U32TOU32(reg)', size=0)
def pattern_i32toi32(context, tree, c0):
    return c0


@thumb_isa.pattern('reg', 'I16TOI32(reg)', size=0)
@thumb_isa.pattern('reg', 'U16TOI32(reg)', size=0)
@thumb_isa.pattern('reg', 'I16TOU32(reg)', size=0)
@thumb_isa.pattern('reg', 'U16TOU32(reg)', size=0)
def pattern_i16_to_i32(context, tree, c0):
    # TODO: do something?
    return c0


@thumb_isa.pattern('reg', 'I32TOI16(reg)', size=0)
@thumb_isa.pattern('reg', 'I32TOU16(reg)', size=0)
@thumb_isa.pattern('reg', 'U32TOI16(reg)', size=0)
@thumb_isa.pattern('reg', 'U32TOU16(reg)', size=0)
def pattern_i32toi16(context, tree, c0):
    # TODO: do something?
    return c0


@thumb_isa.pattern('reg', 'I8TOI32(reg)', size=0)
@thumb_isa.pattern('reg', 'U8TOI32(reg)', size=0)
@thumb_isa.pattern('reg', 'I8TOU32(reg)', size=0)
@thumb_isa.pattern('reg', 'U8TOU32(reg)', size=0)
def pattern_i8toi32(context, tree, c0):
    # TODO: do something?
    return c0


@thumb_isa.pattern('reg', 'I32TOI8(reg)', size=0)
@thumb_isa.pattern('reg', 'I32TOU8(reg)', size=0)
@thumb_isa.pattern('reg', 'U32TOI8(reg)', size=0)
@thumb_isa.pattern('reg', 'U32TOU8(reg)', size=0)
def pattern_i32toi8(context, tree, c0):
    # TODO: do something?
    return c0


@thumb_isa.pattern('reg', 'ADDI32(reg,reg)', size=2)
@thumb_isa.pattern('reg', 'ADDU32(reg,reg)', size=2)
def pattern_add32(context, tree, c0, c1):
    d = context.new_reg(LowArmRegister)
    context.emit(Add3(d, c0, c1))
    return d


@thumb_isa.pattern('reg', 'ADDI8(reg,reg)', size=1)
def pattern_add8(context, tree, c0, c1):
    d = context.new_reg(LowArmRegister)
    context.emit(Add3(d, c0, c1))
    return d


@thumb_isa.pattern('reg', 'LABEL', size=2)
def pattern_label(context, tree):
    d = context.new_reg(LowArmRegister)
    ln = context.frame.add_constant(tree.value)
    context.emit(Ldr3(d, ln))
    return d


@thumb_isa.pattern(
    'reg', 'FPRELU32', size=9, cycles=9)
def pattern_fprel32(context, tree):
    d = context.new_reg(LowArmRegister)
    c1 = tree.value.offset
    if c1 >= 0:
        if c1 < 8:
            context.emit(AddImm(d, R7, c1))
        elif c1 < 256:
            d2 = context.new_reg(LowArmRegister)
            context.emit(Mov3(d2, c1))
            context.emit(Add3(d, R7, d2))
        else:
            d2 = context.new_reg(LowArmRegister)
            ln = context.frame.add_constant(c1)
            context.emit(Ldr3(d2, ln))
            context.emit(Add3(d, R7, d2))
    else:
        c1 = -c1
        if c1 < 8:
            context.emit(SubImm(d, R7, c1))
        elif c1 < 256:
            d2 = context.new_reg(LowArmRegister)
            context.emit(Mov3(d2, c1))
            context.emit(Sub3(d, R7, d2))
        else:
            d2 = context.new_reg(LowArmRegister)
            ln = context.frame.add_constant(c1)
            context.emit(Ldr3(d2, ln))
            context.emit(Sub3(d, R7, d2))
    return d


@thumb_isa.pattern('reg', 'CONSTI32', size=6, cycles=4, energy=4)
@thumb_isa.pattern('reg', 'CONSTU32', size=6, cycles=4, energy=4)
@thumb_isa.pattern('reg', 'CONSTI16', size=6, cycles=4, energy=4)
@thumb_isa.pattern('reg', 'CONSTU16', size=6, cycles=4, energy=4)
def pattern_const32(context, tree):
    d = context.new_reg(LowArmRegister)
    ln = context.frame.add_constant(tree.value)
    context.emit(Ldr3(d, ln))
    return d


@thumb_isa.pattern(
    'reg', 'CONSTU32', size=2, cycles=1, energy=1,
    condition=lambda x: x.value in range(256))
@thumb_isa.pattern(
    'reg', 'CONSTI32', size=2, cycles=1, energy=1,
    condition=lambda x: x.value in range(256))
def pattern_const32_imm(context, tree):
    """ 8 bit constant loading """
    d = context.new_reg(LowArmRegister)
    context.emit(Mov3(d, tree.value))
    return d


@thumb_isa.pattern('reg', 'CONSTI8', size=6, cycles=4, energy=4)
@thumb_isa.pattern('reg', 'CONSTU8', size=6, cycles=4, energy=4)
def pattern_const8(context, tree):
    d = context.new_reg(LowArmRegister)
    ln = context.frame.add_constant(tree.value)
    context.emit(Ldr3(d, ln))
    return d


@thumb_isa.pattern(
    'reg', 'CONSTI8', size=2, cycles=1, energy=1,
    condition=lambda x: x.value in range(256))
@thumb_isa.pattern(
    'reg', 'CONSTU8', size=2, cycles=1, energy=1,
    condition=lambda x: x.value in range(256))
def pattern_const8_imm(context, tree):
    """ 8 bit constant loading """
    d = context.new_reg(LowArmRegister)
    context.emit(Mov3(d, tree.value))
    return d


@thumb_isa.pattern('stm', 'MOVU32(reg)', size=2)
@thumb_isa.pattern('stm', 'MOVI32(reg)', size=2)
def pattern_mov32(context, tree, c0):
    reg = tree.value
    context.move(reg, c0)


@thumb_isa.pattern('stm', 'MOVI16(reg)', size=2)
@thumb_isa.pattern('stm', 'MOVU16(reg)', size=2)
@thumb_isa.pattern('stm', 'MOVI8(reg)', size=2)
@thumb_isa.pattern('stm', 'MOVU8(reg)', size=2)
def pattern_mov8(context, tree, c0):
    reg = tree.value
    context.move(reg, c0)


@thumb_isa.pattern('stm', 'CJMPI32(reg,reg)', size=6)
@thumb_isa.pattern('stm', 'CJMPI16(reg,reg)', size=6)
@thumb_isa.pattern('stm', 'CJMPI8(reg,reg)', size=6)
def pattern_cjmp_signed(context, tree, c0, c1):
    op, yes_label, no_label = tree.value
    opnames = {"<": Bltw, ">": Bgtw, "==": Beqw, "!=": Bnew, ">=": Bgew}
    Bop = opnames[op]
    jmp_ins = Bw(no_label.name, jumps=[no_label])
    context.emit(Cmp(c0, c1))
    context.emit(Bop(yes_label.name, jumps=[yes_label, jmp_ins]))
    context.emit(jmp_ins)


@thumb_isa.pattern('stm', 'CJMPU32(reg,reg)', size=6)
@thumb_isa.pattern('stm', 'CJMPU16(reg,reg)', size=6)
@thumb_isa.pattern('stm', 'CJMPU8(reg,reg)', size=6)
def pattern_cjmp_unsigned(context, tree, c0, c1):
    op, yes_label, no_label = tree.value
    opnames = {
        "<": Blow, ">": Bhiw,
        "==": Beqw, "!=": Bnew,
        "<=": Blsw, ">=": Bhsw
    }
    Bop = opnames[op]
    jmp_ins = Bw(no_label.name, jumps=[no_label])
    context.emit(Cmp(c0, c1))
    context.emit(Bop(yes_label.name, jumps=[yes_label, jmp_ins]))
    context.emit(jmp_ins)


@thumb_isa.pattern('mem', 'reg', size=0)
def pattern_mem_reg(context, tree, c0):
    return c0, 0


@thumb_isa.pattern('stm', 'STRI8(mem,reg)', size=2)
@thumb_isa.pattern('stm', 'STRU8(mem,reg)', size=2)
def pattern_str8(context, tree, c0, c1):
    rg, offset = c0
    context.emit(Strb(c1, rg, offset))


@thumb_isa.pattern('stm', 'STRI16(mem,reg)', size=2)
@thumb_isa.pattern('stm', 'STRU16(mem,reg)', size=2)
def pattern_str16(context, tree, c0, c1):
    rg, offset = c0
    context.emit(Strh(c1, rg, offset))


@thumb_isa.pattern('stm', 'STRI32(mem, reg)', size=2)
@thumb_isa.pattern('stm', 'STRU32(mem, reg)', size=2)
def pattern_str32(context, tree, c0, c1):
    rg, offset = c0
    context.emit(Str2(c1, rg, offset))


@thumb_isa.pattern('reg', 'LDRI8(mem)', size=2)
@thumb_isa.pattern('reg', 'LDRU8(mem)', size=2)
def pattern_ldr8(context, tree, c0):
    rg, offset = c0
    d = context.new_reg(LowArmRegister)
    context.emit(Ldrb(d, rg, offset))
    return d


@thumb_isa.pattern('reg', 'LDRI16(mem)', size=2)
@thumb_isa.pattern('reg', 'LDRU16(mem)', size=2)
def pattern_ldr16(context, tree, c0):
    rg, offset = c0
    d = context.new_reg(LowArmRegister)
    context.emit(Ldrh(d, rg, offset))
    return d


@thumb_isa.pattern('reg', 'LDRI32(mem)', size=2)
@thumb_isa.pattern('reg', 'LDRU32(mem)', size=2)
def pattern_ldr32(context, tree, c0):
    rg, offset = c0
    d = context.new_reg(LowArmRegister)
    context.emit(Ldr2(d, rg, offset))
    return d


# Arithmatic patterns:
@thumb_isa.pattern('reg', 'SUBU32(reg,reg)', size=2)
@thumb_isa.pattern('reg', 'SUBI32(reg,reg)', size=2)
def pattern_sub32(context, tree, c0, c1):
    d = context.new_reg(LowArmRegister)
    context.emit(Sub3(d, c0, c1))
    return d


@thumb_isa.pattern(
    'reg', 'SUBI32(reg,CONSTI32)', size=2,
    condition=lambda x: x[1].value in range(8))
def pattern_sub32_imm3(context, tree, c0):
    d = context.new_reg(LowArmRegister)
    c1 = tree[1].value
    context.emit(SubImm(d, c0, c1))
    return d


@thumb_isa.pattern('reg', 'SUBI8(reg,reg)', size=2)
def pattern_sub8(context, tree, c0, c1):
    d = context.new_reg(LowArmRegister)
    context.emit(Sub3(d, c0, c1))
    return d


@thumb_isa.pattern('reg', 'SHRI8(reg, reg)', size=4)
@thumb_isa.pattern('reg', 'SHRI16(reg, reg)', size=4)
@thumb_isa.pattern('reg', 'SHRI32(reg, reg)', size=4)
def pattern_shr_i32(context, tree, c0, c1):
    d = context.new_reg(LowArmRegister)
    context.move(d, c0)
    context.emit(Asr(d, c1))
    return d


@thumb_isa.pattern('reg', 'SHRU8(reg, reg)', size=4)
@thumb_isa.pattern('reg', 'SHRU16(reg, reg)', size=4)
@thumb_isa.pattern('reg', 'SHRU32(reg, reg)', size=4)
def pattern_shr_u32(context, tree, c0, c1):
    d = context.new_reg(LowArmRegister)
    context.move(d, c0)
    context.emit(Lsr(d, c1))
    return d


@thumb_isa.pattern('reg', 'NEGI32(reg)', size=2)
@thumb_isa.pattern('reg', 'NEGU32(reg)', size=2)
@thumb_isa.pattern('reg', 'NEGI16(reg)', size=2)
@thumb_isa.pattern('reg', 'NEGU16(reg)', size=2)
@thumb_isa.pattern('reg', 'NEGI8(reg)', size=2)
@thumb_isa.pattern('reg', 'NEGU8(reg)', size=2)
def pattern_neg32(context, tree, c0):
    d = context.new_reg(LowArmRegister)
    context.emit(Rsb(d, c0))
    return d


@thumb_isa.pattern('reg', 'ORI32(reg, reg)', size=4)
@thumb_isa.pattern('reg', 'ORU32(reg, reg)', size=4)
@thumb_isa.pattern('reg', 'ORI16(reg, reg)', size=4)
@thumb_isa.pattern('reg', 'ORU16(reg, reg)', size=4)
@thumb_isa.pattern('reg', 'ORI8(reg, reg)', size=4)
@thumb_isa.pattern('reg', 'ORU8(reg, reg)', size=4)
def pattern_or32(context, tree, c0, c1):
    d = context.new_reg(LowArmRegister)
    context.move(d, c0)
    context.emit(Orr(d, c1))
    return d


@thumb_isa.pattern('reg', 'ANDI32(reg, reg)', size=4)
@thumb_isa.pattern('reg', 'ANDU32(reg, reg)', size=4)
@thumb_isa.pattern('reg', 'ANDI16(reg, reg)', size=4)
@thumb_isa.pattern('reg', 'ANDU16(reg, reg)', size=4)
@thumb_isa.pattern('reg', 'ANDI8(reg, reg)', size=4)
@thumb_isa.pattern('reg', 'ANDU8(reg, reg)', size=4)
def pattern_and32(context, tree, c0, c1):
    d = context.new_reg(LowArmRegister)
    context.move(d, c0)
    context.emit(And(d, c1))
    return d


@thumb_isa.pattern('reg', 'SHLI32(reg, reg)', size=4)
@thumb_isa.pattern('reg', 'SHLU32(reg, reg)', size=4)
@thumb_isa.pattern('reg', 'SHLI16(reg, reg)', size=4)
@thumb_isa.pattern('reg', 'SHLU16(reg, reg)', size=4)
@thumb_isa.pattern('reg', 'SHLI8(reg, reg)', size=4)
@thumb_isa.pattern('reg', 'SHLU8(reg, reg)', size=4)
def pattern_shl32(context, tree, c0, c1):
    d = context.new_reg(LowArmRegister)
    context.move(d, c0)
    context.emit(Lsl(d, c1))
    return d


@thumb_isa.pattern('reg', 'MULI32(reg, reg)', size=5)
@thumb_isa.pattern('reg', 'MULU32(reg, reg)', size=5)
def pattern_mul32(context, tree, c0, c1):
    d = context.new_reg(LowArmRegister)
    context.move(d, c0)
    # Attention: multiply takes the second argument as use and def:
    context.emit(Mul(c1, d))
    return d


@thumb_isa.pattern('reg', 'DIVI32(reg, reg)', size=10)
def pattern_div32(context, tree, c0, c1):
    d = context.new_reg(LowArmRegister)
    context.emit(Sdiv(d, c0, c1))
    return d


@thumb_isa.pattern('reg', 'REMI32(reg, reg)', size=6, cycles=10, energy=5)
def pattern_rem32(context, tree, c0, c1):
    d2 = context.new_reg(LowArmRegister)
    context.emit(Sdiv(d2, c0, c1))
    # Multiply result by divider:
    context.emit(Mul(c1, d2))

    # Substract from divident:
    d = context.new_reg(LowArmRegister)
    context.emit(Sub3(d, c0, d2))
    return d


@thumb_isa.pattern('reg', 'XORI32(reg, reg)', size=4)
@thumb_isa.pattern('reg', 'XORU32(reg, reg)', size=4)
@thumb_isa.pattern('reg', 'XORI16(reg, reg)', size=4)
@thumb_isa.pattern('reg', 'XORU16(reg, reg)', size=4)
@thumb_isa.pattern('reg', 'XORI8(reg, reg)', size=4)
@thumb_isa.pattern('reg', 'XORU8(reg, reg)', size=4)
def pattern_xor32(context, tree, c0, c1):
    d = context.new_reg(LowArmRegister)
    context.move(d, c0)
    context.emit(Eor(d, c1))
    return d
