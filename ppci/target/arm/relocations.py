
from ...bitfun import encode_imm32
import struct
reloc_map = {}


def reloc(t):
    def f(c):
        reloc_map[t] = c
    return f


def align(x, m):
    while ((x % m) != 0):
        x = x + 1
    return x


def wrap_negative(x, bits):
    b = struct.unpack('<I', struct.pack('<i', x))[0]
    mask = (1 << bits) - 1
    return b & mask


@reloc('rel8')
def apply_rel8(reloc, sym_value, section, reloc_value):
    assert sym_value % 2 == 0
    offset = sym_value - (align(reloc_value, 2) + 4)
    assert offset in range(-256, 254, 2), str(offset) + str(reloc)
    imm8 = wrap_negative(offset >> 1, 8)
    section.data[reloc.offset] = imm8


@reloc('b_imm24')
def apply_b_imm24(reloc, sym_value, section, reloc_value):
    assert sym_value % 4 == 0
    assert reloc_value % 4 == 0
    offset = (sym_value - (reloc_value + 8))
    rel24 = wrap_negative(offset >> 2, 24)
    section.data[reloc.offset+2] = (rel24 >> 16) & 0xFF
    section.data[reloc.offset+1] = (rel24 >> 8) & 0xFF
    section.data[reloc.offset+0] = rel24 & 0xFF


@reloc('ldr_imm12')
def apply_ldr_imm12(reloc, sym_value, section, reloc_value):
    assert sym_value % 4 == 0
    assert reloc_value % 4 == 0
    offset = (sym_value - (reloc_value + 8))
    U = 1
    if offset < 0:
        offset = -offset
        U = 0
    assert offset < 4096, "{} < 4096 {} {} {}".format(
        offset, sym_value, section, reloc)
    section.data[reloc.offset+2] |= (U << 7)
    section.data[reloc.offset+1] |= (offset >> 8) & 0xF
    section.data[reloc.offset+0] = offset & 0xFF


@reloc('adr_imm12')
def apply_adr_imm12(reloc, sym_value, section, reloc_value):
    assert sym_value % 4 == 0
    assert reloc_value % 4 == 0
    offset = (sym_value - (reloc_value + 8))
    U = 2
    if offset < 0:
        offset = -offset
        U = 1
    assert offset < 4096
    offset = encode_imm32(offset)
    section.data[reloc.offset+2] |= (U << 6)
    section.data[reloc.offset+1] |= (offset >> 8) & 0xF
    section.data[reloc.offset+0] = offset & 0xFF


@reloc('absaddr32')
def apply_absaddr32(reloc, sym_value, section, reloc_value):
    assert sym_value % 4 == 0
    assert reloc_value % 4 == 0
    offset = sym_value
    section.data[reloc.offset+3] = (offset >> 24) & 0xFF
    section.data[reloc.offset+2] = (offset >> 16) & 0xFF
    section.data[reloc.offset+1] = (offset >> 8) & 0xFF
    section.data[reloc.offset+0] = offset & 0xFF
