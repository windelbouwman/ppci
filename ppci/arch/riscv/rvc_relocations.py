from ...utils.bitfun import wrap_negative, BitView
from ..encoding import Relocation
from .tokens import RiscvToken, RiscvcToken
import logging


class CRel(Relocation):
    pass


class CBImm11Relocation(CRel):
    """ 32-bit relocation for `J` instruction """

    name = "cb_imm11"
    token = RiscvToken

    def apply(self, sym_value, data, reloc_value):
        assert sym_value % 2 == 0
        assert reloc_value % 2 == 0
        offset = sym_value - reloc_value
        bv = BitView(data, 0, 4)
        rel20 = wrap_negative(offset >> 1, 20)
        bv[21:31] = rel20 & 0x3FF
        bv[20:21] = rel20 >> 10 & 0x1
        bv[12:20] = rel20 >> 11 & 0xFF
        bv[31:32] = rel20 >> 19 & 0x1
        return data

    def can_shrink(self, sym_value, reloc_value):
        """ Test if we can optimize. """
        assert sym_value % 2 == 0
        assert reloc_value % 2 == 0
        offset = sym_value - reloc_value
        return isinsrange(12, offset)

    def do_shrink(self, sym_value, data, reloc_value):
        """ Optimize instruction!

        Do several cool things now:
        - Patch memory to change opcode.
        - Return new relocation.
        """
        assert sym_value % 2 == 0
        assert reloc_value % 2 == 0
        bv = BitView(data, 0, 4)
        bv[0:2] = 0b01
        bv[13:16] = 0b101  # C.J opcode

        data = data[:2]  # Take first data!
        new_reloc = BcImm11Relocation(self.symbol_name)
        return data, [new_reloc]


class CBlImm11Relocation(CRel):
    """ 32 bit relocation for `jal` instruction. """

    name = "cbl_imm11"
    token = RiscvToken

    def apply(self, sym_value, data, reloc_value):
        assert sym_value % 2 == 0
        assert reloc_value % 2 == 0
        offset = sym_value - reloc_value
        bv = BitView(data, 0, 4)
        rel20 = wrap_negative(offset >> 1, 20)
        bv[21:31] = rel20 & 0x3FF
        bv[20:21] = rel20 >> 10 & 0x1
        bv[12:20] = rel20 >> 11 & 0xFF
        bv[31:32] = rel20 >> 19 & 0x1
        return data

    def can_shrink(self, sym_value, reloc_value):
        assert sym_value % 2 == 0
        assert reloc_value % 2 == 0
        offset = sym_value - reloc_value
        return isinsrange(12, offset)

    def do_shrink(self, sym_value, data, reloc_value):
        assert sym_value % 2 == 0
        assert reloc_value % 2 == 0
        bv = BitView(data, 0, 4)
        bv[0:2] = 0b01
        bv[13:16] = 0b001  # c.jal opcode

        data = data[:2]  # Take first data!
        new_reloc = BcImm11Relocation(self.symbol_name)
        return data, [new_reloc]


class BcImm11Relocation(CRel):
    name = "bc_imm11"
    token = RiscvcToken

    def apply(self, sym_value, data, reloc_value):
        assert sym_value % 2 == 0
        assert reloc_value % 2 == 0
        offset = sym_value - reloc_value
        rel11 = wrap_negative(offset >> 1, 11)
        bv = BitView(data, 0, 4)
        apply_cool_mapping(bv, rel11)
        return data


class BcImm8Relocation(CRel):
    name = "bc_imm8"
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


def apply_cool_mapping(bv, rel11):
    """ This is some really nice bit fiddling! """
    bv[2:3] = rel11 >> 4 & 0x1
    bv[3:6] = rel11 & 0x7
    bv[6:7] = rel11 >> 6 & 0x1
    bv[7:8] = rel11 >> 5 & 0x1
    bv[8:9] = rel11 >> 9 & 0x1
    bv[9:11] = rel11 >> 7 & 0x3
    bv[11:12] = rel11 >> 3 & 0x1
    bv[12:13] = rel11 >> 10 & 0x1


def isinsrange(bits, val):
    """ Helper function to test if value is withing range. """
    msb = 1 << (bits - 1)
    ll = -msb
    return val <= (msb - 1) and (val >= ll)
