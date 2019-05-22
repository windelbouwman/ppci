""" M68k instruction descriptions.

"""

# pylint: disable=invalid-name
from ..isa import Isa
from ..encoding import Instruction, Syntax, Operand, Constructor
from ..encoding import Relocation
from ..token import Token, bit_range, Endianness
from .registers import DataRegister, AddressRegister
from . import registers


m68k_isa = Isa()


# Tokens:
class M68kToken(Token):
    class Info:
        size = 16
        endianness = Endianness.BIG

    effective_address = bit_range(0, 6)
    ea_register = bit_range(0, 3)
    ea_mode = bit_range(3, 6)
    opmode = bit_range(6, 9)
    size = bit_range(6, 8)
    register = bit_range(9, 12)
    opcode = bit_range(12, 16)
    opcode2 = bit_range(8, 16)
    bit8 = bit_range(8, 9)
    w = bit_range(0, 16)
    imm8 = bit_range(0, 8)


class Imm16Token(Token):
    class Info:
        size = 16
        endianness = Endianness.BIG

    imm16 = bit_range(0, 16)


class Imm16Token2(Token):
    class Info:
        size = 16
        endianness = Endianness.BIG

    imm16_2 = bit_range(0, 16)


class Imm32Token(Token):
    class Info:
        size = 32
        endianness = Endianness.BIG

    imm32 = bit_range(0, 32)


# Relocations:
@m68k_isa.register_relocation
class Rel16Relocation(Relocation):
    name = "rel16"
    token = Imm16Token
    field = "imm16"

    def calc(self, sym_value, reloc_value):
        return sym_value - reloc_value


# Helpers:
class DataRegEa(Constructor):
    """ Data register access """

    reg = Operand("reg", DataRegister, read=True)
    syntax = Syntax([reg])
    patterns = {"ea_mode": 0, "ea_register": reg}


class AddressRegEa(Constructor):
    """ Address register access """

    reg = Operand("reg", AddressRegister, read=True)
    syntax = Syntax([reg])
    patterns = {"ea_mode": 1, "ea_register": reg}


class AddressEa(Constructor):
    """ Access location pointed to by address register """

    reg = Operand("reg", AddressRegister, read=True)
    syntax = Syntax(["(", reg, ")"])
    patterns = {"ea_mode": 2, "ea_register": reg}


class AddressOffsetEa(Constructor):
    """ Access location pointed to by address register """

    imm = Operand("imm", int)
    reg = Operand("reg", AddressRegister, read=True)
    syntax = Syntax(["(", imm, ",", " ", reg, ")"])
    patterns = {"ea_mode": 5, "ea_register": reg, "imm16": imm}
    tokens = [Imm16Token]


class ImmediateEa(Constructor):
    """ Access an immediate value """

    imm = Operand("imm", int)
    syntax = Syntax(["#", imm])
    patterns = {"ea_mode": 0b111, "ea_register": 0b100, "imm16": imm}
    tokens = [Imm16Token]


class PcRelEa(Constructor):
    """ PC relative location """

    label = Operand("label", str)
    # Use priority here to solve ambiguity with register:
    syntax = Syntax([label], priority=2)
    patterns = {"ea_mode": 0b111, "ea_register": 0b010}
    tokens = [Imm16Token]

    def gen_relocations(self):
        yield Rel16Relocation(self.label, offset=0)


class AbsNearEa(Constructor):
    """ Access an absolute near address """

    imm = Operand("imm", int)
    syntax = Syntax(["(", imm, ")", ".", "w"])
    patterns = {"ea_mode": 0b111, "ea_register": 0b000, "imm16": imm}
    tokens = [Imm16Token]


ea_modes = (
    DataRegEa,
    AddressRegEa,
    AddressEa,
    AddressOffsetEa,
    ImmediateEa,
    PcRelEa,
    AbsNearEa,
)


# Sub constructs used as destination operands:
class DataRegDstEa(Constructor):
    """ Data register access """

    reg = Operand("reg", DataRegister, read=True)
    syntax = Syntax([reg])
    patterns = {"opmode": 0, "register": reg}


class AddressDstEa(Constructor):
    """ Store to location pointed to by address register """

    reg = Operand("reg", AddressRegister, read=True)
    syntax = Syntax(["(", reg, ")"])
    patterns = {"opmode": 2, "register": reg}


class AddressOffsetDstEa(Constructor):
    """ Store to location pointed to by address register """

    imm = Operand("imm", int)
    reg = Operand("reg", AddressRegister, read=True)
    syntax = Syntax(["(", imm, ",", " ", reg, ")"])
    patterns = {"opmode": 5, "register": reg, "imm16_2": imm}
    tokens = [Imm16Token2]


dst_ea_modes = (DataRegDstEa, AddressDstEa, AddressOffsetDstEa)


class M68kInstruction(Instruction):
    isa = m68k_isa


def make_ea_dn(mnemonic, opcode, opmode):
    """ Create an instruction with two operands: ea and dn.

    The form is a such:
        instr ea, dn

    """
    dn = Operand("dn", DataRegister, read=True, write=True)
    ea = Operand("ea", ea_modes)
    syntax = Syntax([mnemonic, " ", ea, ",", " ", dn])
    patterns = {"opcode": opcode, "register": dn, "opmode": opmode}
    members = {
        "dn": dn,
        "ea": ea,
        "syntax": syntax,
        "patterns": patterns,
        "tokens": [M68kToken],
    }
    class_name = mnemonic.title()
    return type(class_name, (M68kInstruction,), members)


def make_dn_ea(mnemonic, opcode, opmode):
    """ Create an instruction with two operands: dn and ea.

    The form is a such:
        instr dn, ea

    """
    dn = Operand("dn", DataRegister, read=True)
    ea = Operand("ea", ea_modes)
    syntax = Syntax([mnemonic, " ", dn, ",", " ", ea])
    patterns = {"opcode": opcode, "register": dn, "opmode": opmode}
    members = {
        "dn": dn,
        "ea": ea,
        "syntax": syntax,
        "patterns": patterns,
        "tokens": [M68kToken],
    }
    class_name = mnemonic.title()
    return type(class_name, (M68kInstruction,), members)


def make_ea(mnemonic, opcode, size):
    ea = Operand("ea", ea_modes)
    syntax = Syntax([mnemonic, " ", ea])
    patterns = {"opcode2": opcode, "size": size}
    members = {
        "ea": ea,
        "syntax": syntax,
        "patterns": patterns,
        "tokens": [M68kToken],
    }
    class_name = mnemonic.title()
    return type(class_name, (M68kInstruction,), members)


@m68k_isa.register_relocation
class BranchRel32Relocation(Relocation):
    name = "branch_rel32"
    token = Imm32Token
    field = "imm32"

    def calc(self, sym_value, reloc_value):
        return sym_value - reloc_value


class BranchBase(M68kInstruction):
    tokens = [M68kToken, Imm32Token]
    target = Operand("target", str)

    def relocations(self):
        return [BranchRel32Relocation(self.target, offset=2)]


def make_jmp(mnemonic, opcode):
    # TODO: there is a difference between 68000 and 68030 machines..
    patterns = {"opcode2": opcode, "imm8": 0xFF}
    syntax = Syntax([mnemonic, " ", BranchBase.target])
    members = {"syntax": syntax, "patterns": patterns}
    class_name = mnemonic.title()
    return type(class_name, (BranchBase,), members)


# Instruction classes:
Addb = make_ea_dn("addb", 0b1101, opmode=0b000)
Addw = make_ea_dn("addw", 0b1101, opmode=0b001)
Addl = make_ea_dn("addl", 0b1101, opmode=0b010)
Andb = make_ea_dn("andb", 0b1100, opmode=0b000)
Andw = make_ea_dn("andw", 0b1100, opmode=0b001)
Andl = make_ea_dn("andl", 0b1100, opmode=0b010)

Bne = make_jmp("bne", 0x66)
Beq = make_jmp("beq", 0x67)
Bge = make_jmp("bge", 0x6C)
Blt = make_jmp("blt", 0x6D)
Bgt = make_jmp("bgt", 0x6E)
Ble = make_jmp("ble", 0x6F)
Bra = make_jmp("bra", 0x60)  # Unconditional branch
Bsr = make_jmp("bsr", 0x61)  # Branch subroutine
Cmpb = make_ea_dn("cmpb", 0b1011, opmode=0b000)
Cmpw = make_ea_dn("cmpw", 0b1011, opmode=0b001)
Cmpl = make_ea_dn("cmpl", 0b1011, opmode=0b010)
Eorb = make_dn_ea("eorb", 0b1011, opmode=0b100)
Eorw = make_dn_ea("eorw", 0b1011, opmode=0b101)
Eorl = make_dn_ea("eorl", 0b1011, opmode=0b110)


class Lea(M68kInstruction):
    """ Load effective address """

    dst = Operand("dst", AddressRegister, write=True)
    ea = Operand("ea", ea_modes)
    syntax = Syntax(["lea", " ", ea, ",", " ", dst])
    patterns = {"opcode": 0x4, "opmode": 0b111, "register": dst}
    tokens = [M68kToken]


class Moveaw(M68kInstruction):
    """ 16 bit movea """

    dst = Operand("dst", AddressRegister, write=True)
    ea = Operand("ea", ea_modes)
    syntax = Syntax(["moveaw", " ", ea, ",", " ", dst])
    patterns = {"opcode": 0x3, "opmode": 1, "register": dst}
    tokens = [M68kToken]


class Moveal(M68kInstruction):
    """ 32 bit movea """

    dst = Operand("dst", AddressRegister, write=True)
    ea = Operand("ea", ea_modes)
    syntax = Syntax(["moveal", " ", ea, ",", " ", dst])
    patterns = {"opcode": 0x2, "opmode": 1, "register": dst}
    tokens = [M68kToken]


class Moveb(M68kInstruction):
    dst_ea = Operand("dst_ea", dst_ea_modes)
    ea = Operand("ea", ea_modes)
    syntax = Syntax(["moveb", " ", ea, ",", " ", dst_ea])
    patterns = {"opcode": 0x1}
    tokens = [M68kToken]


class Movew(M68kInstruction):
    """ 16 bit move """

    dst_ea = Operand("dst_ea", dst_ea_modes)
    ea = Operand("ea", ea_modes)
    syntax = Syntax(["movew", " ", ea, ",", " ", dst_ea])
    patterns = {"opcode": 0x3}
    tokens = [M68kToken]


class Movel(M68kInstruction):
    """ 32 bit move """

    dst_ea = Operand("dst_ea", dst_ea_modes)
    ea = Operand("ea", ea_modes)
    syntax = Syntax(["movel", " ", ea, ",", " ", dst_ea])
    patterns = {"opcode": 0x2}
    tokens = [M68kToken]


class Moveq(M68kInstruction):
    """ 32 bit move quick. Sign extend an 8 bit operand into a 32 bit reg. """

    dst = Operand("dst", DataRegister, write=True)
    imm = Operand("imm", int)
    syntax = Syntax(["moveq", " ", "#", imm, ",", " ", dst])
    patterns = {"opcode": 0b0111, "register": dst, "bit8": 0, "imm8": imm}
    tokens = [M68kToken]


Orb = make_ea_dn("orb", 0b1000, opmode=0b000)
Orw = make_ea_dn("orw", 0b1000, opmode=0b001)
Orl = make_ea_dn("orl", 0b1000, opmode=0b010)
Subb = make_ea_dn("subb", 0b1101, opmode=0b000)
Subw = make_ea_dn("subw", 0b1101, opmode=0b001)
Subl = make_ea_dn("subl", 0b1101, opmode=0b010)

Jsr = make_ea("jsr", 0x4E, 2)

Negb = make_ea("negb", 0x44, 0)
Negw = make_ea("negw", 0x44, 1)
Negl = make_ea("negl", 0x44, 2)


class Nop(M68kInstruction):
    """ Does nothing """

    syntax = Syntax(["nop"])
    patterns = {"w": 0x4E71}
    tokens = [M68kToken]


Notb = make_ea("notb", 0x46, 0)
Notw = make_ea("notw", 0x46, 1)
Notl = make_ea("notl", 0x46, 2)


class Rts(M68kInstruction):
    """ Return from subroutine """

    syntax = Syntax(["rts"])
    patterns = {"w": 0x4E75}
    tokens = [M68kToken]


# Instruction patterns:
@m68k_isa.pattern("regd", "REGI8", size=0, cycles=0, energy=0)
@m68k_isa.pattern("regd", "REGU8", size=0, cycles=0, energy=0)
@m68k_isa.pattern("regd", "REGI16", size=0, cycles=0, energy=0)
@m68k_isa.pattern("regd", "REGU16", size=0, cycles=0, energy=0)
@m68k_isa.pattern("regd", "REGI32", size=0, cycles=0, energy=0)
@m68k_isa.pattern("regd", "REGU32", size=0, cycles=0, energy=0)
def pattern_reg(context, tree):
    return tree.value


@m68k_isa.pattern("ea32", "regd")
@m68k_isa.pattern("ea16", "regd")
@m68k_isa.pattern("ea8", "regd")
def pattern_ea_reg(context, tree, regd):
    return DataRegEa(regd)


@m68k_isa.pattern("ea32", "LDRU32(rega)")
@m68k_isa.pattern("ea16", "LDRI16(rega)")
@m68k_isa.pattern("ea16", "LDRU16(rega)")
def pattern_ea_ldr32(context, tree, ptr):
    return AddressEa(ptr)


@m68k_isa.pattern("dst_ea", "FPRELU32")
def pattern_dst_fprel(context, tree):
    offset = tree.value.offset
    return AddressOffsetDstEa(offset, registers.A0)


@m68k_isa.pattern("ea32", "LDRI32(FPRELU32)")
@m68k_isa.pattern("ea32", "LDRU32(FPRELU32)")
@m68k_isa.pattern("ea16", "LDRI16(FPRELU32)")
@m68k_isa.pattern("ea16", "LDRU16(FPRELU32)")
@m68k_isa.pattern("ea8", "LDRI8(FPRELU32)")
@m68k_isa.pattern("ea8", "LDRU8(FPRELU32)")
def pattern_src_fprel(context, tree):
    offset = tree[0].value.offset
    return AddressOffsetEa(offset, registers.A0)


@m68k_isa.pattern("rega", "regd")
def pattern_rega(context, tree, regd):
    rega = context.new_reg(AddressRegister)
    raise NotImplementedError()
    # TODO: move!
    # context.emit(Movea(regd))
    return rega


@m68k_isa.pattern("regd", "ea32")
def pattern_regd_from_ea32(context, tree, ea):
    dst = context.new_reg(DataRegister)
    context.emit(Movel(ea, DataRegDstEa(dst)))
    return dst


@m68k_isa.pattern("stm", "MOVI32(ea32)")
@m68k_isa.pattern("stm", "MOVU32(ea32)")
def pattern_mov32(context, tree, ea):
    dst = tree.value
    context.emit(Movel(ea, DataRegDstEa(dst)))


@m68k_isa.pattern("stm", "MOVI16(ea16)")
@m68k_isa.pattern("stm", "MOVU16(ea16)")
def pattern_mov16(context, tree, ea):
    dst = tree.value
    context.emit(Movew(ea, DataRegDstEa(dst)))


@m68k_isa.pattern("stm", "MOVI8(ea8)")
@m68k_isa.pattern("stm", "MOVU8(ea8)")
def pattern_mov8(context, tree, ea):
    dst = tree.value
    context.emit(Moveb(ea, DataRegDstEa(dst)))


@m68k_isa.pattern("stm", "STRI32(dst_ea, ea32)")
@m68k_isa.pattern("stm", "STRU32(dst_ea, ea32)")
def pattern_str32(context, tree, dst_ea, ea):
    context.emit(Movel(ea, dst_ea))


@m68k_isa.pattern("stm", "STRI16(dst_ea, ea16)")
@m68k_isa.pattern("stm", "STRU16(dst_ea, ea16)")
def pattern_str16(context, tree, dst_ea, ea):
    context.emit(Movew(ea, dst_ea))


@m68k_isa.pattern("stm", "STRI8(dst_ea, ea8)")
@m68k_isa.pattern("stm", "STRU8(dst_ea, ea8)")
def pattern_str8(context, tree, dst_ea, ea):
    context.emit(Moveb(ea, dst_ea))


# Arithmatic patterns:
@m68k_isa.pattern("regd", "ADDI32(regd, ea32)", size=2)
@m68k_isa.pattern("regd", "ADDU32(regd, ea32)", size=2)
def pattern_add(context, tree, regd, ea):
    dst = context.new_reg(DataRegister)
    context.move(dst, regd)
    context.emit(Addl(ea, dst))
    return dst


@m68k_isa.pattern("regd", "ADDI16(regd, ea16)", size=2)
@m68k_isa.pattern("regd", "ADDU16(regd, ea16)", size=2)
def pattern_add16(context, tree, regd, ea):
    dst = context.new_reg(DataRegister)
    context.move(dst, regd)
    context.emit(Addw(ea, dst))
    return dst


@m68k_isa.pattern("regd", "ADDI8(regd, ea8)", size=2)
@m68k_isa.pattern("regd", "ADDU8(regd, ea8)", size=2)
def pattern_add8(context, tree, regd, ea):
    dst = context.new_reg(DataRegister)
    context.move(dst, regd)
    context.emit(Addb(ea, dst))
    return dst


@m68k_isa.pattern("regd", "SUBI32(regd, ea32)", size=2)
@m68k_isa.pattern("regd", "SUBU32(regd, ea32)", size=2)
def pattern_sub32(context, tree, regd, ea):
    dst = context.new_reg(DataRegister)
    context.move(dst, regd)
    context.emit(Subl(ea, dst))  # dst = dst - ea
    return dst


@m68k_isa.pattern("regd", "SUBI16(regd, ea16)", size=2)
@m68k_isa.pattern("regd", "SUBU16(regd, ea16)", size=2)
def pattern_sub16(context, tree, regd, ea):
    dst = context.new_reg(DataRegister)
    context.move(dst, regd)
    context.emit(Subw(ea, dst))  # dst = dst - ea
    return dst


@m68k_isa.pattern("regd", "SUBI8(regd, ea8)")
@m68k_isa.pattern("regd", "SUBU8(regd, ea8)")
def pattern_sub8(context, tree, regd, ea):
    dst = context.new_reg(DataRegister)
    context.move(dst, regd)
    context.emit(Subb(ea, dst))  # dst = dst - ea
    return dst


@m68k_isa.pattern("regd", "NEGI32(regd)", size=2)
@m68k_isa.pattern("regd", "NEGU32(regd)", size=2)
def pattern_neg32(context, tree, regd):
    dst = context.new_reg(DataRegister)
    context.move(dst, regd)
    context.emit(Negl(DataRegEa(dst)))
    return dst


@m68k_isa.pattern("regd", "NEGI16(regd)", size=2)
@m68k_isa.pattern("regd", "NEGU16(regd)", size=2)
def pattern_neg16(context, tree, regd):
    dst = context.new_reg(DataRegister)
    context.move(dst, regd)
    context.emit(Negw(DataRegEa(dst)))
    return dst


@m68k_isa.pattern("regd", "NEGI8(regd)", size=2)
@m68k_isa.pattern("regd", "NEGU8(regd)", size=2)
def pattern_neg8(context, tree, regd):
    dst = context.new_reg(DataRegister)
    context.move(dst, regd)
    context.emit(Negb(DataRegEa(dst)))
    return dst


# Bitwise patterns:


@m68k_isa.pattern("regd", "ANDI32(regd, ea32)", size=2)
@m68k_isa.pattern("regd", "ANDU32(regd, ea32)", size=2)
def pattern_and32(context, tree, regd, ea):
    dst = context.new_reg(DataRegister)
    context.move(dst, regd)
    context.emit(Andl(ea, dst))
    return dst


@m68k_isa.pattern("regd", "ANDI16(regd, ea16)", size=2)
@m68k_isa.pattern("regd", "ANDU16(regd, ea16)", size=2)
def pattern_and16(context, tree, regd, ea):
    dst = context.new_reg(DataRegister)
    context.move(dst, regd)
    context.emit(Andw(ea, dst))
    return dst


@m68k_isa.pattern("regd", "ANDI8(regd, ea8)", size=2)
@m68k_isa.pattern("regd", "ANDU8(regd, ea8)", size=2)
def pattern_and8(context, tree, regd, ea):
    dst = context.new_reg(DataRegister)
    context.move(dst, regd)
    context.emit(Andb(ea, dst))
    return dst


@m68k_isa.pattern("regd", "ORI32(regd, ea32)", size=2)
@m68k_isa.pattern("regd", "ORU32(regd, ea32)", size=2)
def pattern_or32(context, tree, regd, ea):
    dst = context.new_reg(DataRegister)
    context.move(dst, regd)
    context.emit(Orl(ea, dst))
    return dst


@m68k_isa.pattern("regd", "ORI16(regd, ea16)", size=2)
@m68k_isa.pattern("regd", "ORU16(regd, ea16)", size=2)
def pattern_or16(context, tree, regd, ea):
    dst = context.new_reg(DataRegister)
    context.move(dst, regd)
    context.emit(Orw(ea, dst))
    return dst


@m68k_isa.pattern("regd", "ORI8(regd, ea8)", size=2)
@m68k_isa.pattern("regd", "ORU8(regd, ea8)", size=2)
def pattern_or8(context, tree, regd, ea):
    dst = context.new_reg(DataRegister)
    context.move(dst, regd)
    context.emit(Orb(ea, dst))
    return dst


@m68k_isa.pattern("regd", "XORI32(regd, ea32)", size=2)
@m68k_isa.pattern("regd", "XORU32(regd, ea32)", size=2)
def pattern_xor32(context, tree, regd, ea):
    dst = context.new_reg(DataRegister)
    context.move(dst, regd)
    context.emit(Eorl(ea, dst))
    return dst


@m68k_isa.pattern("regd", "XORI16(regd, ea16)", size=2)
@m68k_isa.pattern("regd", "XORU16(regd, ea16)", size=2)
def pattern_xor16(context, tree, regd, ea):
    dst = context.new_reg(DataRegister)
    context.move(dst, regd)
    context.emit(Eorw(ea, dst))
    return dst


@m68k_isa.pattern("regd", "XORI8(regd, ea8)", size=2)
@m68k_isa.pattern("regd", "XORU8(regd, ea8)", size=2)
def pattern_xor8(context, tree, regd, ea):
    dst = context.new_reg(DataRegister)
    context.move(dst, regd)
    context.emit(Eorb(ea, dst))
    return dst


@m68k_isa.pattern("regd", "INVI32(regd)", size=2)
@m68k_isa.pattern("regd", "INVU32(regd)", size=2)
def pattern_inv32(context, tree, regd):
    dst = context.new_reg(DataRegister)
    context.move(dst, regd)
    context.emit(Notl(DataRegEa(dst)))
    return dst


@m68k_isa.pattern("regd", "INVI16(regd)", size=2)
@m68k_isa.pattern("regd", "INVU16(regd)", size=2)
def pattern_inv16(context, tree, regd):
    dst = context.new_reg(DataRegister)
    context.move(dst, regd)
    context.emit(Notw(DataRegEa(dst)))
    return dst


@m68k_isa.pattern("regd", "INVI8(regd)", size=2)
@m68k_isa.pattern("regd", "INVU8(regd)", size=2)
def pattern_inv8(context, tree, regd):
    dst = context.new_reg(DataRegister)
    context.move(dst, regd)
    context.emit(Notb(DataRegEa(dst)))
    return dst


# Branching and jumping:
@m68k_isa.pattern("stm", "JMP", size=2)
def pattern_jmp(context, tree):
    tgt = tree.value
    context.emit(Bra(tgt.name, jumps=[tgt]))


@m68k_isa.pattern("stm", "CJMPI32(regd, ea32)", size=4)
def pattern_cjmp_i32(context, tree, regd, ea):
    op, yes_label, no_label = tree.value
    context.emit(Cmpl(ea, regd))
    cjmp_impl(context, op, yes_label, no_label)


@m68k_isa.pattern("stm", "CJMPU32(regd, ea32)", size=4)
def pattern_cjmp_u32(context, tree, regd, ea):
    op, yes_label, no_label = tree.value
    context.emit(Cmpl(ea, regd))
    cjmp_impl_unsigned(context, op, yes_label, no_label)


@m68k_isa.pattern("stm", "CJMPI16(regd, ea16)", size=4)
def pattern_cjmp_i16(context, tree, regd, ea):
    op, yes_label, no_label = tree.value
    context.emit(Cmpw(ea, regd))
    cjmp_impl(context, op, yes_label, no_label)


@m68k_isa.pattern("stm", "CJMPU16(regd, ea16)", size=4)
def pattern_cjmp_u16(context, tree, regd, ea):
    op, yes_label, no_label = tree.value
    context.emit(Cmpw(ea, regd))
    cjmp_impl_unsigned(context, op, yes_label, no_label)


@m68k_isa.pattern("stm", "CJMPI8(regd, ea8)", size=4)
def pattern_cjmp_i8(context, tree, regd, ea):
    op, yes_label, no_label = tree.value
    context.emit(Cmpb(ea, regd))
    cjmp_impl(context, op, yes_label, no_label)


@m68k_isa.pattern("stm", "CJMPU8(regd, ea8)", size=4)
def pattern_cjmp_u8(context, tree, regd, ea):
    op, yes_label, no_label = tree.value
    context.emit(Cmpb(ea, regd))
    cjmp_impl_unsigned(context, op, yes_label, no_label)


def cjmp_impl(context, op, yes_label, no_label):
    opnames = {"<": Blt, ">": Bgt, "==": Beq, "!=": Bne, "<=": Ble, ">=": Bge}
    Bop = opnames[op]
    jmp_ins = Bra(no_label.name, jumps=[no_label])
    context.emit(Bop(yes_label.name, jumps=[yes_label, jmp_ins]))
    context.emit(jmp_ins)


def cjmp_impl_unsigned(context, op, yes_label, no_label):
    opnames = {"<": Blt, ">": Bgt, "==": Beq, "!=": Bne, "<=": Ble, ">=": Bge}
    Bop = opnames[op]
    jmp_ins = Bra(no_label.name, jumps=[no_label])
    context.emit(Bop(yes_label.name, jumps=[yes_label, jmp_ins]))
    context.emit(jmp_ins)
