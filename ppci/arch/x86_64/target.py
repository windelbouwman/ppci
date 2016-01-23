"""
    X86-64 target description.
"""

from ..target import Target, VCall
from ...binutils.assembler import BaseAssembler
from ...ir import i64, i8, ptr
from ..data_instructions import data_isa
from .instructions import isa
from .instructions import MovRegRm, RmRegister
from .registers import rax, rbx, rcx, rdx, rbp, rsp
from .registers import r8, r9, r10, r11, r12, r13, r14, r15, X86Register
from .registers import rdi, rsi, get_register
from .frame import X86Frame


class X86Target(Target):
    """ x86_64 target """
    def __init__(self):
        super().__init__('x86_64')
        self.value_classes[i64] = X86Register
        self.value_classes[ptr] = X86Register
        self.value_classes[i8] = X86Register
        self.byte_sizes['int'] = 8  # For front end!
        self.byte_sizes['ptr'] = 8  # For front end!
        self.isa = isa + data_isa
        self.assembler = BaseAssembler(self)
        self.FrameClass = X86Frame
        self.assembler.gen_asm_parser()

    def move(self, dst, src):
        """ Generate a move from src to dst """
        return MovRegRm(dst, RmRegister(src), ismove=True)

    def determine_arg_locations(self, arg_types, ret_type):
        """ Given a set of argument types, determine locations
            the first arguments go into registers. The others on the stack.

        see also http://www.x86-64.org/documentation/abi.pdf

        ABI:
        p1 = rdi
        p2 = rsi
        p3 = rdx
        p4 = rcx
        p5 = r8
        p6 = r9

        return value in rax

        self.rv = rax
        """
        arg_locs = []
        live_in = set()
        regs = [rdi, rsi, rdx, rcx, r8, r9]
        for a in arg_types:
            # Determine register:
            r = regs.pop(0)
            arg_locs.append(r)
            live_in.add(r)
        live_out = set()
        rv = rax
        live_out.add(rv)
        return arg_locs, tuple(live_in), rv, tuple(live_out)

    def gen_call(self, label, arg_types, ret_type, args, res_var):
        """ Generate code for call sequence. This function saves registers
            and moves arguments in the proper locations.
        """

        arg_locs, live_in, rv, live_out = self.determine_arg_locations(arg_types, ret_type)

        # Setup parameters:
        for arg_loc, arg in zip(arg_locs, args):
            if isinstance(arg_loc, X86Register):
                yield self.move(arg_loc, arg)
            else:  # pragma: no cover
                raise NotImplementedError('Parameters in memory not impl')
        yield VCall(label, extra_uses=live_in, extra_defs=live_out)
        yield self.move(res_var, rv)
