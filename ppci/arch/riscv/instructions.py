""" Definitions of Riscv instructions. """

# pylint: disable=no-member,invalid-name

from ..isa import Isa
from ..encoding import Instruction, Syntax, Operand
from ..data_instructions import Dd
from ...utils.bitfun import wrap_negative
from .registers import RiscvRegister
from .relocations import AbsAddr32Relocation
from .relocations import BImm12Relocation, BImm20Relocation
from .relocations import Abs32Imm20Relocation
from .relocations import Abs32Imm12Relocation, RelImm20Relocation
from .relocations import RelImm12Relocation
from .tokens import RiscvToken, RiscvIToken
from ...ir import i32


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


def Mov(*args):
    if len(args) == 2:
        if isinstance(args[1], int):
            return Movi(*args)
        elif isinstance(args[1], RiscvRegister):
            return Movr(*args)
    raise Exception()


class Movi(RiscvInstruction):
    """ Mov Rd, imm16 """
    rd = Operand('rd', RiscvRegister, write=True)
    imm = Operand('imm', int)
    syntax = Syntax(['mov', rd, ',', imm])

    def encode(self):
        tokens = self.get_tokens()
        imm12 = wrap_negative(self.imm, 12)
        tokens[0][0:7] = 0b0010011
        tokens[0][7:12] = self.rd.num
        tokens[0][12:20] = 0
        tokens[0][20:32] = imm12
        return tokens[0].encode()


class Movr(RiscvInstruction):
    rd = Operand('rd', RiscvRegister, write=True)
    rm = Operand('rm', RiscvRegister, read=True)
    syntax = Syntax(['mov', rd, ',', rm])
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
        if self.invert:
            self.imm = -self.imm
        if self.imm < 0:
            imm12 = wrap_negative(self.imm, 12)
        else:
            imm12 = self.imm & 0xFFF
        tokens[0][20:32] = imm12
        return tokens[0].encode()


def make_i(mnemonic, func, invert):
    rd = Operand('rd', RiscvRegister, write=True)
    rs1 = Operand('rs1', RiscvRegister, read=True)
    imm = Operand('imm', int)
    syntax = Syntax([mnemonic, rd, ',', rs1, ',', imm])
    members = {
        'syntax': syntax, 'func': func,
        'rd': rd, 'rs1': rs1, 'imm': imm,
        'invert': invert}
    return type(mnemonic + '_ins', (IBase,), members)


Addi = make_i('add', 0b000, False)
Addi2 = make_i('addi', 0b000, False)
Subi = make_i('sub', 0b000, True)
Slti = make_i('slti', 0b010, False)
Sltiu = make_i('sltiu', 0b011, False)
Xori = make_i('xori', 0b100, False)
Ori = make_i('ori', 0b110, False)
Andi = make_i('andi', 0b111, False)


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


class Sbreak(RiscvInstruction):
    syntax = Syntax(['sbreak'])
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
        if self.imm < 0:
            imm20 = wrap_negative(self.imm >> 12, 20)
        else:
            imm20 = self.imm >> 12
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


class Adrlrel(RiscvInstruction):
    rd = Operand('rd', RiscvRegister, write=True)
    rs1 = Operand('rs1', RiscvRegister, read=True)
    label = Operand('label', str)
    syntax = Syntax(['lw', ' ', rd, ' ', ',', rs1, ' ', ',', ' ', label])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:7] = 0b0000011
        tokens[0][7:12] = self.rd.num
        tokens[0][12:15] = 0b010
        tokens[0][15:20] = self.rs1.num
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
Bltu = make_branch('bltu', 0b110, False)
Bge = make_branch('bge', 0b101, False)
Bgeu = make_branch('bgeu', 0b111, False)
Bgt = make_branch('bgt', 0b100, True)


def reg_list_to_mask(reg_list):
    mask = 0
    for reg in reg_list:
        mask |= (1 << reg.num)
    return mask


class StrBase(RiscvInstruction):
    def encode(self):
        if self.offset < 0:
            imml5 = wrap_negative(-((-self.offset) & 0x1f), 5)
        else:
            imml5 = self.offset & 0x1f
        immh7 = wrap_negative(self.offset >> 5, 7)
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
    syntax = Syntax([mnemonic, ' ', rd, ',', ' ', offset, '(',  rs1, ')'])
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


# Instruction selection patterns:
@isa.pattern('stm', 'STRI32(reg, reg)', size=2)
def _(self, tree, c0, c1):
    self.emit(Sw(c1, 0, c0))


@isa.pattern(
    'stm', 'STRI32(ADDI32(reg, CONSTI32), reg)',
    size=2,
    condition=lambda t: t.children[0].children[1].value < 256)
def _(context, tree, c0, c1):
    # TODO: something strange here: when enabeling this rule, programs
    # compile correctly...
    offset = tree.children[0].children[1].value
    context.emit(Sw(c1, offset, c0))


@isa.pattern('stm', 'STRI8(reg, reg)', size=2)
def pattern_stri8(context, tree, c0, c1):
    context.emit(Sb(c1, 0, c0))


@isa.pattern('reg', 'MOVI32(reg)', size=2)
def pattern_movi32(context, tree, c0):
    context.move(tree.value, c0)
    return tree.value


@isa.pattern('reg', 'MOVI8(reg)', size=2)
def pattern_movi8(context, tree, c0):
    context.move(tree.value, c0)
    return tree.value


@isa.pattern('stm', 'JMP', size=2)
def _(context, tree):
    tgt = tree.value
    context.emit(B(tgt.name, jumps=[tgt]))


@isa.pattern('reg', 'REGI32', size=0)
def _(context, tree):
    return tree.value


@isa.pattern('reg', 'I32TOI32(reg)', size=0)
def _(context, tree, c0):
    return c0


@isa.pattern('reg', 'I8TOI32(reg)', size=0)
def _(context, tree, c0):
    # TODO: do something like sign extend or something else?
    return c0


@isa.pattern('reg', 'I32TOI8(reg)', size=0)
def _(context, tree, c0):
    # TODO: do something like sign extend or something else?
    return c0


@isa.pattern('reg', 'REGI8', size=0)
def _(context, tree):
    return tree.value


@isa.pattern('reg', 'CONSTI32', size=4)
def _(context, tree):
    d = context.new_reg(RiscvRegister)
    c0 = tree.value
    if((c0&0x800)!=0):
        c0 -= 0xFFFFF000
    context.emit(Lui(d, c0))
    context.emit(Addi(d, d, c0))
    return d


@isa.pattern('reg', 'CONSTI32', size=2, condition=lambda t: t.value>=-2048 and t.value < 2048)
def _(context, tree):
    d = context.new_reg(RiscvRegister)
    c0 = tree.value
    assert isinstance(c0, int)
    assert c0 < 2048 and c0 >= -2048
    context.emit(Movi(d, c0))
    return d


@isa.pattern('reg', 'CONSTI8', size=2, condition=lambda t: t.value < 256)
def _(context, tree):
    d = context.new_reg(RiscvRegister)
    c0 = tree.value
    assert isinstance(c0, int)
    assert c0 < 256 and c0 >= 0
    context.emit(Movi(d, c0))
    return d


@isa.pattern('stm', 'CJMP(reg, reg)', size=2)
def _(context, tree, c0, c1):
    op, yes_label, no_label = tree.value
    opnames = {"<": Blt, ">": Bgt, "==": Beq, "!=": Bne, ">=": Bge, "<=": Bgt}
    Bop = opnames[op]
    if(op=="<="):
        jmp_ins = B(yes_label.name, jumps=[yes_label])
        context.emit(Bop(c0, c1, yes_label.name, jumps=[no_label, jmp_ins]))
        context.emit(jmp_ins)
    else:
        jmp_ins = B(no_label.name, jumps=[no_label])
        context.emit(Bop(c0, c1, yes_label.name, jumps=[yes_label, jmp_ins]))
        context.emit(jmp_ins)


@isa.pattern('reg', 'ADDI32(reg, reg)', size=2)
def _(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Addr(d, c0, c1))
    return d


@isa.pattern('reg', 'ADDI8(reg, reg)', size=2)
def _(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Addr(d, c0, c1))
    return d


@isa.pattern(
    'reg', 'ADDI32(reg, CONSTI32)', size=2,
    condition=lambda t: t.children[1].value < 2048)
def _(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[1].value
    context.emit(Addi(d, c0, c1))
    return d


@isa.pattern(
    'reg', 'ADDI32(CONSTI32, reg)', size=2,
    condition=lambda t: t.children[0].value < 2048)
def _(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[0].value
    context.emit(Addi(d, c0, c1))
    return d


@isa.pattern('reg', 'SUBI32(reg, reg)', size=2)
def _(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Subr(d, c0, c1))
    return d


@isa.pattern('reg', 'SUBI8(reg, reg)', size=2)
def _(context, tree, c0, c1):
    # TODO: temporary fix this with an 32 bits sub
    d = context.new_reg(RiscvRegister)
    context.emit(Subr(d, c0, c1))
    return d


@isa.pattern('reg', 'LABEL', size=6)
def _(context, tree):
    d = context.new_reg(RiscvRegister)
    ln = context.frame.add_constant(tree.value)
    context.emit(Adru(d, ln))
    context.emit(Adrl(d, d, ln))
    context.emit(Lw(d, 0, d))
    return d

@isa.pattern('reg', 'LABEL', size=4)
def _(context, tree):
    d = context.new_reg(RiscvRegister)
    ln = context.frame.add_constant(tree.value)
    context.emit(Adrurel(d, ln))
    context.emit(Adrlrel(d, d, ln))
    return d

@isa.pattern('reg', 'LDRI8(reg)', size=2)
def _(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    context.emit(Lbu(d, 0, c0))
    return d


@isa.pattern('reg', 'LDRI32(reg)', size=2)
def _(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    context.emit(Lw(d, 0, c0))
    return d


@isa.pattern('reg', 'CALL', size=2)
def _(context, tree):
    return context.gen_call(tree.value)


@isa.pattern('reg', 'ANDI32(reg, reg)', size=2)
def _(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(And(d, c0, c1))
    return d


@isa.pattern(
    'reg', 'ANDI32(reg, CONSTI32)', size=2,
    condition=lambda t: t.children[1].value < 2048)
def _(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[1].value
    context.emit(Andi(d, c0, c1))
    return d


@isa.pattern( 'reg', 'ANDI8(reg, CONSTI8)', size=2,
              condition=lambda t: t.children[1].value < 256)
def _(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[1].value
    context.emit(Andi(d, c0, c1))
    return d


@isa.pattern( 'reg', 'ANDI8(CONSTI8, reg)', size=2,
              condition=lambda t: t.children[0].value < 256)
def _(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[0].value
    context.emit(Andi(d, c0, c1))
    return d


@isa.pattern('reg', 'ORI32(reg, reg)', size=2)
def _(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Orr(d, c0, c1))
    return d


@isa.pattern(
    'reg', 'ORI32(reg, CONSTI32)', size=2,
    condition=lambda t: t.children[1].value < 2048)
def _(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[1].value
    context.emit(Ori(d, c0, c1))
    return d


@isa.pattern(
    'reg', 'ORI32(CONSTI32, reg)', size=2,
    condition=lambda t: t.children[0].value < 2048)
def _(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[0].value
    context.emit(Ori(d, c0, c1))
    return d


@isa.pattern('reg', 'SHRI32(reg, reg)', size=2)
def _(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Srl(d, c0, c1))
    return d


@isa.pattern(
    'reg', 'SHRI32(reg, CONSTI32)',
    size=2, condition=lambda t: t.children[1].value < 32)
def _(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[1].value
    context.emit(Srli(d, c0, c1))
    return d


@isa.pattern(
    'reg', 'SHRI32(CONSTI32, reg)', size=2,
    condition=lambda t: t.children[0].value < 32)
def _(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[0].value
    context.emit(Srli(d, c0, c1))
    return d


@isa.pattern('reg', 'SHLI32(reg, reg)', size=2)
def _(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Sll(d, c0, c1))
    return d


@isa.pattern(
    'reg', 'SHLI32(reg, CONSTI32)', size=2,
    condition=lambda t: t.children[1].value < 32)
def _(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[1].value
    context.emit(Slli(d, c0, c1))
    return d


@isa.pattern(
    'reg', 'SHLI32(CONSTI32, reg)', size=2,
    condition=lambda t: t.children[0].value < 32)
def _(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[0].value
    context.emit(Slli(d, c0, c1))
    return d


@isa.pattern('reg', 'MULI32(reg, reg)', size=10)
def _(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Mul(d, c0, c1))
    return d


@isa.pattern('reg', 'LDRI32(ADDI32(reg, CONSTI32))', size=2)
def _(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[0].children[1].value
    assert isinstance(c1, int)
    context.emit(Lw(d, c1, c0))
    return d


@isa.pattern('reg', 'DIVI32(reg, reg)', size=10)
def _(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    # Generate call into runtime lib function!
    context.gen_call(('__sdiv', [i32, i32], i32, [c0, c1], d))
    return d


@isa.pattern('reg', 'REMI32(reg, reg)', size=10)
def _(context, tree, c0, c1):
    # Implement remainder as a combo of div and mls (multiply substract)
    d = context.new_reg(RiscvRegister)
    context.gen_call(('__sdiv', [i32, i32], i32, [c0, c1], d))
    context.emit(Mul(c1, c1, d))
    d2 = context.new_reg(RiscvRegister)
    context.emit(Subr(d2, c0, c1))
    return d2


@isa.pattern('reg', 'XORI32(reg, reg)', size=2)
def _(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Xor(d, c0, c1))
    return d


@isa.pattern(
    'reg', 'XORI32(reg, CONSTI32)', size=2,
    condition=lambda t: t.children[1].value < 2048)
def _(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[1].value
    context.emit(Xori(d, c0, c1))
    return d


@isa.pattern(
    'reg', 'XORI32(CONSTI32, reg)', size=2,
    condition=lambda t: t.children[0].value < 2048)
def _(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[0].value
    context.emit(Xori(d, c0, c1))
    return d
# TODO: implement DIVI32 by library call.
# TODO: Do that here, or in irdag?
