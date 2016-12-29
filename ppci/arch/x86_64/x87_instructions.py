""" x87 floating point unit instructions """

from ..isa import Isa
from ..encoding import Operand, Syntax, Instruction
from .instructions import mem_modes
from .instructions import OpcodeToken, SecondaryOpcodeToken
from .instructions import RexToken, ModRmToken

x87_isa = Isa()


class X87Instruction(Instruction):
    """ x87 FPU instruction """
    isa = x87_isa


class Fsqrt(X87Instruction):
    """ Floating point square root """
    syntax = Syntax(['fsqrt'])
    patterns = {'opcode': 0xd9, 'opcode2': 0xfa}
    tokens = [OpcodeToken, SecondaryOpcodeToken]


class Fld32(X87Instruction):
    """ Push 32 bit operand on the FPU stack, suffix s=32 bit """
    m = Operand('m', mem_modes)
    syntax = Syntax(['flds', ' ', m])
    patterns = {'opcode': 0xd9, 'reg': 0}
    tokens = [RexToken, OpcodeToken, ModRmToken]


class Fld64(X87Instruction):
    """ Push 64 bit operand on the FPU stack, suffix l=64 bit """
    m = Operand('m', mem_modes)
    syntax = Syntax(['fldl', ' ', m])
    patterns = {'opcode': 0xdd, 'reg': 0}
    tokens = [RexToken, OpcodeToken, ModRmToken]


class Fld80(X87Instruction):
    """ Push 80 bit operand on the FPU stack, suffix t=80 bit """
    m = Operand('m', mem_modes)
    syntax = Syntax(['fldt', ' ', m])
    patterns = {'opcode': 0xdb, 'reg': 5}
    tokens = [RexToken, OpcodeToken, ModRmToken]


class Fst32(X87Instruction):
    """ Store 32 bit float into memory """
    m = Operand('m', mem_modes)
    syntax = Syntax(['fsts', ' ', m])
    patterns = {'opcode': 0xd9, 'reg': 2}
    tokens = [RexToken, OpcodeToken, ModRmToken]


class Fstp32(X87Instruction):
    """ Store 32 bit float into memory and pop """
    m = Operand('m', mem_modes)
    syntax = Syntax(['fsts', ' ', m])
    patterns = {'opcode': 0xd9, 'reg': 3}
    tokens = [RexToken, OpcodeToken, ModRmToken]


class Fst64(X87Instruction):
    """ Store 64 bit float into memory """
    m = Operand('m', mem_modes)
    syntax = Syntax(['fstl', ' ', m])
    patterns = {'opcode': 0xdd, 'reg': 2}
    tokens = [RexToken, OpcodeToken, ModRmToken]


@x87_isa.pattern('stm', 'STRF32(reg64, regfp)', size=2)
def pattern_str_f32(context, tree, c0, c1):
    # context.emit(Fst32(RmMem(c0)))
    # TODO: exchange?

    # context.emit(Fst32(RmMem(c0)))
    raise NotImplementedError()
