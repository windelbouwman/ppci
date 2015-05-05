import struct
from .. import Register, Instruction, Target
from .registers import r4, r5, r6, r7, r8, r9, r10, r11, r12, r13, r14, r15
from .instructions import isa, SourceOperand, DestinationOperand
from ...assembler import BaseAssembler


# Create the target class (singleton):

class Msp430Assembler(BaseAssembler):
    def __init__(self, target):
        super().__init__(target)
        kws = list(isa.calc_kws())

        # Registers:
        self.add_keyword('r4')
        self.add_keyword('r5')
        self.add_keyword('r6')
        self.add_keyword('r7')
        self.add_keyword('r8')
        self.add_keyword('r9')
        self.add_keyword('r10')
        self.add_keyword('r11')
        self.add_keyword('r12')
        self.add_keyword('r13')
        self.add_keyword('r14')
        self.add_keyword('r15')
        self.add_rule('reg', ['r4'], lambda rhs: r4)
        self.add_rule('reg', ['r5'], lambda rhs: r5)
        self.add_rule('reg', ['r6'], lambda rhs: r6)
        self.add_rule('reg', ['r7'], lambda rhs: r7)
        self.add_rule('reg', ['r8'], lambda rhs: r8)
        self.add_rule('reg', ['r9'], lambda rhs: r9)

        self.add_rule('reg', ['r10'], lambda rhs: r10)
        self.add_rule('reg', ['r11'], lambda rhs: r11)
        self.add_rule('reg', ['r12'], lambda rhs: r12)
        self.add_rule('reg', ['r13'], lambda rhs: r13)
        self.add_rule('reg', ['r14'], lambda rhs: r14)
        self.add_rule('reg', ['r15'], lambda rhs: r15)

        # For label:
        self.add_rule('strrr', ['ID'], lambda rhs: rhs[0].val)
        self.add_rule('src', ['reg'], lambda rhs: SourceOperand(rhs[0]))
        self.add_rule('src', ['imm16'], lambda rhs: SourceOperand(rhs[0]))
        self.add_rule('dst', ['reg'], lambda rhs: DestinationOperand(rhs[0]))

        self.gen_asm_parser(isa)
        self.parser.g.add_terminals(kws)
        self.lexer.kws |= set(kws)


def align(x, m):
    while ((x % m) != 0):
        x = x + 1
    return x


def wrap_negative(x, bits):
    b = struct.unpack('<I', struct.pack('<i', x))[0]
    mask = (1 << bits) - 1
    return b & mask


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
