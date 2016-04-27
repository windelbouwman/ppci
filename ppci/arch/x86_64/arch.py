"""
    X86-64 architecture description.
"""

import io
from ..arch import Architecture, VCall
from ...binutils.assembler import BaseAssembler
from ...ir import i64, i8, ptr
from ..data_instructions import data_isa
from .instructions import MovRegRm, RmReg, isa
from .registers import rax, rcx, rdx, r8, r9, X86Register, rdi, rsi
from .registers import all_registers, get_register
from .frame import X86Frame


class X86_64Arch(Architecture):
    """ x86_64 architecture """
    name = 'x86_64'
    option_names = ('sse2', 'sse3')

    def __init__(self, options=None):
        super().__init__(options=options)
        self.value_classes[i64] = X86Register
        self.value_classes[ptr] = X86Register
        self.value_classes[i8] = X86Register
        self.byte_sizes['int'] = 8  # For front end!
        self.byte_sizes['ptr'] = 8  # For front end!
        self.isa = isa + data_isa
        self.registers.extend(all_registers)
        self.assembler = BaseAssembler()
        self.assembler.gen_asm_parser(self.isa)
        self.FrameClass = X86Frame

    def move(self, dst, src):
        """ Generate a move from src to dst """
        return MovRegRm(dst, RmReg(src), ismove=True)

    def get_register(self, color):
        return get_register(color)

    def get_runtime(self):
        from ...api import asm
        asm_src = ''
        return asm(io.StringIO(asm_src), self)

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

        arg_locs, live_in, rv, live_out = \
            self.determine_arg_locations(arg_types, ret_type)

        # Setup parameters:
        for arg_loc, arg in zip(arg_locs, args):
            if isinstance(arg_loc, X86Register):
                yield self.move(arg_loc, arg)
            else:  # pragma: no cover
                raise NotImplementedError('Parameters in memory not impl')
        yield VCall(label, extra_uses=live_in, extra_defs=live_out)
        yield self.move(res_var, rv)
