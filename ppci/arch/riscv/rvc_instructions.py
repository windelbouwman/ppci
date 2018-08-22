""" Definitions of Riscv instructions. """

from ..isa import Isa
from ..encoding import Instruction, Syntax, Operand
from .registers import RiscvRegister
from .tokens import RiscvToken, RiscvcToken
from .rvc_relocations import BcImm11Relocation, BcImm8Relocation
from .rvc_relocations import CBImm11Relocation, CBlImm11Relocation, CRel
from ..generic_instructions import ArtificialInstruction
from .instructions import Andr, Orr, Xorr, Subr, Addi, Slli, Srli
from .instructions import Lw, Sw, Blt, Bgt, Bge, B, Beq, Bne, Ble, Blr, Bgtu, Bltu, Bgeu, Bleu
import logging

class RegisterSet(set):
    def __repr__(self):
        reg_names = sorted(str(r) for r in self)
        return ', '.join(reg_names)


rvcisa = Isa()

rvcisa.register_relocation(CRel)
rvcisa.register_relocation(BcImm11Relocation)
rvcisa.register_relocation(BcImm8Relocation)
rvcisa.register_relocation(CBImm11Relocation)
rvcisa.register_relocation(CBlImm11Relocation)


class RiscvcInstruction(Instruction):
    tokens = [RiscvcToken]
    isa = rvcisa

class RiscvInstruction(Instruction):
    tokens = [RiscvToken]
    isa = rvcisa 


class PseudoRiscvInstruction(ArtificialInstruction):
    """ These instruction is used to switch between RV and RVC-encoding """
    pass


class OpcRegReg(RiscvcInstruction):
    """ c.sub rd, rn """

    def encode(self):
        tokens = self.get_tokens()
        tokens[0].op = 0b01
        tokens[0][2:5] = self.rn.num - 8
        tokens[0][5:7] = self.func
        tokens[0][7:10] = self.rd.num - 8
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
        tokens[0][7:10] = self.rd.num - 8
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

class CMovr(RiscvcInstruction):    
    rd = Operand('rd', RiscvRegister, write=True)
    rm = Operand('rm', RiscvRegister, read=True)
    syntax = Syntax(['c', '.','mv', ' ', rd, ',', ' ', rm])
    
    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:2] = 0b10
        tokens[0][2:7] = self.rm.num
        tokens[0][7:12] = self.rd.num
        tokens[0][12:16] = 0b1000
        return tokens[0].encode()

        
class CBl(RiscvInstruction):
    target = Operand('target', str)
    rd = Operand('rd', RiscvRegister, write=True)
    syntax = Syntax(['jal', ' ', rd, ',', ' ', target])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:7] = 0b1101111
        tokens[0][7:12] = self.rd.num
        return tokens[0].encode()

    def relocations(self):
        return [CBlImm11Relocation(self.target)] 

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


class CB(RiscvInstruction):
    target = Operand('target', str)
    syntax = Syntax(['j', ' ', target])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:7] = 0b1101111
        tokens[0][7:12] = 0
        return tokens[0].encode()

    def relocations(self):
        return [CBImm11Relocation(self.target)] 
        
        
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

class CBlr(PseudoRiscvInstruction):
    rd = Operand('rd', RiscvRegister, write=True)
    rs1 = Operand('rs1', RiscvRegister, read=True)
    offset = Operand('offset', int)
    syntax = Syntax(['jalr', ' ', rd, ',', rs1, ',', ' ', offset]) 
    
    def render(self):
        if self.rd.num == 1 and not self.offset:                        
            yield CJalr(self.rs1)
        else:
            yield Blr(self.rd, self.rs1, self.offset)
    

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
    syntax = Syntax(['c', '.', 'beqz', ' ', rn, ',', ' ', target])
    patterns = {'op': 0b01, 'funct3': 0b110}

    def encode(self):
        tokens = self.get_tokens()
        self.set_all_patterns(tokens)
        tokens[0][7:10] = self.rn.num - 8
        return tokens[0].encode()

    def relocations(self):
        return [BcImm8Relocation(self.target)]


class CBnez(RiscvcInstruction):
    rn = Operand('rn', RiscvRegister, read=True)
    target = Operand('target', str)
    syntax = Syntax(['c', '.', 'bneqz', ' ', rn, ',', ' ', target])
    patterns = {'op': 0b01, 'funct3': 0b111}

    def encode(self):
        tokens = self.get_tokens()
        self.set_all_patterns(tokens)
        tokens[0][7:10] = self.rn.num - 8
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
        tokens[0][2:5] = self.rs2.num - 8
        tokens[0][5:6] = self.offset >> 6 & 1
        tokens[0][6:7] = self.offset >> 2 & 1
        tokens[0][7:10] = self.rs1.num - 8
        tokens[0][10:13] = self.offset >> 3 & 0x7
        tokens[0].funct3 = 0b110
        return tokens[0].encode()


class CLwsp(RiscvcInstruction):
    rd = Operand('rd', RiscvRegister, write=True)
    offset = Operand('offset', int)
    #rs1 = Operand('rs1', RiscvRegister, read=True)
    syntax = Syntax(['c', '.', 'lwsp', ' ', rd, ',', offset, '(', 'x2', ')'])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:2] = 0b10
        tokens[0][2:4] = self.offset >> 6 & 3
        tokens[0][4:7] = self.offset >> 2 & 7
        tokens[0][7:12] = self.rd.num
        tokens[0][12:13] = self.offset >> 5 & 1
        tokens[0][13:16] = 0b010
        return tokens[0].encode()

class CAddi4spn(RiscvcInstruction): 
    rd = Operand('rd', RiscvRegister, write=True)
    imm = Operand('imm', int)
    syntax = Syntax(['c', '.', 'addi4spn', ' ', rd,  ' ', imm])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:2] = 0b00
        tokens[0][2:5] = self.rd.num - 8
        tokens[0][5:6] = self.imm >> 3 & 1        
        tokens[0][6:7] = self.imm >> 2 & 1 
        tokens[0][7:11] = self.imm >> 6 & 0xf
        tokens[0][11:13] = self.imm >> 4 & 0x3
        tokens[0][13:16] = 0b000
        return tokens[0].encode()
        
class CAddi16sp(RiscvcInstruction):    
    imm = Operand('imm', int)
    syntax = Syntax(['c', '.', 'addi16sp', ' ', imm])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:2] = 0b01
        tokens[0][2:3] = self.imm >> 5 & 1
        tokens[0][3:5] = self.imm >> 7 & 3        
        tokens[0][5:6] = self.imm >> 6 & 1
        tokens[0][6:7] = self.imm >> 4 & 1
        tokens[0][7:12] = 2
        tokens[0][12:13] = self.imm >> 9 & 1
        tokens[0][13:16] = 0b011
        return tokens[0].encode()

class CSwsp(RiscvcInstruction):
    rs2 = Operand('rs2', RiscvRegister, read=True)
    offset = Operand('offset', int)
    #rs1 = Operand('rs1', RiscvRegister, read=True)
    syntax = Syntax(['c', '.', 'swsp', ' ', rs2, ',', offset, '(', 'x2', ')'])

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
        imm6 = self.imm & 0x3f
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
    syntax = Syntax(['lw', ' ', rd, ',', ' ', offset, '(', rs1, ')'])

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
    syntax = Syntax(['sw', ' ', rs2, ',', ' ', offset, '(', rs1, ')'])

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
        c0 += 0x1000
    context.emit(CLui(d, c0 >> 12))
    context.emit(Addi(d, d, c0 & 0xfff))
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

@rvcisa.pattern('reg', 'LDRU32(mem)', size=1)
@rvcisa.pattern('reg', 'LDRI32(mem)', size=1)
def pattern_ldri32(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    base_reg, offset = c0 
    context.emit(Lwv(d, offset, base_reg))
    return d


@rvcisa.pattern('reg', 'LDRI32(ADDI32(reg, CONSTI32))', size=1)
def pattern_ldri32_addi32(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[0].children[1].value
    assert isinstance(c1, int)
    context.emit(Lwv(d, c1, c0))
    return d

@rvcisa.pattern('stm', 'STRU32(mem, reg)', size=1)
@rvcisa.pattern('stm', 'STRI32(mem, reg)', size=1)
def pattern_stri32(self, tree, c0, c1):
    base_reg, offset = c0 
    self.emit(Swv(c1, offset, base_reg))


@rvcisa.pattern(
    'stm', 'STRI32(ADDI32(reg, CONSTI32), reg)', size=1,
    condition=lambda t: t.children[0].children[1].value < 256)
def pattern_stri32_addi32(context, tree, c0, c1):
    # TODO: something strange here: when enabeling this rule, programs
    # compile correctly...
    offset = tree.children[0].children[1].value
    context.emit(Swv(c1, offset, c0))


@rvcisa.pattern('stm', 'CJMPI32(reg, reg)', size=2)
@rvcisa.pattern('stm', 'CJMPI16(reg, reg)', size=2)
@rvcisa.pattern('stm', 'CJMPI8(reg, reg)', size=2)
def pattern_cjmp(context, tree, c0, c1):
    op, yes_label, no_label = tree.value
    opnames = {"<": Blt, ">": Bgt, "==": Beq, "!=": Bne, ">=": Bge, "<=": Ble}
    Bop = opnames[op]
    jmp_ins = CB(no_label.name, jumps=[no_label])
    context.emit(Bop(c0, c1, yes_label.name, jumps=[yes_label, jmp_ins]))
    context.emit(jmp_ins)

@rvcisa.pattern('stm', 'CJMPU8(reg, reg)', size=2)
@rvcisa.pattern('stm', 'CJMPU16(reg, reg)', size=2)
@rvcisa.pattern('stm', 'CJMPU32(reg, reg)', size=2)
def pattern_cjmpu(context, tree, c0, c1):
    op, yes_label, no_label = tree.value
    opnames = {
        "<": Bltu, ">": Bgtu, "==": Beq, "!=": Bne, ">=": Bgeu, "<=": Bleu
    }
    Bop = opnames[op]
    jmp_ins = CB(no_label.name, jumps=[no_label])
    context.emit(Bop(c0, c1, yes_label.name, jumps=[yes_label, jmp_ins]))
    context.emit(jmp_ins) 
    
    
@rvcisa.pattern('stm', 'JMP', size=2)
def pattern_jmp(context, tree):
    tgt = tree.value
    context.emit(CB(tgt.name, jumps=[tgt]))    
    
@rvcisa.postlink
def opt(cls, dst):
    logger = logging.getLogger('linker')
    lst = dst.arch.isa.relocation_map['c_base'].l
    s = ", ".join(format(x, '08x') for x in lst)
    logger.debug('Relocation list: %s\n' %s)
    lst.append(-1)
    
    def countdiff(adrdst, adrofs):
        indofs = 0
        while lst[indofs]>=0 and adrofs > lst[indofs]:
            indofs += 1
        inddst = 0
        while lst[inddst]>=0 and adrdst > lst[inddst]:
            inddst += 1
        return inddst - indofs
    
    def getsection(adr, image):
        if adr>=imageadr and adr<=imageadr+imagesize:
            for section in image.sections:
                if adr>=sectionadr[section.name] and \
                adr<=sectionadr[section.name]+sectionsize[section.name]:
                    return section
        else:
            return False
    
    for image in dst.images:  
        sectionnames = []
        sectionadr = {}
        sectionsize = {}
        imagesize = image.size
        imageadr = image.address
        for s in image.sections:
            sectionnames.append(s.name)
            sectionadr[s.name] = s.address
            sectionsize[s.name] = s.size
        symbols = []
        relocs = []
        
        for s in dst.symbols:
            if s.section in sectionnames:
                section = dst.get_section(s.section)
                symbols.append((s, s.value + section.address))
        symbols.sort(key=lambda x: x[1])
        
        for r in dst.relocations:
            if r.section in sectionnames:
                 section = dst.get_section(r.section)
                 relocs.append((r, r.offset + section.address))
        relocs.sort(key=lambda x: x[1])
           
        
        for se in image.sections:
            delta = countdiff(se.address, image.address)
            logger.debug('RVC-sectororchanging %s at %08x with -%08x to %08x' %(se.name, se.address, 2*delta, se.address-2*delta))
            se.address -= 2*delta
        
        for s in symbols:
            sym = s[0]
            delta = countdiff(s[1], sectionadr[sym.section])
            logger.debug('RVC-symbolchanging %s at %08x with -%08x to %08x' %(sym.name, sym.value, 2*delta, sym.value-2*delta))
            sym.value -= 2*delta
            
        
        for r in relocs:
            reloc = r[0]
            delta = countdiff(r[1], sectionadr[reloc.section])
            logger.debug('RVC-relocationchanging %s at %08x with -%08x to %08x' %(reloc.symbol_name, r[1], 2*delta, r[1]-2*delta))
            reloc.offset -= delta*2
        
        lst2 = lst[:-1]
        for (i,absadr) in enumerate(lst2):
            section = getsection(absadr, image)
            if section:
                adr = absadr - section.address + 2 - i*2
                section.data.pop(adr)
                section.data.pop(adr)
    
    
    cls.do_relocations(dst, opt=True)
    dst.arch.isa.relocation_map['c_base'].l = []
    

