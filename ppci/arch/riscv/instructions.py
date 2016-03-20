"""
    Definitions of Riscv instructions.
"""

# pylint: disable=no-member,invalid-name

from ..isa import Instruction, Isa, Syntax
from ..isa import register_argument
from ..data_instructions import Dd
from ...utils.bitfun import wrap_negative
from .registers import RiscvRegister
from ..token import Token, u32, bit_range
from .relocations import apply_absaddr32
from .relocations import apply_b_imm12, apply_b_imm20, apply_abs32_imm20
from .relocations import apply_abs32_imm12


# TODO: do not use ir stuff here!
from ...ir import i32


isa = Isa()

isa.register_relocation(apply_b_imm12)
isa.register_relocation(apply_b_imm20)
isa.register_relocation(apply_absaddr32)
isa.register_relocation(apply_abs32_imm20)
isa.register_relocation(apply_abs32_imm12)



# Tokens:
class RiscvToken(Token):
    def __init__(self):
        super().__init__(32)

    def encode(self):
        return u32(self.bit_value)




# Instructions:

class RiscvInstruction(Instruction):
    tokens = [RiscvToken]
    isa = isa


def dcd(v):
    if type(v) is int:
        return Dd(v)
    elif type(v) is str:
        return Dcd2(v)
    else:  # pragma: no cover
        raise NotImplementedError()


class Dcd2(RiscvInstruction):
    v = register_argument('v', str)
    syntax = Syntax(['dcd', '=', v])

    def encode(self):
        self.token1[0:32] = 0
        return self.token1.encode()

    def relocations(self):
        return [(self.v, apply_absaddr32)]


def Mov(*args):
    if len(args) == 2:
        if isinstance(args[1], int):
            return Mov1(*args)
        elif isinstance(args[1], RiscvRegister):
            return Mov2(*args)
    raise Exception()


class Mov1(RiscvInstruction):
    """ Mov Rd, imm16 """
    rd = register_argument('rd', RiscvRegister, write=True)
    imm = register_argument('imm', int)
    syntax = Syntax(['mov', rd, ',', imm])

    def encode(self):
        self.token1[0:7] = 0b0010011
        self.token1[7:12] = self.rd.num
        self.token1[12:20] = 0
        self.token1[20:32] = self.imm
        return self.token1.encode()


class Mov2(RiscvInstruction):
    rd = register_argument('rd', RiscvRegister, write=True)
    rm = register_argument('rm', RiscvRegister, read=True)
    syntax = Syntax(['mov', rd, ',', rm])

    def encode(self):
        self.token1[0:7] = 0b0010011
        self.token1[7:12] = self.rd.num
        self.token1[12:15] = 0
        self.token1[15:20] = self.rm.num
        self.token1[20:32] = 0
        return self.token1.encode()



def Add(*args):
    if len(args) == 3 and isinstance(args[0], RiscvRegister) and \
            isinstance(args[1], RiscvRegister):
        if isinstance(args[2], RiscvRegister):
            return Add1(args[0], args[1], args[2])
        elif isinstance(args[2], int):
            return Add2(args[0], args[1], args[2])
    raise Exception()


def Sub(*args):
    if len(args) == 3 and isinstance(args[0], RiscvRegister) and \
            isinstance(args[1], RiscvRegister):
        if isinstance(args[2], RiscvRegister):
            return Sub1(args[0], args[1], args[2])
        elif isinstance(args[2], int):
            return Sub2(args[0], args[1], args[2])
    raise Exception()





class OpRegRegReg(RiscvInstruction):
    """ add rd, rn, rm """
    def encode(self):
        self.token1[0:7] = 0b0110011
        self.token1[7:12] = self.rd.num
        self.token1[12:15] = self.func
        self.token1[15:20] = self.rn.num
        self.token1[20:25] = self.rm.num
        self.token1[25:32] = self.opcode
        return self.token1.encode()


def make_regregreg(mnemonic, opcode, func):
    rd = register_argument('rd', RiscvRegister, write=True)
    rn = register_argument('rn', RiscvRegister, read=True)
    rm = register_argument('rm', RiscvRegister, read=True)
    syntax = Syntax([mnemonic, rd, ',', rn, ',', rm])
    members = {
        'syntax': syntax, 'rd': rd, 'rn': rn, 'rm': rm, 'opcode': opcode,'func': func}
    return type(mnemonic + '_ins', (OpRegRegReg,), members)

Add3 = make_regregreg('add', 0b0000000,0b000)
Sub3 = make_regregreg('sub', 0b0100000,0b000)
Sll = make_regregreg('sll', 0b0000000,0b001)
Slt = make_regregreg('slt', 0b0000000,0b010)
Sltu = make_regregreg('sltu', 0b0000000,0b011)
Xor = make_regregreg('xor', 0b0000000,0b100)
Srl = make_regregreg('srl', 0b0000000,0b101)
Sra = make_regregreg('sra', 0b0100000,0b101)
Or = make_regregreg('or', 0b0000000,0b110)
And = make_regregreg('and', 0b0000000,0b111)

Add1 = Add3
Sub1 = Sub3
Orr1 = Or
Orr = Or
And1 = And
Eor1 = Xor
Lsl = Sll
Lsl1 = Lsl
Lsr = Srl
Lsr1 = Lsr



class ShiftiBase(RiscvInstruction):
    def encode(self):
        self.token1[0:7] = 0b0010011
        self.token1[7:12] = self.rd.num
        self.token1[12:15] = self.func
        self.token1[15:20] = self.rs1.num
        self.token1[20:25] = self.imm
        self.token1[25:32] = self.code
        return self.token1.encode()

def make_i(mnemonic, code, func):
    rd = register_argument('rd', RiscvRegister, write=True)
    rs1 = register_argument('rs1', RiscvRegister, read=True)
    imm = register_argument('imm', int)
    syntax = Syntax([mnemonic, rd, ',', rs1, ',', imm])
    members = {'syntax': syntax,'func':func, 'code':code,'rd':rd, 'rs1':rs1,'imm':imm}
    return type(mnemonic + '_ins', (ShiftiBase,), members)

Slli = make_i('slli',0b0000000, 0b001)
Srli = make_i('srli',0b0000000, 0b101)
Srai = make_i('srai',0b0100000, 0b101)


class IBase(RiscvInstruction):
    def encode(self):
        self.token1[0:7] = 0b0010011
        self.token1[7:12] = self.rd.num
        self.token1[12:15] = self.func
        self.token1[15:20] = self.rs1.num
        if(self.invert==True):
            self.imm=-self.imm
        if(self.imm<0):
            imm12 = wrap_negative(self.imm, 12)
        else:
            imm12 = self.imm&0xFFF
        self.token1[20:32] = imm12
        return self.token1.encode()

def make_i(mnemonic, func, invert):
    rd = register_argument('rd', RiscvRegister, write=True)
    rs1 = register_argument('rs1', RiscvRegister, read=True)
    imm = register_argument('imm', int)
    syntax = Syntax([mnemonic, rd, ',', rs1, ',', imm])
    members = {'syntax': syntax,'func':func, 'rd':rd, 'rs1':rs1,'imm':imm,'invert':invert}
    return type(mnemonic + '_ins', (IBase,), members)

Addi = make_i('add',0b000, False)
Addi2 = make_i('addi',0b000, False)
Subi = make_i('sub',0b000, True)
Slti = make_i('slti',0b010, False)
Sltiu = make_i('sltiu',0b011, False)
Xori = make_i('xori',0b100, False)
Ori = make_i('ori',0b110, False)
Ori = make_i('andi',0b111, False)

Add2 = Addi
Sub2 = Subi
# Branches:

class Nop(RiscvInstruction):
    syntax = Syntax(['nop'])
    def encode(self):
        self.token1[0:7] = 0b0010011
        self.token1[7:12] = 0
        self.token1[12:15] = 0b000
        self.token1[15:20] = 0
        self.token1[20:32] = 0
        return self.token1.encode()

class SmBase(RiscvInstruction):
    def encode(self):
        self.token1[0:7] = 0b1110011
        self.token1[7:12] = self.rd.num
        self.token1[12:15] = 0b010
        self.token1[15:20] = 0
        self.token1[20:32] = self.code
        return self.token1.encode()

def make_sm(mnemonic,code):
    rd = register_argument('rd', RiscvRegister, write=True)
    imm = register_argument('imm', int)
    syntax = Syntax([mnemonic, rd])
    members = {'syntax': syntax, 'rd':rd, 'code':code}
    return type(mnemonic + '_ins', (SmBase,), members)

Rdcyclei =      make_sm('rdcycle',   0b110000000000)
Rdcyclehi =     make_sm('rdcycleh',  0b110010000000)
Rdtimei =       make_sm('rdtime',    0b110000000001)
Rdtimehi =      make_sm('rdtimeh',   0b110010000001)
Rdinstreti =    make_sm('rdinstret', 0b110000000010)
Rdinstrethi =   make_sm('rdinstreth',0b110010000010)

class Sbreak(RiscvInstruction):
    syntax = Syntax(['sbreak'])
    def encode(self):
        self.token1[0:7] = 0b1110011
        self.token1[7:20] = 0
        self.token1[20:32] = 0b000000000001
        return self.token1.encode()



class BranchBase(RiscvInstruction):
    target = register_argument('target', str)
    def encode(self):
        self.token1[0:7] = 0b1100011
        self.token1[12:15] = self.cond
        if self.invert==True: 
            self.token1[15:20] =  self.rm.num
            self.token1[20:25] =  self.rn.num
        else:
            self.token1[15:20] = self.rn.num
            self.token1[20:25] = self.rm.num
        return self.token1.encode()

    def relocations(self):
        return [(self.target, apply_b_imm12)]




class Bl(RiscvInstruction):
    target = register_argument('target', str)
    rd = register_argument('rd', RiscvRegister, write=True)
    syntax = Syntax(['jal',rd,',', target])
    def encode(self):
        self.token1[0:7] = 0b1101111
        self.token1[7:12] = self.rd.num
        return self.token1.encode()

    def relocations(self):
        return [(self.target, apply_b_imm20)] 

class B(RiscvInstruction):
    target = register_argument('target', str)
    syntax = Syntax(['j', target])
    def encode(self):
        self.token1[0:7] = 0b1101111
        self.token1[7:12] = 0
        return self.token1.encode()

    def relocations(self):
        return [(self.target, apply_b_imm20)] 


class Blr(RiscvInstruction):
    rd = register_argument('rd', RiscvRegister, write=True)
    rs1 = register_argument('rs1', RiscvRegister, read=True)
    offset = register_argument('offset', int)
    syntax = Syntax(['jalr',rd,',',rs1,',',offset])
    def encode(self):
        self.token1[0:7] = 0b1100111
        self.token1[7:12] = self.rd.num
        self.token1[12:15] = 0
        self.token1[15:20] = self.rs1.num
        self.token1[20:32] = self.offset
        return self.token1.encode()


class Lui(RiscvInstruction):
    rd = register_argument('rd', RiscvRegister, write=True)
    imm = register_argument('imm', int)
    syntax = Syntax(['lui',rd,',', imm])
    def encode(self):
        if self.imm<0:
            imm20 = wrap_negative(self.imm>>12,20)
        else:
            imm20 = self.imm>>12
        self.token1[0:7] = 0b0110111
        self.token1[7:12] = self.rd.num
        self.token1[12:32] = imm20
        return self.token1.encode()
        
class Adru(RiscvInstruction):
    rd = register_argument('rd', RiscvRegister, write=True)
    label = register_argument('label', str)
    syntax = Syntax(['lui',rd,',', label])
    def encode(self):
        self.token1[0:7] = 0b0110111
        self.token1[7:12] = self.rd.num
        self.token1[12:32] = 0
        return self.token1.encode()
    def relocations(self):
        return [(self.label, apply_abs32_imm20)]

class Adrl(RiscvInstruction):
    rd = register_argument('rd', RiscvRegister, write=True)
    rs1 = register_argument('rs1', RiscvRegister, read=True)
    label = register_argument('label', str)
    syntax = Syntax(['addi', rd, ',', rs1, ',', label])
    def encode(self):
        self.token1[0:7] = 0b0010011
        self.token1[7:12] = self.rd.num
        self.token1[12:15] = 0
        self.token1[15:20] = self.rs1.num
        self.token1[20:32] = 0
        return self.token1.encode()
    def relocations(self):
        return [(self.label, apply_abs32_imm12)]
    

class Auipc(RiscvInstruction):
    rd = register_argument('rd', RiscvRegister, write=True)
    imm = register_argument('imm', int)
    syntax = Syntax(['auipc',rd,',', imm])
    def encode(self):
        self.token1[0:7] = 0b0010111
        self.token1[7:12] = self.rd.num
        self.token1[12:32] = self.imm
        return self.token1.encode()

def make_branch(mnemonic, cond, invert):
    target = register_argument('target', str)
    rn = register_argument('rn', RiscvRegister, read=True)
    rm = register_argument('rm', RiscvRegister, read=True)
    syntax = Syntax([mnemonic,rn,',',rm,',',target])
    
    members = {
        'syntax': syntax, 'target': target, 'rn':rn, 'rm':rm, 'cond': cond,'invert':invert}
    return type(mnemonic + '_ins', (BranchBase,), members)


Beq = make_branch('beq',0b000, False)
Bne = make_branch('bne', 0b001, False)
Blt = make_branch('blt', 0b100, False)
Bltu = make_branch('bltu', 0b110, False)
Bge = make_branch('bge', 0b101, False)
Bgeu = make_branch('bgeu', 0b111, False)

Bgt = make_branch('bgt', 0b100, True)




def reg_list_to_mask(reg_list):
    mask = 0
    for reg in reg_list:
        mask |= (1 << reg.num)
    return mask





class StrBase(RiscvInstruction):
    def encode(self):
        if (self.offset<0):
            imml5 = wrap_negative(-((-self.offset)&0x1f),5)
        else:
            imml5 = self.offset&0x1f
        immh7 = wrap_negative(self.offset>>5,7)
        self.token1[0:7]=0b0100011
        self.token1[7:12]=imml5
        self.token1[12:15]=self.func
        self.token1[15:20]=self.rs1.num
        self.token1[20:25]=self.rs2.num
        self.token1[25:32]=immh7
        return self.token1.encode()

def make_str(mnemonic, func):
    rs1 = register_argument('rs1', RiscvRegister, read=True)
    rs2 = register_argument('rs2', RiscvRegister, read=True)
    offset = register_argument('offset', int)
    syntax = Syntax([mnemonic, rs1,',',rs2,',',offset])
    members = {'syntax': syntax,'func':func, 'offset': offset, 'rs1':rs1, 'rs2':rs2}
    return type(mnemonic + '_ins', (StrBase,), members)

Sb = make_str('sb', 0b000)
Sh = make_str('sh', 0b001)
Sw = make_str('sw', 0b010)

class LdrBase(RiscvInstruction):
    def encode(self):
        self.token1[0:7]=0b0000011
        self.token1[7:12]=self.rd.num
        self.token1[12:15]=self.func
        self.token1[15:20]=self.rs1.num
        self.token1[20:32]=self.offset&0x3ff
        return self.token1.encode()

def make_ldr(mnemonic, func):
    rd = register_argument('rd', RiscvRegister, write=True)
    rs1 = register_argument('rs1', RiscvRegister, read=True)
    offset = register_argument('offset', int)
    syntax = Syntax([mnemonic, rd,',',rs1,',',offset])
    members = {'syntax': syntax,'func':func, 'offset': offset, 'rd':rd, 'rs1':rs1}
    return type(mnemonic + '_ins', (LdrBase,), members)

Lb = make_ldr('lb', 0b000)
Lh = make_ldr('lh', 0b001)
Lw = make_ldr('lw', 0b010)
Lbu = make_ldr('lbu', 0b100)
Lhu = make_ldr('lhu', 0b101)



class MextBase(RiscvInstruction):
    def encode(self):
        self.token1[0:7]=0b0110011
        self.token1[7:12]=self.rd.num
        self.token1[12:15]=self.func
        self.token1[15:20]=self.rs1.num
        self.token1[20:25]=self.rs2.num
        self.token1[25:32]=0b0000001
        return self.token1.encode()

def make_mext(mnemonic, func):
    rs1 = register_argument('rs1', RiscvRegister, read=True)
    rs2 = register_argument('rs2', RiscvRegister, read=True)
    rd = register_argument('rd', RiscvRegister, write=True)
    syntax = Syntax([mnemonic, rd,',',rs1,',',rs2])
    members = {'syntax': syntax,'func':func, 'rd':rd, 'rs1':rs1, 'rs2':rs2}
    return type(mnemonic + '_ins', (MextBase,), members)

Mul = make_mext('mul', 0b000)
Div = make_mext('div', 0b100)

    


# Instruction selection patterns:
@isa.pattern('stm', 'STRI32(reg, reg)', cost=2)
def _(self, tree, c0, c1):
    self.emit(Sw(c0, c1, 0))


@isa.pattern(
    'stm', 'STRI32(ADDI32(reg, CONSTI32), reg)',
    cost=2,
    condition=lambda t: t.children[0].children[1].value < 256)
def _(context, tree, c0, c1):
    # TODO: something strange here: when enabeling this rule, programs
    # compile correctly...
    offset = tree.children[0].children[1].value
    context.emit(Sw(c0, c1, offset))


@isa.pattern('stm', 'STRI8(reg, reg)', cost=2)
def _(context, tree, c0, c1):
    context.emit(Sb(c0, c1, 0))


@isa.pattern('reg', 'MOVI32(reg)', cost=2)
def _(context, tree, c0):
    context.move(tree.value, c0)
    return tree.value


@isa.pattern('reg', 'MOVI8(reg)', cost=2)
def _(context, tree, c0):
    context.move(tree.value, c0)
    return tree.value


@isa.pattern('stm', 'JMP', cost=2)
def _(context, tree):
    tgt = tree.value
    context.emit(B(tgt.name, jumps=[tgt]))


@isa.pattern('reg', 'REGI32', cost=0)
def _(context, tree):
    return tree.value


@isa.pattern('reg', 'REGI8', cost=0)
def _(context, tree):
    return tree.value


@isa.pattern('reg', 'CONSTI32', cost=4)
def _(context, tree):
    d = context.new_reg(RiscvRegister)
    c0 = tree.value
    context.emit(Lui(d, c0))
    context.emit(Add2(d, d, c0))
    return d


@isa.pattern('reg', 'CONSTI32', cost=2, condition=lambda t: t.value < 256)
def _(context, tree):
    d = context.new_reg(RiscvRegister)
    c0 = tree.value
    assert isinstance(c0, int)
    assert c0 < 256 and c0 >= 0
    context.emit(Mov1(d, c0))
    return d


@isa.pattern('reg', 'CONSTI8', cost=2, condition=lambda t: t.value < 256)
def _(context, tree):
    d = context.new_reg(RiscvRegister)
    c0 = tree.value
    assert isinstance(c0, int)
    assert c0 < 256 and c0 >= 0
    context.emit(Mov1(d, c0))
    return d


@isa.pattern('stm', 'CJMP(reg, reg)', cost=2)
def _(context, tree, c0, c1):
    op, yes_label, no_label = tree.value
    opnames = {"<": Blt, ">": Bgt, "==": Beq, "!=": Bne, ">=": Bge}
    Bop = opnames[op]
    jmp_ins = B(no_label.name, jumps=[no_label])
    context.emit(Bop(c0, c1, yes_label.name, jumps=[yes_label, jmp_ins]))
    context.emit(jmp_ins)


@isa.pattern('reg', 'ADDI32(reg, reg)', cost=2)
def _(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Add1(d, c0, c1))
    return d


@isa.pattern('reg', 'ADDI8(reg, reg)', cost=2)
def _(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Add1(d, c0, c1))
    return d


@isa.pattern(
    'reg', 'ADDI32(reg, CONSTI32)', cost=2,
    condition=lambda t: t.children[1].value < 256)
def _(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[1].value
    context.emit(Add2(d, c0, c1))
    return d


@isa.pattern(
    'reg', 'ADDI32(CONSTI32, reg)', cost=2,
    condition=lambda t: t.children[0].value < 256)
def _(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[0].value
    context.emit(Add2(d, c0, c1))
    return d


@isa.pattern('reg', 'SUBI32(reg, reg)', cost=2)
def _(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Sub1(d, c0, c1))
    return d


@isa.pattern('reg', 'SUBI8(reg, reg)', cost=2)
def _(context, tree, c0, c1):
    # TODO: temporary fix this with an 32 bits sub
    d = context.new_reg(RiscvRegister)
    context.emit(Sub1(d, c0, c1))
    return d


@isa.pattern('reg', 'LABEL', cost=6)
def _(context, tree):
    d = context.new_reg(RiscvRegister)
    ln = context.frame.add_constant(tree.value)
    context.emit(Adru(d,ln))
    context.emit(Adrl(d,d, ln))
    context.emit(Lw(d, d, 0))
    return d


@isa.pattern('reg', 'LDRI8(reg)', cost=2)
def _(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    context.emit(Lb(d, c0, 0))
    return d


@isa.pattern('reg', 'LDRI32(reg)', cost=2)
def _(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    context.emit(Lw(d, c0, 0))
    return d


@isa.pattern('reg', 'CALL', cost=2)
def _(context, tree):
    label, arg_types, ret_type, args, res_var = tree.value
    context.gen_call(label, arg_types, ret_type, args, res_var)
    return res_var


@isa.pattern('reg', 'ANDI32(reg, reg)', cost=2)
def _(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(And1(d, c0, c1))
    return d


@isa.pattern('reg', 'ORI32(reg, reg)', cost=2)
def _(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Orr1(d, c0, c1))
    return d


@isa.pattern('reg', 'SHRI32(reg, reg)', cost=2)
def _(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Lsr1(d, c0, c1))
    return d


@isa.pattern('reg', 'SHLI32(reg, reg)', cost=2)
def _(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Lsl1(d, c0, c1))
    return d


@isa.pattern('reg', 'MULI32(reg, reg)', cost=10)
def _(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Mul(d, c0, c1))
    return d


@isa.pattern('reg', 'LDRI32(ADDI32(reg, CONSTI32))', cost=2)
def _(context, tree, c0):
    d = context.new_reg(RiscvRegister)
    c1 = tree.children[0].children[1].value
    assert isinstance(c1, int)
    context.emit(Lw(d, c0, c1))
    return d


@isa.pattern('reg', 'DIVI32(reg, reg)', cost=10)
def _(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    # Generate call into runtime lib function!
    context.gen_call('__sdiv', [i32, i32], i32, [c0, c1], d)
    return d


@isa.pattern('reg', 'REMI32(reg, reg)', cost=10)
def _(context, tree, c0, c1):
    # Implement remainder as a combo of div and mls (multiply substract)
    d = context.new_reg(RiscvRegister)
    context.gen_call('__sdiv', [i32, i32], i32, [c0, c1], d)
    context.emit(Mul(c1, c1, d))
    d2 = context.new_reg(RiscvRegister)
    context.emit(Sub(d2,c0,c1))
    return d2


@isa.pattern('reg', 'XORI32(reg, reg)', cost=2)
def _(context, tree, c0, c1):
    d = context.new_reg(RiscvRegister)
    context.emit(Eor1(d, c0, c1))
    return d

# TODO: implement DIVI32 by library call.
# TODO: Do that here, or in irdag?


