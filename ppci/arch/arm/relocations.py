
from ...utils.bitfun import encode_imm32, align, wrap_negative, BitView


def apply_rel8(sym_value, data, reloc_value):
    assert sym_value % 2 == 0
    offset = sym_value - (align(reloc_value, 2) + 4)
    assert offset in range(-256, 254, 2), str(offset)
    imm8 = wrap_negative(offset >> 1, 8)
    data[0] = imm8


def apply_b_imm24(sym_value, data, reloc_value):
    assert sym_value % 4 == 0
    assert reloc_value % 4 == 0
    offset = (sym_value - (reloc_value + 8))
    rel24 = wrap_negative(offset >> 2, 24)
    bv = BitView(data, 0, 3)
    bv[0:24] = rel24


def apply_ldr_imm12(sym_value, data, reloc_value):
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


def apply_adr_imm12(sym_value, data, reloc_value):
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
