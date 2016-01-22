"""
Definitions of msp430 instruction set.
"""

from ..isa import Instruction, Isa, register_argument, Syntax, Constructor
from ..token import Token, u16, bit_range, bit, u8
from .registers import Msp430Register, r0, r2, SP, PC
from ...utils.bitfun import align, wrap_negative

# pylint: disable=no-member,invalid-name


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


class Dst(Constructor):
    reg = register_argument('reg', Msp430Register, write=True)
    imm = register_argument('imm', int)
    addr = register_argument('addr', str, default_value='')
    Ad = register_argument('Ad', int, default_value=0)
    syntaxi = 'dst'

    @property
    def extra_bytes(self):
        if self.addr != '':
            return u16(0)
        elif (self.Ad == 1):
            return u16(self.imm)
        return bytes()


class RegDst(Dst):
    syntax = Syntax([Dst.reg], set_props={Dst.Ad: 0})


class AddrDst(Dst):
    """  absolute address """
    syntax = Syntax(['&', Dst.addr], set_props={Dst.Ad: 1, Dst.reg: r2})


class MemDst(Dst):
    """  register offset memory access, for example: 0x88(R8) """
    syntax = Syntax([Dst.imm, '(', Dst.reg, ')'], set_props={Dst.Ad: 1})


class Src(Constructor):
    reg = register_argument('reg', Msp430Register, read=True)
    imm = register_argument('imm', int)
    As = register_argument('As', int, default_value=0)
    addr = register_argument('addr', str, default_value='')
    syntaxi = 'src'

    @property
    def extra_bytes(self):
        if self.addr != '':
            return u16(0)
        elif (self.As == 1) or (self.As == 3 and self.reg == r0):
            return u16(self.imm)
        return bytes()


class ConstSrc(Src):
    """ Equivalent to @PC+ """
    syntax = Syntax(['#', Src.imm], set_props={Src.As: 3, Src.reg: r0})


class RegSrc(Src):
    """ Simply refer to a register """
    syntax = Syntax([Src.reg], set_props={Src.As: 0})


class AdrSrc(Src):
    """ absolute address """
    syntax = Syntax(['&', Src.addr], set_props={Src.As: 1, Src.reg: r2})


class MemSrc(Src):
    syntax = Syntax(['@', Src.reg], set_props={Src.As: 2})


class MemSrcInc(Src):
    syntax = Syntax(['@', Src.reg, '+'], set_props={Src.As: 3})


class MemSrcOffset(Src):
    syntax = Syntax([Src.imm, '(', Src.reg, ')'], set_props={Src.As: 1})


class Msp430Instruction(Instruction):
    isa = isa
    tokens = [Msp430Token]


# Data instructions:

class Dcd2(Msp430Instruction):
    v = register_argument('v', str)
    syntax = Syntax(['dcd', '=', v])

    def encode(self):
        self.token1[0:16] = 0
        return self.token1.encode()

    def relocations(self):
        return [(self.v, apply_abs16_imm0)]


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
def apply_abs16_imm0(sym_value, data, reloc_value):
    """ Lookup address and assign to 16 bit """
    assert sym_value % 2 == 0
    data[0] = sym_value & 0xff
    data[1] = (sym_value >> 8) & 0xff


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
        self.token1.condition = self.condition
        self.token1.offset = 0
        self.token1[13] = 1
        return self.token1.encode()

    def relocations(self):
        yield (self.target, apply_rel10bit)


def create_jump_instruction(name, condition):
    target = register_argument('target', str)
    syntax = Syntax([name, target])
    members = {'syntax': syntax, 'target': target, 'condition': condition}
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
        self.token1[10:16] = 0b000100
        self.token1[7:10] = self.opcode
        self.token1.bw = self.b
        self.token1.As = self.src.As
        self.token1.register = self.src.reg.num
        return self.token1.encode() + self.src.extra_bytes

    def relocations(self):
        return []


def one_op_instruction(mne, opcode, b=0):
    """ Helper function to define a one operand arithmetic instruction """
    src = register_argument('src', Src)
    syntax = Syntax([mne, src])
    members = {'opcode': opcode, 'syntax': syntax, 'src': src, 'b': b}
    return type(mne + '_ins', (OneOpArith,), members)


Rrc = one_op_instruction('rrc', 0)
Swpb = one_op_instruction('swpb', 1)
Rra = one_op_instruction('rra', 2)
Sxt = one_op_instruction('sxt', 3)
Push = one_op_instruction('push', 4)
Call = one_op_instruction('call', 5)


class Reti(Msp430Instruction):
    syntax = Syntax(['reti'])

    def encode(self):
        self.token1[0:16] = 0x1300
        return self.token1.encode()


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
        self.token1.bw = self.b  # When b=1, the operation is byte mode
        self.token1.As = self.src.As
        self.token1.Ad = self.dst.Ad
        self.token1.destination = self.dst.reg.num
        self.token1.source = self.src.reg.num
        self.token1.opcode = self.opcode
        return self.token1.encode() + self.src.extra_bytes + \
            self.dst.extra_bytes

    def relocations(self):
        if self.src.addr != '':
            yield (self.src.addr, apply_abs16_imm1)
        if self.dst.addr != '':
            if self.src.addr != '':
                yield (self.dst.addr, apply_abs16_imm2)
            else:
                yield (self.dst.addr, apply_abs16_imm1)


def two_op_ins(mne, opc, b=0):
    """ Helper function to define a two operand arithmetic instruction """
    src = register_argument('src', Src)
    dst = register_argument('dst', Dst)
    mne += '.b' if b else '.w'
    syntax = Syntax([mne, src, ',', dst])
    members = {'opcode': opc, 'src': src, 'dst': dst, 'syntax': syntax, 'b': b}
    return type(mne + '_ins', (TwoOpArith,), members)


Mov = two_op_ins('mov', 4)
Movb = two_op_ins('mov', 4, b=1)
Add = two_op_ins('add', 5)
Addc = two_op_ins('addc', 6)
Subc = two_op_ins('subc', 7)
Sub = two_op_ins('sub', 8)
Cmp = two_op_ins('cmp', 9)
Dadd = two_op_ins('dadd', 10)
Bit = two_op_ins('bit', 11)
Bitb = two_op_ins('bit', 11, b=1)
Bic = two_op_ins('bic', 12)
Bicb = two_op_ins('bic', 12, b=1)
Bis = two_op_ins('bis', 13)
Bisb = two_op_ins('bis', 13, b=1)
Xor = two_op_ins('xor', 14)
Xorb = two_op_ins('xor', 14, b=1)
And = two_op_ins('and', 15)
Andb = two_op_ins('and', 15, b=1)


# pseudo instructions:
def ret():
    return pop(PC)


def pop(dst):
    """ Pop value from stack """
    return Mov(MemSrcInc(SP), RegDst(dst))


def push(src):
    return Push(RegSrc(src))


def call(label):
    return Call(AdrSrc(label))


def mov(src, dst):
    """ Register to register move """
    return Mov(RegSrc(src), RegDst(dst), ismove=True)


# -- for instruction selection:

@isa.pattern('stm', 'JMP', cost=2)
def _(self, tree):
    tgt = tree.value
    self.emit(Jmp(tgt.name, jumps=[tgt]))


@isa.pattern('stm', 'CJMP(reg, reg)', cost=2)
def _(context, tree, lhs, rhs):
    op, true_tgt, false_tgt = tree.value
    opnames = {"<": Jl, ">": Jc, "==": Jz, "!=": Jne, ">=": Jge}
    op = opnames[op]
    jmp_ins = Jmp(false_tgt.name, jumps=[false_tgt])
    context.emit(Cmp(RegSrc(lhs), RegDst(rhs)))
    context.emit(op(true_tgt.name, jumps=[true_tgt, jmp_ins]))
    context.emit(jmp_ins)


@isa.pattern('reg', 'MOVI16(reg)', cost=2)
def _(self, tree, c0):
    dst = tree.value
    self.emit(mov(c0, dst))


@isa.pattern('reg', 'MOVI8(reg)', cost=2)
def _(self, tree, c0):
    dst = tree.value
    self.emit(mov(c0, dst))


@isa.pattern('reg', 'CONSTI16', cost=4)
def _(self, tree):
    dst = self.new_reg(Msp430Register)
    cnst = tree.value
    self.emit(Mov(ConstSrc(cnst), RegDst(dst)))
    return dst


@isa.pattern('reg', 'CONSTI8', cost=4)
def _(self, tree):
    dst = self.new_reg(Msp430Register)
    cnst = tree.value
    self.emit(Mov(ConstSrc(cnst), RegDst(dst)))
    return dst


@isa.pattern('reg', 'REGI16', cost=0)
def _(self, tree):
    return tree.value


@isa.pattern('reg', 'REGI8', cost=0)
def _(self, tree):
    return tree.value


@isa.pattern('reg', 'CALL', cost=2)
def _(context, tree):
    label, arg_types, ret_type, args, res_var = tree.value
    context.gen_call(label, arg_types, ret_type, args, res_var)
    return res_var


@isa.pattern('reg', 'MULI16(reg, reg)', cost=10)
def _(self, tree, c0, c1):
    d = self.newTmp()
    self.emit(Mul1(d, c0, c1))
    return d


@isa.pattern('reg', 'ANDI16(reg, reg)', cost=4)
def _(context, tree, c0, c1):
    dst = context.new_reg(Msp430Register)
    context.emit(mov(c0, dst))
    context.emit(And(RegSrc(c1), RegDst(dst)))
    return dst


@isa.pattern('reg', 'SHRI16(reg, reg)', cost=4)
def _(context, tree, c0, c1):
    d = context.new_reg(Msp430Register)
    #context.emit(Mov(c0, RegDst(d)))
    #context.emit(Shr(c1, RegDst(d)))
    # TODO!
    return d


@isa.pattern('reg', 'ADDI16(reg, reg)', cost=4)
def _(context, tree, c0, c1):
    d = context.new_reg(Msp430Register)
    context.emit(mov(c0, d))
    context.emit(Add(RegSrc(c1), RegDst(d)))
    return d


@isa.pattern('reg', 'SUBI16(reg, reg)', cost=4)
def _(context, tree, c0, c1):
    d = context.new_reg(Msp430Register)
    context.emit(mov(c0, d))
    context.emit(Sub(RegSrc(c1), RegDst(d)))
    return d


@isa.pattern('stm', 'STRI16(reg, reg)', cost=2)
def _(context, tree, c0, c1):
    context.emit(Mov(RegSrc(c1), MemDst(0, c0)))


@isa.pattern('stm', 'STRI8(reg, reg)', cost=2)
def _(context, tree, c0, c1):
    context.emit(Movb(RegSrc(c1), MemDst(0, c0)))


@isa.pattern('reg', 'LDRI16(reg)', cost=2)
def _(context, tree, c0):
    d = context.new_reg(Msp430Register)
    context.emit(Mov(MemSrc(c0), RegDst(d)))
    return d


@isa.pattern('reg', 'LDRI8(reg)', cost=2)
def _(context, tree, c0):
    d = context.new_reg(Msp430Register)
    context.emit(Movb(MemSrc(c0), RegDst(d)))
    return d


@isa.pattern('reg', 'LABEL', cost=2)
def _(context, tree):
    d = context.new_reg(Msp430Register)
    ln = context.frame.add_constant(tree.value)
    context.emit(Mov(AdrSrc(ln), RegDst(d)))
    return d
