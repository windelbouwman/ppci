from ..target import Target, Label
from .instructions import Dcd, Ds
from .instructions import isa
from ..arm.registers import register_range

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
        self.parser.assembler = self
        self.add_extra_rules(self.parser)
        self.gen_asm_parser(isa)

    def add_extra_rules(self, parser):
        # Implement register list syntaxis:
        self.typ2nt[set] = 'reg_list'
        parser.add_rule('reg_list', ['{', 'reg_list_inner', '}'], lambda rhs: rhs[1])
        parser.add_rule('reg_list_inner', ['reg_or_range'], lambda rhs: rhs[0])
        parser.add_rule('reg_list_inner', ['reg_or_range', ',', 'reg_list_inner'], lambda rhs: rhs[0] | rhs[2])
        parser.add_rule('reg_or_range', ['reg'], lambda rhs: set([rhs[0]]))
        parser.add_rule('reg_or_range', ['reg', '-', 'reg'], lambda rhs: register_range(rhs[0], rhs[2]))


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
        else:  # pragma: no cover
            raise NotImplementedError()

    def get_runtime_src(self):
        """ No runtime for thumb required yet .. """
        return """
        """
