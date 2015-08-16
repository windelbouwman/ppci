
from ..isa import Instruction, Isa, register_argument, Syntax
from ..token import Token, u16, bit_range, bit, u8
from .registers import Msp430Register, r0, r2, SP, PC
from ...bitfun import align, wrap_negative

isa = Isa()


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


class Imm16Token(Token):
    value = bit_range(0, 16)

    def __init__(self):
        super().__init__(16)

    def encode(self):
        return u16(self.bit_value)


class Msp430Operand:
    pass


class DestinationOperand(Msp430Operand):
    reg = register_argument('reg', Msp430Register, read=True)
    imm = register_argument('imm', int)
    addr = register_argument('addr', str, default_value='')
    Ad = register_argument('Ad', int, default_value=0)
    syntaxi = 'dst', [
        Syntax([reg], set_props={Ad: 0}),
        Syntax(['&', addr], set_props={Ad: 1, reg: r2}),  # absolute address
        Syntax([imm, '(', reg, ')'], set_props={Ad: 1}),
        ]

    @property
    def extra_bytes(self):
        if self.addr != '':
            return u16(0)
        elif (self.Ad == 1):
            return u16(self.imm)
        return bytes()


def reg_dst(reg):
    dst = DestinationOperand()
    dst.reg = reg
    dst.Ad = 0
    return dst


class SourceOperand(Msp430Operand):
    reg = register_argument('reg', Msp430Register, read=True)
    imm = register_argument('imm', int)
    As = register_argument('As', int, default_value=0)
    addr = register_argument('addr', str, default_value='')
    syntaxi = 'src', [
        Syntax([reg], set_props={As: 0}),
        Syntax([imm, '(', reg, ')'], set_props={As: 1}),
        Syntax(['&', addr], set_props={As: 1, reg: r2}),  # absolute address
        Syntax(['@', reg], set_props={As: 2}),
        Syntax(['@', reg, '+'], set_props={As: 3}),
        Syntax(['#', imm], set_props={As: 3, reg: r0}),  # Equivalent to @PC+
        ]

    @property
    def extra_bytes(self):
        if self.addr != '':
            return u16(0)
        elif (self.As == 1) or (self.As == 3 and self.reg == r0):
            return u16(self.imm)
        return bytes()


def const_source(value):
    src = SourceOperand()
    src.As = 3
    src.imm = value
    src.reg = r0
    return src


def reg_src(reg, memref=False, incr=False):
    src = SourceOperand()
    if memref and incr:
        src.As = 3
    elif memref and not incr:
        src.As = 2
    else:
        src.As = 0
    src.reg = reg
    return src


class Msp430Instruction(Instruction):
    isa = isa
    b = 0
    tokens = [Msp430Token]


#########################
# Jump instructions:
#########################

@isa.register_relocation
def apply_rel10bit(sym_value, data, reloc_value):
    """ Apply 10 bit signed relocation """
    assert sym_value % 2 == 0
    offset = (sym_value - (align(reloc_value, 2)) - 2) >> 1
    assert offset in range(-511, 511, 1), str(offset)
    imm10 = wrap_negative(offset, 10)
    data[0] = imm10 & 0xff
    cmd = data[1] & 0xfc
    data[1] = cmd | (imm10 >> 8)


@isa.register_relocation
def apply_abs16_imm1(sym_value, data, reloc_value):
    """ Lookup address and assign to 16 bit """
    assert sym_value % 2 == 0
    data[2] = sym_value & 0xff
    data[3] = (sym_value >> 8) & 0xff


@isa.register_relocation
def apply_abs16_imm2(sym_value, data, reloc_value):
    """ Lookup address and assign to 16 bit """
    # TODO: merge this with imm2 variant
    assert sym_value % 2 == 0
    data[4] = sym_value & 0xff
    data[5] = (sym_value >> 8) & 0xff


class JumpInstruction(Msp430Instruction):
    def encode(self):
        self.token.condition = self.condition
        self.token.offset = 0
        self.token[13] = 1
        return self.token.encode()

    def relocations(self):
        yield (self.target, apply_rel10bit)


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
        self.token[10:16] = 0b000100
        self.token[7:10] = self.opcode
        self.token.bw = self.b
        self.token.As = self.src.As
        self.token.register = self.src.reg.num
        return self.token.encode() + self.src.extra_bytes

    def relocations(self):
        return []


def oneOpIns(mne, opcode):
    """ Helper function to define a one operand arithmetic instruction """
    src = register_argument('src', SourceOperand)
    syntax = [mne, src]
    members = {'opcode': opcode, 'syntax': syntax, 'src': src}
    return type(mne + '_ins', (OneOpArith,), members)


Rrc = oneOpIns('rrc', 0)
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

    def relocations(self):
        if self.src.addr != '':
            yield (self.src.addr, apply_abs16_imm1)
        if self.dst.addr != '':
            if self.src.addr != '':
                yield (self.dst.addr, apply_abs16_imm2)
            else:
                yield (self.dst.addr, apply_abs16_imm1)


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


# pseudo instructions:
def ret():
    return Mov(SourceOperand(reg=SP, As=3), PC)

# -- for instruction selection:

@isa.pattern('stm', 'JMP', cost=2)
def _(self, tree):
    label, tgt = tree.value
    self.emit(Jmp(label, jumps=[tgt]))


@isa.pattern('stm', 'MOVI16(REGI16, reg)', cost=2)
def _(self, tree, c0):
    dst = tree.children[0].value
    self.emit(Mov(reg_src(c0), reg_dst(dst)))


@isa.pattern('reg', 'CONSTI32', cost=4)
def _(self, tree):
    dst = self.newTmp()
    cnst = tree.value
    self.emit(Mov(const_source(cnst), reg_dst(dst)))
    return dst


@isa.pattern('reg', 'REGI16', cost=0)
def _(self, tree):
    return tree.value


# TODO: this is a what strange construct:
@isa.pattern('stm', 'CALL', cost=2)
def _(self, tree):
    label, args, res_var = tree.value
    self.frame.gen_call(label, args, res_var)


@isa.pattern('reg', 'MULI16(reg, reg)', cost=10)
def _(self, tree, c0, c1):
    d = self.newTmp()
    self.emit(Mul1(d, c0, c1))
    return d


@isa.pattern('reg', 'ANDI16(reg, reg)', cost=10)
def _(context, tree, c0, c1):
    d = self.newTmp()
    context.emit(Mov(c0, d))
    context.emit(And(c1, d))
    return d


@isa.pattern('stm', 'STRI16(ANDI16(LDRI16(reg1), reg), reg1)', cost=10)
def _(context, tree, c0, c1):
    d = self.newTmp()
    context.emit(Mov(c0, d))
    context.emit(And(c1, d, As=3))
    return d


#@isa.pattern('reg', 'GLOBALADDRESS', cost=4)
#def _(self, tree):
#    d = self.newTmp()
#    ln = self.frame.add_constant(tree.value)
#    self.emit(Ldr3(d, ln))
#    return d
