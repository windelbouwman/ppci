
from ..isa import Instruction, Isa, register_argument, Syntax
from ..token import Token, u16, bit_range, bit
from .registers import Msp430Register, r0

isa = Isa()
isa.typ2nt[int] = 'imm16'
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


class Msp430Operand:
    pass


class DestinationOperand(Msp430Operand):
    reg = register_argument('reg', Msp430Register, read=True)
    imm = register_argument('imm', int)
    Ad = register_argument('Ad', int, default_value=0)
    syntaxi = 'dst', [
        Syntax([reg], set_props={Ad: 0}),
        Syntax([imm, '(', reg, ')'], set_props={Ad: 1}),
        ]

    @property
    def extra_bytes(self):
        if (self.Ad == 1):
            return u16(self.imm)
        return bytes()


class SourceOperand(Msp430Operand):
    reg = register_argument('reg', Msp430Register, read=True)
    imm = register_argument('imm', int)
    As = register_argument('As', int, default_value=0)
    syntaxi = 'src', [
        Syntax([reg], set_props={As: 0}),
        Syntax([imm, '(', reg, ')'], set_props={As: 1}),
        Syntax(['@', reg], set_props={As: 2}),
        Syntax(['@', reg, '+'], set_props={As: 3}),
        Syntax(['#', imm], set_props={As: 3, reg: r0}),  # Equivalent to @PC+
        ]

    @property
    def extra_bytes(self):
        if (self.As == 1) or (self.As == 3 and self.reg == r0):
            return u16(self.imm)
        return bytes()


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
        self.token.destination = self.dst.reg.num
        self.token.source = self.src.reg.num
        self.token.opcode = self.opcode
        return self.token.encode() + self.src.extra_bytes + self.dst.extra_bytes


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
