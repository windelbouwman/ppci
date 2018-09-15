""" Definitions of Riscv instructions. """

from ..isa import Isa
from ..encoding import Instruction, Syntax, Operand
from .registers import RiscvFRegister, RiscvRegister, F1, F2
from .tokens import RiscvToken
from .instructions import call_internal2, call_internal1


class RegisterSet(set):
    def __repr__(self):
        reg_names = sorted(str(r) for r in self)
        return ', '.join(reg_names)


rvfisa = Isa()


class RiscvInstruction(Instruction):
    tokens = [RiscvToken]
    isa = rvfisa 



def make_fregfregfreg(mnemonic, rounding, func):
    rd = Operand('rd', RiscvFRegister, write=True)
    rn = Operand('rn', RiscvFRegister, read=True)
    rm = Operand('rm', RiscvFRegister, read=True)
    syntax = Syntax([mnemonic, '.','s', ' ', rd, ',', ' ', rn, ',', ' ', rm])
    tokens = [RiscvToken]
    patterns = {
        'opcode': 0b1010011, 'rd': rd, 'funct3': rounding,
        'rs1': rn, 'rs2': rm, 'funct7': func} 
    members = {
        'syntax': syntax, 'rd': rd, 'rn': rn, 'rm': rm,
        'patterns': patterns, 'tokens': tokens, 
        'rounding':rounding, 'func': func}
    return type(mnemonic + '_ins', (RiscvInstruction,), members)


FAdd = make_fregfregfreg('fadd', 0b111, 0b0000000)
FSub = make_fregfregfreg('fsub', 0b111, 0b0000100)
FMul = make_fregfregfreg('fmul', 0b111, 0b0001000)
FDiv = make_fregfregfreg('fdiv', 0b111, 0b0001100)
FSgnj = make_fregfregfreg('fsgnj', 0b000, 0b0010000)
FSgnjn = make_fregfregfreg('fsgnjn', 0b001, 0b0010000)
FSgnjx = make_fregfregfreg('fsgnjx', 0b010, 0b0010000)

class Movxs(RiscvInstruction):
    rd = Operand('rd', RiscvRegister, write=True)
    rm = Operand('rm', RiscvFRegister, read=True)    
    syntax = Syntax(['fmv', '.', 'x', '.', 's',' ', rd, ',', ' ', rm])
    patterns = {
        'opcode': 0b1010011, 'rd': rd, 'funct3': 0, 'rs1': rm,
        'rs2': 0, 'funct7': 0b1110000} 

class Movsx(RiscvInstruction):
    rd = Operand('rd', RiscvFRegister, write=True)
    rm = Operand('rm', RiscvRegister, read=True)
    syntax = Syntax(['fmv', '.', 's', '.', 'x',' ', rd, ',', ' ', rm])
    patterns = {
        'opcode': 0b1010011, 'rd': rd, 'funct3': 0, 'rs1': rm,
        'rs2': 0, 'funct7': 0b1111000} 

class Fcvtsw(RiscvInstruction):
    rd = Operand('rd', RiscvFRegister, write=True)
    rm = Operand('rm', RiscvRegister, read=True)    
    syntax = Syntax(['fcvt', '.', 's', '.', 'w',' ', rd, ',', ' ', rm])
    patterns = {
        'opcode': 0b1010011, 'rd': rd, 'funct3': 0, 'rs1': rm,
        'rs2': 0, 'funct7': 0b1101000} 

class Fcvtswu(RiscvInstruction):
    rd = Operand('rd', RiscvFRegister, write=True)
    rm = Operand('rm', RiscvRegister, read=True)    
    syntax = Syntax(['fcvt', '.', 's', '.', 'wu',' ', rd, ',', ' ', rm])
    patterns = {
        'opcode': 0b1010011, 'rd': rd, 'funct3': 0, 'rs1': rm,
        'rs2': 0b00001, 'funct7': 0b1101000} 

class Fcvtws(RiscvInstruction):
    rd = Operand('rd', RiscvRegister, write=True)
    rm = Operand('rm', RiscvFRegister, read=True)    
    syntax = Syntax(['fcvt', '.', 'w', '.', 's',' ', rd, ',', ' ', rm])
    patterns = {
        'opcode': 0b1010011, 'rd': rd, 'funct3': 0, 'rs1': rm,
        'rs2': 0, 'funct7': 0b1100000} 

class Fcvtwus(RiscvInstruction):
    rd = Operand('rd', RiscvRegister, write=True)
    rm = Operand('rm', RiscvFRegister, read=True)    
    syntax = Syntax(['fcvt', '.', 'wu', '.', 's',' ', rd, ',', ' ', rm])
    patterns = {
        'opcode': 0b1010011, 'rd': rd, 'funct3': 0, 'rs1': rm,
        'rs2': 0b00001, 'funct7': 0b1100000} 


    
def make_fcmp(mnemonic, func3):
    """ Factory function for immediate value instructions """    
    rd = Operand('rd', RiscvRegister, write=True)
    rn = Operand('rn', RiscvFRegister, read=True)
    rm = Operand('rm', RiscvFRegister, read=True)
    tokens = [RiscvToken]
    syntax = Syntax(['f', '.', mnemonic, '.', 's',' ', rd, ',', ' ', rn, ',', ' ', rm])
    patterns = {
        'opcode': 0b1010011, 'rd': rd, 'funct3': func3,
        'rs1': rn, 'rs2': rm, 'funct7': 0b1010000} 
    members = {
        'syntax': syntax, 'rd': rd, 'rn': rn, 'rm': rm,
        'patterns': patterns, 'tokens': tokens, 
        'func3': func3}
    return type(mnemonic + '_ins', (RiscvInstruction,), members)
    

Feq = make_fcmp('feq', 0b010)
Fle = make_fcmp('fle', 0b000)
Flt = make_fcmp('flt', 0b001)


@rvfisa.pattern('reg', 'ADDF64(reg, reg)', size=5)    
@rvfisa.pattern('reg', 'ADDF32(reg, reg)', size=5)
def pattern_add_f32(context, tree, c0, c1):    
    return call_internal2(context,'__float32_addhw', c0, c1, clobbers=context.arch.caller_save) 
	
@rvfisa.pattern('reg', 'SUBF64(reg, reg)', size=5)    
@rvfisa.pattern('reg', 'SUBF32(reg, reg)', size=5)
def pattern_sub_f32(context, tree, c0, c1):    
    return call_internal2(context,'__float32_subhw', c0, c1, clobbers=context.arch.caller_save) 

@rvfisa.pattern('reg', 'MULF64(reg, reg)', size=5)    
@rvfisa.pattern('reg', 'MULF32(reg, reg)', size=5)
def pattern_mul_f32(context, tree, c0, c1):    
    return call_internal2(context,'__float32_mulhw', c0, c1, clobbers=context.arch.caller_save) 

@rvfisa.pattern('reg', 'DIVF64(reg, reg)', size=5)    
@rvfisa.pattern('reg', 'DIVF32(reg, reg)', size=5)
def pattern_div_f32(context, tree, c0, c1):    
    return call_internal2(context,'__float32_divhw', c0, c1, clobbers=context.arch.caller_save) 

@rvfisa.pattern('reg', 'NEGF64(reg)', size=5)
@rvfisa.pattern('reg', 'NEGF32(reg)', size=5)
def pattern_neg_f32(context, tree, c0):    
    return call_internal1(context,'__float32_neghw', c0, clobbers=context.arch.caller_save) 