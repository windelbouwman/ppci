"""
    X86 target descriptions and encodings.
"""

from ..isa import Instruction, Isa, register_argument, Syntax
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


class Mov1(X86Instruction):
    """ Mov r64 to r64 """
    reg1 = register_argument('reg1', X86Register, write=True)
    reg2 = register_argument('reg2', X86Register, read=True)
    syntax = Syntax(['mov', reg1, ',', reg2])
    tokens = [RexToken, OpcodeToken, ModRmToken]

    def encode(self):
        dst = self.reg1
        src = self.reg2
        self.token1.w = 1
        self.token1.r = src.rexbit
        self.token1.b = dst.rexbit
        self.token2[0:8] = 0x89  # mov r/m64, r64
        self.token3.mod = 3
        self.token3.rm = dst.regbits
        self.token3.reg = src.regbits
        return self.token1.encode() + self.token2.encode() + self.token3.encode()


class Mov3a(X86Instruction):
    opcode = 0x8b  # mov r64, r/m64


class regregbase(X86Instruction):
    args = [('reg1', X86Register), ('reg2', X86Register)]
    tokens = [RexToken, OpcodeToken, ModRmToken]

    def encode(self):
        self.token.w = 1
        self.token.r = self.reg2.rexbit
        self.token.b = self.reg1.rexbit
        self.token2[0:8] = self.opcode
        self.token3.mod = 3
        self.token3.rm = self.reg1.regbits
        self.token3.reg = self.reg2.regbits
        return self.token.encode() + self.token2.encode() + self.token3.encode()


def make_regreg(mnemonic, opcode):
    reg1 = register_argument('reg1', X86Register, write=True, read=True)
    reg2 = register_argument('reg2', X86Register, read=True)
    syntax = Syntax([mnemonic, reg1, ',', reg2])
    members = {
        'syntax': syntax, 'reg1': reg1, 'reg2': reg2, 'opcode': opcode}
    return type(mnemonic + '_ins', (regregbase,), members)


# opcode = 0x31  # XOR r/m64, r64
Xor1 = make_regreg('xor', 0x31)
Add = make_regreg('add', 0x1)
Sub = make_regreg('sub', 0x29)


class Cmp(regregbase):
    reg1 = register_argument('reg1', X86Register, write=True, read=True)
    reg2 = register_argument('reg2', X86Register, read=True)
    syntax = Syntax(['cmp', reg1, ',', reg2])
    opcode = 0x39  # CMP r/m64, r64


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

Add2 = make_regimm('add', 0x81, 0)
Sub2 = make_regimm('sub', 0x81, 5)


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
