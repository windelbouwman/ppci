from ...utils.bitfun import wrap_negative, BitView
from ..encoding import Relocation
from .tokens import *

# 6 byte aligned means 48 bits
ATALLA_INSN_ALIGNMENT = 6

class AtallaBR_Imm10_Relocation(Relocation):
    name = "BR_i10"
    token = AtallaBRToken

    def calc(self, sym_value, reloc_value):
        offset = (sym_value - reloc_value) // ATALLA_INSN_ALIGNMENT
        return wrap_negative(offset, 10)

    # def calc(self, sym_value, reloc_value):
    #     pc_next = reloc_value + ATALLA_INSN_ALIGNMENT
    #     offset = (sym_value - pc_next) // ATALLA_INSN_ALIGNMENT
    #     return wrap_negative(offset, 10)

    def apply(self, sym_value, data, reloc_value):
        imm10 = self.calc(sym_value, reloc_value)
        token = self.token.from_data(data)
        token.imm10 = imm10
        return token.encode()

class AtallaMI_JAL_Imm25_Relocation(Relocation):
    name = "MI_jal_i25"
    token = AtallaMIToken
    field = "imm25"

    def calc(self, sym_value, reloc_value):
        offset = (sym_value - reloc_value) // ATALLA_INSN_ALIGNMENT
        return wrap_negative(offset, 25)

# Maybe don't need this, but if lui uses or loads symbol addresses then it would be needed
class AtallaMI_Abs_Imm25_Relocation(Relocation):
    name = "MI_abs_i25"
    token = AtallaMIToken
    field = "imm25"
    
    def calc(self, sym_value, reloc_value):
        return sym_value & 0x1FFFFFF #for masking to 25 bits

# May not need JALR if the offset is always literal and not a symbol value
class AtallaI_JALR_Imm12_Relocation(Relocation):
    name = "I_i12"
    token = AtallaIToken
    field = "imm12"
    def calc(self, sym_value, reloc_value):
        return sym_value & 0xFFF # You need the lower 12 bits absolute for jalr
