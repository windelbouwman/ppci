""" SSE2 instructions """

import struct
from ..isa import Isa
from ..encoding import Operand, Syntax, Instruction, Constructor
from .instructions import rm_modes
from .instructions import OpcodeToken
from .instructions import PrefixToken
from .instructions import RexToken, ModRmToken, SibToken
from .instructions import Imm32Token, Imm8Token
from .instructions import RmMem, RmMemDisp, RmReg, RmAbs, MovAdr
from .instructions import Jb, Jae, NearJump
from .instructions import SubImm, AddImm
from .registers import XmmRegister, X86Register, rsp
from ..arch import ArtificialInstruction

sse1_isa = Isa()
sse2_isa = Isa()


class SseInstruction(Instruction):
    tokens = [
        PrefixToken,
        RexToken, OpcodeToken, ModRmToken, SibToken,
        Imm8Token, Imm32Token]

    def set_user_patterns(self, tokens):
        # TODO: Improve this way of setting 'r':
        tokens.set_field('r', (self.r.num & 8) >> 3)
        tokens.set_field('reg', self.r.num & 0x7)

    def encode(self):
        """ Use a custom encode... """
        # TODO: find a better way for this!
        # 1. Set patterns:
        tokens = self.get_tokens()
        self.set_all_patterns(tokens)

        # 2. Encode:
        r = bytes()

        # prefix:
        if tokens[0].prefix != 0:
            r += tokens[0].encode()

        # Rex prefix:
        if tokens[1][0:4] > 0:
            r += tokens[1].encode()

        # 0f:
        r += bytes([0x0f])

        # opcode:
        r += tokens[2].encode()

        # rm byte:
        r += tokens[3].encode()

        # Encode sib byte:
        if tokens[3].mod != 3 and tokens[3].rm == 4:
            r += tokens[4].encode()

        # Encode displacement bytes:
        if tokens[3].mod == 1:
            r += tokens[5].encode()
        if tokens[3].mod == 2:
            r += tokens[6].encode()

        # Rip relative addressing mode with disp32
        if tokens[3].mod == 0 and tokens[3].rm == 5:
            r += tokens[6].encode()

        # sib byte and ...
        if tokens[3].mod == 0 and tokens[3].rm == 4:
            if tokens[4].base == 5:
                r += tokens[6].encode()
        return r


class Sse1Instruction(SseInstruction):
    """ Sse1 instruction """
    isa = sse1_isa


class Sse2Instruction(SseInstruction):
    """ Sse2 instruction """
    isa = sse2_isa


class RmXmmReg(Constructor):
    """ Xmm register access """
    reg_rm = Operand('reg_rm', XmmRegister, read=True)
    syntax = Syntax([reg_rm])
    patterns = {'mod': 3}

    def set_user_patterns(self, tokens):
        # TODO: Improve this way of setting 'r':
        tokens.set_field('b', (self.reg_rm.num & 8) >> 3)
        tokens.set_field('rm', self.reg_rm.num & 0x7)


xmm_rm_modes = (RmXmmReg, RmMem, RmMemDisp, RmAbs)


class Movss(Sse1Instruction):
    """ Move scalar single-fp value """
    r = Operand('r', XmmRegister, write=True)
    rm = Operand('rm', xmm_rm_modes)
    syntax = Syntax(['movss', ' ', r, ',', ' ', rm])
    patterns = {'prefix': 0xf3, 'opcode': 0x10}


class Movsd(Sse2Instruction):
    """ Move scalar double-fp value """
    r = Operand('r', XmmRegister, write=True)
    rm = Operand('rm', xmm_rm_modes)
    syntax = Syntax(['movsd', ' ', r, ',', ' ', rm])
    patterns = {'prefix': 0xf2, 'opcode': 0x10}


class Movss2(Sse1Instruction):
    """ Move scalar single-fp value """
    rm = Operand('rm', xmm_rm_modes)
    r = Operand('r', XmmRegister, read=True)
    syntax = Syntax(['movss', ' ', rm, ',', ' ', r], priority=1)
    patterns = {'prefix': 0xf3, 'opcode': 0x11}


class Movsd2(Sse2Instruction):
    """ Move scalar double-fp value """
    rm = Operand('rm', xmm_rm_modes)
    r = Operand('r', XmmRegister, read=True)
    syntax = Syntax(['movsd', ' ', rm, ',', ' ', r], priority=1)
    patterns = {'prefix': 0xf2, 'opcode': 0x11}


class Addss(Sse1Instruction):
    """ Add scalar single-fp value """
    r = Operand('r', XmmRegister, write=True)
    rm = Operand('rm', xmm_rm_modes, read=True)
    patterns = {'prefix': 0xf3, 'opcode': 0x58}
    syntax = Syntax(['addss', ' ', r, ',', ' ', rm])


class Addsd(Sse2Instruction):
    """ Add scalar double-fp value """
    r = Operand('r', XmmRegister, write=True)
    rm = Operand('rm', xmm_rm_modes, read=True)
    patterns = {'prefix': 0xf2, 'opcode': 0x58}
    syntax = Syntax(['addsd', ' ', r, ',', ' ', rm])


class Subss(Sse1Instruction):
    """ Sub scalar single-fp value """
    r = Operand('r', XmmRegister, write=True)
    rm = Operand('rm', xmm_rm_modes, read=True)
    patterns = {'prefix': 0xf3, 'opcode': 0x5c}
    syntax = Syntax(['subss', ' ', r, ',', ' ', rm])


class Subsd(Sse2Instruction):
    """ Sub scalar double-fp value """
    r = Operand('r', XmmRegister, write=True)
    rm = Operand('rm', xmm_rm_modes, read=True)
    patterns = {'prefix': 0xf2, 'opcode': 0x5c}
    syntax = Syntax(['subsd', ' ', r, ',', ' ', rm])


class Mulss(Sse1Instruction):
    """ Multiply scalar single-fp value """
    r = Operand('r', XmmRegister, write=True)
    rm = Operand('rm', xmm_rm_modes, read=True)
    patterns = {'prefix': 0xf3, 'opcode': 0x59}
    syntax = Syntax(['mulss', ' ', r, ',', ' ', rm])


class Mulsd(Sse2Instruction):
    """ Multiply scalar double-fp value """
    r = Operand('r', XmmRegister, write=True)
    rm = Operand('rm', xmm_rm_modes, read=True)
    patterns = {'prefix': 0xf2, 'opcode': 0x59}
    syntax = Syntax(['mulsd', ' ', r, ',', ' ', rm])


class Divss(Sse1Instruction):
    """ Divide scalar single-fp value """
    r = Operand('r', XmmRegister, write=True)
    rm = Operand('rm', xmm_rm_modes, read=True)
    patterns = {'prefix': 0xf3, 'opcode': 0x5e}
    syntax = Syntax(['divss', ' ', r, ',', ' ', rm])


class Divsd(Sse2Instruction):
    """ Divide scalar double-fp value """
    r = Operand('r', XmmRegister, write=True)
    rm = Operand('rm', xmm_rm_modes, read=True)
    patterns = {'prefix': 0xf2, 'opcode': 0x5e}
    syntax = Syntax(['divsd', ' ', r, ',', ' ', rm])


class Cvtss2si(Sse1Instruction):
    """ Convert scalar single-fp to integer """
    r = Operand('r', X86Register, write=True)
    rm = Operand('rm', xmm_rm_modes, read=True)
    syntax = Syntax(['cvtss2si', ' ', r, ',', ' ', rm])
    patterns = {'prefix': 0xf3, 'opcode': 0x2d, 'w': 1}


class Cvtsd2si(Sse2Instruction):
    """ Convert scalar double-fp to integer """
    r = Operand('r', X86Register, write=True)
    rm = Operand('rm', xmm_rm_modes, read=True)
    syntax = Syntax(['cvtsd2si', ' ', r, ',', ' ', rm])
    patterns = {'prefix': 0xf2, 'opcode': 0x2d, 'w': 1}


class Cvtsi2ss(Sse1Instruction):
    """ Convert integer to scalar single-fp """
    r = Operand('r', XmmRegister, write=True)
    rm = Operand('rm', rm_modes, read=True)
    syntax = Syntax(['cvtsi2ss', ' ', r, ',', ' ', rm])
    patterns = {'prefix': 0xf3, 'opcode': 0x2a, 'w': 1}


class Cvtsi2sd(Sse2Instruction):
    """ Convert integer to scalar double-fp """
    r = Operand('r', XmmRegister, write=True)
    rm = Operand('rm', rm_modes, read=True)
    syntax = Syntax(['cvtsi2sd', ' ', r, ',', ' ', rm])
    patterns = {'prefix': 0xf2, 'opcode': 0x2a, 'w': 1}


class Cvtss2sd(Sse2Instruction):
    """ Convert scalar single-fp to scalar double-fp """
    r = Operand('r', XmmRegister, write=True)
    rm = Operand('rm', xmm_rm_modes, read=True)
    syntax = Syntax(['cvtss2sd', ' ', r, ',', ' ', rm])
    patterns = {'prefix': 0xf3, 'opcode': 0x5a}


class Cvtsd2ss(Sse2Instruction):
    """ Convert scalar double-fp to scalar single-fp """
    r = Operand('r', XmmRegister, write=True)
    rm = Operand('rm', xmm_rm_modes, read=True)
    syntax = Syntax(['cvtsd2ss', ' ', r, ',', ' ', rm])
    patterns = {'prefix': 0xf2, 'opcode': 0x5a}


class Comiss(Sse1Instruction):
    """ Scalar compare single-fp values """
    r = Operand('r', XmmRegister, read=True)
    rm = Operand('rm', xmm_rm_modes, read=True)
    syntax = Syntax(['comiss', ' ', r, ',', ' ', rm])
    patterns = {'opcode': 0x2f}


class Ucomiss(Sse1Instruction):
    """ Unordered scalar compare single-fp values """
    r = Operand('r', XmmRegister, read=True)
    rm = Operand('rm', xmm_rm_modes, read=True)
    syntax = Syntax(['ucomiss', ' ', r, ',', ' ', rm])
    patterns = {'opcode': 0x2e}


class SsePseudoInstruction(ArtificialInstruction):
    isa = sse1_isa


class PushXmm(SsePseudoInstruction):
    r = Operand('r', XmmRegister, read=True)
    syntax = Syntax(['push', ' ', r])

    def render(self):
        # sub rsp, 16
        yield SubImm(rsp, 16)

        # movdqu [rsp], r
        yield Movsd2(RmMem(rsp), self.r)


class PopXmm(SsePseudoInstruction):
    r = Operand('r', XmmRegister, write=True)
    syntax = Syntax(['pop', ' ', r])

    def render(self):
        # movdqu [rsp], r
        yield Movsd(self.r, RmMem(rsp))

        # add rsp, 16
        yield AddImm(rsp, 16)


@sse2_isa.pattern('regfp', 'F64TOF32(regfp)', size=6, cycles=3, energy=3)
def pattern_f64tof32(context, tree, c0):
    d = context.new_reg(XmmRegister)
    context.emit(Cvtsd2ss(d, RmXmmReg(c0)))
    return d


@sse2_isa.pattern('regfp', 'F32TOF64(regfp)', size=6, cycles=3, energy=3)
def pattern_f32tof64(context, tree, c0):
    d = context.new_reg(XmmRegister)
    context.emit(Cvtss2sd(d, RmXmmReg(c0)))
    return d


@sse1_isa.pattern('reg64', 'F32TOI64(regfp)', size=6, cycles=2, energy=2)
def pattern_f32toi64(context, tree, c0):
    d = context.new_reg(X86Register)
    context.emit(Cvtss2si(d, RmXmmReg(c0)))
    return d


@sse2_isa.pattern('reg64', 'F64TOI64(regfp)', size=6, cycles=3, energy=3)
def pattern_f64toi64(context, tree, c0):
    d = context.new_reg(X86Register)
    context.emit(Cvtsd2si(d, RmXmmReg(c0)))
    return d


@sse1_isa.pattern('regfp', 'I64TOF32(reg64)', size=6, cycles=2, energy=2)
def pattern_i64tof32(context, tree, c0):
    d = context.new_reg(XmmRegister)
    context.emit(Cvtsi2ss(d, RmReg(c0)))
    return d


@sse2_isa.pattern('regfp', 'I64TOF64(reg64)', size=6, cycles=3, energy=3)
def pattern_i64tof64(context, tree, c0):
    d = context.new_reg(XmmRegister)
    context.emit(Cvtsi2sd(d, RmReg(c0)))
    return d


@sse1_isa.pattern('regfp', 'CONSTF32', size=8, cycles=6, energy=2)
def pattern_const_f32(context, tree):
    float_const = struct.pack('f', tree.value)
    const_label = context.frame.add_constant(float_const)
    label_addr = context.new_reg(X86Register)
    context.emit(MovAdr(label_addr, const_label))
    d = context.new_reg(XmmRegister)
    context.emit(Movss(d, RmMem(label_addr)))
    return d


@sse2_isa.pattern('regfp', 'CONSTF64', size=8, cycles=9, energy=4)
def pattern_const_f64(context, tree):
    float_const = struct.pack('d', tree.value)
    const_label = context.frame.add_constant(float_const)
    label_addr = context.new_reg(X86Register)
    context.emit(MovAdr(label_addr, const_label))
    d = context.new_reg(XmmRegister)
    context.emit(Movsd(d, RmMem(label_addr)))
    return d


@sse1_isa.pattern('regfp', 'ADDF32(regfp, regfp)', size=6, cycles=2, energy=2)
def pattern_addf32(context, tree, c0, c1):
    d = context.new_reg(XmmRegister)
    context.emit(Movss(d, RmXmmReg(c0)))
    context.emit(Addss(d, RmXmmReg(c1)))
    return d


@sse2_isa.pattern('regfp', 'ADDF64(regfp, regfp)', size=6, cycles=4, energy=3)
def pattern_addf64(context, tree, c0, c1):
    d = context.new_reg(XmmRegister)
    context.emit(Movsd(d, RmXmmReg(c0)))
    context.emit(Addsd(d, RmXmmReg(c1)))
    return d


@sse1_isa.pattern('regfp', 'SUBF32(regfp, regfp)', size=6, cycles=2, energy=2)
def pattern_sub_f32(context, tree, c0, c1):
    d = context.new_reg(XmmRegister)
    context.emit(Movss(d, RmXmmReg(c0)))
    context.emit(Subss(d, RmXmmReg(c1)))
    return d


@sse2_isa.pattern('regfp', 'SUBF64(regfp, regfp)', size=6, cycles=3, energy=3)
def pattern_sub_f64(context, tree, c0, c1):
    d = context.new_reg(XmmRegister)
    context.emit(Movsd(d, RmXmmReg(c0)))
    context.emit(Subsd(d, RmXmmReg(c1)))
    return d


@sse1_isa.pattern('regfp', 'MULF32(regfp, regfp)', size=6, cycles=2, energy=2)
def pattern_mul_f32(context, tree, c0, c1):
    d = context.new_reg(XmmRegister)
    context.emit(Movss(d, RmXmmReg(c0)))
    context.emit(Mulss(d, RmXmmReg(c1)))
    return d


@sse2_isa.pattern('regfp', 'MULF64(regfp, regfp)', size=6, cycles=3, energy=3)
def pattern_mul_f64(context, tree, c0, c1):
    d = context.new_reg(XmmRegister)
    context.emit(Movsd(d, RmXmmReg(c0)))
    context.emit(Mulsd(d, RmXmmReg(c1)))
    return d


@sse1_isa.pattern('regfp', 'DIVF32(regfp, regfp)', size=6, cycles=2, energy=2)
def pattern_div_f32(context, tree, c0, c1):
    d = context.new_reg(XmmRegister)
    context.emit(Movss(d, RmXmmReg(c0)))
    context.emit(Divss(d, RmXmmReg(c1)))
    return d


@sse2_isa.pattern('regfp', 'DIVF64(regfp, regfp)', size=6, cycles=4, energy=3)
def pattern_div_f64(context, tree, c0, c1):
    d = context.new_reg(XmmRegister)
    context.emit(Movsd(d, RmXmmReg(c0)))
    context.emit(Divsd(d, RmXmmReg(c1)))
    return d


@sse1_isa.pattern('stm', 'MOVF32(regfp)', size=3, cycles=2, energy=2)
def pattern_mov_f32(context, tree, c0):
    context.emit(Movss(tree.value, RmXmmReg(c0)))


@sse2_isa.pattern('stm', 'MOVF64(regfp)', size=3, cycles=3, energy=3)
def pattern_mov_f64(context, tree, c0):
    context.emit(Movsd(tree.value, RmXmmReg(c0)))


@sse2_isa.pattern('regfp', 'REGF64', size=0, cycles=0, energy=0)
@sse1_isa.pattern('regfp', 'REGF32', size=0, cycles=0, energy=0)
def pattern_reg_fp(context, tree):
    return tree.value


@sse1_isa.pattern('stm', 'STRF32(reg64, regfp)', size=6, cycles=2, energy=2)
def pattern_str_f32(context, tree, c0, c1):
    context.emit(Movss2(RmMem(c0), c1))


@sse2_isa.pattern('stm', 'STRF64(reg64, regfp)', size=6, cycles=3, energy=3)
def pattern_str_f64(context, tree, c0, c1):
    context.emit(Movsd2(RmMem(c0), c1))


@sse1_isa.pattern('regfp', 'LDRF32(reg64)', size=6, cycles=2, energy=2)
def pattern_ldr_f32(context, tree, c0):
    d = context.new_reg(XmmRegister)
    context.emit(Movss(d, RmMem(c0)))
    return d


@sse2_isa.pattern('regfp', 'LDRF64(reg64)', size=6, cycles=3, energy=3)
def pattern_ldr_f64(context, tree, c0):
    d = context.new_reg(XmmRegister)
    context.emit(Movsd(d, RmMem(c0)))
    return d


@sse1_isa.pattern('stm', 'CJMP(regfp,regfp)', size=6, cycles=3, energy=3)
def pattern_cjmp_f(context, tree, c0, c1):
    # TODO: is it float32 or float64?
    context.emit(Ucomiss(c0, RmXmmReg(c1)))

    op, yes_label, no_label = tree.value
    opnames = {"<": Jb, ">": Jae}
    Bop = opnames[op]
    jmp_ins = NearJump(no_label.name, jumps=[no_label])
    context.emit(Bop(yes_label.name, jumps=[yes_label, jmp_ins]))
    context.emit(jmp_ins)
