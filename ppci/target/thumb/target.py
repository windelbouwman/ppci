from ..target import Target, Label
from .instructions import isa
from ..data_instructions import data_isa
from ..arm.registers import register_range, ArmRegister, Reg8Op
from ...ir import i8, i32, ptr
from .frame import ThumbFrame
from ...binutils.assembler import BaseAssembler


""" Thumb target description. """

# TODO: encode this in DSL (domain specific language)
# TBD: is this required?
# TODO: make a difference between armv7 and armv5?


class ThumbAssembler(BaseAssembler):
    def __init__(self, target):
        super().__init__(target)
        self.parser.assembler = self
        self.add_extra_rules()
        self.gen_asm_parser()

    def add_extra_rules(self):
        # Implement register list syntaxis:
        self.typ2nt[set] = 'reg_list'
        self.add_rule('reg_list', ['{', 'reg_list_inner', '}'], lambda rhs: rhs[1])
        self.add_rule('reg_list_inner', ['reg_or_range'], lambda rhs: rhs[0])

        # For a left right parser, or right left parser, this is important:
        self.add_rule('reg_list_inner', ['reg_list_inner', ',', 'reg_or_range'], lambda rhs: rhs[0] | rhs[2])
        # self.add_rule('reg_list_inner', ['reg_or_range', ',', 'reg_list_inner'], lambda rhs: rhs[0] | rhs[2])

        self.add_rule('reg_or_range', ['reg'], lambda rhs: set([rhs[0]]))
        self.add_rule('reg_or_range', ['reg', '-', 'reg'], lambda rhs: register_range(rhs[0], rhs[2]))


class ThumbTarget(Target):
    def __init__(self):
        super().__init__('thumb')
        self.isa = isa + data_isa
        self.FrameClass = ThumbFrame
        self.assembler = ThumbAssembler(self)
        self.value_classes[i32] = Reg8Op
        self.value_classes[i8] = Reg8Op
        self.value_classes[ptr] = Reg8Op

    def get_runtime_src(self):
        """ No runtime for thumb required yet .. """
        return """
        """
