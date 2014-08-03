import types
from ppci import CompilerError
from ..bitfun import encode_imm32
import struct

"""
  Base classes for defining a target
"""

class Instruction:
    """ Base instruction class """
    def encode(self):
        return bytes()

    def relocations(self):
        return []

    def symbols(self):
        return []

    def literals(self, add_literal):
        pass


class Nop(Instruction):
    """ Instruction that does nothing and has zero size """
    def encode(self):
        return bytes()

    def __repr__(self):
        return 'NOP'


class PseudoInstruction(Instruction):
    pass


class Label(PseudoInstruction):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '{}:'.format(self.name)

    def symbols(self):
        return [self.name]


class Comment(PseudoInstruction):
    def __init__(self, txt):
        self.txt = txt

    def encode(self):
        return bytes()

    def __repr__(self):
        return '; {}'.format(self.txt)


class Alignment(PseudoInstruction):
    def __init__(self, a):
        self.align = a

    def __repr__(self):
        return 'ALIGN({})'.format(self.align)

    def encode(self):
        pad = []
        # TODO
        address = 0
        while (address % self.align) != 0:
            address += 1
            pad.append(0)
        return bytes(pad)


class Register:
    def __init__(self, name):
        self.name = name

    def __gt__(self, other):
        return self.num > other.num


class LabelAddress:
    def __init__(self, name):
        self.name = name


class Target:
    def __init__(self, name, desc=''):
        self.name = name
        self.desc = desc
        self.registers = []
        self.byte_sizes = {'int' : 4}  # For front end!
        self.byte_sizes['byte'] = 1

        # For lowering:
        self.lower_functions = {}

        # For assembler:
        self.assembler_rules = []
        self.asm_keywords = []

        self.generate_base_rules()
        self.reloc_map = reloc_map  # TODO: make this target specific.

    def generate_base_rules(self):
        # Base rules for constants:
        self.add_rule('imm32', ['val32'], lambda x: x[0].val)
        self.add_rule('imm32', ['imm16'], lambda x: x[0])

        self.add_rule('imm16', ['val16'], lambda x: x[0].val)
        self.add_rule('imm16', ['imm12'], lambda x: x[0])

        self.add_rule('imm12', ['val12'], lambda x: x[0].val)
        self.add_rule('imm12', ['imm8'], lambda x: x[0])

        self.add_rule('imm8', ['val8'], lambda x: x[0].val)
        self.add_rule('imm8', ['imm5'], lambda x: x[0])

        self.add_rule('imm5', ['val5'], lambda x: x[0].val)
        self.add_rule('imm5', ['imm3'], lambda x: x[0])

        self.add_rule('imm3', ['val3'], lambda x: x[0].val)

    def add_keyword(self, kw):
        self.asm_keywords.append(kw)

    def add_instruction(self, rhs, f):
        self.add_rule('instruction', rhs, f)

    def add_rule(self, lhs, rhs, f):
        if type(f) is int:
            f2 = lambda x: f
        else:
            f2 = f
        assert type(f2) in [types.FunctionType, types.MethodType]
        self.assembler_rules.append((lhs, rhs, f2))

    def lower_frame_to_stream(self, frame, outs):
        """ Lower instructions from frame to output stream """
        for im in frame.instructions:
            if isinstance(im.assem, Instruction):
                outs.emit(im.assem)
            else:
                # TODO assert isinstance(Abs
                ins = self.lower_functions[im.assem](im)
                outs.emit(ins)

    def add_lowering(self, cls, f):
        """ Add a function to the table of lowering options for this target """
        self.lower_functions[cls] = f

    def add_reloc(self, name, f):
        self.reloc_map[name] = f



def align(x, m):
    while ((x % m) != 0):
        x = x + 1
    return x

def wrap_negative(x, bits):
    b = struct.unpack('<I', struct.pack('<i', x))[0]
    mask = (1 << bits) - 1
    return b & mask


reloc_map = {}

def reloc(t):
    def f(c):
        reloc_map[t] = c
    return f


@reloc('lit_add_8')
def apply_lit8(reloc, sym_value, section, reloc_value):
    assert sym_value % 4 == 0, '{}: {} not multiple of 4'.format(reloc, sym_value)
    offset = (sym_value - (align(reloc_value + 2, 4)))
    assert offset in range(0, 1024, 4), str(offset)+str(self.dst.sections)
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
    s = (imm32 >> 24) & 0x1
    section.data[reloc.offset + 2] = imm11 & 0xFF
    section.data[reloc.offset + 3] |= (imm11 >> 8) & 0x7
    section.data[reloc.offset] |= imm6
    section.data[reloc.offset + 1] |= (s << 2)

# ARM reloc!!
# TODO: move to target classes???
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
    assert offset < 4096, str(sym) + str(section) + str(reloc)
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
