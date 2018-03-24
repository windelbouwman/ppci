""" Definitions of msp430 instruction set. """

from ..encoding import Instruction, Operand, Syntax, Constructor, Transform
from ..generic_instructions import ArtificialInstruction
from ..generic_instructions import RegisterUseDef
from ..isa import Relocation, Isa
from ..token import Token, bit_range, bit
from .registers import Msp430Register, r2, r3, r12, r13, SP, PC
from ...utils.bitfun import align

# pylint: disable=no-member,invalid-name


isa = Isa()


class Msp430Token(Token):
    class Info:
        size = 16


class Msp430SingleOperandToken(Msp430Token):
    prefix = bit_range(10, 16)
    opcode = bit_range(7, 10)
    bw = bit(6)
    As = bit_range(4, 6)
    source = bit_range(0, 4)


class Msp430JumpToken(Msp430Token):
    opcode = bit_range(13, 16)
    condition = bit_range(10, 13)
    offset = bit_range(0, 10)


class Msp430TwoOperandToken(Msp430Token):
    opcode = bit_range(12, 16)
    source = bit_range(8, 12)
    Ad = bit(7)
    bw = bit(6)
    As = bit_range(4, 6)
    destination = bit_range(0, 4)


class SrcImmToken(Msp430Token):
    srcimm = bit_range(0, 16)


class DstImmToken(Msp430Token):
    dstimm = bit_range(0, 16)


# Relocation functions:
@isa.register_relocation
class Rel10Relocation(Relocation):
    """ Apply 10 bit signed relocation """
    name = 'rel10'
    token = Msp430JumpToken
    field = 'offset'

    def calc(self, sym_value, reloc_value):
        assert sym_value % 2 == 0
        offset = (sym_value - (align(reloc_value, 2)) - 2) >> 1
        assert offset in range(-511, 511, 1), str(offset)
        return offset


@isa.register_relocation
class Abs16Relocation(Relocation):
    """ Lookup address and assign to 16 bit """
    name = 'abs16'
    token = SrcImmToken
    field = 'srcimm'

    def calc(self, sym_value, reloc_value):
        assert sym_value % 2 == 0
        return sym_value


class Dst(Constructor):
    reg = Operand('reg', Msp430Register, write=True)
    imm = Operand('imm', int)
    Ad = Operand('Ad', int)
    is_reg_target = False
    is_special = False


class RegDst(Dst):
    is_reg_target = True
    syntax = Syntax([Dst.reg])
    patterns = {'Ad': 0, 'destination': Dst.reg}


class AddrDst(Dst):
    """  absolute address """
    addr = Operand('addr', str)
    tokens = [DstImmToken]
    syntax = Syntax(['&', addr])
    is_special = True
    patterns = {'Ad': 1, 'destination': 2}

    def gen_relocations(self):
        yield Abs16Relocation(self.addr)


class MemDst(Dst):
    """  register offset memory access, for example: 0x88(R8) """
    tokens = [DstImmToken]
    syntax = Syntax([Dst.imm, '(', Dst.reg, ')'])
    patterns = {'Ad': 1, 'destination': Dst.reg, 'dstimm': Dst.imm}


dst_modes = (RegDst, AddrDst, MemDst)


class Src(Constructor):
    reg = Operand('reg', Msp430Register, read=True)
    imm = Operand('imm', int)
    As = Operand('As', int)
    is_reg_target = False
    is_special = False


class ConstSrc(Src):
    """ Equivalent to @PC+ """
    tokens = [SrcImmToken]
    syntax = Syntax(['#', Src.imm])
    is_special = True
    patterns = {'As': 3, 'source': 0, 'srcimm': Src.imm}


class ConstLabelSrc(Src):
    """ Equivalent to @PC+ """
    addr = Operand('addr', str)
    tokens = [SrcImmToken]
    syntax = Syntax(['#', addr])
    is_special = True
    patterns = {'As': 3, 'source': 0}

    def gen_relocations(self):
        yield Abs16Relocation(self.addr)


class AsConstTransform(Transform):
    as_cn_map = {-1: 3, 0: 0, 1: 1, 2: 2, 4: 2, 8: 3}

    def forwards(self, value):
        return self.as_cn_map[value]


class RegConstTransform(Transform):
    rg_cn_map = {-1: 3, 0: 3, 1: 3, 2: 3, 4: 2, 8: 2}

    def forwards(self, value):
        return self.rg_cn_map[value]


class SmallConstSrc(Src):
    """ A small integer constant special encoding """
    syntax = Syntax(['#', Src.imm], priority=2)
    is_special = True
    patterns = {
        'As': AsConstTransform(Src.imm),
        'source': RegConstTransform(Src.imm),
        }


def small_const_src(x):
    """ Helper to generate small integer constants """
    assert x in (-1, 0, 1, 2, 4, 8)
    if x == -1:
        return SmallConstSrc(-1, reg=r3, As=3)
    elif x == 0:
        return SmallConstSrc(0, reg=r3, As=0)
    elif x == 1:
        return SmallConstSrc(1, reg=r3, As=1)
    elif x == 2:
        return SmallConstSrc(2, reg=r3, As=2)
    elif x == 4:
        return SmallConstSrc(4, reg=r2, As=2)
    elif x == 8:
        return SmallConstSrc(8, reg=r2, As=3)
    else:
        raise NotImplementedError()


class RegSrc(Src):
    """ Simply refer to a register """
    is_reg_target = True
    syntax = Syntax([Src.reg])
    patterns = {'As': 0, 'source': Src.reg}


class AdrSrc(Src):
    """ absolute address """
    is_special = True
    addr = Operand('addr', str)
    tokens = [SrcImmToken]
    syntax = Syntax(['&', addr])
    patterns = {'As': 1, 'source': 2}

    def gen_relocations(self):
        yield Abs16Relocation(self.addr)


class MemSrc(Src):
    """ Memory content """
    syntax = Syntax(['@', Src.reg])
    patterns = {'As': 2, 'source': Src.reg}


class MemSrcInc(Src):
    """ Memory content post increment """
    syntax = Syntax(['@', Src.reg, '+'])
    patterns = {'As': 3, 'source': Src.reg}


class MemSrcOffset(Src):
    tokens = [SrcImmToken]
    syntax = Syntax([Src.imm, '(', Src.reg, ')'])
    patterns = {'As': 1, 'source': Src.reg, 'srcimm': Src.imm}


src_modes = (
    AdrSrc, RegSrc, MemSrc, MemSrcInc, MemSrcOffset,
    SmallConstSrc, ConstSrc, ConstLabelSrc)


class Msp430Instruction(Instruction):
    isa = isa


#########################
# Jump instructions:
#########################

class JumpInstruction(Msp430Instruction):
    tokens = [Msp430JumpToken]

    def gen_relocations(self):
        yield Rel10Relocation(self.target)


def create_jump_instruction(name, condition):
    target = Operand('target', str)
    syntax = Syntax([name, ' ', target])
    patterns = {'condition': condition, 'opcode': 1}
    members = {
        'syntax': syntax, 'target': target, 'patterns': patterns}
    return type(name.title(), (JumpInstruction, ), members)


Jne = create_jump_instruction('jne', 0)
Jnz = create_jump_instruction('jnz', 0)
Jeq = create_jump_instruction('jeq', 1)
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
    tokens = [Msp430SingleOperandToken]


def one_op_instruction(mne, opcode, b=0, src_write=True):
    """ Helper function to define a one operand arithmetic instruction """
    src = Operand('src', src_modes)
    patterns = {'prefix': 0b000100, 'opcode': opcode, 'bw': b}
    if b:
        syntax = Syntax([mne, '.', 'b', ' ', src])
        class_name = mne + 'b'
    else:
        syntax = Syntax([mne, ' ', src])
        class_name = mne
    members = {
        'opcode': opcode, 'syntax': syntax, 'src': src, 'patterns': patterns}
    return type(class_name.title(), (OneOpArith,), members)


class MemByReg(Instruction):
    """ Memory content """
    reg = Operand('reg', Msp430Register, read=True)
    tokens = []
    patterns = {'As': 2, 'source': reg}
    syntax = Syntax(['@', reg])


Rrcw = one_op_instruction('rrc', 0, b=0)
Rrcb = one_op_instruction('rrc', 0, b=1)
Swpb = one_op_instruction('swpb', 1)
Rraw = one_op_instruction('rra', 2, b=0)
Rrab = one_op_instruction('rra', 2, b=1)
Sxt = one_op_instruction('sxt', 3)
Push = one_op_instruction('push', 4, src_write=False)
Call = one_op_instruction('call', 5, src_write=False)


class Reti(Msp430Instruction):
    tokens = [SrcImmToken]
    syntax = Syntax(['reti'])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:16] = 0x1300
        return tokens.encode()


#########################
# Two operand arithmatic instructions:
#########################


class TwoOpArithInstruction(Msp430Instruction):
    tokens = [Msp430TwoOperandToken]

    @property
    def used_registers(self):
        s = []
        # Source:
        if not self.src.is_special:
            if self.src.is_reg_target:
                s.append(self.src.reg)
            else:
                s.append(self.src.reg)

        # Dst:
        if not self.dst.is_special:
            if self.dst.is_reg_target:
                if self.dst_read:
                    s.append(self.dst.reg)
            else:
                s.append(self.dst.reg)
        s.extend(self.extra_uses)
        return s

    @property
    def defined_registers(self):
        s = []
        if self.dst.is_reg_target and not self.dst.is_special:
            if self.dst_write:
                s.append(self.dst.reg)
        s.extend(self.extra_defs)
        return s


def two_op_ins(mne, opc, b=0, dst_read=True, dst_write=True):
    """ Helper function to define a two operand arithmetic instruction """
    src = Operand('src', src_modes)
    dst = Operand('dst', dst_modes)
    if b:
        syntax = Syntax([mne, '.', 'b', ' ', src, ',', ' ', dst])
        class_name = mne + 'b'
    else:
        syntax = Syntax([mne, '.', 'w', ' ', src, ',', ' ', dst])
        class_name = mne + 'w'
    patterns = {'opcode': opc, 'bw': b}
    members = {
        'patterns': patterns, 'src': src, 'dst': dst, 'syntax': syntax,
        'dst_read': dst_read, 'dst_write': dst_write
        }
    return type(class_name.title(), (TwoOpArithInstruction,), members)


Mov = two_op_ins('mov', 4, dst_read=False)
Movb = two_op_ins('mov', 4, b=1, dst_read=False)
Add = two_op_ins('add', 5)
Addc = two_op_ins('addc', 6)
Subc = two_op_ins('subc', 7)
Sub = two_op_ins('sub', 8)
Cmp = two_op_ins('cmp', 9, dst_write=False)
Cmpb = two_op_ins('cmp', 9, b=1, dst_write=False)
Dadd = two_op_ins('dadd', 10)
Bit = two_op_ins('bit', 11, dst_write=False)
Bitb = two_op_ins('bit', 11, b=1, dst_write=False)
Bicw = two_op_ins('bic', 12)
Bicb = two_op_ins('bic', 12, b=1)
Bisw = two_op_ins('bis', 13)
Bisb = two_op_ins('bis', 13, b=1)
Xor = two_op_ins('xor', 14)
Xorb = two_op_ins('xor', 14, b=1)
And = two_op_ins('and', 15)
Andb = two_op_ins('and', 15, b=1)


# pseudo instructions:


class PseudoMsp430Instruction(ArtificialInstruction):
    """ Base class for all pseudo instructions """
    isa = isa


class Ret(PseudoMsp430Instruction):
    """ Pop value from stack """
    syntax = Syntax(['ret'])

    def render(self):
        yield Pop(PC)


class Pop(PseudoMsp430Instruction):
    """ Pop value from stack """
    dst = Operand('dst', Msp430Register, write=True)
    syntax = Syntax(['pop', ' ', dst])

    def render(self):
        yield Mov(MemSrcInc(SP), RegDst(self.dst))


class Nop(PseudoMsp430Instruction):
    """ no op implemented as mov #0, r3 """
    syntax = Syntax(['nop'])

    def render(self):
        yield Mov(small_const_src(0), RegDst(r3))


class Clrc(PseudoMsp430Instruction):
    """ clear carry implemented as bic #1, sr """
    syntax = Syntax(['clrc'])

    def render(self):
        yield Bicw(small_const_src(1), RegDst(r2))


class Clrn(PseudoMsp430Instruction):
    """ clear negative implemented as bic #4, sr """
    syntax = Syntax(['clrn'])

    def render(self):
        yield Bicw(small_const_src(4), RegDst(r2))


class Clrz(PseudoMsp430Instruction):
    """ clear zero implemented as bic #2, sr """
    syntax = Syntax(['clrz'])

    def render(self):
        yield Bicw(small_const_src(2), RegDst(r2))


def push(reg):
    """ Push register helper """
    return Push(RegSrc(reg))


def call(label, clobbers=()):
    """ Helper function which creates a call instruction """
    if isinstance(label, str):
        return Call(ConstLabelSrc(label), clobbers=clobbers)
    elif isinstance(label, Msp430Register):
        return Call(RegSrc(label), clobbers=clobbers)
    else:
        raise TypeError('Expected str or register, got {}'.format(label))


def mov(src, dst):
    """ Register to register move """
    return Mov(RegSrc(src), RegDst(dst), ismove=True)


# -- for instruction selection:

@isa.pattern('stm', 'JMP', size=4)
def pattern_jmp(context, tree):
    tgt = tree.value
    context.emit(Jmp(tgt.name, jumps=[tgt]))


@isa.pattern('stm', 'CJMPI16(reg, reg)', size=10)
@isa.pattern('stm', 'CJMPI8(reg, reg)', size=10)
def pattern_cjmp(context, tree, lhs, rhs):
    op, true_tgt, false_tgt = tree.value
    opnames = {
        "<": Jl, ">": Jl, "==": Jz, "!=": Jne, ">=": Jge, '<=': Jge,
    }
    op_ins = opnames[op]
    if op in ['>', '<=']:
        # Swap operands here!
        # This is really hairy code, but it should work!
        lhs, rhs = rhs, lhs
    jmp_ins = Jmp(false_tgt.name, jumps=[false_tgt])
    # cmp does a dummy dst - src
    context.emit(Cmp(RegSrc(rhs), RegDst(lhs)))
    context.emit(op_ins(true_tgt.name, jumps=[true_tgt, jmp_ins]))
    context.emit(jmp_ins)


@isa.pattern('stm', 'MOVI16(reg)', size=2, cycles=1, energy=1)
@isa.pattern('stm', 'MOVU16(reg)', size=2, cycles=1, energy=1)
def pattern_mov16(context, tree, c0):
    dst = tree.value
    context.emit(mov(c0, dst))


@isa.pattern('stm', 'MOVI8(reg)', size=2)
@isa.pattern('stm', 'MOVU8(reg)', size=2)
def pattern_mov8(context, tree, c0):
    dst = tree.value
    context.emit(mov(c0, dst))


@isa.pattern('cnst', 'CONSTI8', size=0, cycles=0, energy=0)
@isa.pattern('cnst', 'CONSTU8', size=0, cycles=0, energy=0)
@isa.pattern('cnst', 'CONSTI16', size=0, cycles=0, energy=0)
@isa.pattern('cnst', 'CONSTU16', size=0, cycles=0, energy=0)
def pattern_cnst(context, tree):
    return tree.value


@isa.pattern('cnst', 'I16TOI16(cnst)', size=0, cycles=0, energy=0)
@isa.pattern('cnst', 'I16TOU16(cnst)', size=0, cycles=0, energy=0)
@isa.pattern('cnst', 'U16TOU16(cnst)', size=0, cycles=0, energy=0)
@isa.pattern('cnst', 'U16TOI16(cnst)', size=0, cycles=0, energy=0)
def pattern_i16toi16_const(context, tree, c0):
    return c0


@isa.pattern('cnstsrc', 'cnst', size=2, cycles=0, energy=0)
def pattern_cnst_src(context, tree, c0):
    return ConstSrc(c0)


@isa.pattern('reg', 'cnstsrc', size=4, cycles=1, energy=1)
def pattern_const16(context, tree, c0):
    dst = context.new_reg(Msp430Register)
    context.emit(Mov(c0, RegDst(dst)))
    return dst


@isa.pattern('reg', 'REGI8', size=0, cycles=0, energy=0)
@isa.pattern('reg', 'REGU8', size=0, cycles=0, energy=0)
@isa.pattern('reg', 'REGI16', size=0, cycles=0, energy=0)
@isa.pattern('reg', 'REGU16', size=0, cycles=0, energy=0)
def pattern_reg16(context, tree):
    return tree.value


@isa.pattern('reg', 'I16TOI16(reg)', size=0, cycles=0, energy=0)
@isa.pattern('reg', 'I16TOU16(reg)', size=0, cycles=0, energy=0)
@isa.pattern('reg', 'U16TOU16(reg)', size=0, cycles=0, energy=0)
@isa.pattern('reg', 'U16TOI16(reg)', size=0, cycles=0, energy=0)
def pattern_i16toi16(context, tree, c0):
    return c0


@isa.pattern('reg', 'I16TOI8(reg)', size=0, cycles=0, energy=0)
@isa.pattern('reg', 'I16TOU8(reg)', size=0, cycles=0, energy=0)
def pattern_i16toi8(context, tree, c0):
    # Create a new register and mask it with 0xff:
    d = context.new_reg(Msp430Register)
    context.emit(mov(c0, d))
    context.emit(And(ConstSrc(0xff), RegDst(d)))
    return d


@isa.pattern('reg', 'I8TOI16(reg)', size=0, cycles=0, energy=0)
def pattern_i8toi16(context, tree, c0):
    """ Sign extend signed byte to signed short """
    d = context.new_reg(Msp430Register)
    context.emit(mov(c0, d))
    context.emit(Sxt(RegSrc(d)))
    return d


@isa.pattern('reg', 'U8TOI16(reg)', size=0, cycles=0, energy=0)
def pattern_u8toi16(context, tree, c0):
    """ byte to signed short """
    d = context.new_reg(Msp430Register)
    context.emit(mov(c0, d))
    context.emit(And(ConstSrc(0xff), RegDst(d)))
    return d


def call_intrinsic(context, label, args, clobbers=()):
    """ Generate a call to an intrinsic function """
    c0, c1 = args
    context.move(r12, c0)
    context.move(r13, c1)
    context.emit(RegisterUseDef(uses=(r12, r13)))
    context.emit(call(label, clobbers=clobbers))
    context.emit(RegisterUseDef(defs=(r12,)))
    d = context.new_reg(Msp430Register)
    context.move(d, r12)
    return d


@isa.pattern('reg', 'MULI16(reg, reg)', size=10)
def pattern_mul_i16(context, tree, c0, c1):
    return call_intrinsic(
        context, 'runtime_mulsi3', (c0, c1),
        clobbers=context.arch.caller_save)


@isa.pattern('reg', 'MULU16(reg, reg)', size=10)
def pattern_mul_u16(context, tree, c0, c1):
    return call_intrinsic(
        context, 'runtime_umulsi3', (c0, c1),
        clobbers=context.arch.caller_save)


@isa.pattern('reg', 'DIVI16(reg, reg)', size=10)
def pattern_div_i16(context, tree, c0, c1):
    return call_intrinsic(
        context, 'runtime_divsi3', (c0, c1),
        clobbers=context.arch.caller_save)


@isa.pattern('reg', 'DIVU16(reg, reg)', size=10)
def pattern_div_u16(context, tree, c0, c1):
    return call_intrinsic(
        context, 'runtime_udivsi3', (c0, c1),
        clobbers=context.arch.caller_save)


@isa.pattern('reg', 'REMI16(reg, reg)', size=10)
def pattern_rem_i16(context, tree, c0, c1):
    return call_intrinsic(
        context, 'runtime_modsi3', (c0, c1),
        clobbers=context.arch.caller_save)


@isa.pattern('reg', 'REMU16(reg, reg)', size=10)
def pattern_rem_u16(context, tree, c0, c1):
    return call_intrinsic(
        context, 'runtime_umodsi3', (c0, c1),
        clobbers=context.arch.caller_save)


@isa.pattern('reg', 'ANDI16(reg, reg)', size=4)
@isa.pattern('reg', 'ANDU16(reg, reg)', size=4)
def pattern_and16(context, tree, c0, c1):
    dst = context.new_reg(Msp430Register)
    context.emit(mov(c0, dst))
    context.emit(And(RegSrc(c1), RegDst(dst)))
    return dst


@isa.pattern('reg', 'ORI16(reg, reg)', size=4)
@isa.pattern('reg', 'ORU16(reg, reg)', size=4)
def pattern_or16(context, tree, c0, c1):
    dst = context.new_reg(Msp430Register)
    context.emit(mov(c0, dst))
    context.emit(Bisw(RegSrc(c1), RegDst(dst)))
    return dst


@isa.pattern('reg', 'SHRI16(reg, reg)', size=4)
def pattern_shr16(context, tree, c0, c1):
    return call_intrinsic(context, '__shr', (c0, c1), clobbers=[r13])


@isa.pattern('reg', 'SHLI16(reg, reg)', size=4)
def pattern_shl16(context, tree, c0, c1):
    return call_intrinsic(context, '__shl', (c0, c1), clobbers=[r13])


@isa.pattern('reg', 'ADDI16(reg, reg)', size=4, cycles=1, energy=1)
@isa.pattern('reg', 'ADDU16(reg, reg)', size=4, cycles=1, energy=1)
def pattern_add16(context, tree, c0, c1):
    d = context.new_reg(Msp430Register)
    context.emit(mov(c0, d))
    context.emit(Add(RegSrc(c1), RegDst(d)))
    return d


@isa.pattern('reg32', 'ADDI32(reg32, reg32)', size=8, cycles=2, energy=2)
@isa.pattern('reg32', 'ADDU32(reg32, reg32)', size=8, cycles=2, energy=2)
def pattern_add32(context, tree, c0, c1):
    # Add two register pairs into a third register pair!
    dh = context.new_reg(Msp430Register)
    dl = context.new_reg(Msp430Register)
    c0h, c0l = c0
    c1h, c1l = c1
    context.emit(mov(c0h, dh))
    context.emit(mov(c0l, dl))
    context.emit(Add(RegSrc(c1l), RegDst(dl)))
    context.emit(Addc(RegSrc(c1h), RegDst(dh)))
    return (dh, dl)


@isa.pattern('reg', 'SUBI16(reg, reg)', size=4)
@isa.pattern('reg', 'SUBU16(reg, reg)', size=4)
def pattern_sub16(context, tree, c0, c1):
    d = context.new_reg(Msp430Register)
    context.emit(mov(c0, d))
    context.emit(Sub(RegSrc(c1), RegDst(d)))
    return d


@isa.pattern('reg32', 'SUBI32(reg32, reg32)', size=8)
@isa.pattern('reg32', 'SUBU32(reg32, reg32)', size=8)
def pattern_sub32(context, tree, c0, c1):
    dh = context.new_reg(Msp430Register)
    dl = context.new_reg(Msp430Register)
    c0h, c0l = c0
    c1h, c1l = c1
    context.emit(mov(c0h, dh))
    context.emit(mov(c0l, dl))
    context.emit(Sub(RegSrc(c1l), RegDst(dl)))
    context.emit(Subc(RegSrc(c1h), RegDst(dh)))
    return (dh, dl)


@isa.pattern('reg', 'NEGI16(reg)', size=4)
@isa.pattern('reg', 'NEGU16(reg)', size=4)
def pattern_neg16(context, tree, c0):
    d = context.new_reg(Msp430Register)
    context.emit(Mov(SmallConstSrc(0), RegDst(d)))
    context.emit(Sub(RegSrc(c0), RegDst(d)))
    return d


@isa.pattern('reg', 'INVU16(reg)', size=4)
def pattern_inv16(context, tree, c0):
    d = context.new_reg(Msp430Register)
    context.emit(mov(c0, d))
    context.emit(Xor(SmallConstSrc(-1), RegDst(d)))
    return d


@isa.pattern('memdst', 'reg', size=2, cycles=0, energy=0)
def pattern_mem_dst(context, tree, c0):
    return MemDst(0, c0)


@isa.pattern('memdst', 'ADDU16(reg, cnst)', size=2, cycles=0, energy=0)
def pattern_mem_dst_const(context, tree, c0, c1):
    return MemDst(c1, c0)


@isa.pattern('memdst', 'FPRELU16', size=2, cycles=0, energy=0)
def pattern_memdst_fprel(context, tree):
    offset = tree.value.offset
    # frame pointer is not used, use stack pointer
    return MemDst(offset, SP)


@isa.pattern('stm', 'STRI16(memdst, reg)', size=2)
@isa.pattern('stm', 'STRU16(memdst, reg)', size=2)
def pattern_str16(context, tree, c0, c1):
    context.emit(Mov(RegSrc(c1), c0))


@isa.pattern('stm', 'STRI8(memdst, reg)', size=2)
@isa.pattern('stm', 'STRU8(memdst, reg)', size=2)
def pattern_str8(context, tree, c0, c1):
    context.emit(Movb(RegSrc(c1), c0))


@isa.pattern('memsrc', 'reg', size=0, cycles=0, energy=0)
def pattern_mem_src(context, tree, c0):
    return MemSrc(c0)


@isa.pattern('memsrc', 'ADDU16(reg, cnst)', size=2, cycles=0, energy=0)
def pattern_mem_src_offset(context, tree, c0, c1):
    return MemSrcOffset(c1, c0)


@isa.pattern('memsrc', 'FPRELU16', size=2, cycles=0, energy=0)
def pattern_mem_src_fprel(context, tree):
    offset = tree.value.offset
    return MemSrcOffset(offset, SP)


@isa.pattern('reg', 'LDRI16(memsrc)', size=2, cycles=3, energy=2)
@isa.pattern('reg', 'LDRU16(memsrc)', size=2, cycles=3, energy=2)
def pattern_ldr16(context, tree, c0):
    d = context.new_reg(Msp430Register)
    context.emit(Mov(c0, RegDst(d)))
    return d


@isa.pattern('reg', 'LDRI8(memsrc)', size=2)
@isa.pattern('reg', 'LDRU8(memsrc)', size=2)
def pattern_ldr8(context, tree, c0):
    d = context.new_reg(Msp430Register)
    context.emit(Movb(c0, RegDst(d)))
    return d


@isa.pattern('reg', 'FPRELU16', size=8, cycles=2, energy=2)
def pattern_fprel(context, tree):
    d = context.new_reg(Msp430Register)
    offset = tree.value.offset
    # frame pointer is r4:
    context.emit(mov(SP, d))
    context.emit(Add(ConstSrc(offset), RegDst(d)))
    return d


@isa.pattern('reg', 'LABEL', size=2)
def pattern_label(context, tree):
    d = context.new_reg(Msp430Register)
    ln = context.frame.add_constant(tree.value)
    context.emit(Mov(AdrSrc(ln), RegDst(d)))
    return d
