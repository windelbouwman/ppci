
from ..basetarget import Target, Label
from ..arm.registers import R0, R1, R2, R3, R4, R5, R6, R7
from ..arm.registers import R8, R9, R10, R11, R12, SP, LR, PC
from ..arm.registers import register_range

from .instructions import Dcd, Mov, Mov1, Add, Add2, Sub, Orr1, Mul, Mov2
from .instructions import Add1, Mul1
from .instructions import Lsr1, Lsl1, And1, Sub1
from .instructions import B, Bl, Ble, Bgt, Beq, Blt, Cmp, Cmp2
from .instructions import Push, Pop, Str, Ldr, Ldr3, Str1, Ldr1, Adr
from .instructions import Mcr, Mrc
from .instructions import LdrPseudo
from .selector import ArmInstructionSelector
from .frame import ArmFrame
from .relocations import reloc_map
from ...assembler import BaseAssembler


class ArmAssembler(BaseAssembler):
    def __init__(self, target):
        super().__init__(target)
        self.target.add_keyword('section')
        self.target.add_instruction(['section', 'ID'],
                lambda rhs: self.select_section(rhs[1].val))
        self.target.add_keyword('repeat')
        self.target.add_keyword('endrepeat')
        self.target.add_instruction(['repeat', 'imm32'], self.begin_repeat)
        self.target.add_instruction(['endrepeat'], self.end_repeat)

        # Construct the parser from the given rules:
        self.make_parser()
        self.lit_pool = []
        self.lit_counter = 0
        self.inMacro = False

    def prepare(self):
        self.inMacro = False

    def begin_repeat(self, rhs):
        if self.inMacro:
            raise Exception()
        self.inMacro = True
        self.rep_count = rhs[1]
        self.recording = []

    def end_repeat(self, rhs):
        if not self.inMacro:
            raise Exception()
        self.inMacro = False
        for rec in self.recording * self.rep_count:
            self.emit(*rec)

    def emit(self, *args):
        if self.inMacro:
            self.recording.append(args)
        else:
            super().emit(*args)

    def select_section(self, name):
        self.flush()
        self.stream.select_section(name)

    def flush(self):
        if self.inMacro:
            raise Exception()
        while self.lit_pool:
            i = self.lit_pool.pop(0)
            self.emit(i)

    def add_literal(self, v):
        """ For use in the pseudo instruction LDR r0, =SOMESYM """
        # Invent some label for the literal and store it.
        self.lit_counter += 1
        label_name = "_lit_{}".format(self.lit_counter)
        self.lit_pool.append(Label(label_name))
        self.lit_pool.append(Dcd(v))
        return label_name


class ArmTarget(Target):
    def __init__(self):
        super().__init__('arm')
        self.make_parser()
        self.ins_sel = ArmInstructionSelector()
        self.FrameClass = ArmFrame
        self.assembler = ArmAssembler(self)

        self.add_lowering(Ldr3, lambda im: Ldr3(im.dst[0], im.others[0]))
        self.add_lowering(Str1, lambda im: Str1(im.src[1], im.src[0], im.others[0]))
        self.add_lowering(Ldr1, lambda im: Ldr1(im.dst[0], im.src[0], im.others[0]))
        self.add_lowering(Adr, lambda im: Adr(im.dst[0], im.others[0]))
        self.add_lowering(Mov2, lambda im: Mov2(im.dst[0], im.src[0]))
        self.add_lowering(Cmp2, lambda im: Cmp2(im.src[0], im.src[1]))
        self.add_lowering(Add1, lambda im: Add1(im.dst[0], im.src[0], im.src[1]))
        self.add_lowering(Add2, lambda im: Add2(im.dst[0], im.src[0], im.others[0]))
        self.add_lowering(Sub1, lambda im: Sub1(im.dst[0], im.src[0], im.src[1]))
        self.add_lowering(Mul1, lambda im: Mul1(im.dst[0], im.src[0], im.src[1]))
        self.add_lowering(Lsr1, lambda im: Lsr1(im.dst[0], im.src[0], im.src[1]))
        self.add_lowering(And1, lambda im: And1(im.dst[0], im.src[0], im.src[1]))
        self.add_lowering(Mov1, lambda im: Mov1(im.dst[0], im.others[0]))

        self.reloc_map = reloc_map

    def emit_global(self, outs, lname):
        outs.emit(Label(lname))
        outs.emit(Dcd(0))

    def make_parser(self):
        # Assembly grammar:
        self.add_keyword('r0')
        self.add_keyword('r1')
        self.add_keyword('r2')
        self.add_keyword('r3')
        self.add_keyword('r4')
        self.add_keyword('r5')
        self.add_keyword('r6')
        self.add_keyword('r7')
        self.add_keyword('r8')
        self.add_keyword('r9')
        self.add_keyword('r10')
        self.add_keyword('r11')
        self.add_keyword('r12')
        self.add_keyword('sp')
        self.add_keyword('lr')
        self.add_keyword('pc')

        self.add_rule('reg', ['r0'], lambda rhs: R0)
        self.add_rule('reg', ['r1'], lambda rhs: R1)
        self.add_rule('reg', ['r2'], lambda rhs: R2)
        self.add_rule('reg', ['r3'], lambda rhs: R3)
        self.add_rule('reg', ['r4'], lambda rhs: R4)
        self.add_rule('reg', ['r5'], lambda rhs: R5)
        self.add_rule('reg', ['r6'], lambda rhs: R6)
        self.add_rule('reg', ['r7'], lambda rhs: R7)
        self.add_rule('reg', ['r8'], lambda rhs: R8)
        self.add_rule('reg', ['r9'], lambda rhs: R9)
        self.add_rule('reg', ['r10'], lambda rhs: R10)
        self.add_rule('reg', ['r11'], lambda rhs: R11)
        self.add_rule('reg', ['r12'], lambda rhs: R12)
        self.add_rule('reg', ['sp'], lambda rhs: SP)
        self.add_rule('reg', ['lr'], lambda rhs: LR)
        self.add_rule('reg', ['pc'], lambda rhs: PC)

        self.add_keyword('dcd')
        self.add_instruction(['dcd', 'imm32'],
                             lambda rhs: Dcd(rhs[1]))

        self.add_keyword('mov')
        self.add_instruction(['mov', 'reg', ',', 'imm32'],
                             lambda rhs: Mov(rhs[1], rhs[3]))
        self.add_instruction(['mov', 'reg', ',', 'reg'],
                             lambda rhs: Mov(rhs[1], rhs[3]))

        self.add_keyword('cmp')
        self.add_instruction(['cmp', 'reg', ',', 'imm32'],
                             lambda rhs: Cmp(rhs[1], rhs[3]))
        self.add_instruction(['cmp', 'reg', ',', 'reg'],
                lambda rhs: Cmp(rhs[1], rhs[3]))

        # Arithmatic:
        self.add_keyword('add')
        self.add_instruction(['add', 'reg', ',', 'reg', ',', 'imm32'],
                lambda rhs: Add(rhs[1], rhs[3], rhs[5]))

        self.add_instruction(['add', 'reg', ',', 'reg', ',', 'reg'],
                lambda rhs: Add(rhs[1], rhs[3], rhs[5]))

        self.add_keyword('sub')
        self.add_instruction(['sub', 'reg', ',', 'reg', ',', 'imm32'],
                lambda rhs: Sub(rhs[1], rhs[3], rhs[5]))

        self.add_instruction(['sub', 'reg', ',', 'reg', ',', 'reg'],
                lambda rhs: Sub(rhs[1], rhs[3], rhs[5]))

        self.add_keyword('mul')
        self.add_instruction(['mul', 'reg', ',', 'reg', ',', 'reg'],
                lambda rhs: Mul(rhs[1], rhs[3], rhs[5]))

        self.add_keyword('orr')
        self.add_instruction(['orr', 'reg', ',', 'reg', ',', 'reg'],
                lambda rhs: Orr1(rhs[1], rhs[3], rhs[5]))

        self.add_keyword('and')
        self.add_instruction(['and', 'reg', ',', 'reg', ',', 'reg'],
                lambda rhs: And1(rhs[1], rhs[3], rhs[5]))

        self.add_keyword('lsr')
        self.add_instruction(['lsr', 'reg', ',', 'reg', ',', 'reg'],
                lambda rhs: Lsr1(rhs[1], rhs[3], rhs[5]))

        self.add_keyword('lsl')
        self.add_instruction(['lsl', 'reg', ',', 'reg', ',', 'reg'],
                lambda rhs: Lsl1(rhs[1], rhs[3], rhs[5]))


        # Jumping:
        self.add_keyword('b')
        self.add_instruction(['b', 'ID'], lambda rhs: B(rhs[1].val))
        self.add_keyword('ble')
        self.add_instruction(['ble', 'ID'], lambda rhs: Ble(rhs[1].val))
        self.add_keyword('bgt')
        self.add_instruction(['bgt', 'ID'], lambda rhs: Bgt(rhs[1].val))
        self.add_keyword('beq')
        self.add_instruction(['beq', 'ID'], lambda rhs: Beq(rhs[1].val))
        self.add_keyword('blt')
        self.add_instruction(['blt', 'ID'], lambda rhs: Blt(rhs[1].val))

        self.add_keyword('bl')
        self.add_instruction(['bl', 'ID'], lambda rhs: Bl(rhs[1].val))

        # memory:
        self.add_keyword('pop')
        self.add_instruction(['pop', 'reg_list'], lambda rhs: Pop(rhs[1]))

        self.add_keyword('push')
        self.add_instruction(['push', 'reg_list'], lambda rhs: Push(rhs[1]))

        self.add_keyword('ldr')
        self.add_instruction(['ldr', 'reg', ',', '[', 'reg', ',', 'imm8', ']'],
            lambda rhs: Ldr(rhs[1], rhs[4], rhs[6]))

        self.add_instruction(['ldr', 'reg', ',', 'ID'],
            lambda rhs: Ldr(rhs[1], rhs[3].val))

        # This is a pseudo instruction:
        self.add_instruction(['ldr', 'reg', ',', '=', 'ID'],
            lambda rhs: LdrPseudo(rhs[1], rhs[4].val, self.assembler.add_literal))

        self.add_keyword('str')
        self.add_instruction(['str', 'reg', ',', '[', 'reg', ',', 'imm8', ']'],
            lambda rhs: Str(rhs[1], rhs[4], rhs[6]))

        self.add_instruction(['str', 'reg', ',', '[', 'reg', ',', 'reg', ']'],
            lambda rhs: Str(rhs[1], rhs[4], rhs[6]))

        self.add_keyword('adr')
        self.add_instruction(['adr', 'reg', ',', 'ID'],
            lambda rhs: Adr(rhs[1], rhs[3].val))


        # Register list grammar:
        self.add_rule('reg_list', ['{', 'reg_list_inner', '}'],
            lambda rhs: rhs[1])
        self.add_rule('reg_list_inner', ['reg_or_range'],
            lambda rhs: rhs[0])
        self.add_rule('reg_list_inner', ['reg_or_range', ',', 'reg_list_inner'],
            lambda rhs: rhs[0] | rhs[2])
        self.add_rule('reg_or_range', ['reg'], lambda rhs: {rhs[0]})

        self.add_rule('reg_or_range', ['reg', '-', 'reg'],
            lambda rhs: register_range(rhs[0], rhs[2]))

        # Add MCR and MRC (co-processor)
        for i in range(16):
            creg = 'c{}'.format(i)
            self.add_keyword(creg)
            self.add_rule('coreg', [creg], i)

        for i in range(8, 16):
            px = 'p{}'.format(i)
            self.add_keyword(px)
            # Ran into trouble when using i inside lambda function:
            # When using inside lambda (as a closure), i is bound to the latest
            # value (15)
            self.add_rule('coproc', [px], i)

        self.add_keyword('mcr')
        self.add_instruction(['mcr', 'coproc', ',', 'imm3', ',', 'reg', ',', 'coreg', ',', 'coreg', ',', 'imm3'],
            lambda rhs: Mcr(rhs[1], rhs[3], rhs[5], rhs[7], rhs[9], rhs[11]))

        self.add_keyword('mrc')
        self.add_instruction(['mrc', 'coproc', ',', 'imm3', ',', 'reg', ',', 'coreg', ',', 'coreg', ',', 'imm3'],
            lambda rhs: Mrc(rhs[1], rhs[3], rhs[5], rhs[7], rhs[9], rhs[11]))
