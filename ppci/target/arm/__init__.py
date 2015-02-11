
from ..basetarget import Target, Label
from .instructions import LdrPseudo, isa
from .instructions import ArmInstructionSelector
from .frame import ArmFrame
from ...assembler import BaseAssembler

from ..arm.registers import R0, R1, R2, R3, R4, R5, R6, R7
from ..arm.registers import R8, R9, R10, R11, R12, SP, LR, PC
from ..arm.registers import register_range

from .instructions import Dcd, Ds, Mcr, Mrc, RegisterSet
from .relocations import reloc_map


class ArmAssembler(BaseAssembler):
    def __init__(self, target):
        super().__init__(target)

        kws = [
            "r0", "r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8", "r9",
            "r10", "r11", "r12", "sp", "lr", "pc",
            "dcd", 'db', 'ds',
            "nop", "mov", "cmp", "add", "sub", "mul",
            "lsl", "lsr", "orr", "and",
            "push", "pop", "b", "bl",
            "blt", "ble", "bgt", "beq", "bge", "bne",
            "ldr", "str", "adr", 'ldrb', 'strb',
            "c0", "c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8", "c9",
            "c10", "c11", "c12", "c13", "c14", "c15",
            "p8", "p9", "p10", "p11", "p12", "p13", "p14", "p15",
            "mcr", "mrc"
            ]
        self.parser.assembler = self
        self.gen_asm_parser(isa)
        self.add_extra_rules(self.parser)
        self.parser.g.add_terminals(kws)
        self.lexer.kws |= set(kws)

        self.lit_pool = []
        self.lit_counter = 0

    def add_extra_rules(self, parser):
        parser.add_rule('reg', ['r0'], lambda rhs: R0)
        parser.add_rule('reg', ['r1'], lambda rhs: R1)
        parser.add_rule('reg', ['r2'], lambda rhs: R2)
        parser.add_rule('reg', ['r3'], lambda rhs: R3)
        parser.add_rule('reg', ['r4'], lambda rhs: R4)
        parser.add_rule('reg', ['r5'], lambda rhs: R5)
        parser.add_rule('reg', ['r6'], lambda rhs: R6)
        parser.add_rule('reg', ['r7'], lambda rhs: R7)

        parser.add_rule('reg', ['r8'], lambda rhs: R8)
        parser.add_rule('reg', ['r9'], lambda rhs: R9)
        parser.add_rule('reg', ['r10'], lambda rhs: R10)
        parser.add_rule('reg', ['r11'], lambda rhs: R11)
        parser.add_rule('reg', ['r12'], lambda rhs: R12)

        parser.add_rule('reg', ['sp'], lambda rhs: SP)
        parser.add_rule('reg', ['lr'], lambda rhs: LR)
        parser.add_rule('reg', ['pc'], lambda rhs: PC)

        parser.add_rule('strrr', ['ID'], lambda rhs: rhs[0].val)

        # Implement register list syntaxis:
        parser.add_rule(
            'reg_list', ['{', 'reg_list_inner', '}'], lambda rhs: rhs[1])
        parser.add_rule('reg_list_inner', ['reg_or_range'], lambda rhs: rhs[0])
        parser.add_rule(
            'reg_list_inner',
            ['reg_or_range', ',', 'reg_list_inner'],
            lambda rhs: RegisterSet(rhs[0] | rhs[2]))
        parser.add_rule(
            'reg_or_range', ['reg'], lambda rhs: RegisterSet([rhs[0]]))
        parser.add_rule(
            'reg_or_range',
            ['reg', '-', 'reg'],
            lambda rhs: RegisterSet(register_range(rhs[0], rhs[2])))

        # Ldr pseudo instruction:
        # TODO: fix the add_literal other way:
        parser.add_rule(
            'instruction',
            ['ldr', 'reg', ',', '=', 'ID'],
            lambda rhs: LdrPseudo(rhs[1], rhs[4].val, self.add_literal))

        # Strange mrc and mcr instructions:
        parser.add_rule('coreg', ['c0'], lambda rhs: 0)
        parser.add_rule('coreg', ['c1'], lambda rhs: 1)
        parser.add_rule('coreg', ['c2'], lambda rhs: 2)
        parser.add_rule('coreg', ['c3'], lambda rhs: 3)
        parser.add_rule('coreg', ['c4'], lambda rhs: 4)
        parser.add_rule('coreg', ['c5'], lambda rhs: 5)
        parser.add_rule('coreg', ['c6'], lambda rhs: 6)
        parser.add_rule('coreg', ['c7'], lambda rhs: 7)
        parser.add_rule('coreg', ['c8'], lambda rhs: 8)
        parser.add_rule('coreg', ['c9'], lambda rhs: 9)
        parser.add_rule('coreg', ['c10'], lambda rhs: 10)
        parser.add_rule('coreg', ['c11'], lambda rhs: 11)
        parser.add_rule('coreg', ['c12'], lambda rhs: 12)
        parser.add_rule('coreg', ['c13'], lambda rhs: 13)
        parser.add_rule('coreg', ['c14'], lambda rhs: 14)
        parser.add_rule('coreg', ['c15'], lambda rhs: 15)

        parser.add_rule('coproc', ['p8'], lambda rhs: 8)
        parser.add_rule('coproc', ['p9'], lambda rhs: 9)
        parser.add_rule('coproc', ['p10'], lambda rhs: 10)
        parser.add_rule('coproc', ['p11'], lambda rhs: 11)
        parser.add_rule('coproc', ['p12'], lambda rhs: 12)
        parser.add_rule('coproc', ['p13'], lambda rhs: 13)
        parser.add_rule('coproc', ['p14'], lambda rhs: 14)
        parser.add_rule('coproc', ['p15'], lambda rhs: 15)

        parser.add_rule(
            'instruction',
            ['mcr', 'coproc', ',', 'imm3', ',', 'reg', ',', 'coreg', ',', 'coreg', ',', 'imm3'],
            lambda rhs: Mcr(rhs[1], rhs[3], rhs[5], rhs[7], rhs[9], rhs[11]))

        parser.add_rule(
            'instruction',
            ['mrc', 'coproc', ',', 'imm3', ',', 'reg', ',', 'coreg', ',', 'coreg', ',', 'imm3'],
            lambda rhs: Mrc(rhs[1], rhs[3], rhs[5], rhs[7], rhs[9], rhs[11]))

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
        assert type(v) is str
        self.lit_counter += 1
        label_name = "_lit_{}".format(self.lit_counter)
        self.lit_pool.append(Label(label_name))
        self.lit_pool.append(Dcd(v))
        return label_name


class ArmTarget(Target):
    def __init__(self):
        super().__init__('arm')
        self.ins_sel = ArmInstructionSelector()
        self.FrameClass = ArmFrame

        self.assembler = ArmAssembler(self)
        self.reloc_map = reloc_map

    def emit_global(self, outs, lname, amount):
        # TODO: alignment?
        outs.emit(Label(lname))
        if amount == 4:
            outs.emit(Dcd(0))
        elif amount > 0:
            outs.emit(Ds(amount))
        else:
            raise NotImplementedError()
