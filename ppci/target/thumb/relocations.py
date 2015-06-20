
from ...bitfun import align, wrap_negative, BitView


def apply_lit8(reloc, sym_value, section, reloc_value):
    assert sym_value % 4 == 0, '{}: {} not multiple of 4'\
        .format(reloc, sym_value)
    offset = (sym_value - (align(reloc_value + 2, 4)))
    assert offset in range(0, 1024, 4), str(offset)+str(section)+str(reloc)
    rel8 = offset >> 2
    section.data[reloc.offset] = rel8


def apply_wrap_new11(reloc, sym_value, section, reloc_value):
    offset = sym_value - (align(reloc_value, 2) + 4)
    assert offset in range(-2048, 2046, 2)
    imm11 = wrap_negative(offset >> 1, 11)
    bv = BitView(section.data, reloc.offset, 2)
    bv[0:11] = imm11


def apply_rel8(reloc, sym_value, section, reloc_value):
    assert sym_value % 2 == 0
    offset = sym_value - (align(reloc_value, 2) + 4)
    assert offset in range(-256, 254, 2), str(offset) + str(reloc)
    imm8 = wrap_negative(offset >> 1, 8)
    section.data[reloc.offset] = imm8


def apply_bl_imm11(reloc, sym_value, section, reloc_value):
    assert sym_value % 2 == 0
    offset = sym_value - (align(reloc_value, 2) + 4)
    assert offset in range(-16777216, 16777214, 2), str(offset)
    imm32 = wrap_negative(offset >> 1, 32)
    imm11 = imm32 & 0x7FF
    imm10 = (imm32 >> 11) & 0x3FF
    s = (imm32 >> 24) & 0x1
    bv = BitView(section.data, reloc.offset, 4)
    bv[0:10] = imm10
    bv[10:11] = s
    bv[16:27] = imm11


def apply_b_imm11_imm6(reloc, sym_value, section, reloc_value):
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
    section.data[reloc.offset + 2] = imm11 & 0xFF
    section.data[reloc.offset + 3] |= (imm11 >> 8) & 0x7
    section.data[reloc.offset + 3] |= (j1 << 5) | (j2 << 3)
    section.data[reloc.offset] |= imm6
    section.data[reloc.offset + 1] |= (s << 2)


def apply_absaddr32(reloc, sym_value, section, reloc_value):
    assert sym_value % 4 == 0
    assert reloc_value % 4 == 0
    offset = sym_value
    bv = BitView(section.data, reloc.offset, 4)
    bv[0:32] = offset
