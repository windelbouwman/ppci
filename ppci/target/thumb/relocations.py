
import struct


def align(x, m):
    while ((x % m) != 0):
        x = x + 1
    return x

reloc_map = {}


def reloc(t):
    def f(c):
        reloc_map[t] = c
    return f


def wrap_negative(x, bits):
    b = struct.unpack('<I', struct.pack('<i', x))[0]
    mask = (1 << bits) - 1
    return b & mask


@reloc('lit_add_8')
def apply_lit8(reloc, sym_value, section, reloc_value):
    assert sym_value % 4 == 0, '{}: {} not multiple of 4'\
        .format(reloc, sym_value)
    offset = (sym_value - (align(reloc_value + 2, 4)))
    assert offset in range(0, 1024, 4), str(offset)+str(section)+str(reloc)
    rel8 = offset >> 2
    section.data[reloc.offset] = rel8


@reloc('wrap_new11')
def apply_wrap_new11(reloc, sym_value, section, reloc_value):
    offset = sym_value - (align(reloc_value, 2) + 4)
    assert offset in range(-2048, 2046, 2)
    imm11 = wrap_negative(offset >> 1, 11)
    section.data[reloc.offset] = (imm11 & 0xff)
    section.data[reloc.offset + 1] |= (imm11 >> 8) & 0x7


@reloc('rel8')
def apply_rel8(reloc, sym_value, section, reloc_value):
    assert sym_value % 2 == 0
    offset = sym_value - (align(reloc_value, 2) + 4)
    assert offset in range(-256, 254, 2), str(offset) + str(reloc)
    imm8 = wrap_negative(offset >> 1, 8)
    section.data[reloc.offset] = imm8


@reloc('bl_imm11_imm10')
def apply_bl_imm11(reloc, sym_value, section, reloc_value):
    assert sym_value % 2 == 0
    offset = sym_value - (align(reloc_value, 2) + 4)
    assert offset in range(-16777216, 16777214, 2), str(offset)
    imm32 = wrap_negative(offset >> 1, 32)
    imm11 = imm32 & 0x7FF
    imm10 = (imm32 >> 11) & 0x3FF
    s = (imm32 >> 24) & 0x1
    section.data[reloc.offset + 2] = imm11 & 0xFF
    section.data[reloc.offset + 3] |= (imm11 >> 8) & 0x7
    section.data[reloc.offset] = imm10 & 0xff
    section.data[reloc.offset + 1] |= ((imm10 >> 8) & 0x3) | (s << 2)


@reloc('b_imm11_imm6')
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


@reloc('absaddr32')
def apply_absaddr32(reloc, sym_value, section, reloc_value):
    assert sym_value % 4 == 0
    assert reloc_value % 4 == 0
    offset = sym_value
    section.data[reloc.offset+3] = (offset >> 24) & 0xFF
    section.data[reloc.offset+2] = (offset >> 16) & 0xFF
    section.data[reloc.offset+1] = (offset >> 8) & 0xFF
    section.data[reloc.offset+0] = offset & 0xFF
