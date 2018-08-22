
from ..isa import Isa
from ..token import Token, bit_range, bit


arm_isa = Isa()
thumb_isa = Isa()
neon_isa = Isa()
vfp_isa = Isa()


# Tokens:
class ArmToken(Token):
    class Info:
        size = 32

    cond = bit_range(28, 32)
    opcode = bit_range(21, 28)
    S = bit(20)
    rd = bit_range(12, 16)
    rn = bit_range(16, 20)
    rm = bit_range(0, 4)
    b4 = bit(4)
    shift_typ = bit_range(5, 7)
    shift_imm = bit_range(7, 12)
    imm24 = bit_range(0, 24)
    imm8 = bit_range(0, 8)
    imm4h_imm4l = bit_range(8, 12) + bit_range(0, 4)


class ArmImmToken(Token):
    class Info:
        size = 32

    cond = bit_range(28, 32)
    opcode = bit_range(21, 28)
    s = bit(20)
    rn = bit_range(16, 20)
    rd = bit_range(12, 16)
    imm12 = bit_range(0, 12)


class ThumbToken(Token):
    class Info:
        size = 16

    rd = bit_range(0, 3)
