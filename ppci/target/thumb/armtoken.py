
from ..token import Token, u16, bit_range

class ThumbToken(Token):
    def __init__(self):
        super().__init__(16)

    rd = bit_range(0, 3)

    def encode(self):
        return u16(self.bit_value)

