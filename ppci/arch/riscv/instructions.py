""" Definitions of Riscv instructions. """

# pylint: disable=no-member,invalid-name

from ..isa import Isa
from ..encoding import Instruction, Syntax, Operand
from ..data_instructions import Dd
from ...utils.bitfun import inrange
from ..generic_instructions import ArtificialInstruction, Alignment
from ..generic_instructions import SectionInstruction
from ..generic_instructions import RegisterUseDef 
from .registers import RiscvRegister, FP, LR, R0, R10, R12, R13
from .relocations import AbsAddr32Relocation
from .relocations import BImm12Relocation, BImm20Relocation
from .relocations import Abs32Imm20Relocation
from .relocations import Abs32Imm12Relocation, RelImm20Relocation
from .relocations import RelImm12Relocation
from .tokens import RiscvToken, RiscvIToken
import struct

isa = Isa()

isa.register_relocation(BImm12Relocation)
isa.register_relocation(BImm20Relocation)
isa.register_relocation(AbsAddr32Relocation)
isa.register_relocation(Abs32Imm20Relocation)
isa.register_relocation(Abs32Imm12Relocation)
isa.register_relocation(RelImm20Relocation)
isa.register_relocation(RelImm12Relocation)


class RiscvInstruction(Instruction):
    tokens = [RiscvToken]
    isa = isa


class PseudoRiscvInstruction(ArtificialInstruction):
    isa = isa
    pass


class Align(PseudoRiscvInstruction):
    imm = Operand('imm', int)
    syntax = Syntax(['.', 'align', ' ', imm])

    def render(self):
        self.rep = self.syntax.render(self)
        yield Alignment(self.imm, self.rep)


class Section(PseudoRiscvInstruction):
    sec = Operand('sec', str)
    syntax = Syntax(['.', 'section', ' ', sec])

    def render(self):
        self.rep = self.syntax.render(self)
        yield SectionInstruction(self.sec, self.rep)


def dcd(v):
    if type(v) is int:
        return Dd(v)
    elif type(v) is str:
        return Dcd2(v)
    else:  # pragma: no cover
        raise NotImplementedError()


class Dcd2(RiscvInstruction):
    v = Operand('v', str)
    syntax = Syntax(['dcd', '=', v])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:32] = 0
        return tokens[0].encode()

    def relocations(self):
        return [AbsAddr32Relocation(self.v)]


class Movr(RiscvInstruction):
    rd = Operand('rd', RiscvRegister, write=True)
    rm = Operand('rm', RiscvRegister, read=True)
    syntax = Syntax(['mv', ' ', rd, ',', ' ', rm])
    patterns = {
        'opcode': 0b0010011, 'rd': rd, 'funct3': 0, 'rs1': rm,
        'rs2': 0, 'funct7': 0}


def make_regregreg(mnemonic, opcode, func):
    rd = Operand('rd', RiscvRegister, write=True)
    rn = Operand('rn', RiscvRegister, read=True)
    rm = Operand('rm', RiscvRegister, read=True)
    syntax = Syntax([mnemonic, ' ', rd, ',', ' ', rn, ',', ' ', rm])
    tokens = [RiscvToken]
    patterns = {
        'opcode': 0b0110011, 'rd': rd, 'funct3': func,
        'rs1': rn, 'rs2': rm, 'funct7': opcode}
    members = {
        'syntax': syntax, 'rd': rd, 'rn': rn, 'rm': rm,
        'patterns': patterns, 'tokens': tokens,
        'opcode': opcode, 'func': func}
    name = mnemonic.title() + 'RegRegReg'
    return type(name, (RiscvInstruction,), members)


Addr = make_regregreg('add', 0b0000000, 0b000)
Subr = make_regregreg('sub', 0b0100000, 0b000)
Sll = make_regregreg('sll', 0b0000000, 0b001)
Slt = make_regregreg('slt', 0b0000000, 0b010)
Sltu = make_regregreg('sltu', 0b0000000, 0b011)
Xorr = make_regregreg('xor', 0b0000000, 0b100)
Srl = make_regregreg('srl', 0b0000000, 0b101)
Sra = make_regregreg('sra', 0b0100000, 0b101)
Orr = make_regregreg('or', 0b0000000, 0b110)
Andr = make_regregreg('and', 0b0000000, 0b111)


def make_si(mnemonic, code, func):
    rd = Operand('rd', RiscvRegister, write=True)
    rs1 = Operand('rs1', RiscvRegister, read=True)
    imm = Operand('imm', int)
    syntax = Syntax([mnemonic, ' ', rd, ',', ' ', rs1, ',', ' ', imm])
    tokens = [RiscvToken]
    patterns = {
        'opcode': 0b0010011, 'rd': rd, 'funct3': func,
        'rs1': rs1, 'rs2': imm, 'funct7': code}
    members = {
        'syntax': syntax, 'tokens': tokens, 'patterns': patterns,
        'rd': rd, 'rs1': rs1, 'imm': imm}
    name = mnemonic.title() + 'ShiftImm'
    return type(name, (RiscvInstruction,), members)


Slli = make_si('slli', 0b0000000, 0b001)
Srli = make_si('srli', 0b0000000, 0b101)
Srai = make_si('srai', 0b0100000, 0b101)


class IBase(RiscvInstruction):
    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:7] = 0b0010011
        tokens[0][7:12] = self.rd.num
        tokens[0][12:15] = self.func
        tokens[0][15:20] = self.rs1.num
        self.imm = self.imm & 0xfff
        tokens[0][20:32] = self.imm
        return tokens[0].encode()


def make_i(mnemonic, func):
    """ Factory function for immediate value instructions """
    rd = Operand('rd', RiscvRegister, write=True)
    rs1 = Operand('rs1', RiscvRegister, read=True)
    imm = Operand('imm', int)
    syntax = Syntax([mnemonic, ' ', rd, ',', ' ', rs1, ',', ' ', imm])
    members = {
        'syntax': syntax, 'func': func,
        'rd': rd, 'rs1': rs1, 'imm': imm}
    return type(mnemonic + '_ins', (IBase,), members)


Addi = make_i('addi', 0b000)
Slti = make_i('slti', 0b010)
Sltiu = make_i('sltiu', 0b011)
Xori = make_i('xori', 0b100)
Ori = make_i('ori', 0b110)
Andi = make_i('andi', 0b111)


# Branches:

class Nop(RiscvInstruction):
    syntax = Syntax(['nop'])
    patterns = {
        'opcode': 0b0010011, 'rd': 0,
        'funct3': 0, 'rs1': 0, 'rs2': 0, 'funct7': 0}


class SmBase(RiscvInstruction):
    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:7] = 0b1110011
        tokens[0][7:12] = self.rd.num
        tokens[0][12:15] = 0b010
        tokens[0][15:20] = 0
        tokens[0][20:32] = self.code
        return tokens[0].encode()


def make_sm(mnemonic, code):
    rd = Operand('rd', RiscvRegister, write=True)
    syntax = Syntax([mnemonic, ' ', rd])
    members = {'syntax': syntax, 'rd': rd, 'code': code}
    return type(mnemonic + '_ins', (SmBase,), members)


Rdcyclei = make_sm('rdcycle', 0b110000000000)
Rdcyclehi = make_sm('rdcycleh', 0b110010000000)
Rdtimei = make_sm('rdtime', 0b110000000001)
Rdtimehi = make_sm('rdtimeh', 0b110010000001)
Rdinstreti = make_sm('rdinstret', 0b110000000010)
Rdinstrethi = make_sm('rdinstreth', 0b110010000010)


class Ebreak(RiscvInstruction):
    syntax = Syntax(['ebreak'])
    patterns = {
        'opcode': 0b1110011, 'rd': 0, 'funct3': 0, 'rs1': 0,
        'rs2': 0b1, 'funct7': 0}


class Bl(RiscvInstruction):
    target = Operand('target', str)
    rd = Operand('rd', RiscvRegister, write=True)
    syntax = Syntax(['jal', ' ', rd, ',', ' ', target])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:7] = 0b1101111
        tokens[0][7:12] = self.rd.num
        return tokens[0].encode()

    def relocations(self):
        return [BImm20Relocation(self.target)]


class B(RiscvInstruction):
    target = Operand('target', str)
    syntax = Syntax(['j', ' ', target])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:7] = 0b1101111
        tokens[0][7:12] = 0
        return tokens[0].encode()

    def relocations(self):
        return [BImm20Relocation(self.target)]


class Blr(RiscvInstruction):
    rd = Operand('rd', RiscvRegister, write=True)
    rs1 = Operand('rs1', RiscvRegister, read=True)
    offset = Operand('offset', int)
    syntax = Syntax(['jalr', ' ', rd, ',', rs1, ',', ' ', offset])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:7] = 0b1100111
        tokens[0][7:12] = self.rd.num
        tokens[0][12:15] = 0
        tokens[0][15:20] = self.rs1.num
        tokens[0][20:32] = self.offset
        return tokens[0].encode()


class Lui(RiscvInstruction):
    rd = Operand('rd', RiscvRegister, write=True)
    imm = Operand('imm', int)
    syntax = Syntax(['lui', ' ', rd, ',', ' ', imm])

    def encode(self):
        tokens = self.get_tokens()
        imm20 = self.imm & 0xfffff
        tokens[0][0:7] = 0b0110111
        tokens[0][7:12] = self.rd.num
        tokens[0][12:32] = imm20
        return tokens[0].encode()


class Adru(RiscvInstruction):
    rd = Operand('rd', RiscvRegister, write=True)
    label = Operand('label', str)
    syntax = Syntax(['lui', ' ', rd, ',', ' ', label])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:7] = 0b0110111
        tokens[0][7:12] = self.rd.num
        tokens[0][12:32] = 0
        return tokens[0].encode()

    def relocations(self):
        return [Abs32Imm20Relocation(self.label)]


class Adrurel(RiscvInstruction):
    rd = Operand('rd', RiscvRegister, write=True)
    label = Operand('label', str)
    syntax = Syntax(['auipc', ' ', rd, ',', ' ', label])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:7] = 0b0010111
        tokens[0][7:12] = self.rd.num
        tokens[0][12:32] = 0
        return tokens[0].encode()

    def relocations(self):
        return [RelImm20Relocation(self.label)]


class Adrl(RiscvInstruction):
    rd = Operand('rd', RiscvRegister, write=True)
    rs1 = Operand('rs1', RiscvRegister, read=True)
    label = Operand('label', str)
    syntax = Syntax(['addi', ' ', rd, ',', ' ', rs1, ',', ' ', label])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:7] = 0b0010011
        tokens[0][7:12] = self.rd.num
        tokens[0][12:15] = 0
        tokens[0][15:20] = self.rs1.num
        tokens[0][20:32] = 0
        return tokens[0].encode()

    def relocations(self):
        return [Abs32Imm12Relocation(self.label)]


class Loadlrel(RiscvInstruction):
    rd = Operand('rd', RiscvRegister, write=True, read=True)
    label = Operand('label', str)
    syntax = Syntax(['lw', ' ', rd, ',', ' ', label])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:7] = 0b0000011
        tokens[0][7:12] = self.rd.num
        tokens[0][12:15] = 0b010
        tokens[0][15:20] = self.rd.num
        tokens[0][20:32] = 0
        return tokens[0].encode()

    def relocations(self):
        return [RelImm12Relocation(self.label)]


class Adrlrel(RiscvInstruction):
    rd = Operand('rd', RiscvRegister, write=True, read=True)
    label = Operand('label', str)
    syntax = Syntax(['addi', ' ', rd, ',', ' ', label])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:7] = 0b0010011
        tokens[0][7:12] = self.rd.num
        tokens[0][12:15] = 0b000
        tokens[0][15:20] = self.rd.num
        tokens[0][20:32] = 0
        return tokens[0].encode()

    def relocations(self):
        return [RelImm12Relocation(self.label)]


class Auipc(RiscvInstruction):
    rd = Operand('rd', RiscvRegister, write=True)
    imm = Operand('imm', int)
    syntax = Syntax(['auipc', ' ', rd, ',', ' ', imm])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:7] = 0b0010111
        tokens[0][7:12] = self.rd.num
        tokens[0][12:32] = self.imm
        return tokens[0].encode()


class Labelrel(PseudoRiscvInstruction):
    rd = Operand('rd', RiscvRegister, write=True)
    label = Operand('label', str)
    syntax = Syntax(['lw', ' ', rd, ',', ' ', label])

    def render(self):
        yield Adrurel(self.rd, self.label)
        yield Loadlrel(self.rd, self.label)


class La(PseudoRiscvInstruction):
    rd = Operand('rd', RiscvRegister, write=True)
    label = Operand('label', str)
    syntax = Syntax(['la', ' ', rd, ',', ' ', label])

    def render(self):
        yield Adrurel(self.rd, self.label)
        yield Adrlrel(self.rd, self.label)


class Li(PseudoRiscvInstruction):
    rd = Operand('rd', RiscvRegister, write=True)
    imm = Operand('imm', int)
    syntax = Syntax(['li', ' ', rd, ',', ' ', imm])

    def render(self):
        # If the immediate value fits into 12 bits, do so!
        if inrange(self.imm, 12):
            yield Addi(self.rd, R0, self.imm)
        else:
            if (self.imm & 0x800) != 0:
                self.imm += 0x1000
            yield Lui(self.rd, self.imm >> 12)
            lower_bits = self.imm & 0xfff
            yield Addi(self.rd, self.rd, lower_bits)


class BranchBase(RiscvInstruction):
    target = Operand('target', str)

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:7] = 0b1100011
        tokens[0][12:15] = self.cond
        if self.invert:
            tokens[0][15:20] = self.rm.num
            tokens[0][20:25] = self.rn.num
        else:
            tokens[0][15:20] = self.rn.num
            tokens[0][20:25] = self.rm.num
        return tokens[0].encode()

    def relocations(self):
        return [BImm12Relocation(self.target)]


def make_branch(mnemonic, cond, invert):
    target = Operand('target', str)
    rn = Operand('rn', RiscvRegister, read=True)
    rm = Operand('rm', RiscvRegister, read=True)
    syntax = Syntax([mnemonic, ' ', rn, ',', ' ', rm, ',', ' ', target])

    members = {
        'syntax': syntax, 'target': target,
        'rn': rn, 'rm': rm, 'cond': cond, 'invert': invert}
    return type(mnemonic + '_ins', (BranchBase,), members)


Beq = make_branch('beq', 0b000, False)
Bne = make_branch('bne', 0b001, False)
Blt = make_branch('blt', 0b100, False)
Bgt = make_branch('bgt', 0b100, True)
Bge = make_branch('bge', 0b101, False)
Ble = make_branch('bge', 0b101, True)
Bltu = make_branch('bltu', 0b110, False)
Bgtu = make_branch('bgtu', 0b110, True)
Bgeu = make_branch('bgeu', 0b111, False)
Bleu = make_branch('bleu', 0b111, True)


def reg_list_to_mask(reg_list):
    mask = 0
    for reg in reg_list:
        mask |= (1 << reg.num)
    return mask


class StrBase(RiscvInstruction):
    def encode(self):
        imml5 = self.offset & 0x1f
        immh7 = (self.offset >> 5) & 0x7f
        tokens = self.get_tokens()
        tokens[0][0:7] = 0b0100011
        tokens[0][7:12] = imml5
        tokens[0][12:15] = self.func
        tokens[0][15:20] = self.rs1.num
        tokens[0][20:25] = self.rs2.num
        tokens[0][25:32] = immh7
        return tokens[0].encode()


def make_str(mnemonic, func):
    rs2 = Operand('rs2', RiscvRegister, read=True)
    offset = Operand('offset', int)
    rs1 = Operand('rs1', RiscvRegister, read=True)
    syntax = Syntax([mnemonic, ' ', rs2, ',', ' ', offset, '(', rs1, ')'])
    members = {
        'syntax': syntax,
        'func': func,
        'offset': offset, 'rs1': rs1, 'rs2': rs2}
    return type(mnemonic.title(), (StrBase,), members)


Sb = make_str('sb', 0b000)
Sh = make_str('sh', 0b001)
Sw = make_str('sw', 0b010)


def make_ldr(mnemonic, func):
    rd = Operand('rd', RiscvRegister, write=True)
    offset = Operand('offset', int)
    rs1 = Operand('rs1', RiscvRegister, read=True)
    syntax = Syntax([mnemonic, ' ', rd, ',', ' ', offset, '(', rs1, ')'])
    tokens = [RiscvIToken]
    patterns = {
        'opcode': 0b0000011, 'rd': rd,
        'funct3': func, 'rs1': rs1, 'imm': offset}
    members = {
        'syntax': syntax, 'tokens': tokens, 'patterns': patterns,
        'offset': offset, 'rd': rd, 'rs1': rs1}
    return type(mnemonic.title(), (RiscvInstruction,), members)


Lb = make_ldr('lb', 0b000)
Lh = make_ldr('lh', 0b001)
Lw = make_ldr('lw', 0b010)
Lbu = make_ldr('lbu', 0b100)
Lhu = make_ldr('lhu', 0b101)


class MextBase(RiscvInstruction):
    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:7] = 0b0110011
        tokens[0][7:12] = self.rd.num
        tokens[0][12:15] = self.func
        tokens[0][15:20] = self.rs1.num
        tokens[0][20:25] = self.rs2.num
        tokens[0][25:32] = 0b0000001
        return tokens[0].encode()


def make_mext(mnemonic, func):
    rs1 = Operand('rs1', RiscvRegister, read=True)
    rs2 = Operand('rs2', RiscvRegister, read=True)
    rd = Operand('rd', RiscvRegister, write=True)
    syntax = Syntax([mnemonic, ' ', rd, ',', ' ', rs1, ',', ' ', rs2])
    members = {
        'syntax': syntax,
        'func': func,
        'rd': rd, 'rs1': rs1, 'rs2': rs2}
    return type(mnemonic + '_ins', (MextBase,), members)


Mul = make_mext('mul', 0b000)
Div = make_mext('div', 0b100)
Divu = make_mext('divu', 0b101)
Rem = make_mext('rem', 0b110)
Remu = make_mext('remu', 0b111)

# Instruction selection patterns:

@isa.pattern('stm', 'MOVI16(reg)', size=2)
@isa.pattern('stm', 'MOVU16(reg)', size=2)
@isa.pattern('stm', 'MOVI32(reg)', size=2)
@isa.pattern('stm', 'MOVU32(reg)', size=2)
@isa.pattern('stm', 'MOVF32(reg)', size=2)
@isa.pattern('stm', 'MOVF64(reg)', size=2)
def pattern_mov32(context, tree, c0):
    context.move(tree.value, c0)
    return tree.value


@isa.pattern('stm', 'MOVU8(reg)', size=2)
@isa.pattern('stm', 'MOVI8(reg)', size=2)
def pattern_movi8(context, tree, c0):
    context.move(tree.value, c0)
    return tree.value


@isa.pattern('stm', 'JMP', size=4)
def pattern_jmp(context, tree):
    tgt = tree.value
    context.emit(B(tgt.name, jumps=[tgt]))
    
@isa.pattern('stm', 'MOVB(reg, reg)', size=40)
def pattern_movb(context, tree, c0, c1):
    # Emit memcpy
    dst = c0
    src = c1
    tmp = context.new_reg(RiscvRegister)
    size = tree.value
    for instruction in context.arch.gen_riscv_memcpy(dst, src, tmp, size):
        context.emit(instruction) 
	

@isa.pattern('reg', 'REGI32', size=0)
@isa.pattern('reg', 'REGI16', size=0)
@isa.pattern('reg', 'REGI8', size=0)
@isa.pattern('reg', 'REGU32', size=0)
@isa.pattern('reg', 'REGF32', size=0)
@isa.pattern('reg', 'REGF64', size=0)
@isa.pattern('reg', 'REGU16', size=0)
@isa.pattern('reg', 'REGU8', size=0)
def pattern_reg(context, tree):
    return tree.value



@isa.pattern('reg', 'U32TOU32(reg)', size=0)
@isa.pattern('reg', 'U32TOI32(reg)', size=0)
@isa.pattern('reg', 'I32TOU32(reg)', size=0)
@isa.pattern('reg', 'I32TOI32(reg)', size=0)
@isa.pattern('reg', 'U32TOU16(reg)', size=0)
@isa.pattern('reg', 'U32TOI16(reg)', size=0)
@isa.pattern('reg', 'I32TOI16(reg)', size=0)
@isa.pattern('reg', 'I32TOU16(reg)', size=0)
@isa.pattern('reg', 'U16TOU16(reg)', size=0)
@isa.pattern('reg', 'U16TOI16(reg)', size=0)
@isa.pattern('reg', 'I16TOI16(reg)', size=0)
@isa.pattern('reg', 'I16TOU16(reg)', size=0)
@isa.pattern('reg', 'U16TOU8(reg)', size=0)
@isa.pattern('reg', 'U16TOI8(reg)', size=0)
@isa.pattern('reg', 'I16TOI8(reg)', size=0)
@isa.pattern('reg', 'I16TOU8(reg)', size=0)
@isa.pattern('reg', 'U8TOU8(reg)', size=0)
@isa.pattern('reg', 'U8TOI8(reg)', size=0)
@isa.pattern('reg', 'I8TOI8(reg)', size=0)
@isa.pattern('reg', 'I8TOU8(reg)', size=0)
@isa.pattern('reg', 'F32TOF64(reg)', size=0)
@isa.pattern('reg', 'F64TOF32(reg)', size=0)
def pattern_i32_to_i32(context, tree, c0):
    return c0


@isa.pattern('reg', 'I8TOI16(reg)', size=4)
@isa.pattern('reg', 'I8TOI32(reg)', size=4)
def pattern_i8_to_i32(context, tree, c0):
    context.emit(Slli(c0, c0, 24))
    context.emit(Srai(c0, c0, 24))
    return c0


@isa.pattern('reg', 'I16TOI32(reg)', size=4)
def pattern_i16_to_i32(context, tree, c0):
    context.emit(Slli(c0, c0, 16))
    context.emit(Srai(c0, c0, 16))
    return c0


@isa.pattern('reg', 'I8TOU16(reg)', size=4)
@isa.pattern('reg', 'U8TOU16(reg)', size=4)
@isa.pattern('reg', 'U8TOI16(reg)', size=4)
def pattern_8_to_16(context, tree, c0):
    context.emit(Slli(c0, c0, 24))
    context.emit(Srli(c0, c0, 24))
    return c0


@isa.pattern('reg', 'I8TOU32(reg)', size=4)
@isa.pattern('reg', 'U8TOU32(reg)', size=4)
@isa.pattern('reg', 'U8TOI32(reg)', size=4)
def pattern_8_to_32(context, tree, c0):
    context.emit(Slli(c0, c0, 24))
    context.emit(Srli(c0, c0, 24))
    return c0


@isa.pattern('reg', 'I16TOU32(reg)', size=4)
@isa.pattern('reg', 'U16TOU32(reg)', size=4)
@isa.pattern('reg', 'U16TOI32(reg)', size=4)
def pattern_16_to_32(context, tree, c0):
    context.emit(Slli(c0, c0, 16))
    context.emit(Srli(c0, c0, 16))
    return c0


@isa.pattern('reg', 'I32TOI8(reg)', size=0)
@isa.pattern('reg', 'I32TOU8(reg)', size=0)
@isa.pattern('reg', 'I32TOI16(reg)', size=0)
@isa.pattern('reg', 'I32TOU16(reg)', size=0)
@isa.pattern('reg', 'U32TOU8(reg)', size=0)
@isa.pattern('reg', 'U32TOI8(reg)', size=0)
@isa.pattern('reg', 'U32TOU16(reg)', size=0)
@isa.pattern('reg', 'U32TOI16(reg)', size=0)
def pattern_32_to_8_16(context, tree, c0):
    # TODO: do something like sign extend or something else?
    return c0

@isa.pattern('reg', 'CONSTI32', size=4)
@isa.pattern('reg', 'CONSTU32', size=4)
@isa.pattern('reg', 'CONSTI16', size=4)
@isa.pattern('reg', 'CONSTU16', size=4)
@isa.pattern(
    'reg', 'CONSTI32', size=2,
    condition=lambda t: t.value in range(-2048, 2048))
@isa.pattern(
    'reg', 'CONSTI16', size=2,
    condition=lambda t: t.value in range(-2048, 2048))
@isa.pattern('reg', 'CONSTI8', size=2,
             condition=lambda t: t.value in range(-128, 128))
@isa.pattern('reg', 'CONSTU8', size=2,
             condition=lambda t: t.value < 256)
def pattern_const_i32(context, tree):
    d = context.new_reg(RiscvRegister)
    c0 = tree.value
    context.emit(Li(d, c0))
    return d

@isa.pattern('reg', 'CONSTF32', size=4)
@isa.pattern('reg', 'CONSTF64', size=4)
def pattern_const_f32(context, tree):
    float_const = struct.pack('f', tree.value)
    c0, = struct.unpack('i', float_const)
    d = context.new_reg(RiscvRegister)    
    context.emit(Li(d, c0))
    return d

@isa.pattern('stm', 'CJMPI32(reg, reg)', size=4)
@isa.pattern('stm', 'CJMPI16(reg, reg)', size=4)
@isa.pattern('stm', 'CJMPI8(reg, reg)', size=4)
def pattern_cjmp(context, tree, c0, c1):
    op, yes_label, no_label = tree.value
    opnames = {"<": Blt, ">": Bgt, "==": Beq, "!=": Bne, ">=": Bge, "<=": Ble}
    Bop = opnames[op]
    jmp_ins = B(no_label.name, jumps=[no_label])
    context.emit(Bop(c0, c1, yes_label.name, jumps=[yes_label, jmp_ins]))
    context.emit(jmp_ins)


@isa.pattern('stm', 'CJMPU8(reg, reg)', size=4)
@isa.pattern('stm', 'CJMPU16(reg, reg)', size=4)
@isa.pattern('stm', 'CJMPU32(reg, reg)', size=4)
def pattern_cjmpu(context, tree, c0, c1):
    op, yes_label, no_label = tree.value
    opnames = {
        "<": Bltu, ">": Bgtu, "==": Beq, "!=": Bne, ">=": Bgeu, "<=": Bleu
    }
    Bop = opnames[op]
    jmp_ins = B(no_label.name, jumps=[no_label])
    context.emit(Bop(c0, c1, yes_label.name, jumps=[yes_label, jmp_ins]))
    context.emit(jmp_ins)


@isa.pattern('reg', 'ADDU32(reg, reg)', size=2)
@isa.pattern('reg', 'ADDI32(reg, reg)', size=2)
def pattern_add_i32(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Addr(d, c0, c1))
    return d


@isa.pattern('reg', 'ADDU16(reg, reg)', size=2)
@isa.pattern('reg', 'ADDI16(reg, reg)', size=2)
def pattern_add_i16(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Addr(d, c0, c1))
    return d


@isa.pattern('reg', 'ADDI8(reg, reg)', size=2)
@isa.pattern('reg', 'ADDU8(reg, reg)', size=2)
def pattern_add8(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Addr(d, c0, c1))
    return d


@isa.pattern(
    'reg', 'ADDI32(reg, CONSTI32)', size=2,
    condition=lambda t: t[1].value < 2048)
@isa.pattern(
    'reg', 'ADDU32(reg, CONSTU32)', size=2,
    condition=lambda t: t[1].value < 2048)
def pattern_add_i32_reg_const(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[1].value
    context.emit(Addi(d, c0, c1))
    return d


@isa.pattern(
    'reg', 'ADDI32(CONSTI32, reg)', size=2,
    condition=lambda t: t.children[0].value < 2048)
@isa.pattern(
    'reg', 'ADDU32(CONSTU32, reg)', size=2,
    condition=lambda t: t.children[0].value < 2048)
def pattern_add_i32_const_reg(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[0].value
    context.emit(Addi(d, c0, c1))
    return d


@isa.pattern('reg', 'SUBI8(reg, reg)', size=2)
@isa.pattern('reg', 'SUBU8(reg, reg)', size=2)
@isa.pattern('reg', 'SUBI16(reg, reg)', size=2)
@isa.pattern('reg', 'SUBU16(reg, reg)', size=2)
@isa.pattern('reg', 'SUBI32(reg, reg)', size=2)
@isa.pattern('reg', 'SUBU32(reg, reg)', size=2)
def pattern_sub_i32(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Subr(d, c0, c1))
    return d


@isa.pattern('reg', 'LABEL', size=6)
def pattern_label1(context, tree):
    d = context.new_reg(RiscvRegister)
    ln = context.frame.add_constant(tree.value)
    context.emit(Adru(d, ln))
    context.emit(Adrl(d, d, ln))
    context.emit(Lw(d, 0, d))
    return d


@isa.pattern('reg', 'LABEL', size=4)
def pattern_label2(context, tree):
    d = context.new_reg(RiscvRegister)
    ln = context.frame.add_constant(tree.value)
    context.emit(Labelrel(d, ln))
    return d


@isa.pattern(
    'reg', 'FPRELU32', size=4,
    condition=lambda t: t.value.offset in range(-2048, 2048))
def pattern_fpreli32(context, tree):
    d = context.new_reg(RiscvRegister)
    offset = tree.value.offset
    context.emit(Addi(d, FP, offset))
    return d


# Memory patterns:
@isa.pattern(
    'mem', 'FPRELU32', size=0,
    condition=lambda t: t.value.offset in range(-2048, 2048))
def pattern_mem_fpreli32(context, tree):
    offset = tree.value.offset
    return FP, offset


@isa.pattern('mem', 'reg', size=0)
def pattern_mem_reg(context, tree, c0):
    return c0, 0


@isa.pattern(
    'mem', 'ADDI32(reg, CONSTI32)', size=0,
    condition=lambda t: t[1].value < 2047)
@isa.pattern(
    'mem', 'ADDU32(reg, CONSTU32)', size=0,
    condition=lambda t: t[1].value < 2047)
def pattern_mem_add_reg_const(context, tree, c0):
    offset = tree[1].value
    return c0, offset


@isa.pattern('stm', 'STRU32(mem, reg)', size=2)
@isa.pattern('stm', 'STRI32(mem, reg)', size=2)
@isa.pattern('stm', 'STRF32(mem, reg)', size=2)
@isa.pattern('stm', 'STRF64(mem, reg)', size=2)
def pattern_sw32(context, tree, c0, c1):
    base_reg, offset = c0
    context.emit(Sw(c1, offset, base_reg))


@isa.pattern('stm', 'STRI16(mem, reg)', size=2)
@isa.pattern('stm', 'STRU16(mem, reg)', size=2)
def pattern_str16(context, tree, c0, c1):
    base_reg, offset = c0
    context.emit(Sh(c1, offset, base_reg))


@isa.pattern('stm', 'STRU8(mem, reg)', size=2)
@isa.pattern('stm', 'STRI8(mem, reg)', size=2)
def pattern_sbi8(context, tree, c0, c1):
    base_reg, offset = c0
    context.emit(Sb(c1, offset, base_reg))


@isa.pattern('reg', 'LDRI8(mem)', size=2)
def pattern_ldri8(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    base_reg, offset = c0
    context.emit(Lb(d, offset, base_reg))
    return d


@isa.pattern('reg', 'LDRU8(mem)', size=2)
def pattern_ldru8_fprel(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    base_reg, offset = c0
    context.emit(Lbu(d, offset, base_reg))
    return d


@isa.pattern('reg', 'LDRU32(mem)', size=2)
@isa.pattern('reg', 'LDRI32(mem)', size=2)
@isa.pattern('reg', 'LDRF32(mem)', size=2)
@isa.pattern('reg', 'LDRF64(mem)', size=2)
def pattern_ldr32_fprel(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    base_reg, offset = c0
    context.emit(Lw(d, offset, base_reg))
    return d


@isa.pattern('reg', 'NEGI8(reg)', size=2)
@isa.pattern('reg', 'NEGI16(reg)', size=2)
@isa.pattern('reg', 'NEGI32(reg)', size=2)
@isa.pattern('reg', 'NEGU32(reg)', size=2)
def pattern_negi32(context, tree, c0):
    context.emit(Subr(c0, R0, c0))
    return c0


@isa.pattern('reg', 'INVI8(reg)', size=2)
@isa.pattern('reg', 'INVU8(reg)', size=2)
@isa.pattern('reg', 'INVU32(reg)', size=2)
@isa.pattern('reg', 'INVI32(reg)', size=2)
def pattern_inv(context, tree, c0):
    context.emit(Xori(c0, c0, -1))
    return c0


@isa.pattern('reg', 'LDRU16(reg)', size=2)
def pattern_ldru16(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    context.emit(Lhu(d, 0, c0))
    return d


@isa.pattern('reg', 'LDRI16(reg)', size=2)
def pattern_ldri16(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    context.emit(Lh(d, 0, c0))
    return d


@isa.pattern('reg', 'LDRU32(reg)', size=2)
@isa.pattern('reg', 'LDRI32(reg)', size=2)
def pattern_ldr_i32(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    context.emit(Lw(d, 0, c0))
    return d


@isa.pattern('reg', 'ANDI8(reg, reg)', size=2)
@isa.pattern('reg', 'ANDU8(reg, reg)', size=2)
@isa.pattern('reg', 'ANDI16(reg, reg)', size=2)
@isa.pattern('reg', 'ANDU16(reg, reg)', size=2)
@isa.pattern('reg', 'ANDI32(reg, reg)', size=2)
@isa.pattern('reg', 'ANDU32(reg, reg)', size=2)
def pattern_and_i(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Andr(d, c0, c1))
    return d


@isa.pattern(
    'reg', 'ANDI32(reg, CONSTI32)', size=2,
    condition=lambda t: t.children[1].value < 2048)
def pattern_and_i32(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[1].value
    context.emit(Andi(d, c0, c1))
    return d


@isa.pattern(
    'reg', 'ANDI8(reg, CONSTI8)', size=2,
    condition=lambda t: t.children[1].value < 256)
@isa.pattern(
    'reg', 'ANDU8(reg, CONSTU8)', size=2,
    condition=lambda t: t.children[1].value < 256)
def pattern_and8_reg_const(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[1].value
    context.emit(Andi(d, c0, c1))
    return d


@isa.pattern('reg', 'ORU32(reg, reg)', size=2)
@isa.pattern('reg', 'ORI32(reg, reg)', size=2)
@isa.pattern('reg', 'ORU16(reg, reg)', size=2)
@isa.pattern('reg', 'ORI16(reg, reg)', size=2)
@isa.pattern('reg', 'ORU8(reg, reg)', size=2)
@isa.pattern('reg', 'ORI8(reg, reg)', size=2)
def pattern_or_i32(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Orr(d, c0, c1))
    return d


@isa.pattern(
    'reg', 'ORI32(reg, CONSTI32)', size=2,
    condition=lambda t: t.children[1].value < 2048)
def pattern_or_i32_reg_const(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[1].value
    context.emit(Ori(d, c0, c1))
    return d


@isa.pattern(
    'reg', 'ORI32(CONSTI32, reg)', size=2,
    condition=lambda t: t.children[0].value < 2048)
def pattern_or_i32_const_reg(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[0].value
    context.emit(Ori(d, c0, c1))
    return d


@isa.pattern('reg', 'SHRU8(reg, reg)', size=2)
@isa.pattern('reg', 'SHRU16(reg, reg)', size=2)
@isa.pattern('reg', 'SHRU32(reg, reg)', size=2)
def pattern_shr_u32(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Srl(d, c0, c1))
    return d


@isa.pattern('reg', 'SHRI8(reg, reg)', size=2)
@isa.pattern('reg', 'SHRI16(reg, reg)', size=2)
@isa.pattern('reg', 'SHRI32(reg, reg)', size=2)
def pattern_shr_i32(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Sra(d, c0, c1))
    return d


@isa.pattern(
    'reg', 'SHRI32(reg, CONSTI32)',
    size=2, condition=lambda t: t.children[1].value < 32)
def pattern_shr_i32_reg_const(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[1].value
    context.emit(Srai(d, c0, c1))
    return d


@isa.pattern('reg', 'SHLU8(reg, reg)', size=2)
@isa.pattern('reg', 'SHLI8(reg, reg)', size=2)
@isa.pattern('reg', 'SHLU16(reg, reg)', size=2)
@isa.pattern('reg', 'SHLI16(reg, reg)', size=2)
@isa.pattern('reg', 'SHLU32(reg, reg)', size=2)
@isa.pattern('reg', 'SHLI32(reg, reg)', size=2)
def pattern_shl_i32(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Sll(d, c0, c1))
    return d


@isa.pattern(
    'reg', 'SHLI32(reg, CONSTI32)', size=2,
    condition=lambda t: t.children[1].value < 32)
def pattern_shl_i32_reg_const(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[1].value
    context.emit(Slli(d, c0, c1))
    return d


@isa.pattern('reg', 'MULI8(reg, reg)', size=10)
@isa.pattern('reg', 'MULU8(reg, reg)', size=10)
@isa.pattern('reg', 'MULU16(reg, reg)', size=10)
@isa.pattern('reg', 'MULI32(reg, reg)', size=10)
@isa.pattern('reg', 'MULU32(reg, reg)', size=10)
def pattern_mul_i32(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Mul(d, c0, c1))
    return d


@isa.pattern('reg', 'LDRI32(ADDI32(reg, CONSTI32))', size=2)
def pattern_ldr_i32_add(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[0].children[1].value
    assert isinstance(c1, int)
    context.emit(Lw(d, c1, c0))
    return d


@isa.pattern('reg', 'DIVI32(reg, reg)', size=10)
def pattern_div_i32(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Div(d, c0, c1))
    return d


@isa.pattern('reg', 'DIVU16(reg, reg)', size=10)
@isa.pattern('reg', 'DIVU32(reg, reg)', size=10)
def pattern_div_u32(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Divu(d, c0, c1))
    return d


@isa.pattern('reg', 'REMI32(reg, reg)', size=10)
def pattern_rem_i32(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Rem(d, c0, c1))
    return d


@isa.pattern('reg', 'REMU16(reg, reg)', size=10)
@isa.pattern('reg', 'REMU32(reg, reg)', size=10)
def pattern_rem_u32(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Remu(d, c0, c1))
    return d


@isa.pattern('reg', 'XORU8(reg, reg)', size=2)
@isa.pattern('reg', 'XORI8(reg, reg)', size=2)
@isa.pattern('reg', 'XORU16(reg, reg)', size=2)
@isa.pattern('reg', 'XORI16(reg, reg)', size=2)
@isa.pattern('reg', 'XORU32(reg, reg)', size=2)
@isa.pattern('reg', 'XORI32(reg, reg)', size=2)
def pattern_xor_i32(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Xorr(d, c0, c1))
    return d


@isa.pattern(
    'reg', 'XORI32(reg, CONSTI32)', size=2,
    condition=lambda t: t.children[1].value < 2048)
def pattern_xor_i32_reg_const(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[1].value
    context.emit(Xori(d, c0, c1))
    return d


@isa.pattern(
    'reg', 'XORI32(CONSTI32, reg)', size=2,
    condition=lambda t: t.children[0].value < 2048)
def pattern_xor_i32_const_reg(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[0].value
    context.emit(Xori(d, c0, c1))
    return d
    

def call_internal2(context, name, a, b, clobbers=()):
    d = context.new_reg(RiscvRegister)
    context.move(R12, a)
    context.move(R13, b)
    context.emit(RegisterUseDef(uses=(R12, R13))) 
    context.emit(Bl(LR, name, clobbers=clobbers)) 
    context.emit(RegisterUseDef(uses=(R10,)))     
    context.move(d, R10)
    return d 

def call_internal1(context, name, a, clobbers=()):
    d = context.new_reg(RiscvRegister)
    context.move(R12, a)    
    context.emit(RegisterUseDef(uses=(R12,))) 
    context.emit(Bl(LR, name, clobbers=clobbers)) 
    context.emit(RegisterUseDef(uses=(R10,)))     
    context.move(d, R10)
    return d 

@isa.pattern('reg', 'ADDF64(reg, reg)', size=10)    
@isa.pattern('reg', 'ADDF32(reg, reg)', size=10)
def pattern_add_f32(context, tree, c0, c1):    
    return call_internal2(context,'float32_add', c0, c1, clobbers=context.arch.caller_save)

@isa.pattern('reg', 'SUBF64(reg, reg)', size=10)    
@isa.pattern('reg', 'SUBF32(reg, reg)', size=10)
def pattern_sub_f32(context, tree, c0, c1):    
    return call_internal2(context,'float32_sub', c0, c1, clobbers=context.arch.caller_save)
    
@isa.pattern('reg', 'MULF64(reg, reg)', size=10)
@isa.pattern('reg', 'MULF32(reg, reg)', size=10)
def pattern_mul_f32(context, tree, c0, c1):    
    return call_internal2(context,'float32_mul', c0, c1, clobbers=context.arch.caller_save)
    
@isa.pattern('reg', 'DIVF64(reg, reg)', size=10)
@isa.pattern('reg', 'DIVF32(reg, reg)', size=10)
def pattern_div_f32(context, tree, c0, c1):    
    return call_internal2(context,'float32_div', c0, c1, clobbers=context.arch.caller_save)
    
@isa.pattern('reg', 'NEGF64(reg)', size=10)
@isa.pattern('reg', 'NEGF32(reg)', size=10)
def pattern_neg_f32(context, tree, c0):    
    return call_internal1(context,'float32_neg', c0, clobbers=context.arch.caller_save)
    
@isa.pattern('reg', 'F32TOI32(reg)', size=10)
@isa.pattern('reg', 'F64TOI32(reg)', size=10)
def pattern_ftoi_f32(context, tree, c0):    
    return call_internal1(context,'float32_to_int32', c0, clobbers=context.arch.caller_save)
    
@isa.pattern('reg', 'I32TOF32(reg)', size=10)
@isa.pattern('reg', 'I32TOF64(reg)', size=10)
def pattern_itof_f32(context, tree, c0):    
    return call_internal1(context,'int32_to_float32', c0, clobbers=context.arch.caller_save)

@isa.pattern('stm', 'CJMPF32(reg, reg)', size=4)
@isa.pattern('stm', 'CJMPF64(reg, reg)', size=4)
def pattern_cjmp(context, tree, c0, c1):
    op, yes_label, no_label = tree.value
    opnames = {"<": "float32_lt", ">": "float32_gt", "==": "float32_eq", "!=": "float32_ne", ">=": "float32_ge", "<=": "float32_le"}
    Bop = opnames[op]
    jmp_ins = B(no_label.name, jumps=[no_label])
    call_internal2(context, Bop, c0, c1, clobbers=context.arch.caller_save)
    context.emit(Bne(R10, R0, yes_label.name, jumps=[yes_label, jmp_ins]))
    context.emit(jmp_ins)
    
    
# TODO: implement DIVI32 by library call.
# TODO: Do that here, or in irdag?
