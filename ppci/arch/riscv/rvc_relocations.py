from ...utils.bitfun import wrap_negative, BitView
from ..encoding import Relocation
from .tokens import RiscvcToken


class BcImm11Relocation(Relocation):
    name = 'bc_imm11'
    token = RiscvcToken

    def apply(self, sym_value, data, reloc_value):
        assert sym_value % 2 == 0
        assert reloc_value % 2 == 0
        offset = sym_value - reloc_value
        rel11 = wrap_negative(offset >> 1, 11)
        bv = BitView(data, 0, 4)
        bv[2:3] = rel11 >> 4 & 0x1
        bv[3:6] = rel11 & 0x7
        bv[6:7] = rel11 >> 6 & 0x1
        bv[7:8] = rel11 >> 5 & 0x1
        bv[8:9] = rel11 >> 9 & 0x1
        bv[9:11] = rel11 >> 7 & 0x3
        bv[11:12] = rel11 >> 3 & 0x1
        bv[12:13] = rel11 >> 10 & 0x1
        return data


class BcImm8Relocation(Relocation):
    name = 'bc_imm8'
    token = RiscvcToken

    def apply(self, sym_value, data, reloc_value):
        assert sym_value % 2 == 0
        assert reloc_value % 2 == 0
        offset = sym_value - reloc_value
        rel8 = wrap_negative(offset >> 1, 8)
        bv = BitView(data, 0, 4)
        bv[2:3] = rel8 >> 4 & 0x1
        bv[3:5] = rel8 & 0x3
        bv[5:7] = rel8 >> 5 & 0x3
        bv[10:12] = rel8 >> 2 & 0x3
        bv[12:13] = rel8 >> 7 & 0x1
        return data
