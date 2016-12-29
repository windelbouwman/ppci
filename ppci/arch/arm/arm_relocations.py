
from ...utils.bitfun import encode_imm32, align, wrap_negative
from ..encoding import Relocation
from .isa import ArmToken, arm_isa


@arm_isa.register_relocation
class Rel8Relocation(Relocation):
    name = 'rel8'
    token = ArmToken
    field = 'imm8'

    def calc(self, sym_value, reloc_value):
        assert sym_value % 2 == 0
        offset = sym_value - (align(reloc_value, 2) + 4)
        assert offset in range(-256, 254, 2), str(offset)
        return wrap_negative(offset >> 1, 8)


@arm_isa.register_relocation
class Imm24Relocation(Relocation):
    name = 'imm24'
    token = ArmToken
    field = 'imm24'

    def calc(self, sym_value, reloc_value):
        assert sym_value % 4 == 0
        assert reloc_value % 4 == 0
        offset = (sym_value - (reloc_value + 8))
        return wrap_negative(offset >> 2, 24)


@arm_isa.register_relocation
class LdrImm12Relocation(Relocation):
    name = 'ldr_imm12'
    token = ArmToken

    def apply(self, sym_value, data, reloc_value):
        assert sym_value % 4 == 0
        assert reloc_value % 4 == 0
        offset = (sym_value - (reloc_value + 8))
        U = 1
        if offset < 0:
            offset = -offset
            U = 0
        assert offset < 4096, "{} < 4096 {} {}".format(
            offset, sym_value, data)
        data[2] |= (U << 7)
        data[1] |= (offset >> 8) & 0xF
        data[0] = offset & 0xFF
        return data


@arm_isa.register_relocation
class AdrImm12Relocation(Relocation):
    name = 'adr_imm12'
    token = ArmToken

    def apply(self, sym_value, data, reloc_value):
        assert sym_value % 4 == 0
        assert reloc_value % 4 == 0
        offset = (sym_value - (reloc_value + 8))
        U = 2
        if offset < 0:
            offset = -offset
            U = 1
        assert offset < 4096
        offset = encode_imm32(offset)
        data[2] |= (U << 6)
        data[1] |= (offset >> 8) & 0xF
        data[0] = offset & 0xFF
        return data
