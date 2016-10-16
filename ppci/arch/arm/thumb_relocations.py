
from .isa import thumb_isa, ThumbToken
from ..encoding import Relocation
from ...utils.bitfun import align, wrap_negative, BitView


@thumb_isa.register_relocation
class Lit8Relocation(Relocation):
    name = 'lit8'
    token = ThumbToken

    def apply(self, sym_value, data, reloc_value):
        assert sym_value % 4 == 0, '{} not multiple of 4'\
            .format(sym_value)
        offset = (sym_value - (align(reloc_value + 2, 4)))
        assert offset in range(0, 1024, 4), str(offset)
        rel8 = offset >> 2
        data[0] = rel8
        return data


@thumb_isa.register_relocation
class WrapNew11Relocation(Relocation):
    name = 'wrap_new11'
    token = ThumbToken

    def apply(self, sym_value, data, reloc_value):
        offset = sym_value - (align(reloc_value, 2) + 4)
        assert offset in range(-2048, 2046, 2)
        imm11 = wrap_negative(offset >> 1, 11)
        bv = BitView(data, 0, 2)
        bv[0:11] = imm11
        return data


@thumb_isa.register_relocation
class Rel8Relocation(Relocation):
    name = 'rel8'
    token = ThumbToken

    def apply(self, sym_value, data, reloc_value):
        assert sym_value % 2 == 0
        offset = sym_value - (align(reloc_value, 2) + 4)
        assert offset in range(-256, 254, 2), str(offset)
        imm8 = wrap_negative(offset >> 1, 8)
        data[0] = imm8
        return data


@thumb_isa.register_relocation
class BlImm11Relocation(Relocation):
    name = 'bl_imm11'

    @classmethod
    def size(cls):
        return 4

    def apply(self, sym_value, data, reloc_value):
        assert sym_value % 2 == 0
        offset = sym_value - (align(reloc_value, 2) + 4)
        assert offset in range(-16777216, 16777214, 2), str(offset)
        imm32 = wrap_negative(offset >> 1, 32)
        imm11 = imm32 & 0x7FF
        imm10 = (imm32 >> 11) & 0x3FF
        s = (imm32 >> 24) & 0x1
        bv = BitView(data, 0, 4)
        bv[0:10] = imm10
        bv[10:11] = s
        bv[16:27] = imm11
        return data


@thumb_isa.register_relocation
class BImm11Imm6Relocation(Relocation):
    name = 'b_imm11_imm6'

    @classmethod
    def size(cls):
        return 4

    def apply(self, sym_value, data, reloc_value):
        assert sym_value % 2 == 0
        offset = sym_value - (align(reloc_value, 2) + 4)
        assert offset in range(-1048576, 1048574, 2), str(offset)
        imm32 = wrap_negative(offset >> 1, 32)
        imm11 = imm32 & 0x7FF
        imm6 = (imm32 >> 11) & 0x3F
        s = (imm32 >> 17) & 0x1
        # TODO: determine i1 and i2 better!
        i1 = s
        i2 = s
        j1 = i1
        j2 = i2
        data[2] = imm11 & 0xFF
        data[3] |= (imm11 >> 8) & 0x7
        data[3] |= (j1 << 5) | (j2 << 3)
        data[0] |= imm6
        data[1] |= (s << 2)
        return data
