""" Definitions of Riscv instructions. """

import struct
from ..isa import Isa
from ..encoding import Instruction, Syntax, Operand
from .registers import RiscvRegister, R0
from .tokens import RiscvToken, RiscvIToken, RiscvSToken
from .instructions import Li, B, Bne, Sw, Lw


class RegisterSet(set):
    def __repr__(self):
        reg_names = sorted(str(r) for r in self)
        return ", ".join(reg_names)


rvfxisa = Isa()


class RiscvInstruction(Instruction):
    tokens = [RiscvToken]
    isa = rvfxisa


def make_fregfregfreg(mnemonic, rounding, func):
    rd = Operand("rd", RiscvRegister, write=True)
    rn = Operand("rn", RiscvRegister, read=True)
    rm = Operand("rm", RiscvRegister, read=True)
    syntax = Syntax([mnemonic, ".", "s", " ", rd, ",", " ", rn, ",", " ", rm])
    tokens = [RiscvToken]
    patterns = {
        "opcode": 0b1010011,
        "rd": rd,
        "funct3": rounding,
        "rs1": rn,
        "rs2": rm,
        "funct7": func,
    }
    members = {
        "syntax": syntax,
        "rd": rd,
        "rn": rn,
        "rm": rm,
        "patterns": patterns,
        "tokens": tokens,
        "rounding": rounding,
        "func": func,
    }
    return type(mnemonic + "_ins", (RiscvInstruction,), members)


FAdd = make_fregfregfreg("fadd", 0b111, 0b0000000)
FSub = make_fregfregfreg("fsub", 0b111, 0b0000100)
FMul = make_fregfregfreg("fmul", 0b111, 0b0001000)
FDiv = make_fregfregfreg("fdiv", 0b111, 0b0001100)
FSgnjn = make_fregfregfreg("fsgnjn", 0b001, 0b0010000)


def negf(dst, src):
    """ Move src into dst register """
    return FSgnjn(dst, src, src)


class Fcvtsw(RiscvInstruction):
    rd = Operand("rd", RiscvRegister, write=True)
    rm = Operand("rm", RiscvRegister, read=True)
    syntax = Syntax(["fcvt", ".", "s", ".", "w", " ", rd, ",", " ", rm])
    patterns = {
        "opcode": 0b1010011,
        "rd": rd,
        "funct3": 0b111,
        "rs1": rm,
        "rs2": 0,
        "funct7": 0b1101000,
    }


class Fcvtswu(RiscvInstruction):
    rd = Operand("rd", RiscvRegister, write=True)
    rm = Operand("rm", RiscvRegister, read=True)
    syntax = Syntax(["fcvt", ".", "s", ".", "wu", " ", rd, ",", " ", rm])
    patterns = {
        "opcode": 0b1010011,
        "rd": rd,
        "funct3": 0b111,
        "rs1": rm,
        "rs2": 0b00001,
        "funct7": 0b1101000,
    }


class Fcvtws(RiscvInstruction):
    rd = Operand("rd", RiscvRegister, write=True)
    rm = Operand("rm", RiscvRegister, read=True)
    syntax = Syntax(["fcvt", ".", "w", ".", "s", " ", rd, ",", " ", rm])
    patterns = {
        "opcode": 0b1010011,
        "rd": rd,
        "funct3": 0b111,
        "rs1": rm,
        "rs2": 0,
        "funct7": 0b1100000,
    }


class Fcvtwus(RiscvInstruction):
    rd = Operand("rd", RiscvRegister, write=True)
    rm = Operand("rm", RiscvRegister, read=True)
    syntax = Syntax(["fcvt", ".", "wu", ".", "s", " ", rd, ",", " ", rm])
    patterns = {
        "opcode": 0b1010011,
        "rd": rd,
        "funct3": 0b111,
        "rs1": rm,
        "rs2": 0b00001,
        "funct7": 0b1100000,
    }


def make_fcmp(mnemonic, func3, invert):
    """ Factory function for immediate value instructions """
    rd = Operand("rd", RiscvRegister, write=True)
    rn = Operand("rn", RiscvRegister, read=True)
    rm = Operand("rm", RiscvRegister, read=True)
    tokens = [RiscvToken]
    syntax = Syntax(
        ["f", ".", mnemonic, ".", "s", " ", rd, ",", " ", rn, ",", " ", rm]
    )
    if not invert:
        patterns = {
            "opcode": 0b1010011,
            "rd": rd,
            "funct3": func3,
            "rs1": rn,
            "rs2": rm,
            "funct7": 0b1010000,
        }
    else:
        patterns = {
            "opcode": 0b1010011,
            "rd": rd,
            "funct3": func3,
            "rs1": rm,
            "rs2": rn,
            "funct7": 0b1010000,
        }
    members = {
        "syntax": syntax,
        "rd": rd,
        "rn": rn,
        "rm": rm,
        "patterns": patterns,
        "tokens": tokens,
        "func3": func3,
    }
    return type(mnemonic + "_ins", (RiscvInstruction,), members)


Feq = make_fcmp("feq", 0b010, False)
Fle = make_fcmp("fle", 0b000, False)
Flt = make_fcmp("flt", 0b001, False)
Fne = make_fcmp("fne", 0b010, True)
Fgt = make_fcmp("fgt", 0b000, True)
Fge = make_fcmp("fge", 0b001, True)


@rvfxisa.pattern("reg", "CONSTF32", size=2)
@rvfxisa.pattern("reg", "CONSTF64", size=2)
def pattern_const_f32(context, tree):
    float_const = struct.pack("f", tree.value)
    (c0,) = struct.unpack("i", float_const)
    d = context.new_reg(RiscvRegister)
    context.emit(Li(d, c0))
    return d


@rvfxisa.pattern("reg", "ADDF64(reg, reg)", size=5)
@rvfxisa.pattern("reg", "ADDF32(reg, reg)", size=5)
def pattern_add_f32(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(FAdd(d, c0, c1))
    return d


@rvfxisa.pattern("reg", "SUBF64(reg, reg)", size=5)
@rvfxisa.pattern("reg", "SUBF32(reg, reg)", size=5)
def pattern_sub_f32(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(FSub(d, c0, c1))
    return d


@rvfxisa.pattern("reg", "MULF64(reg, reg)", size=5)
@rvfxisa.pattern("reg", "MULF32(reg, reg)", size=5)
def pattern_mul_f32(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(FMul(d, c0, c1))
    return d


@rvfxisa.pattern("reg", "DIVF64(reg, reg)", size=5)
@rvfxisa.pattern("reg", "DIVF32(reg, reg)", size=5)
def pattern_div_f32(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(FDiv(d, c0, c1))
    return d


@rvfxisa.pattern("reg", "NEGF64(reg)", size=5)
@rvfxisa.pattern("reg", "NEGF32(reg)", size=5)
def pattern_neg_f32(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    context.emit(negf(d, c0))
    return d


@rvfxisa.pattern("stm", "MOVF32(reg)", size=5)
@rvfxisa.pattern("stm", "MOVF64(reg)", size=5)
def pattern_mov32(context, tree, c0):
    context.move(tree.value, c0)
    return tree.value


@rvfxisa.pattern("reg", "REGF32", size=2)
@rvfxisa.pattern("reg", "REGF64", size=2)
def pattern_reg(context, tree):
    return tree.value


@rvfxisa.pattern("reg", "F32TOF64(reg)", size=2)
@rvfxisa.pattern("reg", "F64TOF32(reg)", size=2)
def pattern_i32_to_i32(context, tree, c0):
    return c0


@rvfxisa.pattern("reg", "F32TOI32(reg)", size=2)
@rvfxisa.pattern("reg", "F64TOI32(reg)", size=2)
def pattern_ftoi_f32(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    context.emit(Fcvtws(d, c0))
    return d


@rvfxisa.pattern("reg", "F32TOU32(reg)", size=2)
@rvfxisa.pattern("reg", "F64TOU32(reg)", size=2)
def pattern_ftou_f32(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    context.emit(Fcvtws(d, c0))
    return d


@rvfxisa.pattern("reg", "I32TOF32(reg)", size=2)
@rvfxisa.pattern("reg", "I32TOF64(reg)", size=2)
def pattern_itof_f32(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    context.emit(Fcvtsw(d, c0))
    return d


@rvfxisa.pattern("reg", "U32TOF32(reg)", size=2)
@rvfxisa.pattern("reg", "U32TOF64(reg)", size=2)
def pattern_utof_f32(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    context.emit(Fcvtswu(d, c0))
    return d


@rvfxisa.pattern("reg", "LDRF32(mem)", size=2)
@rvfxisa.pattern("reg", "LDRF64(mem)", size=2)
def pattern_ldr32_fprel(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    base_reg, offset = c0
    Code = Lw(d, offset, base_reg)
    Code.fprel = True
    context.emit(Code)
    return d


@rvfxisa.pattern("reg", "LDRF32(reg)", size=2)
@rvfxisa.pattern("reg", "LDRF64(reg)", size=2)
def pattern_ldr32_fprel(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    base_reg, offset = c0, 0
    Code = Lw(d, offset, base_reg)
    context.emit(Code)
    return d


@rvfxisa.pattern("stm", "STRF32(mem, reg)", size=2)
@rvfxisa.pattern("stm", "STRF64(mem, reg)", size=2)
def pattern_sw32(context, tree, c0, c1):
    base_reg, offset = c0
    Code = Sw(c1, offset, base_reg)
    Code.fprel = True
    context.emit(Code)


@rvfxisa.pattern("stm", "STRF32(reg, reg)", size=2)
@rvfxisa.pattern("stm", "STRF64(reg, reg)", size=2)
def pattern_sw32(context, tree, c0, c1):
    base_reg, offset = c0, 0
    Code = Sw(c1, offset, base_reg)
    context.emit(Code)


@rvfxisa.pattern("stm", "CJMPF32(reg, reg)", size=2)
@rvfxisa.pattern("stm", "CJMPF64(reg, reg)", size=2)
def pattern_cjmp(context, tree, c0, c1):
    op, yes_label, no_label = tree.value
    opnames = {"<": Flt, ">": Fgt, "==": Feq, "!=": Fne, ">=": Fge, "<=": Fle}
    Bop = opnames[op]
    jmp_ins = B(no_label.name, jumps=[no_label])
    d = context.new_reg(RiscvRegister)
    context.emit(Bop(d, c0, c1))
    context.emit(Bne(d, R0, yes_label.name, jumps=[yes_label, jmp_ins]))
    context.emit(jmp_ins)
