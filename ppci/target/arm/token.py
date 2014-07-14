
from ..token import Token, u32, bit_range


class ArmToken(Token):
    def __init__(self):
        super().__init__(32)

    cond = bit_range(28, 32)
    S = bit_range(20, 21)
    Rd = bit_range(12, 16)
    Rn = bit_range(16, 20)
    Rm = bit_range(0, 4)

    def encode(self):
        return u32(self.bit_value)
