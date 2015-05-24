from ..target import Target
from .registers import r10, r11, r12, r13, r14, r15
from .instructions import isa
from ...assembler import BaseAssembler
from ...bitfun import align, wrap_negative


# Create the target class (singleton):

class Msp430Assembler(BaseAssembler):
    def __init__(self, target):
        super().__init__(target)
        kws = list(isa.calc_kws())
        self.gen_asm_parser(isa)
        self.parser.g.add_terminals(kws)
        self.lexer.kws |= set(kws)


def apply_rel10bit(reloc, sym_value, section, reloc_value):
    """ Apply 10 bit signed relocation """
    assert sym_value % 2 == 0
    offset = (sym_value - (align(reloc_value, 2)) - 2) >> 1
    assert offset in range(-511, 511, 1), str(offset) + str(reloc)
    imm10 = wrap_negative(offset, 10)
    section.data[reloc.offset] = imm10 & 0xff
    cmd = section.data[reloc.offset + 1] & 0xfc
    section.data[reloc.offset + 1] = cmd | (imm10 >> 8)


class Msp430Target(Target):
    def __init__(self):
        super().__init__('msp430')

        self.assembler = Msp430Assembler(self)
        # TODO: rethink this reloc hell:
        self.reloc_map = {'msp_reloc': apply_rel10bit}

        self.registers.append(r10)
        self.registers.append(r11)
        self.registers.append(r12)
        self.registers.append(r13)
        self.registers.append(r14)
        self.registers.append(r15)

    def get_runtime_src(self):
        return ''
