from ..basetarget import Register, Instruction, Target, Label, Alignment
from .instructions import Add2, Sub, Sub3, Add3, Cmp, Lsl, Lsr, Orr, Add, Cmp2, Sub2, Mul, And
from .instructions import Dcd, Pop, Push, Yield, Mov2, Mov3
from .instructions import B, Bl, Bne, Beq, Blt, Bgt, Ble, Bge
from .instructions import Ldr, Str2, Ldr2, Str1, Ldr1, Ldr3, Adr

from .frame import ArmFrame
from .arminstructionselector import ArmInstructionSelector
from ..arm.registers import R0, R1, R2, R3, R4, R5, R6, R7, SP, LR, PC
from ..arm.registers import register_range
from ...assembler import BaseAssembler


""" ARM target description. """

# TODO: encode this in DSL (domain specific language)
# TBD: is this required?
# TODO: make a difference between armv7 and armv5?


class ThumbAssembler(BaseAssembler):
    def __init__(self, target):
        super().__init__(target)
        self.target.add_keyword('section')
        self.target.add_instruction(['section', 'ID'],
                lambda rhs: self.select_section(rhs[1].val))
        self.make_parser()

    def select_section(self, name):
        self.flush()
        self.stream.select_section(name)


class ThumbTarget(Target):
    def __init__(self):
        super().__init__('thumb')
        self.ins_sel = ArmInstructionSelector()
        self.FrameClass = ArmFrame
        self.add_rules()

        # Add lowering options:
        self.add_lowering(Str2, lambda im: Str2(im.src[1], im.src[0], im.others[0]))
        self.add_lowering(Ldr2, lambda im: Ldr2(im.dst[0], im.src[0], im.others[0]))
        self.add_lowering(Ldr3, lambda im: Ldr3(im.dst[0],  im.others[0]))
        self.add_lowering(Adr, lambda im: Adr(im.dst[0],  im.others[0]))
        self.add_lowering(Mov3, lambda im: Mov3(im.dst[0],  im.others[0]))
        self.add_lowering(Add2, lambda im: Add2(im.dst[0], im.src[0], im.others[0]))
        self.add_lowering(Sub2, lambda im: Sub2(im.dst[0], im.src[0], im.others[0]))
        self.add_lowering(Mov2, lambda im: Mov2(im.dst[0], im.src[0]))
        self.add_lowering(Add3, lambda im: Add3(im.dst[0], im.src[0], im.src[1]))
        self.add_lowering(Sub3, lambda im: Sub3(im.dst[0], im.src[0], im.src[1]))
        self.add_lowering(Mul, lambda im: Mul(im.src[0], im.dst[0]))
        self.add_lowering(And, lambda im: And(im.src[0], im.src[1]))
        self.add_lowering(Orr, lambda im: Orr(im.src[0], im.src[1]))
        self.add_lowering(Lsl, lambda im: Lsl(im.src[0], im.src[1]))
        self.add_lowering(Lsr, lambda im: Lsr(im.src[0], im.src[1]))
        self.add_lowering(Cmp, lambda im: Cmp(im.src[0], im.src[1]))

        self.assembler = ThumbAssembler(self)

    def emit_global(self, outs, lname):
        outs.emit(Label(lname))
        outs.emit(Dcd(0))

    def add_rules(self):

        # Add instructions:
        self.add_keyword('dcd')
        self.add_instruction(['dcd', 'imm32'], lambda rhs: Dcd(rhs[1]))

        self.add_keyword('mov')
        self.add_instruction(['mov', 'reg8', ',', 'reg8'],
                lambda rhs: Mov2(rhs[1], rhs[3]))

        self.add_instruction(['mov', 'reg8', ',', 'imm8'],
                lambda rhs: Mov3(rhs[1], rhs[3]))

        self.add_keyword('add')
        self.add_instruction(['add', 'reg8', ',', 'reg8', ',', 'imm3'],
                lambda rhs: Add2(rhs[1], rhs[3], rhs[5]))

        self.add_instruction(['add', 'reg8', ',', 'reg8', ',', 'reg8'],
                lambda rhs: Add3(rhs[1], rhs[3], rhs[5]))

        self.add_keyword('sub')
        self.add_instruction(['sub', 'reg8', ',', 'reg8', ',', 'imm3'],
                lambda rhs: Sub(rhs[1], rhs[3], rhs[5]))

        self.add_instruction(['sub', 'sp', ',', 'sp', ',', 'imm8'],
                lambda rhs: Sub(SP, SP, rhs[5]))

        self.add_instruction(['add', 'sp', ',', 'sp', ',', 'imm8'],
                lambda rhs: Add(SP, SP, rhs[5]))

        self.add_keyword('cmp')
        self.add_instruction(['cmp', 'reg8', ',', 'reg8'],
                lambda rhs: Cmp(rhs[1], rhs[3]))
        self.add_instruction(['cmp', 'reg8', ',', 'imm8'],
                lambda rhs: Cmp2(rhs[1], rhs[3]))

        self.add_keyword('lsl')
        self.add_instruction(['lsl', 'reg8', ',', 'reg8'],
                lambda rhs: Lsl(rhs[1], rhs[3]))

        self.add_keyword('lsr')
        self.add_instruction(['lsr', 'reg8', ',', 'reg8'],
                lambda rhs: Lsr(rhs[1], rhs[3]))

        self.add_keyword('orr')
        self.add_instruction(['orr', 'reg8', ',', 'reg8'],
                lambda rhs: Orr(rhs[1], rhs[3]))

        self.add_keyword('and')
        self.add_instruction(['and', 'reg8', ',', 'reg8'],
                lambda rhs: And(rhs[1], rhs[3]))

        self.add_keyword('str')
        self.add_instruction(['str', 'reg8', ',', '[', 'reg8', '+', 'imm5', ']'],
                lambda rhs: Str2(rhs[1], rhs[4], rhs[6]))

        self.add_keyword('ldr')
        self.add_instruction(['ldr', 'reg8', ',', '[', 'reg8', '+', 'imm5', ']'],
                lambda rhs: Ldr2(rhs[1], rhs[4], rhs[6]))

        self.add_instruction(['str', 'reg8', ',', '[', 'sp', '+', 'imm8', ']'],
                lambda rhs: Str1(rhs[1], rhs[6]))

        self.add_instruction(['ldr', 'reg8', ',', '[', 'sp', '+', 'imm8', ']'],
                lambda rhs: Ldr1(rhs[1], rhs[6]))

        self.add_keyword('adr')
        self.add_instruction(['adr', 'reg8', ',', 'ID'],
                lambda rhs: Adr(rhs[1], rhs[3].val))

        self.add_keyword('pop')
        self.add_instruction(['pop', 'reg_list'], lambda rhs: Pop(rhs[1]))
        self.add_keyword('push')
        self.add_instruction(['push', 'reg_list'], lambda rhs: Push(rhs[1]))

        self.add_keyword('yield')
        self.add_instruction(['yield'], lambda rhs: Yield())

        self.add_keyword('b')
        self.add_keyword('bl')
        self.add_instruction(['b', 'ID'], lambda rhs: B(rhs[1].val))
        self.add_instruction(['bl', 'ID'], lambda rhs: Bl(rhs[1].val))
        self.add_keyword('beq')
        self.add_keyword('bne')
        self.add_keyword('blt')
        self.add_keyword('ble')
        self.add_keyword('bgt')
        self.add_keyword('bge')
        self.add_instruction(['beq', 'ID'], lambda rhs: Beq(rhs[1].val))
        self.add_instruction(['bne', 'ID'], lambda rhs: Bne(rhs[1].val))
        self.add_instruction(['blt', 'ID'], lambda rhs: Blt(rhs[1].val))
        self.add_instruction(['ble', 'ID'], lambda rhs: Ble(rhs[1].val))
        self.add_instruction(['bgt', 'ID'], lambda rhs: Bgt(rhs[1].val))
        self.add_instruction(['bge', 'ID'], lambda rhs: Bge(rhs[1].val))

        self.add_keyword('align')
        self.add_instruction(['align', 'imm8'], lambda rhs: Alignment(rhs[1]))

        self.add_instruction(['ldr', 'reg8', ',', 'ID'],
                lambda rhs: Ldr(rhs[1], rhs[3].val))

        # Additional rules:

        # Register list grammar:
        self.add_rule('reg_list', ['{', 'reg_list_inner', '}'],
            lambda rhs: rhs[1])
        self.add_rule('reg_list_inner', ['reg_or_range'],
            lambda rhs: rhs[0])
        self.add_rule('reg_list_inner', ['reg_or_range', ',', 'reg_list_inner'],
            lambda rhs: rhs[0] | rhs[2])
        self.add_rule('reg_or_range', ['reg8'], lambda rhs: {rhs[0]})
        self.add_rule('reg_or_range', ['lr'], lambda rhs: {LR})
        self.add_rule('reg_or_range', ['pc'], lambda rhs: {PC})

        self.add_rule('reg_or_range', ['reg8', '-', 'reg8'],
            lambda rhs: register_range(rhs[0], rhs[2]))

        self.add_keyword('r0')
        self.add_keyword('r1')
        self.add_keyword('r2')
        self.add_keyword('r3')
        self.add_keyword('r4')
        self.add_keyword('r5')
        self.add_keyword('r6')
        self.add_keyword('r7')
        self.add_keyword('sp')
        self.add_keyword('lr')
        self.add_keyword('pc')
        self.add_rule('reg8', ['r0'], lambda rhs: R0)
        self.add_rule('reg8', ['r1'], lambda rhs: R1)
        self.add_rule('reg8', ['r2'], lambda rhs: R2)
        self.add_rule('reg8', ['r3'], lambda rhs: R3)
        self.add_rule('reg8', ['r4'], lambda rhs: R4)
        self.add_rule('reg8', ['r5'], lambda rhs: R5)
        self.add_rule('reg8', ['r6'], lambda rhs: R6)
        self.add_rule('reg8', ['r7'], lambda rhs: R7)

