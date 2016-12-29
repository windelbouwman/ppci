""" Definitions of Riscv instructions. """

from ...utils.bitfun import wrap_negative
from ..isa import Isa
from ..encoding import Instruction, Syntax, Operand
from .registers import RiscvRegister
from .tokens import RiscvcToken
from .rvc_relocations import BcImm11Relocation, BcImm8Relocation
from ..arch import ArtificialInstruction
from .instructions import Andr, Orr, Xorr, Subr, Addi, Slli, Srli
from .instructions import Lw, Sw, Blt, Bgt, Bge, B, Beq, Bne


class RegisterSet(set):
    def __repr__(self):
        reg_names = sorted(str(r) for r in self)
        return ', '.join(reg_names)


rvcisa = Isa()

rvcisa.register_relocation(BcImm11Relocation)
rvcisa.register_relocation(BcImm8Relocation)


class RiscvcInstruction(Instruction):
    tokens = [RiscvcToken]
    isa = rvcisa


class PseudoRiscvInstruction(ArtificialInstruction):
    """ These instruction is used to switch between RV and RVC-encoding """
    pass


class OpcRegReg(RiscvcInstruction):
    """ c.sub rd, rn """
    def encode(self):
        tokens = self.get_tokens()
        tokens[0].op = 0b01
        tokens[0][2:5] = self.rn.num-8
        tokens[0][5:7] = self.func
        tokens[0][7:10] = self.rd.num-8
        tokens[0][10:16] = 0b100011
        return tokens[0].encode()


def makec_regreg(mnemonic, func):
    rd = Operand('rd', RiscvRegister, write=True)
    rn = Operand('rn', RiscvRegister, read=True)
    syntax = Syntax(['c', '.', mnemonic, ' ', rd, ',', ' ', rn])
    members = {
        'syntax': syntax, 'rd': rd, 'rn': rn, 'func': func}
    return type('c' + mnemonic + '_ins', (OpcRegReg,), members)


CSub = makec_regreg('sub', 0b00)
CXor = makec_regreg('xor', 0b01)
COr = makec_regreg('or', 0b10)
CAnd = makec_regreg('and', 0b11)


class CSlli(RiscvcInstruction):
    rd = Operand('rd', RiscvRegister, write=True)
    rs = Operand('rs', RiscvRegister, read=True)
    imm = Operand('imm', int)
    syntax = Syntax(['c', '.', 'slli', ' ', rd, ',', ' ', rs, ',', ' ', imm])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:2] = 0b10
        tokens[0][2:7] = self.imm & 0xF
        tokens[0][7:12] = self.rd.num
        tokens[0][13:16] = 0b0000
        return tokens[0].encode()


class CiBase(RiscvcInstruction):
    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:2] = 0b01
        tokens[0][2:7] = self.imm
        tokens[0][7:10] = self.rd.num-8
        tokens[0][10:12] = self.func
        tokens[0][12:16] = 0b1000
        return tokens[0].encode()


def makec_i(mnemonic, func):
    rd = Operand('rd', RiscvRegister, write=True)
    rs = Operand('rs', RiscvRegister, read=True)
    imm = Operand('imm', int)
    syntax = Syntax(['c', '.', mnemonic, ' ', rd, ',', ' ', rs, ',', ' ', imm])
    members = {'syntax': syntax, 'func': func, 'rd': rd, 'rs': rs, 'imm': imm}
    return type('c_' + mnemonic + '_ins', (CiBase,), members)


CSrli = makec_i('srli', 0b00)
CSrai = makec_i('srai', 0b01)
CAndi = makec_i('andi', 0b10)


class CAddi(RiscvcInstruction):
    rd = Operand('rd', RiscvRegister, write=True)
    imm = Operand('imm', int)
    syntax = Syntax(['c', '.', 'addi', ' ', rd, ',', ' ', rd, ',', ' ', imm])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:2] = 0b01
        tokens[0][2:7] = self.imm
        tokens[0][7:12] = self.rd.num
        tokens[0][12:16] = 0b0000
        return tokens[0].encode()


class CNop(RiscvcInstruction):
    syntax = Syntax(['c', '.', 'nop'])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:2] = 0b01
        tokens[0][2:16] = 0
        return tokens[0].encode()


class CEbreak(RiscvcInstruction):
    syntax = Syntax(['c', '.', 'ebreak'])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:16] = 0b1001000000000010
        return tokens[0].encode()


class CJal(RiscvcInstruction):
    target = Operand('target', str)
    syntax = Syntax(['c', '.', 'jal', ' ', target])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:2] = 0b01
        tokens[0][13:16] = 0b001
        return tokens[0].encode()

    def relocations(self):
        return [BcImm11Relocation(self.target)]


class CJ(RiscvcInstruction):
    target = Operand('target', str)
    syntax = Syntax(['c', '.', 'j', ' ', target])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:2] = 0b01
        tokens[0][13:16] = 0b101
        return tokens[0].encode()

    def relocations(self):
        return [BcImm11Relocation(self.target)]


class CJr(RiscvcInstruction):
    rs1 = Operand('rs1', RiscvRegister, read=True)
    syntax = Syntax(['c', '.', 'jr', ' ', rs1])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:7] = 0b0000010
        tokens[0][7:12] = self.rs1.num
        tokens[0][12:16] = 0b1000
        return tokens[0].encode()


class CJalr(RiscvcInstruction):
    rs1 = Operand('rs1', RiscvRegister, read=True)
    syntax = Syntax(['c', '.', 'jalr', ' ', rs1])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:7] = 0b0000010
        tokens[0][7:12] = self.rs1.num
        tokens[0][12:16] = 0b1001
        return tokens[0].encode()


class CBeqz(RiscvcInstruction):
    rn = Operand('rn', RiscvRegister, read=True)
    target = Operand('target', str)
    syntax = Syntax(['c', '.', 'beqz', ' ', rn, ' ', target])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:2] = 0b01
        tokens[0][7:10] = self.rn.num - 8
        tokens[0][13:16] = 0b110
        return tokens[0].encode()

    def relocations(self):
        return [BcImm8Relocation(self.target)]


class CBnez(RiscvcInstruction):
    rn = Operand('rn', RiscvRegister, read=True)
    target = Operand('target', str)
    syntax = Syntax(['c', '.', 'bneqz', ' ', rn, ',', ' ', target])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:2] = 0b01
        tokens[0][7:10] = self.rn.num-8
        tokens[0][13:16] = 0b111
        return tokens[0].encode()

    def relocations(self):
        return [BcImm8Relocation(self.target)]


class CLw(RiscvcInstruction):
    rd = Operand('rd', RiscvRegister, write=True)
    rs1 = Operand('rs1', RiscvRegister, read=True)
    offset = Operand('offset', int)
    syntax = Syntax(['c', '.', 'lw', ' ', rd, ',', ' ', offset, '(', rs1, ')'])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:2] = 0b00
        tokens[0][2:5] = self.rd.num - 8
        tokens[0][5:6] = self.offset >> 6 & 1
        tokens[0][6:7] = self.offset >> 2 & 1
        tokens[0][7:10] = self.rs1.num - 8
        tokens[0][10:13] = self.offset >> 3 & 0x7
        tokens[0][13:16] = 0b010
        return tokens[0].encode()


class CSw(RiscvcInstruction):
    rs2 = Operand('rs2', RiscvRegister, read=True)
    rs1 = Operand('rs1', RiscvRegister, read=True)
    offset = Operand('offset', int)
    syntax = Syntax(
        ['c', '.', 'sw', ' ', rs2, ',', ' ', offset, '(', rs1, ')'])
    tokens = [RiscvcToken]

    def encode(self):
        tokens = self.get_tokens()
        tokens[0].op = 0b00
        tokens[0][2:5] = self.rs2.num-8
        tokens[0][5:6] = self.offset >> 6 & 1
        tokens[0][6:7] = self.offset >> 2 & 1
        tokens[0][7:10] = self.rs1.num - 8
        tokens[0][10:13] = self.offset >> 3 & 0x7
        tokens[0].funct3 = 0b110
        return tokens[0].encode()


class CLwsp(RiscvcInstruction):
    rd = Operand('rd', RiscvRegister, write=True)
    offset = Operand('offset', int)
    rs1 = Operand('rs1', RiscvRegister, read=True)
    syntax = Syntax(['c', '.', 'lwsp', ' ', rd, ',', offset, '(', rs1, ')'])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:2] = 0b10
        tokens[0][2:4] = self.offset >> 6 & 3
        tokens[0][4:7] = self.offset >> 2 & 7
        tokens[0][7:12] = self.rd.num
        tokens[0][12:13] = self.offset >> 5 & 1
        tokens[0][13:16] = 0b010
        return tokens[0].encode()


class CSwsp(RiscvcInstruction):
    rs2 = Operand('rs2', RiscvRegister, read=True)
    offset = Operand('offset', int)
    rs1 = Operand('rs1', RiscvRegister, read=True)
    syntax = Syntax(['c', '.', 'swsp', ' ', rs2, ',', offset, '(', rs1, ')'])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0].op = 0b10
        tokens[0][2:7] = self.rs2.num
        tokens[0][7:9] = self.offset >> 6 & 0x3
        tokens[0][9:13] = self.offset >> 2 & 0xF
        tokens[0].funct3 = 0b110
        return tokens[0].encode()


class CLi(RiscvcInstruction):
    rd = Operand('rd', RiscvRegister, write=True)
    imm = Operand('imm', int)
    syntax = Syntax(['c', '.', 'li', ' ', rd, ',', ' ', imm])
    patterns = {'op': 0b01, 'imm': imm, 'rd': rd, 'funct3': 0b010}


class CLui(RiscvcInstruction):
    rd = Operand('rd', RiscvRegister, write=True)
    imm = Operand('imm', int)
    syntax = Syntax(['c', '.', 'lui', ' ', rd, ',', ' ', imm])

    def encode(self):
        if self.imm < 0:
            imm6 = wrap_negative(self.imm >> 12, 6)
        else:
            imm6 = self.imm >> 12 & 0x3F
        tokens = self.get_tokens()
        tokens[0].op = 0b01
        tokens[0][2:7] = imm6 & 0x1F
        tokens[0][7:12] = self.rd.num
        tokens[0][12:13] = imm6 >> 5 & 1
        tokens[0][13:16] = 0b011
        return tokens[0].encode()


class Andv(PseudoRiscvInstruction):
    rd = Operand('rd', RiscvRegister, write=True)
    rn = Operand('rn', RiscvRegister, read=True)
    rm = Operand('rm', RiscvRegister, read=True)
    syntax = Syntax(['and', ' ', rd, ',', ' ', rn, ',', ' ', rm])

    def render(self):
        if self.rd.num in range(8, 16) and self.rn.num in range(8, 16) and \
                self.rm.num in range(8, 16) and \
                (self.rd.num == self.rn.num or self.rd.num == self.rm.num):
            yield CAnd(self.rd, self.rm)
        else:
            yield Andr(self.rd, self.rn, self.rm)


class Orv(PseudoRiscvInstruction):
    rd = Operand('rd', RiscvRegister, write=True)
    rn = Operand('rn', RiscvRegister, read=True)
    rm = Operand('rm', RiscvRegister, read=True)
    syntax = Syntax(['or', ' ', rd, ',', ' ', rn, ',', ' ', rm])

    def render(self):
        if self.rd.num in range(8, 16) and self.rn.num in range(8, 16) and \
                self.rm.num in range(8, 16) and \
                (self.rd.num == self.rn.num or self.rd.num == self.rm.num):
            yield COr(self.rd, self.rm)
        else:
            yield Orr(self.rd, self.rn, self.rm)


class Xorv(PseudoRiscvInstruction):
    rd = Operand('rd', RiscvRegister, write=True)
    rn = Operand('rn', RiscvRegister, read=True)
    rm = Operand('rm', RiscvRegister, read=True)
    syntax = Syntax(['xor', ' ', rd, ',', ' ', rn, ',', ' ', rm])

    def render(self):
        if self.rd.num in range(8, 16) and self.rn.num in range(8, 16) and \
                self.rm.num in range(8, 16) and \
                (self.rd.num == self.rn.num or self.rd.num == self.rm.num):
            yield CXor(self.rd, self.rm)
        else:
            yield Xorr(self.rd, self.rn, self.rm)


class Subv(PseudoRiscvInstruction):
    rd = Operand('rd', RiscvRegister, write=True)
    rn = Operand('rn', RiscvRegister, read=True)
    rm = Operand('rm', RiscvRegister, read=True)
    syntax = Syntax(['sub', ' ', rd, ',', ' ', rn, ',', ' ', rm])

    def render(self):
        if self.rd.num in range(8, 16) and self.rn.num in range(8, 16) and \
                self.rm.num in range(8, 16) and \
                (self.rd.num == self.rn.num):
            yield CSub(self.rd, self.rm)
        else:
            yield Subr(self.rd, self.rn, self.rm)


class Addiv(PseudoRiscvInstruction):
    rd = Operand('rd', RiscvRegister, write=True)
    rs1 = Operand('rs1', RiscvRegister, read=True)
    imm = Operand('imm', int)
    syntax = Syntax(['addi', ' ', rd, ',', ' ', rs1, ',', ' ', imm])

    def render(self):
        if self.rd.num == self.rs1.num and self.imm in range(-32, 32):
            yield CAddi(self.rd, self.rs1, self.imm)
        else:
            yield Addi(self.rd, self.rs1, self.imm)


class Slliv(PseudoRiscvInstruction):
    rd = Operand('rd', RiscvRegister, write=True)
    rs1 = Operand('rs1', RiscvRegister, read=True)
    imm = Operand('imm', int)
    syntax = Syntax(['slli', ' ', rd, ',', ' ', rs1, ',', ' ', imm])

    def render(self):
        if self.rd.num == self.rs1.num and self.imm < 16:
            yield CSlli(self.rd, self.rs1, self.imm)
        else:
            yield Slli(self.rd, self.rs1, self.imm)


class Srliv(PseudoRiscvInstruction):
    rd = Operand('rd', RiscvRegister, write=True)
    rs1 = Operand('rs1', RiscvRegister, read=True)
    imm = Operand('imm', int)
    syntax = Syntax(['srli', ' ', rd, ',', ' ', rs1, ',', ' ', imm])

    def render(self):
        if self.rd.num == self.rs1.num and self.rd.num in range(8, 16) and \
                self.imm < 16:
            yield CSrli(self.rd, self.rs1, self.imm)
        else:
            yield Srli(self.rd, self.rs1, self.imm)


class Lwv(PseudoRiscvInstruction):
    rd = Operand('rd', RiscvRegister, write=True)
    offset = Operand('offset', int)
    rs1 = Operand('rs1', RiscvRegister, read=True)
    syntax = Syntax(['lw', ' ', rd, ',', ' ', offset, '(',  rs1, ')'])

    def render(self):
        if self.rd.num in range(8, 16) and self.rs1.num in range(8, 16) and \
                self.offset in range(0, 128):
            yield CLw(self.rd, self.offset, self.rs1)
        elif self.rs1.num == 2 and self.offset >= 0 and self.offset < 256:
            yield CLwsp(self.rd, self.offset, self.rs1)
        else:
            yield Lw(self.rd, self.offset, self.rs1)


class Swv(PseudoRiscvInstruction):
    rs2 = Operand('rs2', RiscvRegister, read=True)
    offset = Operand('offset', int)
    rs1 = Operand('rs1', RiscvRegister, read=True)
    syntax = Syntax(['sw', ' ', rs2, ',', ' ', offset, '(',  rs1, ')'])

    def render(self):
        if (self.rs2.num <= 15) and (self.rs2.num >= 8) and \
                (self.rs1.num <= 15) and (self.rs1.num >= 8) and \
                (self.offset >= 0) and (self.offset < 128):
            yield CSw(self.rs2, self.offset, self.rs1)
        elif self.rs1.num == 2 and self.offset >= 0 and self.offset < 256:
            yield CSwsp(self.rs2, self.offset, self.rs1)
        else:
            yield Sw(self.rs2, self.offset, self.rs1)


class Beqv(PseudoRiscvInstruction):
    rn = Operand('rn', RiscvRegister, read=True)
    rm = Operand('rm', RiscvRegister, read=True)
    target = Operand('target', str)
    syntax = Syntax(['beq', ' ', rn, ',', ' ', rm, ' ', target])

    def render(self):
        if self.rn.num in range(8, 16):
            yield CBeqz(self.rn, self.target)
        else:
            yield Beq(self.rn, self.rm, self.target)


class Bnev(PseudoRiscvInstruction):
    rn = Operand('rn', RiscvRegister, read=True)
    rm = Operand('rm', RiscvRegister, read=True)
    target = Operand('target', str)
    syntax = Syntax(['bneq', ' ', rn, ',', ' ', rm, ' ', target])

    def render(self):
        if self.rn.num in range(8, 16):
            yield CBnez(self.rn, self.target)
        else:
            yield Bne(self.rn, self.rm, self.target)


# Instruction selection patterns:
@rvcisa.pattern(
    'reg', 'CONSTI32', size=1,
    condition=lambda t: t.value in range(-32, 32))
def pattern_consti32(context, tree):
    d = context.new_reg(RiscvRegister)
    c0 = tree.value
    assert isinstance(c0, int)
    assert c0 in range(-32, 32)
    context.emit(CLi(d, c0))
    return d


@rvcisa.pattern(
    'reg', 'CONSTI32', size=3, condition=lambda t: t.value < 0x20000)
def pattern_consti32_2(context, tree):
    d = context.new_reg(RiscvRegister)
    c0 = tree.value
    if (c0 & 0x800) != 0:
        c0 -= 0xFFFFF000
    context.emit(CLui(d, c0))
    context.emit(Addi(d, d, c0))
    return d


@rvcisa.pattern('reg', 'ANDI32(reg, reg)', size=1)
def pattern_andi32(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Andv(d, c0, c1))
    return d


@rvcisa.pattern('reg', 'ORI32(reg, reg)', size=1)
def pattern_ori32(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Orv(d, c0, c1))
    return d


@rvcisa.pattern('reg', 'XORI32(reg, reg)', size=1)
def pattern_xori32(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Xorv(d, c0, c1))
    return d


@rvcisa.pattern('reg', 'SUBI32(reg, reg)', size=1)
def pattern_subi32(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Subv(d, c0, c1))
    return d


@rvcisa.pattern(
    'reg', 'ADDI32(reg, CONSTI32)', size=1,
    condition=lambda t: t.children[1].value < 256)
def pattern_addi32_1(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[1].value
    context.emit(Addiv(d, c0, c1))
    return d


@rvcisa.pattern(
    'reg', 'ADDI32(CONSTI32, reg)', size=1,
    condition=lambda t: t.children[0].value < 256)
def pattern_addi32_2(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[0].value
    context.emit(Addiv(d, c0, c1))
    return d


@rvcisa.pattern(
    'reg', 'SHLI32(reg, CONSTI32)', size=1,
    condition=lambda t: t.children[1].value < 16)
def pattern_shli32_1_(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[1].value
    context.emit(Slliv(d, c0, c1))
    return d


@rvcisa.pattern(
    'reg', 'SHLI32(CONSTI32, reg)', size=1,
    condition=lambda t: t.children[0].value < 16)
def pattern_shli32_2(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[0].value
    context.emit(Slliv(d, c0, c1))
    return d


@rvcisa.pattern(
    'reg', 'SHRI32(reg, CONSTI32)', size=1,
    condition=lambda t: t.children[1].value < 16)
def pattern_shri32(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[1].value
    context.emit(Srliv(d, c0, c1))
    return d


@rvcisa.pattern(
    'reg', 'SHRI32(CONSTI32, reg)', size=1,
    condition=lambda t: t.children[0].value < 16)
def pattern_stri32_const(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[0].value
    context.emit(Srliv(d, c0, c1))
    return d


@rvcisa.pattern('reg', 'LDRI32(reg)', size=1)
def pattern_ldri32(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    context.emit(Lwv(d, 0, c0))
    return d


@rvcisa.pattern('reg', 'LDRI32(ADDI32(reg, CONSTI32))', size=1)
def pattern_ldri32_addi32(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[0].children[1].value
    assert isinstance(c1, int)
    context.emit(Lwv(d, c1, c0))
    return d


@rvcisa.pattern('stm', 'STRI32(reg, reg)', size=1)
def pattern_stri32(self, tree, c0, c1):
    self.emit(Swv(c1, 0, c0))


@rvcisa.pattern(
    'stm', 'STRI32(ADDI32(reg, CONSTI32), reg)', size=1,
    condition=lambda t: t.children[0].children[1].value < 256)
def pattern_stri32_addi32(context, tree, c0, c1):
    # TODO: something strange here: when enabeling this rule, programs
    # compile correctly...
    offset = tree.children[0].children[1].value
    context.emit(Swv(c1, offset, c0))


@rvcisa.pattern('stm', 'CJMP(reg, reg)', size=1)
def pattern_cjmp(context, tree, c0, c1):
    op, yes_label, no_label = tree.value
    opnames = {
        "<": Blt, ">": Bgt, "==": Beq, "!=": Bne,
        ">=": Bge, '<=': Bgt
        }
    Bop = opnames[op]
    if op == "<=":
        jmp_ins = B(yes_label.name, jumps=[yes_label])
        context.emit(Bop(c0, c1, yes_label.name, jumps=[no_label, jmp_ins]))
        context.emit(jmp_ins)
    else:
        jmp_ins = B(no_label.name, jumps=[no_label])
        context.emit(Bop(c0, c1, yes_label.name, jumps=[yes_label, jmp_ins]))
        context.emit(jmp_ins)
