from ..target import Target, VCall
from .registers import r10, r11, r12, r13, r14, r15, Msp430Register
from ...ir import i8, i16, ptr
from .instructions import isa, mov
from ..data_instructions import data_isa
from .frame import Msp430Frame
from ...binutils.assembler import BaseAssembler


class Msp430Target(Target):
    def __init__(self):
        super().__init__('msp430')
        self.byte_sizes['int'] = 2
        self.byte_sizes['ptr'] = 2
        self.value_classes[i16] = Msp430Register
        self.value_classes[ptr] = Msp430Register
        self.value_classes[i8] = Msp430Register
        self.isa = isa + data_isa
        self.assembler = BaseAssembler(self)
        self.assembler.gen_asm_parser()

        self.FrameClass = Msp430Frame

        self.registers.append(r10)
        self.registers.append(r11)
        self.registers.append(r12)
        self.registers.append(r13)
        self.registers.append(r14)
        self.registers.append(r15)

    def move(self, dst, src):
        """ Generate a move from src to dst """
        return mov(src, dst)

    def gen_call(self, label, arg_types, ret_type, args, res_var):
        arg_locs, live_in, rv, live_out = self.determine_arg_locations(arg_types, ret_type)

        # Setup parameters:
        for arg_loc, arg in zip(arg_locs, args):
            if isinstance(arg_loc, Msp430Register):
                yield self.move(arg_loc, arg)
            else:  # pragma: no cover
                raise NotImplementedError('Parameters in memory not impl')

        yield VCall(label, extra_uses=live_in, extra_defs=live_out)
        yield self.move(res_var, rv)

    def determine_arg_locations(self, arg_types, ret_type):
        """
            Given a set of argument types, determine location for argument
            ABI:
        self.rv = r10
        self.p1 = r11
        self.p2 = r12
        self.p3 = r13
        self.p4 = r14
        """
        l = []
        live_in = set()
        regs = [r11, r12, r13, r14]
        for a in arg_types:
            r = regs.pop(0)
            l.append(r)
            live_in.add(r)

        live_out = set()
        rv = r10
        live_out.add(rv)
        return l, tuple(live_in), rv, tuple(live_out)
