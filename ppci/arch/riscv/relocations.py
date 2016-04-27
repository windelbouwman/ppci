
from ...utils.bitfun import wrap_negative, BitView



def apply_b_imm12(sym_value, data, reloc_value):
    assert sym_value % 4 == 0
    assert reloc_value % 4 == 0
    offset = sym_value - reloc_value
    rel12 = wrap_negative(offset >> 1, 12)
    bv = BitView(data, 0, 4)
    bv[8:12] = rel12 & 0xF
    bv[25:31] = rel12>>4 & 0x3F
    bv[7:8] = rel12>>10 & 0x1
    bv[31:32] = rel12>>11 & 0x1

def apply_b_imm20(sym_value, data, reloc_value):
    assert sym_value % 4 == 0
    assert reloc_value % 4 == 0
    offset = sym_value - reloc_value
    rel20 = wrap_negative(offset >> 1, 20)
    bv = BitView(data, 0, 4)
    bv[21:31] = rel20 & 0x3FF
    bv[20:21] = rel20>>10 & 0x1
    bv[12:20] = rel20>>11 & 0xFF
    bv[31:32] = rel20>>19 & 0x1

def apply_abs32_imm20(sym_value, data, reloc_value):
    assert sym_value % 4 == 0
    bv = BitView(data, 0, 4)
    bv[12:32] = (sym_value>>12)&0xfffff

def apply_abs32_imm12(sym_value, data, reloc_value):
    assert sym_value % 4 == 0
    bv = BitView(data, 0, 4)
    bv[20:32] = sym_value&0xfff


def apply_absaddr32(sym_value, data, reloc_value):
    assert sym_value % 4 == 0
    assert reloc_value % 4 == 0
    offset = sym_value
    bv = BitView(data, 0, 4)
    bv[0:32] = offset
