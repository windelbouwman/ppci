from ..basetarget import Register, Instruction, Target, Label, Alignment
from .instructions import Dcd, Ldr3, Ds
from .instructions import isa
from ..arm.registers import R0, R1, R2, R3, R4, R5, R6, R7
from ..arm.registers import R8, R9, R10, R11, R12, SP, LR, PC, register_range

from .frame import ArmFrame
from .instructions import ThumbInstructionSelector
from .relocations import reloc_map
from ...assembler import BaseAssembler


""" Thumb target description. """

# TODO: encode this in DSL (domain specific language)
# TBD: is this required?
# TODO: make a difference between armv7 and armv5?


class ThumbAssembler(BaseAssembler):
    def __init__(self, target):
        super().__init__(target)
        kws = list(isa.calc_kws())
        kws += [
            "r0", "r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8", "r9",
            "r10", "r11", "r12", "sp", "lr", "pc"
            ]
        self.parser.assembler = self
        self.gen_asm_parser(isa)
        self.add_extra_rules(self.parser)
        self.parser.g.add_terminals(kws)
        self.lexer.kws |= set(kws)

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
        parser.add_rule('reg_list', ['{', 'reg_list_inner', '}'], lambda rhs: rhs[1])
        parser.add_rule('reg_list_inner', ['reg_or_range'], lambda rhs: rhs[0])
        parser.add_rule('reg_list_inner', ['reg_or_range', ',', 'reg_list_inner'], lambda rhs: rhs[0] | rhs[2])
        parser.add_rule('reg_or_range', ['reg'], lambda rhs: set([rhs[0]]))
        parser.add_rule('reg_or_range', ['reg', '-', 'reg'], lambda rhs: register_range(rhs[0], rhs[2]))

    def select_section(self, name):
        self.flush()
        self.stream.select_section(name)


class ThumbTarget(Target):
    def __init__(self):
        super().__init__('thumb')
        self.ins_sel = ThumbInstructionSelector()
        self.FrameClass = ArmFrame

        self.assembler = ThumbAssembler(self)
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
