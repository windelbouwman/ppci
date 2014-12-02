
from ..basetarget import Register, Instruction, Target, Isa
from ..token import Token, u16, bit_range
from .registers import Msp430Register

isa = Isa()
isa.typ2nt[Msp430Register] = 'reg'

class Msp430Token(Token):
    def __init__(self):
        super().__init__(16)

    condition = bit_range(10, 13)
    opcode = bit_range(12, 16)
    register = bit_range(0, 4)
    destination = bit_range(0, 4)
    source = bit_range(8, 12)
    bw = bit_range(6, 7)  # TODO: actually a single bit!
    Ad = bit_range(7, 8)  # TODO: actually a single bit!
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

class Msp430DestinationOperand(Msp430Operand):
    def __init__(self, param):
        if isinstance(param, Msp430Register):
            self.reg = param.num
            self.Ad = 0
        else:
            raise Exception()


class Msp430SourceOperand(Msp430Operand):
    def __init__(self, param):
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


class Msp430Instruction(Instruction):
    isa = isa
    b = 0
    tokens = [Msp430Token]

    def __init__(self):
        self.token = Msp430Token()


class Reti(Msp430Instruction):
    syntax = ['reti']

    def encode(self):
        self.token[0:16] = 0x1300
        return self.token.encode()


#########################
# Jump instructions:
#########################

class JumpInstruction(Msp430Instruction):
    def __init__(self, target):
        super().__init__()
        self.target = target

    def encode(self):
        self.token.condition = self.condition
        self.token.offset = 0
        self.token[13] = 1
        return self.token.encode()

    def relocations(self):
        return [(self.target, 'msp_reloc')]


class Jnz(JumpInstruction):
    condition = 0


class Jz(JumpInstruction):
    condition = 1


class Jnc(JumpInstruction):
    condition = 2


class Jc(JumpInstruction):
    condition = 3


class Jn(JumpInstruction):
    condition = 4


class Jge(JumpInstruction):
    condition = 5


class Jl(JumpInstruction):
    condition = 6


class Jmp(JumpInstruction):
    condition = 7


#########################
# Single operand arithmatic:
#########################


class OneOpArith(Msp430Instruction):
    def __init__(self, op1):
        self.op1 = op1

    def encode(self):
        # TODO:
        bits[15:10] = '00100'
        h1 = (self.opcode << 4)
        return pack_ins(h1)


def oneOpIns(mne, opc):
    """ Helper function to define a one operand arithmetic instruction """
    members = {'opcode': opc}
    ins_cls = type(mne + '_ins', (OneOpArith,), members)


class rrr_ins(OneOpArith):
    opcode = 0


oneOpIns('swpb', 1)
oneOpIns('rra', 2)
oneOpIns('sxt', 3)
oneOpIns('push', 4)
oneOpIns('call', 5)


#########################
# Two operand arithmatic instructions:
#########################


class TwoOpArith(Msp430Instruction):
    def __init__(self, src, dst):
        super().__init__()
        self.src = Msp430SourceOperand(src)
        self.dst = Msp430DestinationOperand(dst)

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
        self.token.bw = self.b # When b=1, the operation is byte mode
        self.token.As = self.src.As
        self.token.Ad = self.dst.Ad
        self.token.destination = self.dst.reg
        self.token.source = self.src.reg
        self.token.opcode = self.opcode
        return self.token.encode() + self.src.extra_bytes


def twoOpIns(mne, opc):
    """ Helper function to define a two operand arithmetic instruction """
    members = {'opcode': opc}
    ins_cls = type(mne + '_ins', (TwoOpArith,), members)


class Mov(TwoOpArith):
    """ Moves the source to the destination """
    opcode = 4


# This is equivalent to the helper function twoOpIns:
class Add(TwoOpArith):
    """ Adds the source to the destination """
    mnemonic = 'add'
    opcode = 5


twoOpIns('addc', 6)
twoOpIns('subc', 7)
twoOpIns('sub', 8)


class Cmp(TwoOpArith):
    opcode = 9


twoOpIns('dadd', 10)
twoOpIns('bit', 11)
twoOpIns('bic', 12)
twoOpIns('bis', 13)
twoOpIns('xor', 14)
twoOpIns('and', 15)
