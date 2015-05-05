
from .. import Instruction, Isa, register_argument
from ..token import Token, u16, bit_range, bit
from .registers import Msp430Register

isa = Isa()
isa.typ2nt[Msp430Register] = 'reg'
isa.typ2nt[str] = 'strrr'


class Msp430Token(Token):
    def __init__(self):
        super().__init__(16)

    condition = bit_range(10, 13)
    opcode = bit_range(12, 16)
    register = bit_range(0, 4)
    destination = bit_range(0, 4)
    source = bit_range(8, 12)
    bw = bit(6)
    Ad = bit(7)
    As = bit_range(4, 6)

    def encode(self):
        return u16(self.bit_value)


REGISTER_MODE = 1
SYMBOLIC_MODE = 3
ABSOLUTE_MODE = 4
#TODO: add more modes!
IMMEDIATE_MODE = 7


class Msp430Operand:
    pass


class DestinationOperand(Msp430Operand):
    def __init__(self, param):
        if isinstance(param, Msp430Register):
            self.reg = param.num
            self.Ad = 0
        else:
            raise Exception()

isa.typ2nt[DestinationOperand] = 'dst'


def optional(x):
    pass


class SourceOperand(Msp430Operand):
    # TODO: make this work!
    syntax = ['reg'], [optional('@'), 'reg']

    def __init__(self, param, auto_inc=False, deref=False):
        if isinstance(param, Msp430Register):
            self.reg = param.num
            self.As = 0
            self.extra_bytes = bytes()
        elif isinstance(param, int):
            self.reg = 0
            self.As = 3
            self.extra_bytes = u16(param)
        else:
            raise Exception()

isa.typ2nt[SourceOperand] = 'src'

class Msp430Instruction(Instruction):
    isa = isa
    b = 0
    tokens = [Msp430Token]


#########################
# Jump instructions:
#########################

class JumpInstruction(Msp430Instruction):
    def encode(self):
        self.token.condition = self.condition
        self.token.offset = 0
        self.token[13] = 1
        return self.token.encode()

    def relocations(self):
        return [(self.target, 'msp_reloc')]


def create_jump_instruction(name, condition):
    label = register_argument('target', str)
    syntax = [name, label]
    members = {'syntax': syntax, 'label': label, 'condition': condition}
    return type(name + '_ins', (JumpInstruction, ), members)


Jne = create_jump_instruction('jne', 0)
Jz = create_jump_instruction('jz', 1)
Jnc = create_jump_instruction('jnc', 2)
Jc = create_jump_instruction('jc', 3)
Jn = create_jump_instruction('jn', 4)
Jge = create_jump_instruction('jge', 5)
Jl = create_jump_instruction('jl', 6)
Jmp = create_jump_instruction('jmp', 7)


#########################
# Single operand arithmatic:
#########################


class OneOpArith(Msp430Instruction):
    def encode(self):
        # TODO:
        bits[15:10] = '00100'
        h1 = (self.opcode << 4)
        return pack_ins(h1)


def oneOpIns(mne, opcode):
    """ Helper function to define a one operand arithmetic instruction """
    members = {'opcode': opcode}
    return type(mne + '_ins', (OneOpArith,), members)


Rrr = oneOpIns('rrc', 0)
Swpb = oneOpIns('swpb', 1)
Rra = oneOpIns('rra', 2)
Sxt = oneOpIns('sxt', 3)
Push = oneOpIns('push', 4)
Call = oneOpIns('call', 5)


class Reti(Msp430Instruction):
    syntax = ['reti']

    def encode(self):
        self.token[0:16] = 0x1300
        return self.token.encode()


#########################
# Two operand arithmatic instructions:
#########################


class TwoOpArith(Msp430Instruction):
    def encode(self):
        """
            Smart things have been done by MSP430 designers.
            As (2 bits) is the source addressing mode selector.
            Ad (1 bit) is the destination adressing mode selector.
            For the source there are 7 different addressing mode.
            For the destination there are 4.
            The trick is to use also the register to distuingish the
            different modes.
        """
        # TODO: Make memory also possible
        self.token.bw = self.b  # When b=1, the operation is byte mode
        self.token.As = self.src.As
        self.token.Ad = self.dst.Ad
        self.token.destination = self.dst.reg
        self.token.source = self.src.reg
        self.token.opcode = self.opcode
        return self.token.encode() + self.src.extra_bytes


def twoOpIns(mne, opc):
    """ Helper function to define a two operand arithmetic instruction """
    src = register_argument('src', SourceOperand)
    dst = register_argument('dst', DestinationOperand)
    syntax = [mne, src, ',', dst]
    members = {'opcode': opc, 'src': src, 'dst': dst, 'syntax': syntax}
    return type(mne + '_ins', (TwoOpArith,), members)


Mov = twoOpIns('mov', 4)
Add = twoOpIns('add', 5)
Addc = twoOpIns('addc', 6)
Subc = twoOpIns('subc', 7)
Sub = twoOpIns('sub', 8)
Cmp = twoOpIns('cmp', 9)
Dadd = twoOpIns('dadd', 10)
Bit = twoOpIns('bit', 11)
Bic = twoOpIns('bic', 12)
Bis = twoOpIns('bis', 13)
Xor = twoOpIns('xor', 14)
And = twoOpIns('and', 15)
