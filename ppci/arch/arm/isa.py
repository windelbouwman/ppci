
from ..isa import Isa
from ..token import Token, bit_range, bit


arm_isa = Isa()
thumb_isa = Isa()


# Tokens:
class ArmToken(Token):
    size = 32
    cond = bit_range(28, 32)
    S = bit(20)
    Rd = bit_range(12, 16)
    Rn = bit_range(16, 20)
    Rm = bit_range(0, 4)
    shift_typ = bit_range(5, 7)
    shift_imm = bit_range(7, 12)
    imm24 = bit_range(0, 24)
    imm8 = bit_range(0, 8)


class ThumbToken(Token):
    size = 16
    rd = bit_range(0, 3)
