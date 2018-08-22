""" Vector floating point instructions """

from ..token import Token, bit_range
from ..encoding import Instruction, Syntax, Operand
from .isa import vfp_isa
from .registers import VfpRegister


class VfpToken(Token):
    class Info:
        size = 32

    cond = bit_range(28, 32)
    x2 = bit_range(24, 28)
    opc1 = bit_range(20, 24)
    opc2 = bit_range(16, 20)
    x2 = bit_range(8, 16)
    opc3 = bit_range(6, 8)
    x3 = bit_range(4, 6)
    opc4 = bit_range(0, 4)


class VfpInstruction(Instruction):
    tokens = [VfpToken]
    isa = vfp_isa
    patterns = {'x1': 0b1110, 'x2': 0b1010, 'x3': 0b0}


class Vadd(VfpInstruction):
    d = Operand('d', VfpRegister, write=True)
    m = Operand('m', VfpRegister, read=True)
    n = Operand('n', VfpRegister, read=True)
    syntax = Syntax(['vadd.f64', ' ', d, ',', ' ', n, ',', ' ', m])
    patterns = {'opc1': 0b0011, 'opc3': 0b00, 'opc': 2}


class Vsubf64(VfpInstruction):
    d = Operand('d', VfpRegister, write=True)
    m = Operand('m', VfpRegister, read=True)
    n = Operand('n', VfpRegister, read=True)
    syntax = Syntax(['vsub.f64', ' ', d, ',', ' ', n, ',', ' ', m])
    patterns = {'opc1': 0b0011, 'opc3': 0b00, 'opc': 2}
