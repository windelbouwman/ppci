""" X86 target descriptions and encodings.

See for a reference: http://ref.x86asm.net/coder64.html
"""

from ..generic_instructions import Label, RegisterUseDef
from ..isa import Isa
from ..encoding import Instruction, Operand, Syntax, Constructor, Relocation
from ...utils.bitfun import wrap_negative
from ..token import Token, u8, u16, u32, u64, bit_range, bit
from .registers import rcx, al, cl, rax, rdx, rbp, eax, edx, ecx, cx
from .registers import rsp, ax, Register32
from .registers import Register64, Register16, Register8

isa = Isa()


# Table 3.1 of the intel manual:
# use REX.W on the table below:


# Helper functions:


class Imm8Token(Token):
    class Info:
        size = 8

    disp8 = bit_range(0, 8, signed=True)


class PrefixToken(Token):
    class Info:
        size = 8

    prefix = bit_range(0, 8)


class Prefix2Token(Token):
    class Info:
        size = 8

    prefix2 = bit_range(0, 8)


class OpcodeToken(Token):
    """ Primary opcode """
    class Info:
        size = 8

    opcode = bit_range(0, 8)


class SecondaryOpcodeToken(Token):
    """ Secondary opcode """
    class Info:
        size = 8

    opcode2 = bit_range(0, 8)


class ModRmToken(Token):
    """ Construct the modrm byte from its components """
    class Info:
        size = 8

    def __init__(self, mod=0, rm=0, reg=0):
        super().__init__()
        self.mod = mod
        self.rm = rm
        self.reg = reg

    mod = bit_range(6, 8)
    rm = bit_range(0, 3)
    reg = bit_range(3, 6)


class SibToken(Token):
    class Info:
        size = 8

    def __init__(self, ss=0):
        super().__init__()
        self.ss = ss

    ss = bit_range(6, 8)
    index = bit_range(3, 6)
    base = bit_range(0, 3)


class RexToken(Token):
    """ Create a REX prefix byte """
    class Info:
        size = 8

    def __init__(self, w=0, r=0, x=0, b=0):
        super().__init__()
        self.w = w
        self.r = r
        self.x = x
        self.b = b
        self.set_bit(6, 1)

    w = bit(3)
    r = bit(2)
    x = bit(1)
    b = bit(0)


class RexOpcodeRmToken(Token):
    """ A single token that combines rex prefix, opcode and mod rm """
    class Info:
        size = 24

    w = bit(1)


class Imm32Token(Token):
    class Info:
        size = 32

    disp32 = bit_range(0, 32)


class Imm64Token(Token):
    class Info:
        size = 64

    disp64 = bit_range(0, 64)


@isa.register_relocation
class Rel32JmpRelocation(Relocation):
    token = Imm32Token
    field = 'disp32'
    name = 'rel32'

    def calc(self, sym_value, reloc_value):
        offset = (sym_value - (reloc_value + 4))
        return offset


@isa.register_relocation
class Abs32Relocation(Relocation):
    """ Absolute 32 bit relocation value """
    token = Imm32Token
    field = 'disp32'
    name = 'abs32'

    def calc(self, sym_value, reloc_value):
        return sym_value


@isa.register_relocation
class Jmp8Relocation(Relocation):
    token = Imm8Token
    field = 'disp8'
    name = 'jmp8'

    def calc(self, sym_value, reloc_value):
        offset = (sym_value - (reloc_value + 1))
        return offset


@isa.register_relocation
class Abs64Relocation(Relocation):
    token = Imm64Token
    field = 'disp64'
    name = 'abs64'

    def calc(self, sym_value, reloc_value):
        return wrap_negative(sym_value, 64)


# Actual instructions:
class X86Instruction(Instruction):
    """ Base instruction for all x86 instructions """
    tokens = [ModRmToken]
    isa = isa


class NearJump(X86Instruction):
    """ jmp imm32 """
    target = Operand('target', str)
    syntax = Syntax(['jmp', ' ', target])
    tokens = [OpcodeToken, Imm32Token]
    patterns = {'opcode': 0xe9}

    def relocations(self):
        return [Rel32JmpRelocation(self.target, offset=1)]


class ConditionalJump(X86Instruction):
    """ j?? imm32 """
    target = Operand('target', str)
    tokens = [PrefixToken, OpcodeToken, Imm32Token]

    def relocations(self):
        return [Rel32JmpRelocation(self.target, offset=2)]


def make_cjump(mnemonic, opcode):
    syntax = Syntax([mnemonic, ' ', ConditionalJump.target])
    patterns = {'prefix': 0xF, 'opcode': opcode}
    members = {'syntax': syntax, 'patterns': patterns}
    return type(mnemonic.title(), (ConditionalJump,), members)


Jb = make_cjump('jb', 0x82)  # cf=1
Jae = make_cjump('jae', 0x83)  # cf=0
Je = make_cjump('jz', 0x84)
Jne = make_cjump('jne', 0x85)
Jbe = make_cjump('jbe', 0x86)
Ja = make_cjump('ja', 0x87)
Js = make_cjump('js', 0x88)

Jl = make_cjump('jl', 0x8c)
Jge = make_cjump('jge', 0x8d)
Jle = make_cjump('jle', 0x8e)
Jg = make_cjump('jg', 0x8f)


class ShortJump(X86Instruction):
    """ jmp imm8 """
    tokens = [OpcodeToken, Imm8Token]
    target = Operand('target', str)
    syntax = Syntax(['jmpshort', target])
    patterns = {'opcode': 0xeb}

    def relocations(self):
        return [Jmp8Relocation(self.target, offset=1)]


class Push(X86Instruction):
    """ Push a register onto the stack """
    reg = Operand('reg', Register64, read=True)
    syntax = Syntax(['push', ' ', reg])

    def encode(self):
        code = []
        if self.reg.rexbit == 1:
            code.append(0x41)
        code.append(0x50 + self.reg.regbits)
        return bytes(code)


class Pop(X86Instruction):
    """ Pop a register of the stack """
    reg = Operand('reg', Register64, write=True)
    syntax = Syntax(['pop', ' ', reg])

    def encode(self):
        code = []
        if self.reg.rexbit == 1:
            code.append(0x41)
        code.append(0x58 + self.reg.regbits)
        return bytes(code)


class Int(X86Instruction):
    """ Trigger an interrupt """
    nr = Operand('nr', int)
    syntax = Syntax(['int', ' ', nr])
    tokens = [OpcodeToken, Imm8Token]
    patterns = {'opcode': 0xcd, 'disp8': nr}


class CallReg(X86Instruction):
    reg = Operand('reg', Register64, read=True)
    syntax = Syntax(['call', ' ', '*', reg])
    tokens = [RexToken, OpcodeToken, ModRmToken]

    def encode(self):
        tokens = self.get_tokens()
        tokens[0].b = self.reg.rexbit
        tokens[1][0:8] = 0xFF  # 0xFF /2 == call r/m64
        tokens[2].mod = 3
        tokens[2].reg = 2
        tokens[2].rm = self.reg.regbits
        return tokens.encode()


class Call(X86Instruction):
    """ call a function """
    target = Operand('target', str)
    syntax = Syntax(['call', ' ', target])
    tokens = [OpcodeToken, Imm32Token]
    patterns = {'opcode': 0xe8}

    def relocations(self):
        return [Rel32JmpRelocation(self.target, offset=1)]


class Ret(X86Instruction):
    syntax = Syntax(['ret'])
    tokens = [OpcodeToken]
    patterns = {'opcode': 0xc3}


class Syscall(X86Instruction):
    syntax = Syntax(['syscall'])
    tokens = [OpcodeToken, SecondaryOpcodeToken]
    patterns = {'opcode': 0x0f, 'opcode2': 0x05}


class Inc(X86Instruction):
    reg = Operand('reg', Register64, read=True, write=True)
    syntax = Syntax(['inc', ' ', reg])
    tokens = [RexToken, OpcodeToken, ModRmToken]
    patterns = {'w': 1, 'opcode': 0xff, 'mod': 3}

    def encode(self):
        tokens = self.get_tokens()
        self.set_all_patterns(tokens)
        # TODO: figure good way for this so that it is in patterns also:
        tokens.set_field('b', self.reg.rexbit)
        tokens.set_field('rm', self.reg.regbits)
        return tokens.encode()


class RmMem(Constructor):
    """ Memory access at memory pointed by register """
    reg = Operand('reg', Register64, read=True)
    syntax = Syntax(['[', reg, ']'])

    def set_user_patterns(self, tokens):
        if self.reg.regbits == 5:
            # this is a rip special case, use offset of 0
            tokens.set_field('mod', 1)
            tokens.set_field('b', self.reg.rexbit)
            tokens.set_field('rm', self.reg.regbits)
            tokens.set_field('disp8', 0)
        elif self.reg.regbits == 4:
            # Switch to sib mode
            tokens.set_field('mod', 0)
            tokens.set_field('rm', 4)
            tokens.set_field('b', self.reg.rexbit)
            tokens.set_field('ss', 0)
            tokens.set_field('x', 0)
            tokens.set_field('index', 4)  # No index
            tokens.set_field('base', self.reg.regbits)
        else:
            # The 'normal' case
            tokens.set_field('mod', 0)
            tokens.set_field('b', self.reg.rexbit)
            tokens.set_field('rm', self.reg.regbits)


class RmMemDisp(Constructor):
    """ register with 8 bit displacement """
    reg = Operand('reg', Register64, read=True)
    disp = Operand('disp', int)
    syntax = Syntax(['[', reg, ',', ' ', disp, ']'], priority=2)

    def set_user_patterns(self, tokens):
        if self.disp <= 127 and self.disp >= -128:
            tokens.set_field('mod', 1)
            tokens.set_field('disp8', self.disp)
        else:
            tokens.set_field('mod', 2)
            tokens.set_field('disp32', self.disp)

        if self.reg.regbits == 4:
            # SIB mode:
            tokens.set_field('b', self.reg.rexbit)
            tokens.set_field('rm', 4)
            tokens.set_field('ss', 0)
            tokens.set_field('x', 0)
            tokens.set_field('index', 4)  # No index
            tokens.set_field('base', self.reg.regbits)
        else:
            # Normal mode:
            tokens.set_field('b', self.reg.rexbit)
            tokens.set_field('rm', self.reg.regbits)


class RmMemDisp2(Constructor):
    """ memory access with base, index and displacement """
    regb = Operand('regb', Register64, read=True)
    regi = Operand('regi', Register64, read=True)
    disp = Operand('disp', int)
    syntax = Syntax(
        ['[', regb, ',', ' ', regi, ',', ' ', disp, ']'], priority=2)
    patterns = {'mod': 1, 'rm': 4, 'ss': 0}

    def set_user_patterns(self, tokens):
        # assert self.regb.regbits != 5
        assert self.regi.regbits != 4
        # SIB mode:
        tokens.set_field('b', self.regb.rexbit)
        tokens.set_field('x', self.regi.rexbit)
        tokens.set_field('index', self.regi.regbits)
        tokens.set_field('base', self.regb.regbits)
        tokens.set_field('disp8', self.disp)


class RmRip(Constructor):
    """ rip with 32 bit displacement special case """
    disp = Operand('disp', int)
    syntax = Syntax(['[', 'rip', ',', ' ', disp, ']'])
    patterns = {'mod': 0, 'rm': 5, 'b': 0}

    def set_user_patterns(self, tokens):
        tokens.set_field('disp32', self.disp)


class RmAbsLabel(Constructor):
    """ absolute address access """
    l = Operand('l', str)
    syntax = Syntax(['[', l, ']'], priority=2)
    patterns = {
        'mod': 0, 'rm': 4, 'index': 4, 'x': 0, 'b': 0, 'ss': 0, 'base': 5
    }

    def set_user_patterns(self, tokens):
        pass

    def gen_relocations(self):
        # TODO: this offset is from the end of all possible tokens..
        yield Abs32Relocation(self.l, offset=-5)


class RmAbs(Constructor):
    """ absolute address access """
    l = Operand('l', int)
    syntax = Syntax(['[', l, ']'], priority=2)
    patterns = {'mod': 0, 'rm': 4, 'index': 4, 'base': 5, 'x': 0, 'b': 0}

    def set_user_patterns(self, tokens):
        tokens.set_field('disp32', self.l)


class RmReg64(Constructor):
    """ Register access, this case is relatively easy """
    reg_rm = Operand('reg_rm', Register64, read=True)
    syntax = Syntax([reg_rm])
    patterns = {'mod': 3}

    def set_user_patterns(self, tokens):
        tokens.set_field('b', self.reg_rm.rexbit)
        tokens.set_field('rm', self.reg_rm.regbits)


class RmReg32(Constructor):
    """ Register access, this case is relatively easy """
    reg_rm = Operand('reg_rm', Register32, read=True)
    syntax = Syntax([reg_rm])
    patterns = {'mod': 3}

    def set_user_patterns(self, tokens):
        tokens.set_field('b', self.reg_rm.rexbit)
        tokens.set_field('rm', self.reg_rm.regbits)


class RmReg16(Constructor):
    """ Short register access """
    reg_rm = Operand('reg_rm', Register16, read=True)
    syntax = Syntax([reg_rm])
    patterns = {'mod': 3}

    def set_user_patterns(self, tokens):
        tokens.set_field('rm', self.reg_rm.num)


class RmReg8(Constructor):
    """ Low register access """
    reg_rm = Operand('reg_rm', Register8, read=True)
    syntax = Syntax([reg_rm])
    patterns = {'mod': 3}

    def set_user_patterns(self, tokens):
        tokens.set_field('b', self.reg_rm.rexbit)
        tokens.set_field('rm', self.reg_rm.regbits)


mem_modes = (RmMem, RmMemDisp, RmMemDisp2)
rm64_modes = mem_modes + (RmReg64, RmRip, RmAbsLabel, RmAbs)
rm8_modes = mem_modes + (RmReg8,)
rm16_modes = mem_modes + (RmReg16,)
rm32_modes = mem_modes + (RmReg32,)


class rmregbase64(X86Instruction):
    """
        Base class for legio instructions involving a register and a
        register / memory location
    """
    tokens = [
        RexToken, OpcodeToken, ModRmToken, SibToken, Imm8Token, Imm32Token]
    patterns = {'w': 1}

    def set_user_patterns(self, tokens):
        tokens.set_field('r', self.reg.rexbit)
        tokens.set_field('reg', self.reg.regbits)
        tokens.set_field('opcode', self.opcode)

    def encode(self):
        # 1. Set patterns:
        tokens = self.get_tokens()
        self.set_all_patterns(tokens)

        # 2. Encode:
        # Rex prefix:
        r = tokens[0].encode()

        # opcode:
        r += tokens[1].encode()
        if self.opcode == 0x0f:
            tokens[1][0:8] = self.opcode2
            r += tokens[1].encode()
            tokens[1][0:8] = self.opcode

        # rm byte:
        r += tokens[2].encode()

        # Encode sib byte:
        if tokens[2].mod != 3 and tokens[2].rm == 4:
            r += tokens[3].encode()

        # Encode displacement bytes:
        if tokens[2].mod == 1:
            r += tokens[4].encode()
        if tokens[2].mod == 2:
            r += tokens[5].encode()

        # Rip relative addressing mode with disp32
        if tokens[2].mod == 0 and tokens[2].rm == 5:
            r += tokens[5].encode()

        # sib byte and ...
        if tokens[2].mod == 0 and tokens[2].rm == 4:
            if tokens[3].base == 5:
                r += tokens[5].encode()
        return r


class RmBase(rmregbase64):
    def set_user_patterns(self, tokens):
        tokens.set_field('reg', self.reg)
        tokens.set_field('opcode', self.opcode)


class rmregbase32(X86Instruction):
    """
        Base class for legio instructions involving a register and a
        register / memory location
    """
    tokens = [
        RexToken, OpcodeToken, ModRmToken, SibToken, Imm8Token, Imm32Token]
    patterns = {'w': 0}  # Switch w=0 meaning -> 32 bits

    def set_user_patterns(self, tokens):
        tokens.set_field('r', self.reg.rexbit)
        tokens.set_field('reg', self.reg.regbits)
        tokens.set_field('opcode', self.opcode)

    def encode(self):
        # 1. Set patterns:
        tokens = self.get_tokens()
        self.set_all_patterns(tokens)

        # 2. Encode:
        # Rex prefix:
        r = tokens[0].encode()

        # opcode:
        r += tokens[1].encode()
        if self.opcode == 0x0f:
            tokens[1][0:8] = self.opcode2
            r += tokens[1].encode()
            tokens[1][0:8] = self.opcode

        # rm byte:
        r += tokens[2].encode()

        # Encode sib byte:
        if tokens[2].mod != 3 and tokens[2].rm == 4:
            r += tokens[3].encode()

        # Encode displacement bytes:
        if tokens[2].mod == 1:
            r += tokens[4].encode()
        if tokens[2].mod == 2:
            r += tokens[5].encode()

        # Rip relative addressing mode with disp32
        if tokens[2].mod == 0 and tokens[2].rm == 5:
            r += tokens[5].encode()

        # sib byte and ...
        if tokens[2].mod == 0 and tokens[2].rm == 4:
            if tokens[3].base == 5:
                r += tokens[5].encode()
        return r


class RmBase32(rmregbase32):
    def set_user_patterns(self, tokens):
        tokens.set_field('reg', self.reg)
        tokens.set_field('opcode', self.opcode)


class rmregbase16(X86Instruction):
    tokens = [
        PrefixToken, RexToken, OpcodeToken, ModRmToken, SibToken,
        Imm8Token, Imm32Token,
        ]

    patterns = {'prefix': 0x66}

    def set_user_patterns(self, tokens):
        tokens.set_field('reg', self.reg.num)

    def encode(self):
        # 1. Set patterns:
        tokens = self.get_tokens()
        self.set_all_patterns(tokens)
        tokens.set_field('opcode', self.opcode)

        # 2. Encode:
        # prefixes:
        r = tokens[0].encode()
        r += tokens[1].encode()

        # opcode:
        r += tokens[2].encode()

        # rm byte:
        rm = tokens[3]
        r += rm.encode()

        # Encode sib byte:
        sib = tokens[4]
        if rm.mod != 3 and rm.rm == 4:
            r += sib.encode()

        # Encode displacement bytes:
        if rm.mod == 1:
            r += tokens[5].encode()
        if rm.mod == 2:
            r += tokens[6].encode()

        # Rip relative addressing mode with disp32
        if rm.mod == 0 and rm.rm == 5:
            r += tokens[6].encode()

        # sib byte and ...
        if rm.mod == 0 and rm.rm == 4:
            if tokens[3].base == 5:
                r += tokens[6].encode()
        return r


class RmBase16(rmregbase16):
    def set_user_patterns(self, tokens):
        tokens.set_field('reg', self.reg)
        tokens.set_field('opcode', self.opcode)


def make_rm64(mnemonic, opcode, o):
    """ Create an instruction taking a 64 bit r/m operand """
    rm = Operand('rm', rm64_modes)
    syntax = Syntax([mnemonic, ' ', rm], priority=2)
    members = {
        'syntax': syntax, 'rm': rm, 'opcode': opcode, 'reg': o,
    }
    return type(mnemonic.title(), (RmBase,), members)


def make_rm32(mnemonic, opcode, o):
    """ Create an instruction taking a 32 bit r/m operand """
    rm = Operand('rm', rm32_modes)
    syntax = Syntax([mnemonic, ' ', rm], priority=2)
    members = {
        'syntax': syntax, 'rm': rm, 'opcode': opcode, 'reg': o,
    }
    return type(mnemonic.title(), (RmBase,), members)


def make_rm16(mnemonic, opcode, o):
    """ Create an instruction taking a 16 bit r/m operand """
    rm = Operand('rm', rm16_modes)
    syntax = Syntax([mnemonic, ' ', rm], priority=2)
    members = {
        'syntax': syntax, 'rm': rm, 'opcode': opcode, 'reg': o,
    }
    return type(mnemonic.title(), (RmBase16,), members)


Dec = make_rm64('dec', 0xff, 1)
Jmp = make_rm64('jmp', 0xff, 4)
# Inc = make_rm('jmp', 0xff, 4)


def make_rm_reg64(mnemonic, opcode, read_op1=True, write_op1=True):
    """ Create instruction class rm, reg """
    rm = Operand('rm', rm64_modes)
    reg = Operand('reg', Register64, read=True)
    syntax = Syntax([mnemonic, ' ', rm, ',', ' ', reg], priority=0)
    members = {
        'syntax': syntax, 'rm': rm, 'reg': reg, 'opcode': opcode}
    return type(mnemonic + '_ins', (rmregbase64,), members)


def make_rm_reg32(mnemonic, opcode, read_op1=True, write_op1=True):
    """ Create instruction class rm, reg """
    rm = Operand('rm', rm32_modes)
    reg = Operand('reg', Register32, read=True)
    syntax = Syntax([mnemonic, ' ', rm, ',', ' ', reg], priority=0)
    members = {
        'syntax': syntax, 'rm': rm, 'reg': reg, 'opcode': opcode}
    return type(mnemonic + '_ins', (rmregbase32,), members)


def make_rm_reg16(mnemonic, opcode, read_op1=True, write_op1=True):
    """ Create instruction class rm, reg """
    rm = Operand('rm', rm16_modes)
    reg = Operand('reg', Register16, read=True)
    syntax = Syntax([mnemonic, ' ', rm, ',', ' ', reg], priority=0)
    members = {
        'syntax': syntax, 'rm': rm, 'reg': reg, 'opcode': opcode}
    return type(mnemonic + '_ins', (rmregbase16,), members)


def make_rm_reg8(mnemonic, opcode, read_op1=True, write_op1=True):
    """ Create instruction class rm, reg """
    rm = Operand('rm', rm8_modes)
    reg = Operand('reg', Register8, read=True)
    syntax = Syntax([mnemonic, ' ', rm, ',', ' ', reg], priority=0)
    members = {
        'syntax': syntax, 'rm': rm, 'reg': reg, 'opcode': opcode}
    return type(mnemonic + '_ins', (rmregbase64,), members)


def make_reg_rm64(mnemonic, opcode, read_op1=True, write_op1=True):
    rm = Operand('rm', rm64_modes)
    reg = Operand('reg', Register64, write=write_op1, read=read_op1)
    syntax = Syntax([mnemonic, ' ', reg, ',', ' ', rm], priority=1)
    members = {
        'syntax': syntax, 'rm': rm, 'reg': reg, 'opcode': opcode}
    return type(mnemonic + '_ins', (rmregbase64,), members)


def make_reg_rm32(mnemonic, opcode, read_op1=True, write_op1=True):
    rm = Operand('rm', rm32_modes)
    reg = Operand('reg', Register32, write=write_op1, read=read_op1)
    syntax = Syntax([mnemonic, ' ', reg, ',', ' ', rm], priority=1)
    members = {
        'syntax': syntax, 'rm': rm, 'reg': reg, 'opcode': opcode}
    return type(mnemonic + '_ins', (rmregbase32,), members)


def make_reg_rm16(mnemonic, opcode, read_op1=True, write_op1=True):
    rm = Operand('rm', rm16_modes)
    reg = Operand('reg', Register16, write=write_op1, read=read_op1)
    syntax = Syntax([mnemonic, ' ', reg, ',', ' ', rm], priority=1)
    members = {
        'syntax': syntax, 'rm': rm, 'reg': reg, 'opcode': opcode}
    return type(mnemonic + '_ins16', (rmregbase16,), members)


def make_reg_rm8(mnemonic, opcode, read_op1=True, write_op1=True):
    rm = Operand('rm', rm8_modes)
    reg = Operand('reg', Register8, write=write_op1, read=read_op1)
    syntax = Syntax([mnemonic, ' ', reg, ',', ' ', rm], priority=1)
    members = {
        'syntax': syntax, 'rm': rm, 'reg': reg, 'opcode': opcode}
    return type(mnemonic + '_ins', (rmregbase64,), members)


class MovsxReg64Rm8(rmregbase64):
    """ Move sign extend, which means take a byte and sign extend it! """
    reg = Operand('reg', Register64, write=True)
    rm = Operand('rm', rm8_modes, read=True)
    syntax = Syntax(['movsx', ' ', reg, ',', ' ', rm])
    opcode = 0x0f
    opcode2 = 0xbe


class MovsxRegRm16(rmregbase64):
    """ Move sign extend, which means take a byte and sign extend it! """
    reg = Operand('reg', Register64, write=True)
    rm = Operand('rm', rm16_modes, read=True)
    syntax = Syntax(['movsx', ' ', reg, ',', ' ', rm])
    opcode = 0x0f
    opcode2 = 0xbf


class MovsxReg32Rm8(rmregbase64):
    """ Move sign extend, which means take a byte and sign extend it! """
    reg = Operand('reg', Register32, write=True)
    rm = Operand('rm', rm8_modes, read=True)
    syntax = Syntax(['movsx', ' ', reg, ',', ' ', rm])
    patterns = {'w': 0}
    opcode = 0x0f
    opcode2 = 0xbe


class MovsxReg32Rm16(rmregbase64):
    """ Move sign extend, which means take a byte and sign extend it! """
    reg = Operand('reg', Register32, write=True)
    rm = Operand('rm', rm16_modes, read=True)
    syntax = Syntax(['movsx', ' ', reg, ',', ' ', rm])
    patterns = {'w': 0}
    opcode = 0x0f
    opcode2 = 0xbf


class MovzxRegRm(rmregbase64):
    """ Move zero extend """
    reg = Operand('reg', Register64, write=True)
    rm = Operand('rm', rm8_modes, read=True)
    syntax = Syntax(['movzx', ' ', reg, ',', ' ', rm])
    opcode = 0x0f
    opcode2 = 0xb6


class InstructionCollection:
    """ Helper class to be able to create instructions in batch """
    def __init__(self, bits):
        make_rm = {
            16: make_rm16,
            32: make_rm32,
            64: make_rm64,
        }[bits]

        make_reg_rm = {
            16: make_reg_rm16,
            32: make_reg_rm32,
            64: make_reg_rm64,
        }[bits]

        make_rm_reg = {
            16: make_rm_reg16,
            32: make_rm_reg32,
            64: make_rm_reg64,
        }[bits]
        rm_modes = {
            16: rm16_modes,
            32: rm32_modes,
            64: rm64_modes,
        }[bits]

        self.AddRmReg = make_rm_reg('add', 0x1)
        self.AddRegRm = make_reg_rm('add', 0x3)
        self.OrRmReg = make_rm_reg('or', 0x9)
        self.OrRegRm = make_reg_rm('or', 0xb)
        self.AndRmReg = make_rm_reg('and', 0x21)
        self.AndRegRm = make_reg_rm('and', 0x23)
        self.SubRmReg = make_rm_reg('sub', 0x29)
        self.SubRegRm = make_reg_rm('sub', 0x2b)

        # opcode = 0x31  # XOR r/m64, r64
        self.XorRmReg = make_rm_reg('xor', 0x31)
        self.XorRegRm = make_reg_rm('xor', 0x33)

        # cmp r/m64 r64
        self.CmpRmReg = make_rm_reg('cmp', 0x39, write_op1=False)

        self.TestRmReg = make_rm_reg('test', 0x85, write_op1=False)

        # mov r64, r/m64
        self.MovRegRm = make_reg_rm('mov', 0x8b, read_op1=False)

        # mov r/m64, r64
        self.MovRmReg = make_rm_reg('mov', 0x89, read_op1=False)

        self.ShrRm = make_rm('shr', 0xd1, 5)
        self.ShlRm = make_rm('shl', 0xd1, 5)
        self.NotRm = make_rm('not', 0xf7, 2)
        self.NegRm = make_rm('neg', 0xf7, 3)

        if bits == 16:
            bit_tokens = [PrefixToken, RexToken, OpcodeToken, ModRmToken]
            extra_patterns = {'w': 0, 'prefix': 0x66}
        elif bits == 32:
            bit_tokens = [RexToken, OpcodeToken, ModRmToken]
            extra_patterns = {'w': 0}
        elif bits == 64:
            bit_tokens = [RexToken, OpcodeToken, ModRmToken]
            extra_patterns = {'w': 1}
        else:
            raise NotImplementedError(str(bits))

        class shift_cl_base(X86Instruction):
            rm = Operand('rm', rm_modes)
            tokens = bit_tokens
            patterns = {'opcode': 0xd3}
            for k, v in extra_patterns.items():
                patterns[k] = v

            def encode(self):
                tokens = self.get_tokens()
                self.set_all_patterns(tokens)
                tokens.set_field('reg', self.r)
                return tokens.encode()

        class ShrCl(shift_cl_base):
            r = 5
            syntax = Syntax(['shr', ' ', shift_cl_base.rm, ',', ' ', 'cl'])
        self.ShrCl = ShrCl

        class ShlCl(shift_cl_base):
            r = 6
            syntax = Syntax(['shl', ' ', shift_cl_base.rm, ',', ' ', 'cl'])
        self.ShlCl = ShlCl

        class SarCl(shift_cl_base):
            r = 7
            syntax = Syntax(['sar', ' ', shift_cl_base.rm, ',', ' ', 'cl'])
        self.SarCl = SarCl


bits16 = InstructionCollection(16)
bits32 = InstructionCollection(32)
bits64 = InstructionCollection(64)


AddRmReg8 = make_rm_reg8('add', 0x0)
AddRegRm8 = make_reg_rm8('add', 0x2)
OrRmReg8 = make_rm_reg8('or', 0x8)
OrRegRm8 = make_reg_rm8('or', 0xa)
AndRmReg8 = make_rm_reg8('and', 0x20)
AndRegRm8 = make_reg_rm8('and', 0x22)
SubRmReg8 = make_rm_reg8('sub', 0x28)
SubRegRm8 = make_reg_rm8('sub', 0x2a)
XorRmReg8 = make_rm_reg8('xor', 0x30)
XorRegRm8 = make_reg_rm8('xor', 0x32)
CmpRmReg8 = make_rm_reg8('cmp', 0x38, write_op1=False)  # cmp r/m8 r8
MovRmReg8 = make_rm_reg8('mov', 0x88, read_op1=False)  # mov r/m8, r8
MovRegRm8 = make_reg_rm8('mov', 0x8a, read_op1=False)  # mov r8, r/m8


# TODO: implement lea otherwise?
Lea = make_reg_rm64('lea', 0x8d, read_op1=False)


class regint32base(X86Instruction):
    tokens = [RexToken, OpcodeToken, ModRmToken, Imm32Token]
    patterns = {'w': 1, 'mod': 3}

    def encode(self):
        tokens = self.get_tokens()
        self.set_all_patterns(tokens)
        tokens[0].b = self.reg.rexbit
        tokens[1][0:8] = self.opcode
        tokens[2].rm = self.reg.regbits
        tokens[2].reg = self.reg_code
        tokens[3][0:32] = wrap_negative(self.imm, 32)
        return tokens.encode()


def make_regimm(mnemonic, opcode, reg_code):
    reg = Operand('reg', Register64, write=True, read=True)
    imm = Operand('imm', int)
    syntax = Syntax([mnemonic, ' ', reg, ',', ' ', imm])
    members = {
        'syntax': syntax, 'reg': reg, 'imm': imm, 'opcode': opcode,
        'reg_code': reg_code}
    return type(mnemonic + '_ins', (regint32base,), members)


AddImm = make_regimm('add', 0x81, 0)
AndImm = make_regimm('and', 0x81, 4)
SubImm = make_regimm('sub', 0x81, 5)
XorImm = make_regimm('xor', 0x81, 6)
CmpImm = make_regimm('cmp', 0x81, 7)


class shift8_cl_base(X86Instruction):
    rm = Operand('rm', rm8_modes)
    tokens = [RexToken, OpcodeToken, ModRmToken]
    patterns = {'opcode': 0xd2}
    opcode = 0xd2

    def encode(self):
        tokens = self.get_tokens()
        self.set_all_patterns(tokens)
        tokens[2].reg = self.r
        return tokens.encode()


class RolCl8(shift8_cl_base):
    r = 0
    syntax = Syntax(['rol', ' ', shift8_cl_base.rm, ',', ' ', 'cl'])


class RorCl8(shift8_cl_base):
    r = 1
    syntax = Syntax(['ror', ' ', shift8_cl_base.rm, ',', ' ', 'cl'])


class ShlCl8(shift8_cl_base):
    r = 4
    syntax = Syntax(['shl', ' ', shift8_cl_base.rm, ',', ' ', 'cl'])


class ShrCl8(shift8_cl_base):
    r = 5
    syntax = Syntax(['shr', ' ', shift8_cl_base.rm, ',', ' ', 'cl'])


class SarCl8(shift8_cl_base):
    r = 7
    syntax = Syntax(['sar', ' ', shift8_cl_base.rm, ',', ' ', 'cl'])


class Imul(X86Instruction):
    """ Multiply imul r64, r/m64 """
    reg1 = Operand('reg1', Register64, write=True, read=True)
    reg2 = Operand('reg2', Register64, read=True)
    syntax = Syntax(['imul', ' ', reg1, ',', ' ', reg2])
    tokens = [RexToken, OpcodeToken, SecondaryOpcodeToken, ModRmToken]
    patterns = {'opcode': 0x0f, 'opcode2': 0xaf, 'w': 1, 'mod': 3}

    def encode(self):
        tokens = self.get_tokens()
        self.set_all_patterns(tokens)
        tokens[0].r = self.reg1.rexbit
        tokens[0].b = self.reg2.rexbit
        tokens[3].rm = self.reg2.regbits
        tokens[3].reg = self.reg1.regbits
        return tokens.encode()


class Imul32(X86Instruction):
    """ Multiply imul r32, r/m32 """
    reg1 = Operand('reg1', Register32, write=True, read=True)
    reg2 = Operand('reg2', Register32, read=True)
    syntax = Syntax(['imul', ' ', reg1, ',', ' ', reg2])
    tokens = [RexToken, OpcodeToken, SecondaryOpcodeToken, ModRmToken]
    patterns = {'opcode': 0x0f, 'opcode2': 0xaf, 'w': 0, 'mod': 3}

    def encode(self):
        tokens = self.get_tokens()
        self.set_all_patterns(tokens)
        tokens[0].r = self.reg1.rexbit
        tokens[0].b = self.reg2.rexbit
        tokens[3].rm = self.reg2.regbits
        tokens[3].reg = self.reg1.regbits
        return tokens.encode()


class Div(X86Instruction):
    """ div r/m64 divide rdx:rax by the operand, leaving the remainder in
    rdx and the quotient in rax.
    """
    reg1 = Operand('reg1', Register64, read=True)
    syntax = Syntax(['div', ' ', reg1])
    tokens = [RexToken, OpcodeToken, ModRmToken]
    patterns = {'opcode': 0xf7, 'reg': 6, 'w': 1, 'mod': 3}

    def encode(self):
        tokens = self.get_tokens()
        self.set_all_patterns(tokens)
        tokens[0].b = self.reg1.rexbit
        tokens[2].rm = self.reg1.regbits
        return tokens.encode()


class Idiv(X86Instruction):
    """ idiv r/m64 divide rdx:rax by the operand, leaving the remainder in
    rdx and the quotient in rax.
    """
    reg1 = Operand('reg1', Register64, read=True)
    syntax = Syntax(['idiv', ' ', reg1])
    tokens = [RexToken, OpcodeToken, ModRmToken]
    patterns = {'opcode': 0xf7, 'reg': 7, 'w': 1, 'mod': 3}

    def encode(self):
        tokens = self.get_tokens()
        self.set_all_patterns(tokens)
        tokens[0].b = self.reg1.rexbit
        tokens[2].rm = self.reg1.regbits
        return tokens.encode()


class Div32(X86Instruction):
    """ idiv r/m32 divide rdx:rax by the operand, leaving the remainder in
    rdx and the quotient in rax.
    """
    reg1 = Operand('reg1', Register32, read=True)
    syntax = Syntax(['div', ' ', reg1])
    tokens = [RexToken, OpcodeToken, ModRmToken]
    patterns = {'opcode': 0xf7, 'reg': 6, 'w': 0, 'mod': 3}

    def encode(self):
        tokens = self.get_tokens()
        self.set_all_patterns(tokens)
        tokens[0].b = self.reg1.rexbit
        tokens[2].rm = self.reg1.regbits
        return tokens.encode()


class Idiv32(X86Instruction):
    """ idiv r/m32 divide rdx:rax by the operand, leaving the remainder in
    rdx and the quotient in rax.
    """
    reg1 = Operand('reg1', Register32, read=True)
    syntax = Syntax(['idiv', ' ', reg1])
    tokens = [RexToken, OpcodeToken, ModRmToken]
    patterns = {'opcode': 0xf7, 'reg': 7, 'w': 0, 'mod': 3}

    def encode(self):
        tokens = self.get_tokens()
        self.set_all_patterns(tokens)
        tokens[0].b = self.reg1.rexbit
        tokens[2].rm = self.reg1.regbits
        return tokens.encode()


class MovImm8(X86Instruction):
    """ Mov immediate into low 8-bit register """
    reg = Operand('reg', Register8, write=True)
    imm = Operand('imm', int)
    syntax = Syntax(['mov', ' ', reg, ',', ' ', imm])
    tokens = [RexToken, OpcodeToken]
    opcode = 0xb0  # mov r8, imm8

    def encode(self):
        tokens = self.get_tokens()
        tokens[0].w = 1
        tokens[0].b = self.reg.rexbit
        tokens[1][0:8] = self.opcode + self.reg.regbits
        return tokens.encode() + u8(self.imm)


class MovImm16(X86Instruction):
    """ Mov immediate into 16 bits register """
    reg = Operand('reg', Register16, write=True)
    imm = Operand('imm', int)
    syntax = Syntax(['mov', ' ', reg, ',', ' ', imm])
    tokens = [PrefixToken, OpcodeToken]
    opcode = 0xb8
    patterns = {'prefix': 0x66}

    def encode(self):
        tokens = self.get_tokens()
        self.set_all_patterns(tokens)
        tokens.set_field('opcode', self.opcode + self.reg.num)
        return tokens.encode() + u16(self.imm)


class MovImm32(X86Instruction):
    """ Mov immediate into 32 bits register """
    reg = Operand('reg', Register32, write=True)
    imm = Operand('imm', int)
    syntax = Syntax(['mov', ' ', reg, ',', ' ', imm])
    tokens = [RexToken, OpcodeToken]
    opcode = 0xb8
    patterns = {'w': 0}

    def encode(self):
        tokens = self.get_tokens()
        self.set_all_patterns(tokens)
        tokens[0].b = self.reg.rexbit
        tokens[1][0:8] = self.opcode + self.reg.regbits
        return tokens.encode() + u32(self.imm)


class MovImm(X86Instruction):
    """ Mov immediate into a 64 bits register """
    reg = Operand('reg', Register64, write=True)
    imm = Operand('imm', int)
    syntax = Syntax(['mov', ' ', reg, ',', ' ', imm])
    tokens = [RexToken, OpcodeToken]
    opcode = 0xb8  # mov r64, imm64
    patterns = {'w': 1}

    def encode(self):
        tokens = self.get_tokens()
        self.set_all_patterns(tokens)
        tokens[0].b = self.reg.rexbit
        tokens[1][0:8] = self.opcode + self.reg.regbits
        return tokens.encode() + u64(self.imm)


class MovAdr(X86Instruction):
    """ Mov address of label into register """
    reg = Operand('reg', Register64, write=True)
    imm = Operand('imm', str)
    syntax = Syntax(['mov', ' ', reg, ',', ' ', imm], priority=22)
    tokens = [RexToken, OpcodeToken]
    opcode = 0xb8  # mov r64, imm64

    def encode(self):
        tokens = self.get_tokens()
        tokens[0].w = 1
        tokens[0].b = self.reg.rexbit
        tokens[1][0:8] = self.opcode + self.reg.regbits
        return tokens.encode() + u64(0)

    def relocations(self):
        return [Abs64Relocation(self.imm, offset=2)]


class Cdqe(X86Instruction):
    """ Convert with sign extension to double size """
    syntax = Syntax(['cdqe'])
    tokens = [RexToken, OpcodeToken]
    patterns = {'w': 1, 'opcode': 0x98}


class Cdq(X86Instruction):
    """ Convert with sign extension to double size into edx:eax """
    syntax = Syntax(['cdq'])
    tokens = [RexToken, OpcodeToken]
    patterns = {'w': 0, 'opcode': 0x99}


class Cqo(X86Instruction):
    """ Convert with sign extension to double size into rdx:rax """
    syntax = Syntax(['cqo'])
    tokens = [RexToken, OpcodeToken]
    patterns = {'w': 1, 'opcode': 0x99}


class Rep(X86Instruction):
    """ Repeat string operation prefix """
    syntax = Syntax(['rep'])

    def encode(self):
        return bytes([0xF3])


class Movsb(X86Instruction):
    """ Move data from string to string """
    syntax = Syntax(['movsb'])

    def encode(self):
        return bytes([0xA4])


@isa.pattern('stm', 'JMP', size=2)
def pattern_jmp(context, tree):
    tgt = tree.value
    context.emit(NearJump(tgt.name, jumps=[tgt]))


jump_opnames = {
    "<": Jl, ">": Jg, "==": Je, "!=": Jne, ">=": Jge, '<=': Jle
}

unsigned_jump_opnames = {
    "<": Jb, ">": Ja, "==": Je, "!=": Jne, ">=": Jae, '<=': Jbe
}


def pattern_cjmp(context, value, signed):
    op, yes_label, no_label = value
    if signed:
        Bop = jump_opnames[op]
    else:
        Bop = unsigned_jump_opnames[op]
    jmp_ins = NearJump(no_label.name, jumps=[no_label])
    context.emit(Bop(yes_label.name, jumps=[yes_label, jmp_ins]))
    context.emit(jmp_ins)


@isa.pattern('stm', 'CJMPI64(reg64, reg64)', size=2)
def pattern_cjmp_i64(context, tree, c0, c1):
    context.emit(bits64.CmpRmReg(RmReg64(c0), c1))
    pattern_cjmp(context, tree.value, True)


@isa.pattern('stm', 'CJMPU64(reg64, reg64)', size=2)
def pattern_cjmp_u64(context, tree, c0, c1):
    context.emit(bits64.CmpRmReg(RmReg64(c0), c1))
    pattern_cjmp(context, tree.value, False)


@isa.pattern('stm', 'CJMPI32(reg32, reg32)', size=2)
def pattern_cjmp_i32(context, tree, c0, c1):
    context.emit(bits32.CmpRmReg(RmReg32(c0), c1))
    pattern_cjmp(context, tree.value, True)


@isa.pattern('stm', 'CJMPU32(reg32, reg32)', size=2)
def pattern_cjmp_u32(context, tree, c0, c1):
    context.emit(bits32.CmpRmReg(RmReg32(c0), c1))
    pattern_cjmp(context, tree.value, False)


@isa.pattern('stm', 'CJMPI16(reg16, reg16)', size=4, cycles=4, energy=2)
def pattern_cjmp_i16(context, tree, c0, c1):
    context.emit(bits16.CmpRmReg(RmReg16(c0), c1))
    pattern_cjmp(context, tree.value, True)


@isa.pattern('stm', 'CJMPU16(reg16, reg16)', size=4, cycles=4, energy=2)
def pattern_cjmp_u16(context, tree, c0, c1):
    context.emit(bits16.CmpRmReg(RmReg16(c0), c1))
    pattern_cjmp(context, tree.value, False)


@isa.pattern('stm', 'CJMPI8(reg8, reg8)', size=2)
def pattern_cjmp_i8(context, tree, c0, c1):
    context.emit(CmpRmReg8(RmReg8(c0), c1))
    pattern_cjmp(context, tree.value, True)


@isa.pattern('stm', 'CJMPU8(reg8, reg8)', size=2)
def pattern_cjmp_u8(context, tree, c0, c1):
    context.emit(CmpRmReg8(RmReg8(c0), c1))
    pattern_cjmp(context, tree.value, False)


@isa.pattern('stm', 'ALLOCA', size=10)
def pattern_alloca(context, tree):
    size = tree.value
    context.emit(SubImm(rsp, size))


@isa.pattern('stm', 'FREEA', size=10)
def pattern_freea(context, tree):
    size = tree.value
    context.emit(AddImm(rsp, size))


@isa.pattern('stm', 'MOVI8(reg8)', size=2)
@isa.pattern('stm', 'MOVU8(reg8)', size=2)
def pattern_mov8(context, tree, c0):
    context.move(tree.value, c0)


@isa.pattern('stm', 'MOVI16(reg16)', size=2)
@isa.pattern('stm', 'MOVU16(reg16)', size=2)
def pattern_mov16(context, tree, c0):
    context.move(tree.value, c0)


@isa.pattern('stm', 'MOVI32(reg32)', size=2)
@isa.pattern('stm', 'MOVU32(reg32)', size=2)
def pattern_mov_32(context, tree, c0):
    context.move(tree.value, c0)


@isa.pattern('stm', 'MOVI64(reg64)', size=2)
@isa.pattern('stm', 'MOVU64(reg64)', size=2)
def pattern_mov_64(context, tree, c0):
    context.move(tree.value, c0)


@isa.pattern('stm', 'MOVB(reg64, reg64)', size=22)
def pattern_movb(context, tree, c0, c1):
    dst = RmMem(c0)
    src = RmMem(c1)
    size = tree.value
    for instruction in context.arch.gen_memcpy(dst, src, size):
        context.emit(instruction)


# Memory operations
@isa.pattern('mem64', 'reg64', size=1, cycles=1, energy=1)
def pattern_mem_reg(context, tree, c0):
    return RmMem(c0)


@isa.pattern('reg64', 'mem64', size=2, cycles=1, energy=1)
def pattern_lea(context, tree, c0):
    # Exploit load effective address to do some math like rax = rbx + 3
    d = context.new_reg(Register64)
    context.emit(Lea(d, c0))
    return d


@isa.pattern('mem64', 'FPRELU64', size=1, cycles=1, energy=1)
def pattern_mem_fp_rel(context, tree):
    offset = tree.value.offset
    return RmMemDisp(rbp, offset)


@isa.pattern('rm8', 'LDRI8(mem64)', size=1)
@isa.pattern('rm8', 'LDRU8(mem64)', size=1)
def pattern_rm8_ldr8(context, tree, c0):
    return c0


@isa.pattern('rm8', 'reg8', size=1)
@isa.pattern('rm8', 'reg8', size=1)
def pattern_rm8_reg8(context, tree, c0):
    return RmReg8(c0)


@isa.pattern('rm16', 'LDRI16(mem64)', size=1, cycles=1, energy=1)
@isa.pattern('rm16', 'LDRU16(mem64)', size=1, cycles=1, energy=1)
def pattern_rm16_ldr16(context, tree, c0):
    return c0


@isa.pattern('rm16', 'reg16', size=1, cycles=1, energy=1)
@isa.pattern('rm16', 'reg16', size=1, cycles=1, energy=1)
def pattern_rm16_reg16(context, tree, c0):
    return RmReg16(c0)


@isa.pattern('rm32', 'LDRI32(mem64)', size=1, cycles=1, energy=1)
@isa.pattern('rm32', 'LDRU32(mem64)', size=1, cycles=1, energy=1)
def pattern_rm32_ldr32(context, tree, c0):
    return c0


@isa.pattern('rm32', 'reg32', size=1, cycles=1, energy=1)
@isa.pattern('rm32', 'reg32', size=1, cycles=1, energy=1)
def pattern_rm32_reg32(context, tree, c0):
    return RmReg32(c0)


@isa.pattern('rm64', 'LDRI64(mem64)', size=1, cycles=1, energy=1)
@isa.pattern('rm64', 'LDRU64(mem64)', size=1, cycles=1, energy=1)
def pattern_rm64_ldr64(context, tree, c0):
    return c0


@isa.pattern('rm64', 'reg64', size=1, cycles=1, energy=1)
@isa.pattern('rm64', 'reg64', size=1, cycles=1, energy=1)
def pattern_rm64_reg64(context, tree, c0):
    return RmReg64(c0)


@isa.pattern('mem64', 'ADDI64(reg64, con32)', size=1, cycles=1, energy=1)
@isa.pattern('mem64', 'ADDU64(reg64, con32)', size=1, cycles=1, energy=1)
def pattern_mem_reg_rel(context, tree, c0, c1):
    offset = c1
    return RmMemDisp(c0, offset)


@isa.pattern('reg64', 'rm64', size=2, cycles=2, energy=2)
@isa.pattern('reg64', 'rm64', size=2, cycles=2, energy=2)
def pattern_ldr64(context, tree, c0):
    d = context.new_reg(Register64)
    context.emit(bits64.MovRegRm(d, c0))
    return d


@isa.pattern('reg32', 'rm32', size=2, cycles=2, energy=2)
@isa.pattern('reg32', 'rm32', size=2, cycles=2, energy=2)
def pattern_ldr_32(context, tree, c0):
    d = context.new_reg(Register32)
    context.emit(bits32.MovRegRm(d, c0))
    return d


@isa.pattern('reg16', 'rm16', size=3, cycles=2, energy=2)
@isa.pattern('reg16', 'rm16', size=3, cycles=2, energy=2)
def pattern_ldr16(context, tree, c0):
    d = context.new_reg(Register16)
    context.emit(bits16.MovRegRm(d, c0))
    return d


@isa.pattern('reg8', 'rm8', size=2)
@isa.pattern('reg8', 'rm8', size=2)
def pattern_ldr8(context, tree, c0):
    d = context.new_reg(Register8)
    context.emit(MovRegRm8(d, c0))
    return d


# TODO: differentiate between u64 and i64?
@isa.pattern('stm', 'STRI64(mem64, reg64)', size=2)
@isa.pattern('stm', 'STRU64(mem64, reg64)', size=2)
def pattern_str64(context, tree, c0, c1):
    context.emit(bits64.MovRmReg(c0, c1))


@isa.pattern('stm', 'STRI32(mem64, reg32)', size=2)
@isa.pattern('stm', 'STRU32(mem64, reg32)', size=2)
def pattern_str32(context, tree, c0, c1):
    context.emit(bits32.MovRmReg(c0, c1))


@isa.pattern('stm', 'STRI16(mem64, reg16)', size=3, cycles=2, energy=2)
@isa.pattern('stm', 'STRU16(mem64, reg16)', size=3, cycles=2, energy=2)
def pattern_str16(context, tree, c0, c1):
    context.emit(bits16.MovRmReg(c0, c1))


@isa.pattern('stm', 'STRI8(mem64, reg8)', size=2)
@isa.pattern('stm', 'STRU8(mem64, reg8)', size=2)
def pattern_str8(context, tree, c0, c1):
    context.emit(MovRmReg8(c0, c1))


# Arithmatic:
@isa.pattern('reg64', 'ADDI64(reg64, rm64)', size=2, cycles=2, energy=1)
@isa.pattern('reg64', 'ADDU64(reg64, rm64)', size=2, cycles=2, energy=1)
def pattern_add64(context, tree, c0, c1):
    d = context.new_reg(Register64)
    context.move(d, c0)
    context.emit(bits64.AddRegRm(d, c1))
    return d


@isa.pattern('reg32', 'ADDI32(reg32, rm32)', size=2, cycles=2, energy=1)
@isa.pattern('reg32', 'ADDU32(reg32, rm32)', size=2, cycles=2, energy=1)
def pattern_add32(context, tree, c0, c1):
    d = context.new_reg(Register32)
    context.move(d, c0)
    context.emit(bits32.AddRegRm(d, c1))
    return d


@isa.pattern('reg16', 'ADDI16(reg16, rm16)', size=3, cycles=2, energy=1)
@isa.pattern('reg16', 'ADDU16(reg16, rm16)', size=3, cycles=2, energy=1)
def pattern_add16(context, tree, c0, c1):
    d = context.new_reg(Register16)
    context.move(d, c0)
    context.emit(bits16.AddRegRm(d, c1))
    return d


@isa.pattern('reg8', 'ADDI8(reg8, rm8)', size=2, cycles=2, energy=1)
@isa.pattern('reg8', 'ADDU8(reg8, rm8)', size=2, cycles=2, energy=1)
def pattern_add8(context, tree, c0, c1):
    d = context.new_reg(Register8)
    context.move(d, c0)
    context.emit(AddRegRm8(d, c1))
    return d


@isa.pattern('reg64', 'FPRELU64', size=8, cycles=3, energy=2)
def pattern_add64_fprel_const(context, tree):
    d = context.new_reg(Register64)
    context.move(d, rbp)
    context.emit(AddImm(d, tree.value.offset))
    return d


# @isa.pattern('reg64', 'SPRELI64', size=8, cycles=3, energy=2)
# def pattern_sprel64(context, tree):
#    d = context.new_reg(X86Register)
#    context.move(d, rsp)
#    context.emit(AddImm(d, tree.value))
#    return d


@isa.pattern('reg64', 'ADDI64(reg64, con32)', size=8, cycles=3, energy=2)
@isa.pattern('reg64', 'ADDU64(reg64, con32)', size=8, cycles=3, energy=2)
def pattern_add64_const_2(context, tree, c0, c1):
    d = context.new_reg(Register64)
    context.move(d, c0)
    context.emit(AddImm(d, c1))
    return d


@isa.pattern(
    'con32', 'CONSTI64', size=4,
    condition=lambda x: x.value in range(-2147483648, 2147483647))
@isa.pattern(
    'con32', 'CONSTU64', size=4,
    condition=lambda x: x.value in range(0, 4294967296))
def pattern_const32(context, tree):
    """ Small 64 bit constants as a constant """
    return tree.value


@isa.pattern('reg64', 'ADDI64(con32, reg64)', size=8)
def pattern_add64_const_1(context, tree, c0, c1):
    d = context.new_reg(Register64)
    context.move(d, c1)
    context.emit(AddImm(d, c0))
    return d


@isa.pattern('reg64', 'SUBI64(reg64, rm64)', size=4)
@isa.pattern('reg64', 'SUBU64(reg64, rm64)', size=4)
def pattern_sub64(context, tree, c0, c1):
    d = context.new_reg(Register64)
    context.move(d, c0)
    context.emit(bits64.SubRegRm(d, c1))
    return d


@isa.pattern('reg32', 'SUBI32(reg32, rm32)', size=4)
@isa.pattern('reg32', 'SUBU32(reg32, rm32)', size=4)
def pattern_sub_32(context, tree, c0, c1):
    d = context.new_reg(Register32)
    context.move(d, c0)
    context.emit(bits32.SubRegRm(d, c1))
    return d


@isa.pattern('reg16', 'SUBU16(reg16, rm16)', size=3, cycles=2, energy=1)
@isa.pattern('reg16', 'SUBI16(reg16, rm16)', size=3, cycles=2, energy=1)
def pattern_sub16(context, tree, c0, c1):
    d = context.new_reg(Register16)
    context.move(d, c0)
    context.emit(bits16.SubRegRm(d, c1))
    return d


@isa.pattern('reg8', 'SUBU8(reg8, rm8)', size=4)
@isa.pattern('reg8', 'SUBI8(reg8, rm8)', size=4)
def pattern_sub8(context, tree, c0, c1):
    d = context.new_reg(Register8)
    context.move(d, c0)
    context.emit(SubRegRm8(d, c1))
    return d


@isa.pattern('reg64', 'MULI64(reg64, reg64)', size=4)
@isa.pattern('reg64', 'MULU64(reg64, reg64)', size=4)
def pattern_mul64_(context, tree, c0, c1):
    dst = context.new_reg(Register64)
    context.move(dst, c0)
    context.emit(Imul(dst, c1))
    return dst


@isa.pattern('reg32', 'MULI32(reg32, reg32)', size=4)
@isa.pattern('reg32', 'MULU32(reg32, reg32)', size=4)
def pattern_mul_32(context, tree, c0, c1):
    dst = context.new_reg(Register32)
    context.move(dst, c0)
    context.emit(Imul32(dst, c1))
    return dst


@isa.pattern('reg64', 'DIVI64(reg64, reg64)', size=14)
def pattern_div_i64(context, tree, c0, c1):
    context.move(rax, c0)
    context.emit(Cqo())  # Extend sign of rax into rdx
    context.emit(Idiv(c1))
    defu2 = RegisterUseDef()
    defu2.add_use(rax)
    defu2.add_use(rdx)
    defu2.add_def(rax)
    context.emit(defu2)
    dst = context.new_reg(Register64)
    context.move(dst, rax)
    return dst


@isa.pattern('reg64', 'DIVU64(reg64, reg64)', size=14)
def pattern_div_u64(context, tree, c0, c1):
    context.move(rax, c0)
    context.emit(MovImm(rdx, 0))
    context.emit(Div(c1))
    defu2 = RegisterUseDef()
    defu2.add_use(rax)
    defu2.add_use(rdx)
    defu2.add_def(rax)
    context.emit(defu2)
    dst = context.new_reg(Register64)
    context.move(dst, rax)
    return dst


@isa.pattern('reg64', 'REMI64(reg64, reg64)', size=14)
def pattern_rem_i64(context, tree, c0, c1):
    context.move(rax, c0)
    context.emit(Cqo())
    context.emit(Idiv(c1))
    defu2 = RegisterUseDef()
    defu2.add_use(rax)
    defu2.add_use(rdx)
    defu2.add_def(rdx)
    context.emit(defu2)
    dst = context.new_reg(Register64)
    context.move(dst, rdx)
    return dst


@isa.pattern('reg64', 'REMU64(reg64, reg64)', size=14)
def pattern_rem_u64(context, tree, c0, c1):
    context.move(rax, c0)
    context.emit(MovImm(rdx, 0))
    context.emit(Div(c1))
    defu2 = RegisterUseDef()
    defu2.add_use(rax)
    defu2.add_use(rdx)
    defu2.add_def(rdx)
    context.emit(defu2)
    dst = context.new_reg(Register64)
    context.move(dst, rdx)
    return dst


@isa.pattern('reg32', 'DIVI32(reg32, reg32)', size=14)
def pattern_div_i32(context, tree, c0, c1):
    context.move(eax, c0)
    context.emit(Cdq())  # Sign extend eax into edx
    context.emit(Idiv32(c1))
    defu2 = RegisterUseDef()
    defu2.add_use(eax)
    defu2.add_use(edx)
    defu2.add_def(eax)
    context.emit(defu2)
    dst = context.new_reg(Register32)
    context.move(dst, eax)
    return dst


@isa.pattern('reg32', 'DIVU32(reg32, reg32)', size=14)
def pattern_div_u32(context, tree, c0, c1):
    context.move(eax, c0)
    context.emit(MovImm32(edx, 0))
    context.emit(Div32(c1))
    defu2 = RegisterUseDef()
    defu2.add_use(eax)
    defu2.add_use(edx)
    defu2.add_def(eax)
    context.emit(defu2)
    dst = context.new_reg(Register32)
    context.move(dst, eax)
    return dst


@isa.pattern('reg32', 'REMI32(reg32, reg32)', size=14)
def pattern_remi32(context, tree, c0, c1):
    context.move(eax, c0)
    context.emit(Cdq())  # Sign extend eax into edx
    context.emit(Idiv32(c1))
    defu2 = RegisterUseDef()
    defu2.add_use(eax)
    defu2.add_use(edx)
    defu2.add_def(edx)
    context.emit(defu2)
    dst = context.new_reg(Register32)
    context.move(dst, edx)
    return dst


@isa.pattern('reg32', 'REMU32(reg32, reg32)', size=14)
def pattern_rem_u32(context, tree, c0, c1):
    context.move(eax, c0)
    context.emit(MovImm32(edx, 0))
    context.emit(Div32(c1))
    defu2 = RegisterUseDef()
    defu2.add_use(eax)
    defu2.add_use(edx)
    defu2.add_def(edx)
    context.emit(defu2)
    dst = context.new_reg(Register32)
    context.move(dst, edx)
    return dst


@isa.pattern('reg64', 'ANDI64(reg64, rm64)', size=4)
@isa.pattern('reg64', 'ANDU64(reg64, rm64)', size=4)
def pattern_and64(context, tree, c0, c1):
    d = context.new_reg(Register64)
    context.move(d, c0)
    context.emit(bits64.AndRegRm(d, c1))
    return d


@isa.pattern('reg32', 'ANDI32(reg32, rm32)', size=4)
@isa.pattern('reg32', 'ANDU32(reg32, rm32)', size=4)
def pattern_and_32(context, tree, c0, c1):
    d = context.new_reg(Register32)
    context.move(d, c0)
    context.emit(bits32.AndRegRm(d, c1))
    return d


@isa.pattern('reg16', 'ANDI16(reg16, rm16)', size=4)
@isa.pattern('reg16', 'ANDU16(reg16, rm16)', size=4)
def pattern_and16(context, tree, c0, c1):
    d = context.new_reg(Register16)
    context.move(d, c0)
    context.emit(bits16.AndRegRm(d, c1))
    return d


@isa.pattern('reg8', 'ANDU8(reg8, rm8)', size=4)
@isa.pattern('reg8', 'ANDI8(reg8, rm8)', size=4)
def pattern_and8(context, tree, c0, c1):
    d = context.new_reg(Register8)
    context.move(d, c0)
    context.emit(AndRegRm8(d, c1))
    return d


@isa.pattern('reg64', 'ANDI64(reg64, con32)', size=10)
@isa.pattern('reg64', 'ANDU64(reg64, con32)', size=10)
def pattern_and64_const(context, tree, c0, c1):
    d = context.new_reg(Register64)
    context.move(d, c0)
    context.emit(AndImm(d, c1))
    return d


@isa.pattern('reg64', 'ORU64(reg64, rm64)', size=4)
@isa.pattern('reg64', 'ORI64(reg64, rm64)', size=4)
def pattern_or64(context, tree, c0, c1):
    d = context.new_reg(Register64)
    context.move(d, c0)
    context.emit(bits64.OrRegRm(d, c1))
    return d


@isa.pattern('reg32', 'ORU32(reg32, rm32)', size=4)
@isa.pattern('reg32', 'ORI32(reg32, rm32)', size=4)
def pattern_or_32(context, tree, c0, c1):
    d = context.new_reg(Register32)
    context.move(d, c0)
    context.emit(bits32.OrRegRm(d, c1))
    return d


@isa.pattern('reg16', 'ORU16(reg16, rm16)', size=3)
@isa.pattern('reg16', 'ORI16(reg16, rm16)', size=3)
def pattern_or16(context, tree, c0, c1):
    d = context.new_reg(Register16)
    context.move(d, c0)
    context.emit(bits16.OrRegRm(d, c1))
    return d


@isa.pattern('reg8', 'ORU8(reg8, rm8)', size=4)
@isa.pattern('reg8', 'ORI8(reg8, rm8)', size=4)
def pattern_or8(context, tree, c0, c1):
    d = context.new_reg(Register8)
    context.move(d, c0)
    context.emit(OrRegRm8(d, c1))
    return d


@isa.pattern('reg64', 'XORU64(reg64, rm64)', size=4)
@isa.pattern('reg64', 'XORI64(reg64, rm64)', size=4)
def pattern_xor_64(context, tree, c0, c1):
    d = context.new_reg(Register64)
    context.move(d, c0)
    context.emit(bits64.XorRegRm(d, c1))
    return d


@isa.pattern('reg32', 'XORU32(reg32, rm32)', size=4)
@isa.pattern('reg32', 'XORI32(reg32, rm32)', size=4)
def pattern_xor_32(context, tree, c0, c1):
    d = context.new_reg(Register32)
    context.move(d, c0)
    context.emit(bits32.XorRegRm(d, c1))
    return d


@isa.pattern('reg16', 'XORU16(reg16, rm16)', size=3, energy=3)
@isa.pattern('reg16', 'XORI16(reg16, rm16)', size=3, energy=3)
def pattern_xor16(context, tree, c0, c1):
    d = context.new_reg(Register8)
    context.move(d, c0)
    context.emit(bits16.XorRegRm(d, c1))
    return d


@isa.pattern('reg8', 'XORU8(reg8, rm8)', size=3, energy=3)
@isa.pattern('reg8', 'XORI8(reg8, rm8)', size=3, energy=3)
def pattern_xor8(context, tree, c0, c1):
    d = context.new_reg(Register8)
    context.move(d, c0)
    context.emit(XorRegRm8(d, c1))
    return d


@isa.pattern('reg64', 'SHRI64(reg64, reg64)', size=2)
def pattern_shr_i64(context, tree, c0, c1):
    d = context.new_reg(Register64)
    context.move(d, c0)
    context.move(rcx, c1)
    context.emit(bits64.SarCl(RmReg64(d)))
    return d


@isa.pattern('reg64', 'SHRU64(reg64, reg64)', size=2)
def pattern_shr_u64(context, tree, c0, c1):
    d = context.new_reg(Register64)
    context.move(d, c0)
    context.move(rcx, c1)
    context.emit(bits64.ShrCl(RmReg64(d)))
    return d


@isa.pattern('reg32', 'SHRI32(reg32, reg32)', size=2)
def pattern_shr_i32(context, tree, c0, c1):
    d = context.new_reg(Register32)
    context.move(d, c0)
    context.move(ecx, c1)
    context.emit(bits32.SarCl(RmReg32(d)))
    return d


@isa.pattern('reg32', 'SHRU32(reg32, reg32)', size=2)
def pattern_shr_u32(context, tree, c0, c1):
    d = context.new_reg(Register32)
    context.move(d, c0)
    context.move(ecx, c1)
    context.emit(bits32.ShrCl(RmReg32(d)))
    return d


@isa.pattern('reg16', 'SHRI16(reg16, reg16)', size=2)
def pattern_shr_i16(context, tree, c0, c1):
    d = context.new_reg(Register16)
    context.move(d, c0)
    context.move(cx, c1)
    context.emit(bits16.SarCl(RmReg16(d)))
    return d


@isa.pattern('reg16', 'SHRU16(reg16, reg16)', size=2)
def pattern_shr_u16(context, tree, c0, c1):
    d = context.new_reg(Register16)
    context.move(d, c0)
    context.move(cx, c1)
    context.emit(bits16.ShrCl(RmReg16(d)))
    return d


@isa.pattern('reg8', 'SHRI8(reg8, reg8)', size=2)
def pattern_shr_i8(context, tree, c0, c1):
    d = context.new_reg(Register8)
    context.move(d, c0)
    context.move(cl, c1)
    context.emit(SarCl8(RmReg8(d)))
    return d


@isa.pattern('reg8', 'SHRU8(reg8, reg8)', size=2)
def pattern_shr_u8(context, tree, c0, c1):
    d = context.new_reg(Register8)
    context.move(d, c0)
    context.move(cl, c1)
    context.emit(ShrCl8(RmReg8(d)))
    return d


@isa.pattern('reg64', 'SHLI64(reg64, reg64)', size=2)
@isa.pattern('reg64', 'SHLU64(reg64, reg64)', size=2)
def pattern_shl64(context, tree, c0, c1):
    d = context.new_reg(Register64)
    context.move(d, c0)
    context.move(rcx, c1)
    context.emit(bits64.ShlCl(RmReg64(d)))
    return d


@isa.pattern('reg32', 'SHLI32(reg32, reg32)', size=2)
@isa.pattern('reg32', 'SHLU32(reg32, reg32)', size=2)
def pattern_shl_32(context, tree, c0, c1):
    d = context.new_reg(Register32)
    context.move(d, c0)
    context.move(ecx, c1)
    context.emit(bits32.ShlCl(RmReg32(d)))
    return d


@isa.pattern('reg16', 'SHLI16(reg16, reg16)', size=2)
@isa.pattern('reg16', 'SHLU16(reg16, reg16)', size=2)
def pattern_shl_16(context, tree, c0, c1):
    d = context.new_reg(Register16)
    context.move(d, c0)
    context.move(cx, c1)
    context.emit(bits16.ShlCl(RmReg16(d)))
    return d


@isa.pattern('reg8', 'SHLI8(reg8, reg8)', size=2)
@isa.pattern('reg8', 'SHLU8(reg8, reg8)', size=2)
def pattern_shl8(context, tree, c0, c1):
    d = context.new_reg(Register8)
    context.move(d, c0)
    context.move(cl, c1)
    context.emit(ShlCl8(RmReg8(d)))
    return d


@isa.pattern('reg64', 'NEGI64(reg64)', size=3)
def pattern_neg64(context, tree, c0):
    d = context.new_reg(Register64)
    context.move(d, c0)
    context.emit(bits64.NegRm(RmReg64(d)))
    return d


@isa.pattern('reg32', 'NEGI32(reg32)', size=3)
def pattern_neg_32(context, tree, c0):
    d = context.new_reg(Register32)
    context.move(d, c0)
    context.emit(bits32.NegRm(RmReg32(d)))
    return d


@isa.pattern('reg16', 'NEGI16(reg16)', size=3)
def pattern_neg_16(context, tree, c0):
    """ 16 bits negation """
    d = context.new_reg(Register16)
    context.move(d, c0)
    context.emit(bits16.NegRm(RmReg16(d)))
    return d


@isa.pattern('reg64', 'INVI64(reg64)', size=3)
def pattern_inv64(context, tree, c0):
    d = context.new_reg(Register64)
    context.move(d, c0)
    context.emit(bits64.NotRm(RmReg64(d)))
    return d


@isa.pattern('reg32', 'INVI32(reg32)', size=3)
def pattern_inv_32(context, tree, c0):
    d = context.new_reg(Register32)
    context.move(d, c0)
    context.emit(bits32.NotRm(RmReg32(d)))
    return d


@isa.pattern('reg64', 'REGI64', size=0)
@isa.pattern('reg64', 'REGU64', size=0)
def pattern_reg64(context, tree):
    return tree.value


@isa.pattern('reg32', 'REGI32', size=0)
@isa.pattern('reg32', 'REGU32', size=0)
def pattern_reg_32(context, tree):
    return tree.value


@isa.pattern('reg16', 'REGI16', size=0)
@isa.pattern('reg16', 'REGU16', size=0)
def pattern_reg16(context, tree):
    return tree.value


@isa.pattern('reg8', 'REGI8', size=0)
@isa.pattern('reg8', 'REGU8', size=0)
def pattern_reg8(context, tree):
    return tree.value


# Unit conversions:
@isa.pattern('reg64', 'I64TOI64(reg64)', size=0)
@isa.pattern('reg64', 'I64TOU64(reg64)', size=0)
@isa.pattern('reg64', 'U64TOI64(reg64)', size=0)
@isa.pattern('reg64', 'U64TOU64(reg64)', size=0)
def pattern_i64toi64(context, tree, c0):
    return c0


@isa.pattern('reg32', 'I32TOI32(reg32)', size=0)
@isa.pattern('reg32', 'I32TOU32(reg32)', size=0)
@isa.pattern('reg32', 'U32TOI32(reg32)', size=0)
@isa.pattern('reg32', 'U32TOU32(reg32)', size=0)
def pattern_i32toi32(context, tree, c0):
    return c0


@isa.pattern('reg16', 'I16TOI16(reg16)', size=0)
@isa.pattern('reg16', 'I16TOU16(reg16)', size=0)
@isa.pattern('reg16', 'U16TOI16(reg16)', size=0)
@isa.pattern('reg16', 'U16TOU16(reg16)', size=0)
def pattern_i16toi16(context, tree, c0):
    return c0


@isa.pattern('reg8', 'I8TOI8(reg8)', size=0)
@isa.pattern('reg8', 'I8TOU8(reg8)', size=0)
@isa.pattern('reg8', 'U8TOU8(reg8)', size=0)
@isa.pattern('reg8', 'U8TOI8(reg8)', size=0)
def pattern_8to8(context, tree, c0):
    return c0


# Conversions:
@isa.pattern('reg16', 'U64TOU16(reg64)', size=4)
@isa.pattern('reg16', 'I64TOU16(reg64)', size=4)
@isa.pattern('reg16', 'I64TOI16(reg64)', size=4)
def pattern_i64toi16(context, tree, c0):
    context.move(rax, c0)
    # raise Warning()
    defu = RegisterUseDef()
    defu.add_use(rax)
    defu.add_def(ax)
    context.emit(defu)

    d = context.new_reg(Register16)
    context.move(d, ax)
    return d


@isa.pattern('reg64', 'I16TOI64(reg16)', size=4)
def pattern_i16_to_i64(context, tree, c0):
    dst = context.new_reg(Register64)
    # sign extend:
    context.emit(MovsxRegRm16(dst, RmReg16(c0)))
    return dst


@isa.pattern('reg64', 'U16TOU64(reg16)', size=4)
@isa.pattern('reg64', 'U16TOI64(reg16)', size=4)
@isa.pattern('reg64', 'I16TOU64(reg16)', size=4)
def pattern_u16toi64(context, tree, c0):
    defu1 = RegisterUseDef()
    defu1.add_def(rax)
    context.emit(defu1)

    context.emit(bits64.XorRmReg(RmReg64(rax), rax))
    context.move(ax, c0)

    defu2 = RegisterUseDef()
    defu2.add_use(ax)
    defu2.add_def(rax)
    context.emit(defu2)

    d = context.new_reg(Register64)
    context.move(d, rax)
    return d


@isa.pattern('reg32', 'I64TOI32(reg64)', size=4)
@isa.pattern('reg32', 'I64TOU32(reg64)', size=4)
@isa.pattern('reg32', 'U64TOU32(reg64)', size=4)
@isa.pattern('reg32', 'U64TOI32(reg64)', size=4)
def pattern_i64toi32(context, tree, c0):
    context.move(rax, c0)
    # raise Warning()
    defu = RegisterUseDef()
    defu.add_use(rax)
    defu.add_def(eax)
    context.emit(defu)

    d = context.new_reg(Register32)
    context.move(d, eax)
    return d


@isa.pattern('reg64', 'U32TOU64(reg32)', size=4)
@isa.pattern('reg64', 'U32TOI64(reg32)', size=4)
@isa.pattern('reg64', 'I32TOU64(reg32)', size=4)
def pattern_u32toi64(context, tree, c0):
    defu1 = RegisterUseDef()
    defu1.add_def(rax)
    context.emit(defu1)

    context.emit(bits64.XorRmReg(RmReg64(rax), rax))
    context.move(eax, c0)

    defu2 = RegisterUseDef()
    defu2.add_use(eax)
    defu2.add_def(rax)
    context.emit(defu2)

    d = context.new_reg(Register64)
    context.move(d, rax)
    return d


@isa.pattern('reg64', 'I32TOI64(reg32)', size=4)
def pattern_i32toi64(context, tree, c0):
    defu1 = RegisterUseDef()
    defu1.add_def(rax)
    context.emit(defu1)

    context.emit(bits64.XorRmReg(RmReg64(rax), rax))
    context.move(eax, c0)

    defu2 = RegisterUseDef()
    defu2.add_use(eax)
    defu2.add_def(rax)
    context.emit(defu2)

    # Sign extend:
    context.emit(Cdqe())

    d = context.new_reg(Register64)
    context.move(d, rax)
    return d


@isa.pattern('reg16', 'U32TOU16(reg32)', size=4)
@isa.pattern('reg16', 'I32TOU16(reg32)', size=4)
@isa.pattern('reg16', 'I32TOI16(reg32)', size=4)
def pattern_i32toi16(context, tree, c0):
    context.move(eax, c0)
    # raise Warning()
    defu = RegisterUseDef()
    defu.add_use(eax)
    defu.add_def(ax)
    context.emit(defu)

    dst = context.new_reg(Register16)
    context.move(dst, ax)
    return dst


@isa.pattern('reg32', 'I16TOI32(reg16)', size=4)
def pattern_i16_to_i32(context, tree, c0):
    dst = context.new_reg(Register32)

    # sign extend:
    context.emit(MovsxReg32Rm16(dst, RmReg16(c0)))
    return dst


@isa.pattern('reg32', 'U16TOU32(reg16)', size=4)
@isa.pattern('reg32', 'U16TOI32(reg16)', size=4)
@isa.pattern('reg32', 'I16TOU32(reg16)', size=4)
def pattern_u16toi32(context, tree, c0):
    defu1 = RegisterUseDef()
    defu1.add_def(eax)
    context.emit(defu1)

    context.emit(bits32.XorRmReg(RmReg32(eax), eax))
    context.move(ax, c0)

    defu2 = RegisterUseDef()
    defu2.add_use(ax)
    defu2.add_def(eax)
    context.emit(defu2)

    dst = context.new_reg(Register32)
    context.move(dst, eax)
    return dst


@isa.pattern('reg8', 'I32TOI8(reg32)', size=4)
@isa.pattern('reg8', 'I32TOU8(reg32)', size=4)
@isa.pattern('reg8', 'U32TOU8(reg32)', size=4)
@isa.pattern('reg8', 'U32TOI8(reg32)', size=4)
def pattern_i32toi8(context, tree, c0):
    context.move(eax, c0)
    defu = RegisterUseDef()
    defu.add_use(eax)
    defu.add_def(al)
    context.emit(defu)

    d = context.new_reg(Register8)
    context.move(d, al)
    return d


@isa.pattern('reg32', 'I8TOI32(reg8)', size=4)
def pattern_i8toi32(context, tree, c0):
    dst = context.new_reg(Register32)
    context.emit(MovsxReg32Rm8(dst, RmReg8(c0)))
    return dst


@isa.pattern('reg32', 'U8TOI32(reg8)', size=4)
@isa.pattern('reg32', 'U8TOU32(reg8)', size=4)
@isa.pattern('reg32', 'I8TOU32(reg8)', size=4)
def pattern_u8toi32(context, tree, c0):
    defu1 = RegisterUseDef()
    defu1.add_def(eax)
    context.emit(defu1)

    context.emit(bits32.XorRmReg(RmReg32(eax), eax))
    context.move(al, c0)
    # raise Warning()

    defu2 = RegisterUseDef()
    defu2.add_use(al)
    defu2.add_def(eax)
    context.emit(defu2)

    d = context.new_reg(Register32)
    context.move(d, eax)
    return d


@isa.pattern('reg8', 'I64TOI8(reg64)', size=4)
@isa.pattern('reg8', 'I64TOU8(reg64)', size=4)
@isa.pattern('reg8', 'U64TOU8(reg64)', size=4)
@isa.pattern('reg8', 'U64TOI8(reg64)', size=4)
def pattern_i64toi8(context, tree, c0):
    context.move(rax, c0)
    # raise Warning()
    defu = RegisterUseDef()
    defu.add_use(rax)
    defu.add_def(al)
    context.emit(defu)

    d = context.new_reg(Register8)
    context.move(d, al)
    return d


@isa.pattern('reg64', 'I8TOI64(reg8)', size=4)
def pattern_i8toi64(context, tree, c0):
    dst = context.new_reg(Register64)
    context.emit(MovsxReg64Rm8(dst, RmReg8(c0)))
    return dst


@isa.pattern('reg64', 'U8TOI64(reg8)', size=4)
@isa.pattern('reg64', 'U8TOU64(reg8)', size=4)
@isa.pattern('reg64', 'I8TOU64(reg8)', size=4)
def pattern_u8toi64(context, tree, c0):
    defu1 = RegisterUseDef()
    defu1.add_def(rax)
    context.emit(defu1)

    context.emit(bits64.XorRmReg(RmReg64(rax), rax))
    context.move(al, c0)
    # raise Warning()

    defu2 = RegisterUseDef()
    defu2.add_use(al)
    defu2.add_def(rax)
    context.emit(defu2)

    d = context.new_reg(Register64)
    context.move(d, rax)
    return d


@isa.pattern('stm', 'MOVI64(LABEL)', size=2)
def pattern_mov64_label(context, tree):
    label = tree.children[0].value
    context.emit(MovAdr(tree.value, label))


@isa.pattern('reg64', 'LABEL', size=2)
def pattern_reg64_label(context, tree):
    label = tree.value
    d = context.new_reg(Register64)
    context.emit(MovAdr(d, label))
    return d


@isa.pattern('reg64', 'CONSTI64', size=11, cycles=3, energy=3)
@isa.pattern('reg64', 'CONSTU64', size=11, cycles=3, energy=3)
def pattern_const64(context, tree):
    d = context.new_reg(Register64)
    context.emit(MovImm(d, tree.value))
    return d


@isa.pattern('reg32', 'CONSTI32', size=11, cycles=3, energy=3)
@isa.pattern('reg32', 'CONSTU32', size=11, cycles=3, energy=3)
def pattern_const_32(context, tree):
    d = context.new_reg(Register32)
    context.emit(MovImm32(d, tree.value))
    return d


# @isa.pattern('reg64', 'CONSTI8', size=11)
def pattern_const8_old(context, tree):
    d = context.new_reg(Register64)
    context.emit(MovImm(d, tree.value))
    return d


@isa.pattern('reg16', 'CONSTI16', size=4)
@isa.pattern('reg16', 'CONSTU16', size=4)
def pattern_const16(context, tree):
    d = context.new_reg(Register16)
    context.emit(MovImm16(d, tree.value))
    return d


@isa.pattern('reg8', 'CONSTI8', size=11)
@isa.pattern('reg8', 'CONSTU8', size=11)
def pattern_const8(context, tree):
    d = context.new_reg(Register8)
    context.emit(MovImm8(d, tree.value))
    return d


@isa.peephole
def peephole_jump_label(a, b):
    print('PH', a, b)
    if isinstance(a, NearJump) and isinstance(b, Label) and \
            a.target == b.name:
        return [b]
    return [a, b]
