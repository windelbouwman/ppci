from ..target import Target, Label, VCall
from .instructions import isa, Mov2
from ..data_instructions import data_isa
from ..arm.registers import register_range, ArmRegister, Reg8Op
from ..arm.registers import R0, R1, R2, R3, R4
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

    def move(self, dst, src):
        """ Generate a mov instruction """
        return Mov2(dst, src, ismove=True)

    def gen_call(self, label, arg_types, res_type, args, res_var):
        """ Generate code for call sequence """
        arg_locs, live_in, rv, live_out = self.determine_arg_locations(arg_types, res_type)

        # Copy args to correct positions:
        for arg_loc, arg in zip(arg_locs, args):
            if type(arg_loc) is type(R0):
                yield self.move(arg_loc, arg)
            else:  # pragma: no cover
                raise NotImplementedError('Parameters in memory not impl')

        # Caller save registers:
        yield VCall(label, extra_uses=live_in, extra_defs=live_out)

        # Copy return value:
        yield self.move(res_var, rv)

    def determine_arg_locations(self, arg_types, ret_type):
        """ Given a set of argument types, determine locations
            the first arguments go into registers. The others on the stack.
        """
        l = []
        live_in = set()
        regs = [R1, R2, R3, R4]
        for a in arg_types:
            # Determine register:
            r = regs.pop(0)
            l.append(r)
            live_in.add(r)
        live_out = set()
        rv = R0
        live_out.add(rv)
        return l, tuple(live_in), rv, tuple(live_out)
