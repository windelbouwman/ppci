""" Microblaze instructions """

from ..encoding import Instruction, Syntax, Operand, Relocation

from ..isa import Isa
from ..token import Token, bit_range, Endianness
from ..generic_instructions import ArtificialInstruction
from ..generic_instructions import RegisterUseDef, Global
from .registers import MicroBlazeRegister, R0
from . import registers


isa = Isa()


class MicroBlazeToken32(Token):
    class Info:
        size = 32
        endianness = Endianness.BIG


# In order to deal with reversed bit ordering, the bit ranges are reversed
# from 0..31 to 31..0.
# The microblaze has two instruction formats named A and B:
class TypeAToken(MicroBlazeToken32):
    opcode = bit_range(26, 32)  # bit_range(0, 6)
    rd = bit_range(21, 26)  # bit_range(6, 11)
    ra = bit_range(16, 21)  # bit_range(11, 16)
    rb = bit_range(11, 16)  # bit_range(16, 21)
    opcode2 = bit_range(0, 11)  # bit_range(21, 32)


class TypeBToken(MicroBlazeToken32):
    opcode = bit_range(26, 32)  # bit_range(0, 6)
    rd = bit_range(21, 26)  # bit_range(6, 11)
    ra = bit_range(16, 21)  # bit_range(11, 16)
    imm = bit_range(0, 16)  # bit_range(16, 32)


class PcRel64Token(Token):
    """ A double immediate field token """

    class Info:
        size = 64
        endianness = Endianness.BIG

    imm = bit_range(32, 48) + bit_range(0, 16)


class MicroBlazeInstruction(Instruction):
    isa = isa


def syntax_from_operands(mnemonic, operands):
    syntax = [mnemonic]
    if operands:
        for operand in operands[:-1]:
            syntax.extend([" ", operand, ","])
        syntax.extend([" ", operands[-1]])
    return Syntax(syntax)


def type_a(
    mnemonic: str, opcode1, opcode2, rd=None, ra=None, rb=None, rd_write=True
):
    """ Create a type a instruction """
    operands = []
    if rd is None:
        if rd_write:
            rd = Operand("rd", MicroBlazeRegister, write=True)
        else:
            rd = Operand("rd", MicroBlazeRegister, read=True)
        operands.append(rd)
    if ra is None:
        ra = Operand("ra", MicroBlazeRegister, read=True)
        operands.append(ra)
    if rb is None:
        rb = Operand("rb", MicroBlazeRegister, read=True)
        operands.append(rb)

    syntax = syntax_from_operands(mnemonic, operands)
    patterns = {
        "opcode": opcode1,
        "opcode2": opcode2,
        "rd": rd,
        "ra": ra,
        "rb": rb,
    }
    members = {
        "tokens": [TypeAToken],
        "rd": rd,
        "ra": ra,
        "rb": rb,
        "syntax": syntax,
        "patterns": patterns,
    }

    name = mnemonic.title()
    return type(name, (MicroBlazeInstruction,), members)


def type_b(mnemonic, opcode, rd=None, ra=None, imm=None, rd_write=True):
    """ Create an instruction class for a type B instruction """
    operands = []
    if rd is None:
        if rd_write:
            rd = Operand("rd", MicroBlazeRegister, write=True)
        else:
            rd = Operand("rd", MicroBlazeRegister, read=True)
        operands.append(rd)

    if ra is None:
        ra = Operand("ra", MicroBlazeRegister, read=True)
        operands.append(ra)

    if imm is None:
        imm = Operand("imm", int)
        operands.append(imm)

    syntax = syntax_from_operands(mnemonic, operands)
    patterns = {"opcode": opcode, "rd": rd, "ra": ra, "imm": imm}
    members = {
        "tokens": [TypeBToken],
        "rd": rd,
        "ra": ra,
        "imm": imm,
        "syntax": syntax,
        "patterns": patterns,
    }

    name = mnemonic.title()
    return type(name, (MicroBlazeInstruction,), members)


# See table 1-6 in the microblaze reference manual:

Add = type_a("add", 0, 0)
Rsub = type_a("rsub", 1, 0)
Addc = type_a("addc", 2, 0)
Rsubc = type_a("rsubc", 3, 0)
Addk = type_a("addk", 4, 0)
Rsubk = type_a("rsubk", 5, 0)
Addkc = type_a("addkc", 6, 0)
Rsubkc = type_a("rsubkc", 7, 0)

Cmp = type_a("cmp", 5, 1)
Cmpu = type_a("cmpu", 5, 3)

Addi = type_b("addi", 8)
Rsubi = type_b("rsubi", 9)
Addic = type_b("addic", 10)
Rsubic = type_b("rsubic", 11)
Addik = type_b("addik", 12)
Rsubik = type_b("rsubik", 13)
Addikc = type_b("addikc", 14)
Rsubikc = type_b("rsubikc", 15)

Mul = type_a("mul", 0x10, 0)
Mulh = type_a("mulh", 0x10, 1)
Mulhu = type_a("mulhu", 0x10, 3)
Mulhsu = type_a("mulhsu", 0x10, 2)

Bsra = type_a("bsra", 0x11, 0x200)
Bsll = type_a("bsll", 0x11, 0x400)

Muli = type_b("muli", 0x18)

Bsrli = 0
Bsrai = 0
Bslli = 0

Idiv = type_a("idiv", 0x12, 0)
Idivu = type_a("idiv", 0x12, 2)


# Floating point instructions:
def type_float(mnemonic, opcode, rb=None):
    return type_a(mnemonic, 0x16, opcode, rb=rb)


Fadd = type_float("fadd", 0)
Frsub = type_float("frsub", 0x80)
Fmul = type_float("fmul", 0x100)
Fdiv = type_float("fdiv", 0x180)
# TODO:
# Fcmp_un = type_float('fcmp.un', 0x200)
# Fcmp_lt = type_float('fcmp.lt', 0x210)
# Fcmp_eq = type_float('fcmp.eq', 0x220)
# Fcmp_le = type_float('fcmp.le', 0x230)
# Fcmp_gt = type_float('fcmp.gt', 0x240)
# Fcmp_ne = type_float('fcmp.ne', 0x250)
# Fcmp_ge = type_float('fcmp.ge', 0x260)
Flt = type_float("flt", 0x280, rb=0)
Fint = type_float("fint", 0x300, rb=0)
Fsqrt = type_float("fsqrt", 0x380, rb=0)

Or = type_a("or", 0x20, 0)
And = type_a("and", 0x21, 0)
Xor = type_a("xor", 0x22, 0)
Andn = type_a("andn", 0x23, 0)
Pcmpbf = type_a("pcmpbf", 0x20, 0x400)
Pcmpeq = type_a("pcmpeq", 0x22, 0x400)
Pcmpne = type_a("pcmpeq", 0x23, 0x400)

Sra = type_b("sra", 0x24, imm=0x1)
Src = type_b("sra", 0x24, imm=0x21)
Srl = type_b("sra", 0x24, imm=0x41)
Sext8 = type_b("sext8", 0x24, imm=0x60)
Sext16 = type_b("sext16", 0x24, imm=0x61)
Wic = type_a("wic", 0x24, 0x68, rd=0)
Wdc = type_a("wic", 0x24, 0x64, rd=0)

Br = type_a("br", 0x26, 0, rd=0, ra=0x0)
Brd = type_a("brd", 0x26, 0, rd=0, ra=0x10)
Brld = type_a("brld", 0x26, 0, ra=0x14)
Bra = type_a("bra", 0x26, 0, rd=0, ra=0x8)
Brad = type_a("brad", 0x26, 0, rd=0, ra=0x18)
Brald = type_a("brald", 0x26, 0, ra=0x1C)
Brk = type_a("brk", 0x26, 0, ra=0xC)

Beq = type_a("beq", 0x27, 0, rd=0x0)
Bne = type_a("bne", 0x27, 0, rd=0x1)
Blt = type_a("blt", 0x27, 0, rd=0x2)
Ble = type_a("ble", 0x27, 0, rd=0x3)
Bgt = type_a("bgt", 0x27, 0, rd=0x4)
Bge = type_a("bge", 0x27, 0, rd=0x5)

Beqd = type_a("beqd", 0x27, 0, rd=0x10)
Bned = type_a("bned", 0x27, 0, rd=0x11)
Bltd = type_a("bltd", 0x27, 0, rd=0x12)
Bled = type_a("bled", 0x27, 0, rd=0x13)
Bgtd = type_a("bgtd", 0x27, 0, rd=0x14)
Bged = type_a("bged", 0x27, 0, rd=0x15)

Ori = type_b("ori", 0x28)
Andi = type_b("andi", 0x29)
Xori = type_b("xori", 0x2A)
Andni = type_b("andni", 0x2B)
Imm = type_b("imm", 0x2C, rd=0, ra=0)

Rtsd = type_b("rtsd", 0x2D, rd=0x10)
Rtid = type_b("rtsd", 0x2D, rd=0x11)
Rtbd = type_b("rtbd", 0x2D, rd=0x12)
Rted = type_b("rted", 0x2D, rd=0x14)

Bri = type_b("bri", 0x2E, rd=0, ra=0)
Brid = type_b("brid", 0x2E, rd=0, ra=0x10)
Brlid = type_b("brlid", 0x2E, ra=0x14)
Brai = type_b("brai", 0x2E, rd=0, ra=0x8)
Braid = type_b("braid", 0x2E, rd=0, ra=0x18)
Bralid = type_b("bralid", 0x2E, ra=0x1C)
Brki = type_b("brki", 0x2E, ra=0xC)

Beqi = type_b("beqi", 0x2F, rd=0x0)
Bnei = type_b("bnei", 0x2F, rd=0x1)
Blti = type_b("blti", 0x2F, rd=0x2)
Blei = type_b("blei", 0x2F, rd=0x3)
Bgti = type_b("bgti", 0x2F, rd=0x4)
Bgei = type_b("bgei", 0x2F, rd=0x5)
Beqid = type_b("beqid", 0x2F, rd=0x10)
Bneid = type_b("bneid", 0x2F, rd=0x11)
Bltid = type_b("bltid", 0x2F, rd=0x12)
Bleid = type_b("bleid", 0x2F, rd=0x13)
Bgtid = type_b("bgtid", 0x2F, rd=0x14)
Bgeid = type_b("bgeid", 0x2F, rd=0x15)

# Memory:
Lbu = type_a("lbu", 0x30, 0)
Lhu = type_a("lhu", 0x31, 0)
Lw = type_a("lw", 0x32, 0)
Sb = type_a("sb", 0x34, 0, rd_write=False)
Sh = type_a("sh", 0x35, 0, rd_write=False)
Sw = type_a("sw", 0x36, 0, rd_write=False)

Lbui = type_b("lbui", 0x38)
Lhui = type_b("lhui", 0x39)
Lwi = type_b("lwi", 0x3A)
Sbi = type_b("sbi", 0x3C, rd_write=False)
Shi = type_b("shi", 0x3D, rd_write=False)
Swi = type_b("swi", 0x3E, rd_write=False)


def label_imm():
    pass


@isa.register_relocation
class PcRelRelocation64(Relocation):
    name = "R_MICROBLAZE_64_PCREL"
    number = 1  # TODO: lookup in elf spec
    token = PcRel64Token
    field = "imm"

    def calc(self, sym_value, reloc_value):
        return sym_value - (reloc_value + 4)


@isa.register_relocation
class AbsRelocation64(Relocation):
    name = "R_MICROBLAZE_64_ABS"
    number = 2  # TODO: lookup in elf spec
    token = PcRel64Token
    field = "imm"

    def calc(self, sym_value, reloc_value):
        return sym_value


class Bri_label(ArtificialInstruction):
    isa = isa
    target = Operand("target", str)
    syntax = Syntax(["bri", " ", target])

    def relocations(self):
        return [PcRelRelocation64(self.target)]

    def render(self):
        yield Imm(0)
        yield Bri(0)


class Brlid_label(ArtificialInstruction):
    isa = isa
    rd = Operand("rd", MicroBlazeRegister, write=True)
    target = Operand("target", str)
    syntax = Syntax(["brlid", " ", rd, ",", " ", target])

    def relocations(self):
        return [PcRelRelocation64(self.target)]

    def render(self):
        yield Imm(0)
        yield Brlid(self.rd, 0)


class Addik_label(ArtificialInstruction):
    isa = isa
    rd = Operand("rd", MicroBlazeRegister, write=True)
    ra = Operand("ra", MicroBlazeRegister, read=True)
    target = Operand("target", str)
    syntax = Syntax(["addik", " ", rd, ",", " ", ra, ",", " ", target])

    def relocations(self):
        return [AbsRelocation64(self.target)]

    def render(self):
        yield Imm(0)
        yield Addik(self.rd, self.ra, 0)


# Branch equal operators
class Beqi_label(ArtificialInstruction):
    isa = isa
    ra = Operand("ra", MicroBlazeRegister, read=True)
    target = Operand("target", str)
    syntax = Syntax(["beqi", " ", ra, ",", " ", target])

    def relocations(self):
        return [PcRelRelocation64(self.target)]

    def render(self):
        yield Imm(0)
        yield Beqi(self.ra, 0)


class Bnei_label(ArtificialInstruction):
    isa = isa
    ra = Operand("ra", MicroBlazeRegister, read=True)
    target = Operand("target", str)
    syntax = Syntax(["bnei", " ", ra, ",", " ", target])

    def relocations(self):
        return [PcRelRelocation64(self.target)]

    def render(self):
        yield Imm(0)
        yield Bnei(self.ra, 0)


class Blti_label(ArtificialInstruction):
    isa = isa
    ra = Operand("ra", MicroBlazeRegister, read=True)
    target = Operand("target", str)
    syntax = Syntax(["blti", " ", ra, ",", " ", target])

    def relocations(self):
        return [PcRelRelocation64(self.target)]

    def render(self):
        yield Imm(0)
        yield Blti(self.ra, 0)


class Blei_label(ArtificialInstruction):
    isa = isa
    ra = Operand("ra", MicroBlazeRegister, read=True)
    target = Operand("target", str)
    syntax = Syntax(["blei", " ", ra, ",", " ", target])

    def relocations(self):
        return [PcRelRelocation64(self.target)]

    def render(self):
        yield Imm(0)
        yield Blei(self.ra, 0)


class Bgti_label(ArtificialInstruction):
    isa = isa
    ra = Operand("ra", MicroBlazeRegister, read=True)
    target = Operand("target", str)
    syntax = Syntax(["bgti", " ", ra, ",", " ", target])

    def relocations(self):
        return [PcRelRelocation64(self.target)]

    def render(self):
        yield Imm(0)
        yield Bgti(self.ra, 0)


class Bgei_label(ArtificialInstruction):
    isa = isa
    ra = Operand("ra", MicroBlazeRegister, read=True)
    target = Operand("target", str)
    syntax = Syntax(["bgei", " ", ra, ",", " ", target])

    def relocations(self):
        return [PcRelRelocation64(self.target)]

    def render(self):
        yield Imm(0)
        yield Bgei(self.ra, 0)


def mov(dst, src):
    """ Move instruction """
    # TODO: use the keep carry variant here?
    return Add(dst, registers.R0, src, ismove=True)


def nop():
    return Or(registers.R0, registers.R0, registers.R0)


# Instruction selection:
# Generic:
@isa.pattern("reg", "REGI8", size=0, cycles=0, energy=0)
@isa.pattern("reg", "REGU8", size=0, cycles=0, energy=0)
@isa.pattern("reg", "REGI16", size=0, cycles=0, energy=0)
@isa.pattern("reg", "REGU16", size=0, cycles=0, energy=0)
@isa.pattern("reg", "REGI32", size=0, cycles=0, energy=0)
@isa.pattern("reg", "REGU32", size=0, cycles=0, energy=0)
def pattern_reg(context, tree):
    return tree.value


@isa.pattern("mem", "reg", size=0, cycles=0, energy=0)
def pattern_reg_as_mem(context, tree, reg):
    return (reg, 0)


@isa.pattern("reg", "mem", size=4, cycles=1, energy=1)
def pattern_mem_as_reg(context, tree, mem):
    base, offset = mem
    dst = context.new_reg(MicroBlazeRegister)
    context.emit(Addik(dst, base, offset))
    return dst


@isa.pattern("stm", "MOVI8(reg)", size=4)
@isa.pattern("stm", "MOVU8(reg)", size=4)
@isa.pattern("stm", "MOVI16(reg)", size=4)
@isa.pattern("stm", "MOVU16(reg)", size=4)
@isa.pattern("stm", "MOVI32(reg)", size=4)
@isa.pattern("stm", "MOVU32(reg)", size=4)
def pattern_mov(context, tree, reg):
    context.move(tree.value, reg)


@isa.pattern("reg", "CONSTI8", size=4)
@isa.pattern("reg", "CONSTU8", size=4)
@isa.pattern("reg", "CONSTI16", size=4)
def pattern_const16(context, tree):
    dst = context.new_reg(MicroBlazeRegister)
    context.emit(Addik(dst, R0, tree.value))
    return dst


@isa.pattern("reg", "CONSTU16", size=4)
@isa.pattern("reg", "CONSTI32", size=4)
@isa.pattern("reg", "CONSTU32", size=4)
def pattern_const32(context, tree):
    dst = context.new_reg(MicroBlazeRegister)
    context.emit(Imm(tree.value >> 16))
    context.emit(Addik(dst, R0, tree.value & 0xFFFF))
    return dst


@isa.pattern("reg", "LABEL", size=8)
def pattern_label(context, tree):
    """ Determine the label address and yield its result """
    dst = context.new_reg(MicroBlazeRegister)
    context.emit(Addik_label(dst, R0, tree.value))
    return dst


@isa.pattern("mem", "FPRELU32", size=0)
def pattern_fprel(context, tree):
    offset = tree.value.offset
    return (registers.R1, offset + 4)  # return address is stored at R1 + 0.


# Data conversion patterns:
@isa.pattern("reg", "U32TOI16(reg)", size=0, cycles=0, energy=0)
@isa.pattern("reg", "I32TOI16(reg)", size=0, cycles=0, energy=0)
@isa.pattern("reg", "U32TOU16(reg)", size=0, cycles=0, energy=0)
@isa.pattern("reg", "I32TOU16(reg)", size=0, cycles=0, energy=0)
def pattern_i32toi16(context, tree, reg):
    return reg


@isa.pattern("reg", "I16TOI32(reg)", size=0, cycles=0, energy=0)
def pattern_i16toi32(context, tree, reg):
    dst = context.new_reg(MicroBlazeRegister)
    context.emit(Sext16(dst, reg))
    return dst


@isa.pattern("reg", "U16TOI32(reg)", size=0, cycles=0, energy=0)
@isa.pattern("reg", "U16TOU32(reg)", size=0, cycles=0, energy=0)
@isa.pattern("reg", "I16TOU32(reg)", size=0, cycles=0, energy=0)
def pattern_16to32(context, tree, reg):
    return reg


@isa.pattern("reg", "U32TOI8(reg)", size=0, cycles=0, energy=0)
@isa.pattern("reg", "I32TOI8(reg)", size=0, cycles=0, energy=0)
@isa.pattern("reg", "U32TOU8(reg)", size=0, cycles=0, energy=0)
@isa.pattern("reg", "I32TOU8(reg)", size=0, cycles=0, energy=0)
def pattern_i32toi8(context, tree, reg):
    return reg


@isa.pattern("reg", "I8TOI32(reg)", size=0, cycles=0, energy=0)
def pattern_i8toi32(context, tree, reg):
    dst = context.new_reg(MicroBlazeRegister)
    context.emit(Sext8(dst, reg))
    return dst


@isa.pattern("reg", "U8TOI32(reg)", size=0, cycles=0, energy=0)
@isa.pattern("reg", "U8TOU32(reg)", size=0, cycles=0, energy=0)
@isa.pattern("reg", "I8TOU32(reg)", size=0, cycles=0, energy=0)
def pattern_8to32(context, tree, reg):
    return reg


# Arithmatics:
@isa.pattern("reg", "ADDI8(reg, reg)", size=4)
@isa.pattern("reg", "ADDU8(reg, reg)", size=4)
@isa.pattern("reg", "ADDI16(reg, reg)", size=4)
@isa.pattern("reg", "ADDU16(reg, reg)", size=4)
@isa.pattern("reg", "ADDI32(reg, reg)", size=4)
@isa.pattern("reg", "ADDU32(reg, reg)", size=4)
def pattern_add(context, tree, c0, c1):
    dst = context.new_reg(MicroBlazeRegister)
    context.emit(Add(dst, c0, c1))
    return dst


@isa.pattern("reg", "SUBI8(reg, reg)", size=4)
@isa.pattern("reg", "SUBU8(reg, reg)", size=4)
@isa.pattern("reg", "SUBI16(reg, reg)", size=4)
@isa.pattern("reg", "SUBU16(reg, reg)", size=4)
@isa.pattern("reg", "SUBI32(reg, reg)", size=4)
@isa.pattern("reg", "SUBU32(reg, reg)", size=4)
def pattern_sub(context, tree, c0, c1):
    dst = context.new_reg(MicroBlazeRegister)
    context.emit(Rsub(dst, c1, c0))
    return dst


@isa.pattern("reg", "MULI8(reg, reg)", size=4)
@isa.pattern("reg", "MULU8(reg, reg)", size=4)
@isa.pattern("reg", "MULI16(reg, reg)", size=4)
@isa.pattern("reg", "MULU16(reg, reg)", size=4)
@isa.pattern("reg", "MULI32(reg, reg)", size=4)
@isa.pattern("reg", "MULU32(reg, reg)", size=4)
def pattern_mul(context, tree, c0, c1):
    dst = context.new_reg(MicroBlazeRegister)
    context.emit(Mul(dst, c0, c1))
    return dst


def call_intrinsic(context, label, args, result):
    """ Generate a call to an intrinsic function """
    c0, c1 = args
    context.move(registers.R5, c0)
    context.move(registers.R6, c1)
    context.emit(RegisterUseDef(uses=(registers.R5, registers.R6)))
    context.emit(Global(label))
    context.emit(
        Brlid_label(registers.R15, label, clobbers=registers.caller_saved)
    )
    context.emit(nop())  # Fill the delay slot!
    context.emit(RegisterUseDef(defs=(registers.R3,)))
    context.move(result, registers.R3)


@isa.pattern("reg", "DIVI8(reg, reg)", size=4)
@isa.pattern("reg", "DIVU8(reg, reg)", size=4)
@isa.pattern("reg", "DIVI16(reg, reg)", size=4)
@isa.pattern("reg", "DIVU16(reg, reg)", size=4)
@isa.pattern("reg", "DIVI32(reg, reg)", size=4)
@isa.pattern("reg", "DIVU32(reg, reg)", size=4)
def pattern_div(context, tree, c0, c1):
    dst = context.new_reg(MicroBlazeRegister)
    call_intrinsic(context, "runtime_divsi3", [c0, c1], dst)
    return dst


@isa.pattern("reg", "REMI8(reg, reg)", size=4)
@isa.pattern("reg", "REMU8(reg, reg)", size=4)
@isa.pattern("reg", "REMI16(reg, reg)", size=4)
@isa.pattern("reg", "REMU16(reg, reg)", size=4)
@isa.pattern("reg", "REMI32(reg, reg)", size=4)
@isa.pattern("reg", "REMU32(reg, reg)", size=4)
def pattern_rem(context, tree, c0, c1):
    dst = context.new_reg(MicroBlazeRegister)
    call_intrinsic(context, "runtime_modsi3", [c0, c1], dst)
    return dst


@isa.pattern("reg", "NEGI8(reg)", size=4)
@isa.pattern("reg", "NEGU8(reg)", size=4)
@isa.pattern("reg", "NEGI16(reg)", size=4)
@isa.pattern("reg", "NEGU16(reg)", size=4)
@isa.pattern("reg", "NEGI32(reg)", size=4)
@isa.pattern("reg", "NEGU32(reg)", size=4)
def pattern_neg(context, tree, c0):
    dst = context.new_reg(MicroBlazeRegister)
    context.emit(Rsubi(dst, c0, 0))
    return dst


# Bitwise instruction matching:
@isa.pattern("reg", "ANDI8(reg, reg)", size=4)
@isa.pattern("reg", "ANDU8(reg, reg)", size=4)
@isa.pattern("reg", "ANDI16(reg, reg)", size=4)
@isa.pattern("reg", "ANDU16(reg, reg)", size=4)
@isa.pattern("reg", "ANDI32(reg, reg)", size=4)
@isa.pattern("reg", "ANDU32(reg, reg)", size=4)
def pattern_and(context, tree, c0, c1):
    dst = context.new_reg(MicroBlazeRegister)
    context.emit(And(dst, c0, c1))
    return dst


@isa.pattern("reg", "ORI8(reg, reg)", size=4)
@isa.pattern("reg", "ORU8(reg, reg)", size=4)
@isa.pattern("reg", "ORI16(reg, reg)", size=4)
@isa.pattern("reg", "ORU16(reg, reg)", size=4)
@isa.pattern("reg", "ORI32(reg, reg)", size=4)
@isa.pattern("reg", "ORU32(reg, reg)", size=4)
def pattern_or(context, tree, c0, c1):
    dst = context.new_reg(MicroBlazeRegister)
    context.emit(Or(dst, c0, c1))
    return dst


@isa.pattern("reg", "XORI8(reg, reg)", size=4)
@isa.pattern("reg", "XORU8(reg, reg)", size=4)
@isa.pattern("reg", "XORI16(reg, reg)", size=4)
@isa.pattern("reg", "XORU16(reg, reg)", size=4)
@isa.pattern("reg", "XORI32(reg, reg)", size=4)
@isa.pattern("reg", "XORU32(reg, reg)", size=4)
def pattern_xor(context, tree, c0, c1):
    dst = context.new_reg(MicroBlazeRegister)
    context.emit(Xor(dst, c0, c1))
    return dst


@isa.pattern("reg", "SHLI8(reg, reg)", size=4)
@isa.pattern("reg", "SHLU8(reg, reg)", size=4)
@isa.pattern("reg", "SHLI16(reg, reg)", size=4)
@isa.pattern("reg", "SHLU16(reg, reg)", size=4)
@isa.pattern("reg", "SHLI32(reg, reg)", size=4)
@isa.pattern("reg", "SHLU32(reg, reg)", size=4)
def pattern_shl(context, tree, c0, c1):
    dst = context.new_reg(MicroBlazeRegister)
    context.emit(Bsll(dst, c0, c1))
    return dst


@isa.pattern("reg", "SHRI8(reg, reg)", size=4)
@isa.pattern("reg", "SHRU8(reg, reg)", size=4)
@isa.pattern("reg", "SHRI16(reg, reg)", size=4)
@isa.pattern("reg", "SHRU16(reg, reg)", size=4)
@isa.pattern("reg", "SHRI32(reg, reg)", size=4)
@isa.pattern("reg", "SHRU32(reg, reg)", size=4)
def pattern_shr(context, tree, c0, c1):
    dst = context.new_reg(MicroBlazeRegister)
    context.emit(Bsra(dst, c0, c1))
    return dst


@isa.pattern("reg", "INVI8(reg)", size=4)
@isa.pattern("reg", "INVU8(reg)", size=4)
@isa.pattern("reg", "INVI16(reg)", size=4)
@isa.pattern("reg", "INVU16(reg)", size=4)
@isa.pattern("reg", "INVI32(reg)", size=4)
@isa.pattern("reg", "INVU32(reg)", size=4)
def pattern_inv(context, tree, c0):
    dst = context.new_reg(MicroBlazeRegister)
    context.emit(Imm(0xFFFF))
    context.emit(Xori(dst, c0, 0xFFFF))
    return dst


# Load / store:
@isa.pattern("reg", "LDRI8(mem)", size=4)
def pattern_ldr_i8(context, tree, mem):
    dst = context.new_reg(MicroBlazeRegister)
    base, offset = mem
    context.emit(Lbui(dst, base, offset))
    context.emit(Sext8(dst, dst))
    return dst


@isa.pattern("reg", "LDRU8(mem)", size=4)
def pattern_ldr_u8(context, tree, mem):
    dst = context.new_reg(MicroBlazeRegister)
    base, offset = mem
    context.emit(Lbui(dst, base, offset))
    return dst


@isa.pattern("reg", "LDRI16(mem)", size=4)
def pattern_ldr_i16(context, tree, mem):
    dst = context.new_reg(MicroBlazeRegister)
    base, offset = mem
    context.emit(Lhui(dst, base, offset))
    context.emit(Sext16(dst, dst))
    return dst


@isa.pattern("reg", "LDRU16(mem)", size=4)
def pattern_ldr_u16(context, tree, mem):
    dst = context.new_reg(MicroBlazeRegister)
    base, offset = mem
    context.emit(Lhui(dst, base, offset))
    return dst


@isa.pattern("reg", "LDRI32(mem)", size=4)
@isa.pattern("reg", "LDRU32(mem)", size=4)
def pattern_ldr32(context, tree, mem):
    dst = context.new_reg(MicroBlazeRegister)
    base, offset = mem
    context.emit(Lwi(dst, base, offset))
    return dst


@isa.pattern("stm", "STRI8(mem, reg)", size=4)
@isa.pattern("stm", "STRU8(mem, reg)", size=4)
def pattern_str8(context, tree, mem, value):
    base, offset = mem
    context.emit(Sbi(value, base, offset))


@isa.pattern("stm", "STRI16(mem, reg)", size=4)
@isa.pattern("stm", "STRU16(mem, reg)", size=4)
def pattern_str16(context, tree, mem, value):
    base, offset = mem
    context.emit(Shi(value, base, offset))


@isa.pattern("stm", "STRI32(mem, reg)", size=4)
@isa.pattern("stm", "STRU32(mem, reg)", size=4)
def pattern_str32(context, tree, mem, value):
    base, offset = mem
    context.emit(Swi(value, base, offset))


# Jumping and branching:
@isa.pattern("stm", "JMP", size=4)
def pattern_jmp(context, tree):
    tgt = tree.value
    context.emit(Bri_label(tgt.name, jumps=[tgt]))


@isa.pattern("stm", "CJMPI8(reg, reg)", size=4)
@isa.pattern("stm", "CJMPI16(reg, reg)", size=4)
@isa.pattern("stm", "CJMPI32(reg, reg)", size=4)
def pattern_cjmp_i8(context, tree, c0, c1):
    cjmp_impl(context, tree, c0, c1, signed=True)


@isa.pattern("stm", "CJMPU8(reg, reg)", size=4)
@isa.pattern("stm", "CJMPU16(reg, reg)", size=4)
@isa.pattern("stm", "CJMPU32(reg, reg)", size=4)
def pattern_cjmp_u8(context, tree, c0, c1):
    cjmp_impl(context, tree, c0, c1, signed=False)


def cjmp_impl(context, tree, c0, c1, signed=False):
    op, yes_label, no_label = tree.value
    opnames = {
        "==": (Beqi_label, False),
        "!=": (Bnei_label, False),
        "<": (Blti_label, False),
        ">": (Bgti_label, False),
        ">=": (Bgei_label, False),
        "<=": (Blei_label, False),
    }
    Bop, _ = opnames[op]

    tst = context.new_reg(MicroBlazeRegister)
    if signed:
        context.emit(Cmp(tst, c1, c0))
    else:
        context.emit(Cmpu(tst, c1, c0))

    jmp_ins_no = Bri_label(no_label.name, jumps=[no_label])
    context.emit(Bop(tst, yes_label.name, jumps=[yes_label, jmp_ins_no]))
    context.emit(jmp_ins_no)
