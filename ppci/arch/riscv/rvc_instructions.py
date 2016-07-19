"""
    Definitions of Riscv instructions.
"""

# pylint: disable=no-member,invalid-name
from ...utils.bitfun import wrap_negative
from ..isa import Instruction, Isa, Syntax
from ..isa import register_argument, value_argument
from .registers import RiscvRegister
from ..token import Token, u16, bit_range
from .rvc_relocations import  apply_bc_imm11, apply_bc_imm8
from ..arch import ArtificialInstruction
from .instructions import Andr, Orr, Xorr, Subr, Addr, Addi, Slli, Srli, Lw, Sw, Blt, Bgt, Bge, B, Beq, Bne

# TODO: do not use ir stuff here!
from ...ir import i32


class RegisterSet(set):
    def __repr__(self):
        reg_names = sorted(str(r) for r in self)
        return ', '.join(reg_names)


rvcisa = Isa()

rvcisa.register_relocation(apply_bc_imm11)
rvcisa.register_relocation(apply_bc_imm8)



class RiscvcToken(Token):
    def __init__(self):
        super().__init__(16)

    def encode(self):
        return u16(self.bit_value)



# Instructions:

class RiscvcInstruction(Instruction):
    tokens = [RiscvcToken]
    isa = rvcisa


class PseudoRiscvInstruction(ArtificialInstruction):
    """ These instruction is used to switch between RV and RVC-encoding """
    pass
    

class OpcRegReg(RiscvcInstruction):
    """ c.sub rd, rn """
    def encode(self):
        self.token1[0:2] = 0b01
        self.token1[2:5] = self.rn.num-8
        self.token1[5:7] = self.func
        self.token1[7:10] = self.rd.num-8
        self.token1[10:16] = 0b100011
        return self.token1.encode()


def makec_regreg(mnemonic, func):
    rd = register_argument('rd', RiscvRegister, write=True)
    rn = register_argument('rn', RiscvRegister, read=True)
    syntax = Syntax([mnemonic, rd, ',', rn])
    members = {
        'syntax': syntax, 'rd': rd, 'rn': rn, 'func': func}
    return type(mnemonic + '_ins', (OpcRegReg,), members)

CSub = makec_regreg('c.sub', 0b00)
CXor = makec_regreg('c.xor', 0b01)
COr = makec_regreg('c.or', 0b10)
CAnd = makec_regreg('c.and', 0b11)

class CSlli(RiscvcInstruction):
    rd = register_argument('rd', RiscvRegister, write=True)
    rs = register_argument('rs', RiscvRegister, read=True)
    imm = register_argument('imm', int)
    syntax = Syntax(['c.slli', rd, ',', rs, ',', imm])
    def encode(self):
        self.token1[0:2] = 0b10
        self.token1[2:7] = self.imm & 0xF
        self.token1[7:12] = self.rd.num        
        self.token1[13:16] = 0b0000
        return self.token1.encode()

class CiBase(RiscvcInstruction):
    def encode(self):
        self.token1[0:2] = 0b01
        self.token1[2:7] = self.imm
        self.token1[7:10] = self.rd.num-8
        self.token1[10:12] = self.func
        self.token1[12:16] = 0b1000
        return self.token1.encode()

def makec_i(mnemonic, func):
    rd = register_argument('rd', RiscvRegister, write=True)
    rs = register_argument('rs', RiscvRegister, read=True)
    imm = register_argument('imm', int)
    syntax = Syntax([mnemonic, rd, ',', rs, ',', imm])
    members = {'syntax': syntax,'func':func, 'rd':rd, 'rs':rs, 'imm':imm}
    return type(mnemonic + '_ins', (CiBase,), members)

CSrli = makec_i('c.srli',0b00)
CSrai = makec_i('c.srai',0b01)
CAndi = makec_i('c.andi',0b10)

class CAddi(RiscvcInstruction):
    rd = register_argument('rd', RiscvRegister, write=True)
    imm = register_argument('imm', int)
    syntax = Syntax(['c.addi', rd, ',', rd, ',', imm])
    def encode(self):
        self.token1[0:2] = 0b01
        self.token1[2:7] = self.imm
        self.token1[7:12] = self.rd.num
        self.token1[12:16] = 0b0000
        return self.token1.encode()

class CNop(RiscvcInstruction):
    syntax = Syntax(['c.nop'])
    def encode(self):
        self.token1[0:2] = 0b01
        self.token1[2:16] = 0
        return self.token1.encode()

class CEbreak(RiscvcInstruction):
    syntax = Syntax(['c.ebreak'])
    def encode(self):
        self.token1[0:16] = 0b1001000000000010
        return self.token1.encode()
        
class CJal(RiscvcInstruction):
    target = register_argument('target', str)
    syntax = Syntax(['c.jal', target])
    def encode(self):
        self.token1[0:2] = 0b01
        self.token1[13:16] = 0b001
        return self.token1.encode()

    def relocations(self):
        return [(self.target, apply_bc_imm11)] 
        
class CJ(RiscvcInstruction):
    target = register_argument('target', str)
    syntax = Syntax(['c.j', target])
    def encode(self):
        self.token1[0:2] = 0b01
        self.token1[13:16] = 0b101
        return self.token1.encode()

    def relocations(self):
        return [(self.target, apply_bc_imm11)] 

class CJr(RiscvcInstruction):
    rs1 = register_argument('rs1', RiscvRegister, read=True)
    syntax = Syntax(['c.jr',rs1])
    def encode(self):
        self.token1[0:7] = 0b0000010
        self.token1[7:12] = self.rs1.num
        self.token1[12:16] = 0b1000
        return self.token1.encode()

class CJalr(RiscvcInstruction):
    rs1 = register_argument('rs1', RiscvRegister, read=True)
    syntax = Syntax(['c.jalr', rs1])
    def encode(self):
        self.token1[0:7] = 0b0000010
        self.token1[7:12] = self.rs1.num
        self.token1[12:16] = 0b1001
        return self.token1.encode()
    
class CBeqz(RiscvcInstruction):
    rn = register_argument('rn', RiscvRegister, read=True)
    target = register_argument('target', str)
    syntax = Syntax(['c.beqz', rn, target])
    def encode(self):
        self.token1[0:2] = 0b01
        self.token1[7:10] = self.rn.num-8
        self.token1[13:16] = 0b110
        return self.token1.encode()

    def relocations(self):
        return [(self.target, apply_bc_imm8)]

class CBnez(RiscvcInstruction):
    rn = register_argument('rn', RiscvRegister, read=True)
    target = register_argument('target', str)
    syntax = Syntax(['c.bneqz', rn, ',', target])
    def encode(self):
        self.token1[0:2] = 0b01
        self.token1[7:10] = self.rn.num-8
        self.token1[13:16] = 0b111
        return self.token1.encode()

    def relocations(self):
        return [(self.target, apply_bc_imm8)]

class CLw(RiscvcInstruction):
    rd = register_argument('rd', RiscvRegister, write=True)
    rs1 = register_argument('rs1', RiscvRegister, read=True)
    offset = register_argument('offset', int)
    syntax = Syntax(['c.lw', rd, ',',  offset, '(', rs1, ')'])
    def encode(self):
        self.token1[0:2]=0b00
        self.token1[2:5]=self.rd.num-8
        self.token1[5:6]=self.offset>>6&1
        self.token1[6:7]=self.offset>>2&1
        self.token1[7:10]=self.rs1.num-8
        self.token1[10:13]=self.offset>>3&0x7
        self.token1[13:16]=0b010
        return self.token1.encode()

class CSw(RiscvcInstruction):
    rs2 = register_argument('rs2', RiscvRegister, read=True)
    rs1 = register_argument('rs1', RiscvRegister, read=True)
    offset = register_argument('offset', int)
    syntax = Syntax(['c.sw', rs2, ',', offset, '(', rs1, ')'])
    def encode(self):
        self.token1[0:2]=0b00
        self.token1[2:5]=self.rs2.num-8
        self.token1[5:6]=self.offset>>6&1
        self.token1[6:7]=self.offset>>2&1
        self.token1[7:10]=self.rs1.num-8
        self.token1[10:13]=self.offset>>3&0x7
        self.token1[13:16]=0b110
        return self.token1.encode()

class CLwsp(RiscvcInstruction):
    rd = register_argument('rd', RiscvRegister, write=True)
    offset = register_argument('offset', int)
    rs1 = register_argument('rs1', RiscvRegister, read=True)
    syntax = Syntax(['c.lwsp', rd, ',', offset,'(',rs1,')'])
    def encode(self):
        self.token1[0:2]=0b10
        self.token1[2:4]=self.offset>>6&3
        self.token1[4:7]=self.offset>>2&7
        self.token1[7:12]=self.rd.num
        self.token1[12:13]=self.offset>>5&1
        self.token1[13:16]=0b010
        return self.token1.encode()
        
class CSwsp(RiscvcInstruction):
    rs2 = register_argument('rs2', RiscvRegister, read=True)
    offset = register_argument('offset', int)
    rs1 = register_argument('rs1', RiscvRegister, read=True)
    syntax = Syntax(['c.swsp', rs2, ',', offset,'(',rs1,')'])
    def encode(self):
        self.token1[0:2]=0b10
        self.token1[2:7]=self.rs2.num
        self.token1[7:9]=self.offset>>6&0x3
        self.token1[9:13]=self.offset>>2&0xF
        self.token1[13:16]=0b110
        return self.token1.encode()

class CLi(RiscvcInstruction):
    rd = register_argument('rd', RiscvRegister, write=True)
    imm = register_argument('imm', int)
    syntax = Syntax(['c.li', rd, ',', imm])
    def encode(self):
        self.token1[0:2] = 0b01
        self.token1[2:7] = self.imm & 0x1F
        self.token1[7:12] = self.rd.num
        self.token1[12:13] = self.imm>>5&1
        self.token1[13:16] = 0b010
        return self.token1.encode()

class CLui(RiscvcInstruction):
    rd = register_argument('rd', RiscvRegister, write=True)
    imm = register_argument('imm', int)
    syntax = Syntax(['c.lui', rd, ',', imm])
    def encode(self):
        if self.imm<0:
            imm6 = wrap_negative(self.imm>>12,6)
        else:
            imm6 = self.imm>>12&6
        self.token1[0:2] = 0b01
        self.token1[2:7] = imm6&0x1F
        self.token1[7:12] = self.rd.num
        self.token1[12:13] = imm6>>5&1
        self.token1[13:16] = 0b011
        return self.token1.encode()
    
class Andv(PseudoRiscvInstruction):   
    rd = register_argument('rd', RiscvRegister, write=True)
    rn = register_argument('rn', RiscvRegister, read=True)
    rm = register_argument('rm', RiscvRegister, read=True)
    syntax = Syntax(['and', rd, ',', rn, ',', rm])
    def render(self):
        if (self.rd.num>=8 and self.rd.num<=15 and self.rn.num>=8 and \
            self.rn.num<=15 and self.rm.num>=8 and self.rm.num<=15 and \
            (self.rd.num==self.rn.num or self.rd.num==self.rm.num )):
            yield CAnd( self.rd, self.rm)
        else:
            yield Andr( self.rd, self.rn, self.rm)

class Orv(PseudoRiscvInstruction):   
    rd = register_argument('rd', RiscvRegister, write=True)
    rn = register_argument('rn', RiscvRegister, read=True)
    rm = register_argument('rm', RiscvRegister, read=True)
    syntax = Syntax(['or', rd, ',', rn, ',', rm])
    def render(self):
        if (self.rd.num>=8 and self.rd.num<=15 and self.rn.num>=8 and \
            self.rn.num<=15 and self.rm.num>=8 and self.rm.num<=15 and \
            (self.rd.num==self.rn.num or self.rd.num==self.rm.num )):
            yield COr( self.rd, self.rm)
        else:
            yield Orr( self.rd, self.rn, self.rm)
         
class Xorv(PseudoRiscvInstruction):   
    rd = register_argument('rd', RiscvRegister, write=True)
    rn = register_argument('rn', RiscvRegister, read=True)
    rm = register_argument('rm', RiscvRegister, read=True)
    syntax = Syntax(['xor', rd, ',', rn, ',', rm])
    def render(self):
        if (self.rd.num>=8 and self.rd.num<=15 and self.rn.num>=8 and \
            self.rn.num<=15 and self.rm.num>=8 and self.rm.num<=15 and \
            (self.rd.num==self.rn.num or self.rd.num==self.rm.num )):
            yield CXor( self.rd, self.rm)
        else:
            yield Xorr( self.rd, self.rn, self.rm)

class Subv(PseudoRiscvInstruction):   
    rd = register_argument('rd', RiscvRegister, write=True)
    rn = register_argument('rn', RiscvRegister, read=True)
    rm = register_argument('rm', RiscvRegister, read=True)
    syntax = Syntax(['sub', rd, ',', rn, ',', rm])
    def render(self):
        if (self.rd.num>=8 and self.rd.num<=15 and self.rn.num>=8 and \
            self.rn.num<=15 and self.rm.num>=8 and self.rm.num<=15 and \
            (self.rd.num==self.rn.num)):
            yield CSub( self.rd, self.rm)
        else:
            yield Subr( self.rd, self.rn, self.rm)

class Addiv(PseudoRiscvInstruction):   
    rd = register_argument('rd', RiscvRegister, write=True)
    rs1 = register_argument('rs1', RiscvRegister, read=True)
    imm = register_argument('imm', int)
    syntax = Syntax(['addi', rd, ',', rs1, ',', imm])
    def render(self):
        if ((self.rd.num==self.rs1.num) and (self.imm<31) and (self.imm>=-32) ):
            yield CAddi( self.rd, self.rs1, self.imm)
        else:
            yield Addi( self.rd, self.rs1, self.imm)

class Slliv(PseudoRiscvInstruction):   
    rd = register_argument('rd', RiscvRegister, write=True)
    rs1 = register_argument('rs1', RiscvRegister, read=True)
    imm = register_argument('imm', int)
    syntax = Syntax(['slli', rd, ',', rs1, ',', imm])
    def render(self):
        if ((self.rd.num==self.rs1.num) and (self.imm<16)):
            yield CSlli( self.rd, self.rs1, self.imm)
        else:
            yield Slli( self.rd, self.rs1, self.imm)

class Srliv(PseudoRiscvInstruction):   
    rd = register_argument('rd', RiscvRegister, write=True)
    rs1 = register_argument('rs1', RiscvRegister, read=True)
    imm = register_argument('imm', int)
    syntax = Syntax(['srli', rd, ',', rs1, ',', imm])
    def render(self):
        if ((self.rd.num==self.rs1.num) and (self.rd.num<=15) and \
            (self.rd.num>=8) and (self.imm<16)):
            yield CSrli( self.rd, self.rs1, self.imm)
        else:
            yield Srli( self.rd, self.rs1, self.imm)

class Lwv(PseudoRiscvInstruction):   
    rd = register_argument('rd', RiscvRegister, write=True)
    offset = register_argument('offset', int)
    rs1 = register_argument('rs1', RiscvRegister, read=True)
    syntax = Syntax(['lw', rd, ',', offset, '(',  rs1, ')']) 
    def render(self):
        if ((self.rd.num<=15) and (self.rd.num>=8) and \
            (self.rs1.num<=15) and (self.rs1.num>=8) and \
            (self.offset>=0) and (self.offset<128)):
            yield CLw( self.rd, self.offset, self.rs1)
        elif ((self.rs1.num==2) and (self.offset>=0) and (self.offset<256)):
            yield CLwsp( self.rd, self.offset, self.rs1)
        else:
            yield Lw( self.rd, self.offset, self.rs1)

class Swv(PseudoRiscvInstruction):   
    rs2 = register_argument('rs2', RiscvRegister, read=True)
    offset = register_argument('offset', int)
    rs1 = register_argument('rs1', RiscvRegister, read=True)
    syntax = Syntax(['sw', rs2, ',', offset, '(',  rs1, ')']) 
    def render(self):
        if ((self.rs2.num<=15) and (self.rs2.num>=8) and \
            (self.rs1.num<=15) and (self.rs1.num>=8) and \
            (self.offset>=0) and (self.offset<128)):
            yield CSw( self.rs2, self.offset, self.rs1)
        elif ((self.rs1.num==2) and (self.offset>=0) and (self.offset<256)):
            yield CSwsp( self.rs2, self.offset, self.rs1)
        else:
            yield Sw( self.rs2, self.offset, self.rs1)

class Beqv(PseudoRiscvInstruction):   
    rn = register_argument('rn', RiscvRegister, read=True)
    rm = register_argument('rm', RiscvRegister, read=True)
    target = register_argument('target', str)
    syntax = Syntax(['beq', rn, ',',rm, target])
    def render(self):
        if ((self.rn.num<=15) and (self.rn.num>=8)): 
            yield CBeqz( self.rn, self.target)
        else:
            yield Beq( self.rn, self.rm, self.target)

class Bnev(PseudoRiscvInstruction):   
    rn = register_argument('rn', RiscvRegister, read=True)
    rm = register_argument('rm', RiscvRegister, read=True)
    target = register_argument('target', str)
    syntax = Syntax(['bneq', rn, ',',rm, target])
    def render(self):
        if ((self.rn.num<=15) and (self.rn.num>=8)):
            yield CBnez( self.rn, self.target)
        else:
            yield Bne( self.rn, self.rm, self.target)

            
# Instruction selection patterns:
@rvcisa.pattern('reg', 'CONSTI32', size=1, condition=lambda t: t.value < 64 )
def _(context, tree):
    d = context.new_reg(RiscvRegister)
    c0 = tree.value
    assert isinstance(c0, int)
    assert c0 < 64 and c0 >= 0
    context.emit(CLi(d, c0))
    return d

@rvcisa.pattern('reg', 'CONSTI32', size=3, condition=lambda t: t.value < 0x20000)
def _(context, tree):
    d = context.new_reg(RiscvRegister)
    c0 = tree.value
    context.emit(CLui(d, c0))
    context.emit(Addi(d, d, c0))
    return d

@rvcisa.pattern('reg', 'ANDI32(reg, reg)', size=1)
def _(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Andv(d, c0, c1))
    return d

@rvcisa.pattern('reg', 'ORI32(reg, reg)', size=1)
def _(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Orv(d, c0, c1))
    return d
    
@rvcisa.pattern('reg', 'XORI32(reg, reg)', size=1)
def _(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Xorv(d, c0, c1))
    return d

@rvcisa.pattern('reg', 'SUBI32(reg, reg)', size=1)
def _(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Subv(d, c0, c1))
    return d

@rvcisa.pattern(
    'reg', 'ADDI32(reg, CONSTI32)', size=1,
    condition=lambda t: t.children[1].value < 256)
def _(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[1].value
    context.emit(Addiv(d, c0, c1))
    return d


@rvcisa.pattern(
    'reg', 'ADDI32(CONSTI32, reg)', size=1,
    condition=lambda t: t.children[0].value < 256)
def _(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[0].value
    context.emit(Addiv(d, c0, c1))
    return d

@rvcisa.pattern('reg', 'SHLI32(reg, CONSTI32)', size=1, condition=lambda t: t.children[1].value< 16)
def _(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[1].value
    context.emit(Slliv(d, c0, c1))
    return d

@rvcisa.pattern('reg', 'SHLI32(CONSTI32, reg)', size=1, condition=lambda t: t.children[0].value< 16)
def _(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[0].value
    context.emit(Slliv(d, c0, c1))
    return d

@rvcisa.pattern('reg', 'SHRI32(reg, CONSTI32)', size=1, condition=lambda t: t.children[1].value< 16)
def _(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[1].value
    context.emit(Srliv(d, c0, c1))
    return d

@rvcisa.pattern('reg', 'SHRI32(CONSTI32, reg)', size=1, condition=lambda t: t.children[0].value< 16)
def _(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[0].value
    context.emit(Srliv(d, c0, c1))
    return d

@rvcisa.pattern('reg', 'LDRI32(reg)', size=1)
def _(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    context.emit(Lwv(d, 0, c0))
    return d

@rvcisa.pattern('reg', 'LDRI32(ADDI32(reg, CONSTI32))', size=1)
def _(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[0].children[1].value
    assert isinstance(c1, int)
    context.emit(Lwv(d, c1, c0))
    return d


@rvcisa.pattern('stm', 'STRI32(reg, reg)', size=1)
def _(self, tree, c0, c1):
    self.emit(Swv(c1, 0, c0))

@rvcisa.pattern('stm', 'STRI32(ADDI32(reg, CONSTI32), reg)', size=1, \
condition=lambda t: t.children[0].children[1].value < 256)
def _(context, tree, c0, c1):
    # TODO: something strange here: when enabeling this rule, programs
    # compile correctly...
    offset = tree.children[0].children[1].value
    context.emit(Swv(c1, offset, c0))

@rvcisa.pattern('stm', 'CJMP(reg, reg)', size=1)
def _(context, tree, c0, c1):
    op, yes_label, no_label = tree.value
    opnames = {"<": Blt, ">": Bgt, "==": Beqv, "!=": Bnev, ">=": Bge}
    Bop = opnames[op]
    jmp_ins = B(no_label.name, jumps=[no_label])
    context.emit(Bop(c0, c1, yes_label.name, jumps=[yes_label, jmp_ins]))
    context.emit(jmp_ins)
