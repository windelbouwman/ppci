""" X86-64 architecture description.

X86 specific frame for functions.

  rbp, rbx, r12, r13, r14 and r15 are callee save. The called function
  must save those. The other registers must be saved by the caller.

"""

import io
from ..arch import Architecture, Label
from ...binutils.assembler import BaseAssembler
from ..data_instructions import data_isa
from ..data_instructions import Db
from .instructions import MovRegRm, RmReg, MovRegRm8, RmReg8, isa
from .instructions import Push, Pop, SubImm, AddImm, MovsxRegRm
from .instructions import Call, Ret
from .registers import rax, rcx, rdx, r8, r9, rdi, rsi
from .registers import all_registers
from .registers import register_classes, X86Register, LowRegister
from .registers import rbx, rbp, rsp, al
from .registers import r12, r13, r14, r15


class X86_64Arch(Architecture):
    """ x86_64 architecture """
    name = 'x86_64'
    option_names = ('sse2', 'sse3')

    def __init__(self, options=None):
        super().__init__(options=options, register_classes=register_classes)
        self.byte_sizes['int'] = 8  # For front end!
        self.byte_sizes['ptr'] = 8  # For front end!
        self.isa = isa + data_isa
        self.registers.extend(all_registers)
        self.assembler = BaseAssembler()
        self.assembler.gen_asm_parser(self.isa)
        self.fp = rbp
        self.callee_save = (rbx, r12, r13, r14, r15)

    def move(self, dst, src):
        """ Generate a move from src to dst """
        if isinstance(dst, LowRegister) and isinstance(src, LowRegister):
            return MovRegRm8(dst, RmReg8(src), ismove=True)
        elif isinstance(dst, LowRegister) and isinstance(src, X86Register):
            raise NotImplementedError()  # pragma: no cover
        elif isinstance(dst, X86Register) and isinstance(src, LowRegister):
            raise NotImplementedError()  # pragma: no cover
        else:
            return MovRegRm(dst, RmReg(src), ismove=True)

    def get_runtime(self):
        from ...api import asm
        asm_src = ''
        return asm(io.StringIO(asm_src), self)

    def determine_arg_locations(self, arg_types):
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
        live_in = set([rbp])
        regs = [rdi, rsi, rdx, rcx, r8, r9]
        for a in arg_types:
            # Determine register:
            r = regs.pop(0)
            arg_locs.append(r)
            live_in.add(r)
        return arg_locs, tuple(live_in)

    def determine_rv_location(self, ret_type):
        """
        return value in rax

        self.rv = rax
        """
        live_out = set([rbp])
        rv = rax
        live_out.add(rv)
        return rv, tuple(live_out)

    def gen_fill_arguments(self, arg_types, args, live):
        """ This function moves arguments in the proper locations.
        """
        arg_locs, live_in = self.determine_arg_locations(arg_types)
        live.update(set(live_in))

        # Setup parameters:
        for arg_loc, arg in zip(arg_locs, args):
            if isinstance(arg_loc, X86Register):
                if isinstance(arg, X86Register):
                    yield self.move(arg_loc, arg)
                elif isinstance(arg, LowRegister):
                    # Upcast to char!
                    yield self.move(al, arg)
                    yield MovsxRegRm(rax, RmReg8(al))
                    yield self.move(arg_loc, rax)
                else:  # pragma: no cover
                    raise NotImplementedError()
            else:  # pragma: no cover
                raise NotImplementedError('Parameters in memory not impl')

    def make_call(self, frame, vcall):
        # R0 is filled with return value, do not save it, it will conflict.
        # Now we now what variables are live
        live_regs = frame.live_regs_over(vcall)

        # Caller save registers:
        for register in live_regs:
            yield Push(register)

        yield Call(vcall.function_name)

        # Restore caller save registers:
        for register in reversed(live_regs):
            yield Pop(register)

    def gen_prologue(self, frame):
        """ Returns prologue instruction sequence """
        # Label indication function:
        yield Label(frame.name)

        yield Push(rbp)

        # Callee save registers:
        for reg in self.callee_save:
            if frame.is_used(reg):
                yield Push(reg)

        # Reserve stack space
        if frame.stacksize > 0:
            yield SubImm(rsp, frame.stacksize)

        yield MovRegRm(rbp, RmReg(rsp))

    def gen_epilogue(self, frame):
        """ Return epilogue sequence for a frame. Adjust frame pointer
            and add constant pool
        """
        if frame.stacksize > 0:
            yield AddImm(rsp, frame.stacksize)

        # Pop save registers back:
        for reg in reversed(self.callee_save):
            if frame.is_used(reg):
                yield Pop(reg)

        yield Pop(rbp)
        yield Ret()

        # Add final literal pool:
        for label, value in frame.constants:
            yield Label(label)
            if isinstance(value, bytes):
                for byte in value:
                    yield Db(byte)
            else:  # pragma: no cover
                raise NotImplementedError('Constant of type {}'.format(value))
