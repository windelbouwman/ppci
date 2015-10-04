"""
    X86 target descriptions and encodings.
"""

from ..isa import Instruction, Isa, register_argument, Syntax, Constructor
from .registers import X86Register
from ...bitfun import wrap_negative

from ..token import Token, u32, u8, bit_range

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
def apply_b_jmp8(sym_value, data, reloc_value):
    offset = (sym_value - (reloc_value + 2))
    rel8 = wrap_negative(offset, 8)
    data[1] = rel8


# Helper functions:


class ByteToken(Token):
    def __init__(self):
        super().__init__(8)

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


class ShortJump(X86Instruction):
    """ jmp imm8 """
    tokens = [OpcodeToken, ByteToken]
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
    tokens = [OpcodeToken, ByteToken]

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
        return self.token1.encode() + self.token2.encode() + self.token3.encode()


class Rm(Constructor):
    syntaxi = 'rm0123'


class Rm0(Rm):
    """ Memory access at memory in register """
    reg_rm = register_argument('reg_rm', X86Register, read=True)
    syntax = Syntax(['[', reg_rm, ']'])
    mod = 0


class Rm1(Rm):
    """ register with 8 bit displacement """
    reg_rm = register_argument('reg_rm', X86Register, read=True)
    disp = register_argument('disp', int)
    syntax = Syntax(['[', reg_rm, ',', disp, ']'])
    mod = 1


class Rm2(Rm):
    """ register with 32 bit displacement """
    reg_rm = register_argument('reg_rm', X86Register, read=True)
    disp = register_argument('disp', int)
    syntax = Syntax(['[', reg_rm, ',', disp, ']'])
    mod = 2


class RmRegister(Rm):
    """ Register access """
    reg_rm = register_argument('reg_rm', X86Register, read=True)
    syntax = Syntax([reg_rm])
    mod = 3


class rmregbase(X86Instruction):
    tokens = [RexToken, OpcodeToken, ModRmToken, SibToken]

    def encode(self):
        self.token.w = 1
        self.token.r = self.reg.rexbit
        self.token.b = self.rm1.reg_rm.rexbit
        self.token2[0:8] = self.opcode
        self.token3.mod = self.rm1.mod
        self.token3.rm = self.rm1.reg_rm.regbits
        self.token3.reg = self.reg.regbits
        sib = bytes()
        if self.rm1.reg_rm.num == 12 and self.rm1.mod != 3:
            self.token4.ss = 0
            self.token.x = 0
            self.token4.index = 4
            self.token4.base = self.rm1.reg_rm.regbits
            sib = self.token4.encode()
        extra = list()
        if self.rm1.mod == 1:
            extra += [self.rm1.disp]
        return self.token.encode() + self.token2.encode() + \
            self.token3.encode() + sib + bytes(extra)


def make_rm_reg(mnemonic, opcode):
    rm1 = register_argument('rm1', Rm)
    reg = register_argument('reg', X86Register, read=True)
    syntax = Syntax([mnemonic, rm1, ',', reg], priority=2)
    members = {
        'syntax': syntax, 'rm1': rm1, 'reg': reg, 'opcode': opcode}
    return type(mnemonic + '_ins', (rmregbase,), members)


def make_reg_rm(mnemonic, opcode):
    rm1 = register_argument('rm1', Rm)
    reg = register_argument('reg', X86Register, write=True, read=True)
    syntax = Syntax([mnemonic, reg, ',', rm1])
    members = {
        'syntax': syntax, 'rm1': rm1, 'reg': reg, 'opcode': opcode}
    return type(mnemonic + '_ins', (rmregbase,), members)


Add1 = make_rm_reg('add', 0x1)
Add2 = make_reg_rm('add', 0x3)
Or1 = make_rm_reg('or', 0x9)
And1 = make_rm_reg('and', 0x21)
And2 = make_reg_rm('and', 0x23)
Sub1 = make_rm_reg('sub', 0x29)
Sub2 = make_reg_rm('sub', 0x2b)
Xor1 = make_rm_reg('xor', 0x31)  # opcode = 0x31  # XOR r/m64, r64
Xor2 = make_reg_rm('xor', 0x33)
Cmp = make_rm_reg('cmp', 0x39)
Mov1 = make_rm_reg('mov', 0x89)  # mov r/m64, r64
Mov2 = make_reg_rm('mov', 0x8b)  # mov r64, r/m64
Lea = make_reg_rm('lea', 0x8d)


class regint32base(X86Instruction):
    tokens = [RexToken, OpcodeToken, ModRmToken, Imm32Token]

    def encode(self):
        self.token.w = 1
        self.token.b = self.reg.rexbit
        self.token2[0:8] = self.opcode
        self.token3.mod = 3
        self.token3.rm = self.reg.regbits
        self.token3.reg = self.reg_code
        self.token4[0:32] = wrap_negative(self.imm, 32)
        return self.token.encode() + self.token2.encode() + self.token3.encode() + self.token4.encode()


def make_regimm(mnemonic, opcode, reg_code):
    reg = register_argument('reg', X86Register, write=True, read=True)
    imm = register_argument('imm', int)
    syntax = Syntax([mnemonic, reg, ',', imm])
    members = {
        'syntax': syntax, 'reg': reg, 'imm': imm, 'opcode': opcode,
        'reg_code': reg_code}
    return type(mnemonic + '_ins', (regint32base,), members)

Add3 = make_regimm('add', 0x81, 0)
Sub3 = make_regimm('sub', 0x81, 5)


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
        self.token.w = 1
        self.token.r = self.reg1.rexbit
        self.token.b = self.reg2.rexbit
        self.token2[0:8] = self.opcode
        self.token3[0:8] = self.opcode2
        self.token4.mod = 3
        self.token4.rm = self.reg2.regbits
        self.token4.reg = self.reg1.regbits
        return self.token.encode() + self.token2.encode() + \
            self.token3.encode() + self.token4.encode()


@isa.pattern('stm', 'JMP', cost=2)
def _(context, tree):
    tgt = tree.value
    context.emit(NearJump(tgt.name, jumps=[tgt]))


@isa.pattern('reg64', 'CALL', cost=10)
def _(context, tree):
    tgt, args, rv = tree.value
    # TODO!!
    return rv


@isa.pattern('reg8', 'MOVI8(reg8)', cost=2)
def _(context, tree, c0):
    context.move(tree.value, c0)
    return tree.value


@isa.pattern('reg64', 'MOVI64(reg64)', cost=2)
def _(context, tree, c0):
    context.move(tree.value, c0)
    return tree.value


@isa.pattern('reg64', 'REGI64', cost=0)
def _(context, tree):
    return tree.value


@isa.pattern('reg64', 'MOVI64(LABEL)', cost=2)
def _(context, tree):
    # TODO!
    src = context.new_tmp()
    context.emit(Lea(tree.value, Rm2(src, 100)))
    return tree.value


@isa.pattern('reg64', 'MOVI8(CONSTI8)', cost=2)
def _(context, tree):
    # context.emit(Movi8(reg))
    return tree.value


@isa.pattern('reg64', 'MOVI64(CONSTI64)', cost=2)
def _(context, tree):
    # context.emit(Movi8(reg))
    return tree.value
