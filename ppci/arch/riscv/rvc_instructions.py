"""
    Definitions of Riscv instructions.
"""

# pylint: disable=no-member,invalid-name

from ..isa import Instruction, Isa, Syntax
from ..isa import register_argument, value_argument
from .registers import RiscvRegister
from ..token import Token, u16, bit_range
from .rvc_relocations import  apply_bc_imm11, apply_bc_imm8


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


  

class OpcRegReg(RiscvcInstruction):
    """ c.sub rd, rn """
    def encode(self):
        self.token1[0:2] = 0b01
        self.token1[2:5] = self.rn.num
        self.token1[5:7] = self.func
        self.token1[7:10] = self.rd.num
        self.token1[10:16] = 0b100011
        return self.token1.encode()


def makec_regreg(mnemonic, func):
    rd = register_argument('rd', RiscvRegister, write=True)
    rn = register_argument('rn', RiscvRegister, read=True)
    syntax = Syntax([mnemonic, rd, ',', rn])
    members = {
        'syntax': syntax, 'rd': rd, 'rn': rn, 'func': func}
    return type(mnemonic + '_ins', (OpcRegReg,), members)

Csub = makec_regreg('c.sub', 0b00)
Cxor = makec_regreg('c.xor', 0b01)
Cor = makec_regreg('c.or', 0b10)
Cand = makec_regreg('c.and', 0b11)


class CiBase(RiscvcInstruction):
    def encode(self):
        self.token1[0:2] = 0b01
        self.token1[2:7] = self.imm
        self.token1[7:10] = self.rd.num
        self.token1[10:12] = self.func
        self.token1[12:16] = 0b1000
        return self.token1.encode()

def makec_i(mnemonic, func):
    rd = register_argument('rd', RiscvRegister, write=True)
    imm = register_argument('imm', int)
    syntax = Syntax([mnemonic, rd, ',', rd, ',', imm])
    members = {'syntax': syntax,'func':func, 'rd':rd, 'imm':imm}
    return type(mnemonic + '_ins', (CiBase,), members)

Csrli = makec_i('c.srli',0b00)
Csrai = makec_i('c.srai',0b01)
Candi = makec_i('c.andi',0b10)

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
    syntax = Syntax(['c.jr', rs1])
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
    syntax = Syntax(['c.beqz', rn, ',', target])
    def encode(self):
        self.token1[0:7] = 0b1100011
        self.token1[13:16] = 0b110
        return self.token1.encode()

    def relocations(self):
        return [(self.target, apply_bc_imm8)]

class CBnez(RiscvcInstruction):
    rn = register_argument('rn', RiscvRegister, read=True)
    target = register_argument('target', str)
    syntax = Syntax(['c.bneqz', rn, ',', target])
    def encode(self):
        self.token1[0:7] = 0b1100011
        self.token1[13:16] = 0b111
        return self.token1.encode()

    def relocations(self):
        return [(self.target, apply_bc_imm8)]

class CLw(RiscvcInstruction):
    rd = register_argument('rd', RiscvRegister, write=True)
    rs1 = register_argument('rs1', RiscvRegister, read=True)
    offset = register_argument('offset', int)
    syntax = Syntax(['c.lw', rd,',',rs1,',',offset])
    def encode(self):
        self.token1[0:2]=0b00
        self.token1[2:5]=self.rd.num
        self.token1[5:6]=self.offset>>6&1
        self.token1[6:7]=self.offset>>2&1
        self.token1[7:10]=self.rs1.num
        self.token1[10:13]=self.offset>>3&0x7
        self.token1[13:16]=0b010
        return self.token1.encode()

class CSw(RiscvcInstruction):
    rs2 = register_argument('rs2', RiscvRegister, read=True)
    rs1 = register_argument('rs1', RiscvRegister, read=True)
    offset = register_argument('offset', int)
    syntax = Syntax(['c.sw', rs2,',',rs1,',',offset])
    def encode(self):
        self.token1[0:2]=0b00
        self.token1[2:5]=self.rs2.num
        self.token1[5:6]=self.offset>>6&1
        self.token1[6:7]=self.offset>>2&1
        self.token1[7:10]=self.rs1.num
        self.token1[10:13]=self.offset>>3&0x7
        self.token1[13:16]=0b110
        return self.token1.encode()

class CLwsp(RiscvcInstruction):
    rd = register_argument('rd', RiscvRegister, write=True)
    offset = register_argument('offset', int)
    syntax = Syntax(['c.lwsp', rd, ',', offset])
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
    syntax = Syntax(['c.swsp', rs2, ',', offset])
    def encode(self):
        self.token1[0:2]=0b10
        self.token1[2:7]=self.rs2.num
        self.token1[7:9]=self.offset>>6&0x3
        self.token1[9:13]=self.offset>>2&0xF
        self.token1[13:16]=0b110
        return self.token1.encode()
    
    
# Instruction selection patterns:



