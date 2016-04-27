"""
    X86 target descriptions and encodings.

    See for a reference: http://ref.x86asm.net/coder64.html
"""

from ..isa import Instruction, Isa, register_argument, Syntax, Constructor
from ..isa import FixedPattern, VariablePattern
from ...utils.bitfun import wrap_negative
from ..token import Token, u32, u8, u64, bit_range
from .registers import X86Register, rcx, LowRegister, al, rax, rdx

isa = Isa()


# Table 3.1 of the intel manual:
# use REX.W on the table below:


@isa.register_relocation
def apply_b_jmp32(sym_value, data, reloc_value):
    offset = (sym_value - (reloc_value + 5))
    rel24 = wrap_negative(offset, 32)
    data[4] = (rel24 >> 24) & 0xFF
    data[3] = (rel24 >> 16) & 0xFF
    data[2] = (rel24 >> 8) & 0xFF
    data[1] = rel24 & 0xFF


@isa.register_relocation
def apply_bc_jmp32(sym_value, data, reloc_value):
    offset = (sym_value - (reloc_value + 6))
    rel24 = wrap_negative(offset, 32)
    data[5] = (rel24 >> 24) & 0xFF
    data[4] = (rel24 >> 16) & 0xFF
    data[3] = (rel24 >> 8) & 0xFF
    data[2] = rel24 & 0xFF


@isa.register_relocation
def apply_b_jmp8(sym_value, data, reloc_value):
    offset = (sym_value - (reloc_value + 2))
    rel8 = wrap_negative(offset, 8)
    data[1] = rel8


@isa.register_relocation
def apply_abs64(sym_value, data, reloc_value):
    offset = sym_value
    abs64 = wrap_negative(offset, 64)
    data[9] = (abs64 >> 56) & 0xFF
    data[8] = (abs64 >> 48) & 0xFF
    data[7] = (abs64 >> 40) & 0xFF
    data[6] = (abs64 >> 32) & 0xFF
    data[5] = (abs64 >> 24) & 0xFF
    data[4] = (abs64 >> 16) & 0xFF
    data[3] = (abs64 >> 8) & 0xFF
    data[2] = abs64 & 0xFF

# Helper functions:


class Imm8Token(Token):
    def __init__(self):
        super().__init__(8)

    disp8 = bit_range(0, 8)

    def encode(self):
        return u8(self.bit_value)


class OpcodeToken(Token):
    def __init__(self):
        super().__init__(8)

    def encode(self):
        return u8(self.bit_value)


class ModRmToken(Token):
    """ Construct the modrm byte from its components """
    def __init__(self, mod=0, rm=0, reg=0):
        super().__init__(8)
        self.mod = mod
        self.rm = rm
        self.reg = reg

    mod = bit_range(6, 8)
    rm = bit_range(0, 3)
    reg = bit_range(3, 6)

    def encode(self):
        return u8(self.bit_value)


class SibToken(Token):
    def __init__(self, ss=0):
        super().__init__(8)
        self.ss = ss

    ss = bit_range(6, 8)
    index = bit_range(3, 6)
    base = bit_range(0, 3)

    def encode(self):
        return u8(self.bit_value)


class RexToken(Token):
    """ Create a REX prefix byte """
    def __init__(self, w=0, r=0, x=0, b=0):
        super().__init__(8)
        self.w = w
        self.r = r
        self.x = x
        self.b = b
        self.set_bit(6, 1)

    w = bit_range(3, 4)
    r = bit_range(2, 3)
    x = bit_range(1, 2)
    b = bit_range(0, 1)

    def encode(self):
        return u8(self.bit_value)


class Imm32Token(Token):
    def __init__(self):
        super().__init__(32)

    disp32 = bit_range(0, 32)

    def encode(self):
        return u32(self.bit_value)


# def sib(ss=0, index=0, base=0):
#   assert(ss <= 3)
#   assert(index <= 7)
#   assert(base <= 7)
#   return (ss << 6) | (index << 3) | base

# tttn = {'L':0xc,'G':0xf,'NE':0x5,'GE':0xd,'LE':0xe, 'E':0x4}

# Actual instructions:
class X86Instruction(Instruction):
    """ Base instruction for all x86 instructions """
    tokens = [ModRmToken]
    isa = isa


class NearJump(X86Instruction):
    """ jmp imm32 """
    target = register_argument('target', str)
    syntax = Syntax(['jmp', target])
    tokens = [OpcodeToken, Imm32Token]

    def encode(self):
        #opcode = 0x80 | tttn[condition] # Jcc imm32
        #return [0x0F, opcode] + imm32(distance)
        #if distance < 0:
        # distance -= 5 # Skip own instruction
        self.token1[0:8] = 0xe9
        return self.token1.encode() + self.token2.encode()

    def relocations(self):
        return [(self.target, apply_b_jmp32)]


class ConditionalJump(X86Instruction):
    """ j?? imm32 """
    target = register_argument('target', str)
    tokens = [OpcodeToken, OpcodeToken, Imm32Token]

    def encode(self):
        #opcode = 0x80 | tttn[condition] # Jcc imm32
        #return [0x0F, opcode] + imm32(distance)
        #if distance < 0:
        # distance -= 5 # Skip own instruction
        self.token1[0:8] = 0xF
        self.token2[0:8] = self.opcode
        return self.token1.encode() + self.token2.encode() + self.token3.encode()

    def relocations(self):
        return [(self.target, apply_bc_jmp32)]


def make_cjump(mnemonic, opcode):
    syntax = Syntax([mnemonic, ConditionalJump.target])
    members = {'syntax': syntax, 'opcode': opcode}
    return type(mnemonic + '_ins', (ConditionalJump,), members)

Jb = make_cjump('jb', 0x82)
Jae = make_cjump('jae', 0x83)
Je = make_cjump('jz', 0x84)
Jne = make_cjump('jne', 0x85)
Jbe = make_cjump('jbe', 0x86)
Ja = make_cjump('ja', 0x87)

Jl = make_cjump('jl', 0x8c)
Jge = make_cjump('jge', 0x8d)
Jle = make_cjump('jle', 0x8e)
Jg = make_cjump('jg', 0x8f)


class ShortJump(X86Instruction):
    """ jmp imm8 """
    tokens = [OpcodeToken, Imm8Token]
    target = register_argument('target', str)
    syntax = Syntax(['jmpshort', target])

    def encode(self):
        opcode = 0xeb  # jmp rel8
        return bytes([opcode, 0])

    def relocations(self):
        return [(self.target, apply_b_jmp8)]


class Push(X86Instruction):
    reg = register_argument('reg', X86Register, read=True)
    syntax = Syntax(['push', reg])

    def encode(self):
        code = []
        if self.reg.rexbit == 1:
            code.append(0x41)
        code.append(0x50 + self.reg.regbits)
        return bytes(code)


class Pop(X86Instruction):
    reg = register_argument('reg', X86Register, write=True)
    syntax = Syntax(['pop', reg])

    def encode(self):
        code = []
        if self.reg.rexbit == 1:
            code.append(0x41)
        code.append(0x58 + self.reg.regbits)
        return bytes(code)


class Int(X86Instruction):
    nr = register_argument('nr', int)
    syntax = Syntax(['int', nr])
    tokens = [OpcodeToken, Imm8Token]

    def encode(self):
        self.token1[0:8] = 0xcd
        self.token2[0:8] = self.nr
        return self.token1.encode() + self.token2.encode()


class CallReg(X86Instruction):
    reg = register_argument('reg', X86Register, read=True)
    syntax = Syntax(['call', '*', reg])
    tokens = [RexToken, OpcodeToken, ModRmToken]

    def encode(self):
        self.token1.b = self.reg.rexbit
        self.token2[0:8] = 0xFF  # 0xFF /2 == call r/m64
        self.token3.mod = 3
        self.token3.reg = 2
        self.token3.rm = self.reg.regbits
        return self.token1.encode() + self.token2.encode() + \
            self.token3.encode()


class Call(X86Instruction):
    """ call a function """
    target = register_argument('target', str)
    syntax = Syntax(['call', target])
    tokens = [OpcodeToken, Imm32Token]

    def encode(self):
        self.token1[0:8] = 0xe8
        return self.token1.encode() + self.token2.encode()

    def relocations(self):
        return [(self.target, apply_b_jmp32)]


class Ret(X86Instruction):
    syntax = Syntax(['ret'])
    tokens = [OpcodeToken]

    def encode(self):
        self.token1[0:8] = 0xc3
        return self.token1.encode()


class Syscall(X86Instruction):
    syntax = Syntax(['syscall'])
    tokens = [OpcodeToken]

    def encode(self):
        self.token1[0:8] = 0x05
        return bytes([0x0F]) + self.token1.encode()


class Inc(X86Instruction):
    reg = register_argument('reg', X86Register, read=True, write=True)
    syntax = Syntax(['inc', reg])
    tokens = [RexToken, OpcodeToken, ModRmToken]

    def encode(self):
        self.token1.w = 1
        self.token1.b = self.reg.rexbit
        self.token2[0:8] = 0xff
        self.token3.mod = 3
        self.token3.rm = self.reg.regbits
        return self.token1.encode() + self.token2.encode() + \
            self.token3.encode()


class Rm(Constructor):
    syntaxi = 'rm0123'


class RmMem(Rm):
    """ Memory access at memory pointed by register """
    reg = register_argument('reg', X86Register, read=True)
    syntax = Syntax(['[', reg, ']'])

    def set_user_patterns(self, tokens):
        if self.reg.regbits == 5:
            # this is a rip special case, use offset of 0
            self.set_field(tokens, 'mod', 1)
            self.set_field(tokens, 'b', self.reg.rexbit)
            self.set_field(tokens, 'rm', self.reg.regbits)
            self.set_field(tokens, 'disp8', 0)
        elif self.reg.regbits == 4:
            # Switch to sib mode
            self.set_field(tokens, 'mod', 0)
            self.set_field(tokens, 'rm', 4)
            self.set_field(tokens, 'b', self.reg.rexbit)
            self.set_field(tokens, 'ss', 0)
            self.set_field(tokens, 'x', 0)
            self.set_field(tokens, 'index', 4)  # No index
            self.set_field(tokens, 'base', self.reg.regbits)
        else:
            # The 'normal' case
            self.set_field(tokens, 'mod', 0)
            self.set_field(tokens, 'b', self.reg.rexbit)
            self.set_field(tokens, 'rm', self.reg.regbits)


class RmMemDisp(Rm):
    """ register with 8 bit displacement """
    reg = register_argument('reg', X86Register, read=True)
    disp = register_argument('disp', int)
    syntax = Syntax(['[', reg, ',', disp, ']'], priority=2)

    def set_user_patterns(self, tokens):
        if self.disp <= 255 and self.disp >= -128:
            self.set_field(tokens, 'mod', 1)
            self.set_field(tokens, 'disp8', wrap_negative(self.disp, 8))
        else:
            self.set_field(tokens, 'mod', 2)
            self.set_field(tokens, 'disp32', wrap_negative(self.disp, 32))

        if self.reg.regbits == 4:
            # SIB mode:
            self.set_field(tokens, 'b', self.reg.rexbit)
            self.set_field(tokens, 'rm', 4)
            self.set_field(tokens, 'ss', 0)
            self.set_field(tokens, 'x', 0)
            self.set_field(tokens, 'index', 4)  # No index
            self.set_field(tokens, 'base', self.reg.regbits)
        else:
            # Normal mode:
            self.set_field(tokens, 'b', self.reg.rexbit)
            self.set_field(tokens, 'rm', self.reg.regbits)


class RmMemDisp2(Rm):
    """ memory access with base, index and displacement """
    regb = register_argument('regb', X86Register, read=True)
    regi = register_argument('regi', X86Register, read=True)
    disp = register_argument('disp', int)
    syntax = Syntax(['[', regb, ',', regi, ',', disp, ']'], priority=2)

    def set_user_patterns(self, tokens):
        # assert self.regb.regbits != 5
        assert self.regi.regbits != 4
        # SIB mode:
        self.set_field(tokens, 'mod', 1)
        self.set_field(tokens, 'b', self.regb.rexbit)
        self.set_field(tokens, 'rm', 4)
        self.set_field(tokens, 'ss', 0)
        self.set_field(tokens, 'x', self.regi.rexbit)
        self.set_field(tokens, 'index', self.regi.regbits)
        self.set_field(tokens, 'base', self.regb.regbits)
        self.set_field(tokens, 'disp8', wrap_negative(self.disp, 8))


class RmRip(Rm):
    """ rip with 32 bit displacement special case """
    disp = register_argument('disp', int)
    syntax = Syntax(['[', 'rip', ',', disp, ']'])
    patterns = [
        FixedPattern('mod', 0),
        FixedPattern('rm', 5),
        FixedPattern('b', 0)]

    def set_user_patterns(self, tokens):
        self.set_field(tokens, 'disp32', wrap_negative(self.disp, 32))


class RmAbsLabel(Rm):
    """ absolute address access """
    l = register_argument('l', str)
    syntax = Syntax(['[', l, ']'], priority=2)
    patterns = [
        FixedPattern('mod', 0),
        FixedPattern('rm', 4),
        FixedPattern('index', 4),
        FixedPattern('x', 0),
        FixedPattern('b', 0)]

    # TODO
    def set_user_patterns(self, tokens):
        raise NotImplementedError('Rm4')


class RmAbs(Rm):
    """ absolute address access """
    l = register_argument('l', int)
    syntax = Syntax(['[', l, ']'], priority=2)
    patterns = [
        FixedPattern('mod', 0),
        FixedPattern('rm', 4),
        FixedPattern('index', 4),
        FixedPattern('base', 5),
        FixedPattern('x', 0),
        FixedPattern('b', 0)]

    def set_user_patterns(self, tokens):
        self.set_field(tokens, 'disp32', wrap_negative(self.l, 32))


class RmReg(Rm):
    """ Register access, this case is relatively easy """
    reg_rm = register_argument('reg_rm', X86Register, read=True)
    syntax = Syntax([reg_rm])
    patterns = [FixedPattern('mod', 3)]

    def set_user_patterns(self, tokens):
        self.set_field(tokens, 'b', self.reg_rm.rexbit)
        self.set_field(tokens, 'rm', self.reg_rm.regbits)


class rmregbase(X86Instruction):
    tokens = [
        RexToken, OpcodeToken, ModRmToken, SibToken, Imm8Token, Imm32Token]
    patterns = [FixedPattern('w', 1)]

    def set_user_patterns(self, tokens):
        self.set_field(tokens, 'r', self.reg.rexbit)
        self.set_field(tokens, 'reg', self.reg.regbits)

    def encode(self):
        # 1. Set patterns:
        self.set_all_patterns()
        self.token2[0:8] = self.opcode


        # 2. Encode:
        r = self.token1.encode() + self.token2.encode() + self.token3.encode()

        # Encode sib byte:
        if self.token3.mod != 3 and self.token3.rm == 4:
            r += self.token4.encode()

        # Encode displacement bytes:
        if self.token3.mod == 1:
            r += self.token5.encode()
        if self.token3.mod == 2:
            r += self.token6.encode()

        # Rip relative addressing mode with disp32
        if self.token3.mod == 0 and self.token3.rm == 5:
            r += self.token6.encode()

        # sib byte and ...
        if self.token3.mod == 0 and self.token3.rm == 4:
            if self.token4.base == 5:
                r += self.token6.encode()
        return r


def make_rm_reg(mnemonic, opcode, read_op1=True, write_op1=True,
                reg_class=X86Register):
    """ Create instruction class rm, reg """
    rm = register_argument('rm', Rm)
    reg = register_argument('reg', reg_class, read=True)
    syntax = Syntax([mnemonic, rm, ',', reg], priority=0)
    members = {
        'syntax': syntax, 'rm': rm, 'reg': reg, 'opcode': opcode}
    return type(mnemonic + '_ins', (rmregbase,), members)


def make_reg_rm(mnemonic, opcode, read_op1=True, write_op1=True,
                reg_class=X86Register):
    rm = register_argument('rm', Rm)
    reg = register_argument('reg', reg_class, write=write_op1, read=read_op1)
    syntax = Syntax([mnemonic, reg, ',', rm], priority=1)
    members = {
        'syntax': syntax, 'rm': rm, 'reg': reg, 'opcode': opcode}
    return type(mnemonic + '_ins', (rmregbase,), members)


AddRmReg = make_rm_reg('add', 0x1)
AddRegRm = make_reg_rm('add', 0x3)
OrRmReg = make_rm_reg('or', 0x9)
OrRegRm = make_reg_rm('or', 0xb)
AndRmReg = make_rm_reg('and', 0x21)
AndRegRm = make_reg_rm('and', 0x23)
SubRmReg = make_rm_reg('sub', 0x29)
SubRegRm = make_reg_rm('sub', 0x2b)
XorRmReg = make_rm_reg('xor', 0x31)  # opcode = 0x31  # XOR r/m64, r64
XorRegRm = make_reg_rm('xor', 0x33)
CmpRmReg = make_rm_reg('cmp', 0x39, write_op1=False)
MovRmReg8 = make_rm_reg('mov', 0x88, read_op1=False, reg_class=LowRegister)  # mov r/m8, r8
MovRmReg = make_rm_reg('mov', 0x89, read_op1=False)  # mov r/m64, r64
MovRegRm8 = make_reg_rm('mov', 0x8a, read_op1=False, reg_class=LowRegister)  # mov r8, r/m8
MovRegRm = make_reg_rm('mov', 0x8b, read_op1=False)  # mov r64, r/m64

# TODO: implement lea otherwise?
Lea = make_reg_rm('lea', 0x8d, read_op1=False)


class regint32base(X86Instruction):
    tokens = [RexToken, OpcodeToken, ModRmToken, Imm32Token]

    def encode(self):
        self.token1.w = 1
        self.token1.b = self.reg.rexbit
        self.token2[0:8] = self.opcode
        self.token3.mod = 3
        self.token3.rm = self.reg.regbits
        self.token3.reg = self.reg_code
        self.token4[0:32] = wrap_negative(self.imm, 32)
        return self.token1.encode() + self.token2.encode() + self.token3.encode() + self.token4.encode()


def make_regimm(mnemonic, opcode, reg_code):
    reg = register_argument('reg', X86Register, write=True, read=True)
    imm = register_argument('imm', int)
    syntax = Syntax([mnemonic, reg, ',', imm])
    members = {
        'syntax': syntax, 'reg': reg, 'imm': imm, 'opcode': opcode,
        'reg_code': reg_code}
    return type(mnemonic + '_ins', (regint32base,), members)

AddImm = make_regimm('add', 0x81, 0)
AndImm = make_regimm('and', 0x81, 4)
SubImm = make_regimm('sub', 0x81, 5)
XorImm = make_regimm('xor', 0x81, 6)
CmpImm = make_regimm('cmp', 0x81, 7)


class shift_cl_base(X86Instruction):
    rm = register_argument('rm', Rm)
    tokens = [RexToken, OpcodeToken, ModRmToken]
    opcode = 0xd3

    def encode(self):
        self.set_all_patterns()
        self.token1.w = 1
        self.token2[0:8] = self.opcode
        self.token3.reg = self.r
        return self.token1.encode() + self.token2.encode() + self.token3.encode()


class ShrCl(shift_cl_base):
    r = 5
    syntax = Syntax(['shr', shift_cl_base.rm, ',', 'cl'])


class ShlCl(shift_cl_base):
    r = 6
    syntax = Syntax(['shl', shift_cl_base.rm, ',', 'cl'])


class SarCl(shift_cl_base):
    r = 7
    syntax = Syntax(['sar', shift_cl_base.rm, ',', 'cl'])


class Imul(X86Instruction):
    """ Multiply
        imul reg1, reg2
    """
    reg1 = register_argument('reg1', X86Register, write=True, read=True)
    reg2 = register_argument('reg2', X86Register, read=True)
    syntax = Syntax(['imul', reg1, ',', reg2])
    tokens = [RexToken, OpcodeToken, OpcodeToken, ModRmToken]
    opcode = 0x0f  # IMUL r64, r/m64
    opcode2 = 0xaf

    def encode(self):
        self.token1.w = 1
        self.token1.r = self.reg1.rexbit
        self.token1.b = self.reg2.rexbit
        self.token2[0:8] = self.opcode
        self.token3[0:8] = self.opcode2
        self.token4.mod = 3
        self.token4.rm = self.reg2.regbits
        self.token4.reg = self.reg1.regbits
        return self.token1.encode() + self.token2.encode() + \
            self.token3.encode() + self.token4.encode()


class Idiv(X86Instruction):
    """
        idiv reg1
    """
    reg1 = register_argument('reg1', X86Register, read=True)
    syntax = Syntax(['idiv', reg1])
    tokens = [RexToken, OpcodeToken, ModRmToken]
    opcode = 0xf7  # 0xf7 /7 = idiv r/m64

    def encode(self):
        self.token1.w = 1
        self.token1.b = self.reg1.rexbit
        self.token2[0:8] = self.opcode
        self.token3.mod = 3
        self.token3.rm = self.reg1.regbits
        self.token3.reg = 7
        return self.token1.encode() + self.token2.encode() + \
            self.token3.encode()


class MovImm(X86Instruction):
    """ Mov immediate into register """
    reg = register_argument('reg', X86Register, write=True)
    imm = register_argument('imm', int)
    syntax = Syntax(['mov', reg, ',', imm])
    tokens = [RexToken, OpcodeToken]
    opcode = 0xb8  # mov r64, imm64

    def encode(self):
        self.token1.w = 1
        self.token1.b = self.reg.rexbit
        self.token2[0:8] = self.opcode + self.reg.regbits
        return self.token1.encode() + self.token2.encode() + u64(self.imm)


class MovAdr(X86Instruction):
    """ Mov address of label into register """
    reg = register_argument('reg', X86Register, write=True)
    imm = register_argument('imm', str)
    syntax = Syntax(['mov', reg, ',', imm], priority=22)
    tokens = [RexToken, OpcodeToken]
    opcode = 0xb8  # mov r64, imm64

    def encode(self):
        self.token1.w = 1
        self.token1.b = self.reg.rexbit
        self.token2[0:8] = self.opcode + self.reg.regbits
        return self.token1.encode() + self.token2.encode() + u64(0)

    def relocations(self):
        return [(self.imm, apply_abs64)]


@isa.pattern('stm', 'JMP', size=2)
def pattern_jmp(context, tree):
    tgt = tree.value
    context.emit(NearJump(tgt.name, jumps=[tgt]))


@isa.pattern('stm', 'CJMP(reg64, reg64)', size=2)
def pattern_cjmp(context, tree, c0, c1):
    op, yes_label, no_label = tree.value
    opnames = {"<": Jl, ">": Jg, "==": Je, "!=": Jne, ">=": Jge}
    Bop = opnames[op]
    context.emit(CmpRmReg(RmReg(c0), c1))
    jmp_ins = NearJump(no_label.name, jumps=[no_label])
    context.emit(Bop(yes_label.name, jumps=[yes_label, jmp_ins]))
    context.emit(jmp_ins)


@isa.pattern('reg64', 'CALL', size=10)
def pattern_call(context, tree):
    label, arg_types, ret_type, args, res_var = tree.value
    context.gen_call(label, arg_types, ret_type, args, res_var)
    return res_var


# TODO: this should not be required (the MOVI8)
@isa.pattern('reg64', 'MOVI8(reg64)', size=2)
@isa.pattern('reg64', 'MOVI64(reg64)', size=2)
def pattern_mov(context, tree, c0):
    context.move(tree.value, c0)
    return tree.value


@isa.pattern('reg64', 'LDRI64(reg64)', size=2)
def pattern_ldr64(context, tree, c0):
    d = context.new_reg(X86Register)
    context.emit(MovRegRm(d, RmMem(c0)))
    return d


@isa.pattern('reg64', 'LDRI8(reg64)', size=2)
def pattern_ldr8(context, tree, c0):
    d = context.new_reg(X86Register)
    context.emit(XorRegRm(rax, RmReg(rax)))
    context.emit(MovRegRm8(al, RmMem(c0)))
    context.move(d, rax)
    return d


@isa.pattern('stm', 'STRI64(reg64, reg64)', size=2)
def pattern_str64(context, tree, c0, c1):
    context.emit(MovRmReg(RmMem(c0), c1))


@isa.pattern('stm', 'STRI64(ADDI64(reg64, CONSTI64), reg64)', size=4)
def pattern_str64_2(context, tree, c0, c1):
    cnst = tree.children[0].children[1].value
    context.emit(MovRmReg(RmMemDisp(c0, cnst), c1))


@isa.pattern('stm', 'STRI8(reg64, reg64)', size=2)
def pattern_str8(context, tree, c0, c1):
    context.move(rax, c1)
    context.emit(MovRmReg8(RmMem(c0), al))


@isa.pattern('reg64', 'ADDI64(reg64, reg64)', size=2)
def pattern_add64(context, tree, c0, c1):
    d = context.new_reg(X86Register)
    context.move(d, c0)
    context.emit(AddRegRm(d, RmReg(c1)))
    return d


@isa.pattern('reg64', 'ADDI64(reg64, CONSTI64)', size=8)
def pattern_add64_const_2(context, tree, c0):
    d = context.new_reg(X86Register)
    context.move(d, c0)
    context.emit(AddImm(d, tree.children[1].value))
    return d


@isa.pattern('reg64', 'ADDI64(CONSTI64, reg64)', size=8)
def pattern_add64_const_1(context, tree, c0):
    d = context.new_reg(X86Register)
    context.move(d, c0)
    context.emit(AddImm(d, tree.children[0].value))
    return d


@isa.pattern('reg64', 'SUBI64(reg64, reg64)', size=4)
def pattern_sub64(context, tree, c0, c1):
    d = context.new_reg(X86Register)
    context.move(d, c0)
    context.emit(SubRegRm(d, RmReg(c1)))
    return d


@isa.pattern('reg64', 'MULI64(reg64, reg64)', size=4)
def pattern_mul64_(context, tree, c0, c1):
    d = context.new_reg(X86Register)
    context.move(d, c0)
    context.emit(Imul(d, c1))
    return d


@isa.pattern('reg64', 'DIVI64(reg64, reg64)', size=14)
def pattern_div64(context, tree, c0, c1):
    context.move(rax, c0)
    context.emit(MovImm(rdx, 0))
    context.emit(Idiv(c1))
    d = context.new_reg(X86Register)
    context.move(d, rax)
    return d


@isa.pattern('reg64', 'ANDI64(reg64, reg64)', size=4)
def pattern_and64(context, tree, c0, c1):
    d = context.new_reg(X86Register)
    context.move(d, c0)
    context.emit(AndRegRm(d, RmReg(c1)))
    return d


@isa.pattern('reg64', 'ANDI64(reg64, CONSTI64)', size=10)
def pattern_and64_const(context, tree, c0):
    d = context.new_reg(X86Register)
    context.move(d, c0)
    context.emit(AndImm(d, tree.children[1].value))
    return d


@isa.pattern('reg64', 'ORI64(reg64, reg64)', size=4)
def pattern_or64(context, tree, c0, c1):
    d = context.new_reg(X86Register)
    context.move(d, c0)
    context.emit(OrRegRm(d, RmReg(c1)))
    return d


@isa.pattern('reg64', 'SHRI64(reg64, reg64)', size=2)
def pattern_shr64(context, tree, c0, c1):
    d = context.new_reg(X86Register)
    context.move(d, c0)
    context.move(rcx, c1)
    context.emit(ShrCl(RmReg(d)))
    return d


@isa.pattern('reg64', 'SHLI64(reg64, reg64)', size=2)
def pattern_shl64(context, tree, c0, c1):
    d = context.new_reg(X86Register)
    context.move(d, c0)
    context.move(rcx, c1)
    context.emit(ShlCl(RmReg(d)))
    return d


@isa.pattern('reg64', 'REGI64', size=0)
def pattern_reg64_(context, tree):
    return tree.value


@isa.pattern('reg64', 'MOVI64(LABEL)', size=2)
def pattern_mov64_label(context, tree):
    label = tree.children[0].value
    context.emit(MovAdr(tree.value, label))
    return tree.value


@isa.pattern('reg64', 'LABEL', size=2)
def pattern_reg64(context, tree):
    label = tree.value
    d = context.new_reg(X86Register)
    context.emit(MovAdr(d, label))
    return d


@isa.pattern('reg64', 'CONSTI64', size=11)
def pattern_const64(context, tree):
    d = context.new_reg(X86Register)
    context.emit(MovImm(d, tree.value))
    return d


@isa.pattern('reg64', 'CONSTI8', size=11)
def patter_const8(context, tree):
    d = context.new_reg(X86Register)
    context.emit(MovImm(d, tree.value))
    return d
