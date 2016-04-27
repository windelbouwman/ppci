from ..arch import Frame, Label
from .registers import rbx, rcx, rdx, rbp, rsp
from .registers import r8, r9, r10, r11, r12, r13, r14, r15, X86Register
from .registers import rdi, rsi
from ..data_instructions import Db
from .instructions import MovRegRm, RmReg, Push, Pop, SubImm, AddImm
from .instructions import Call, Ret


class X86Frame(Frame):
    """ X86 specific frame for functions.


        rbp, rbx, r12, r13, r14 and r15 are callee save. The called function
        must save those. The other registers must be saved by the caller.
    """
    def __init__(self, name, arg_locs, live_in, rv, live_out):
        super().__init__(name, arg_locs, live_in, rv, live_out)
        # Allocatable registers:
        self.regs = [rbx, rdx, rcx, rdi, rsi, r8, r9, r10, r11, r14, r15]
        self.fp = rbp

        self.callee_save = (rbx, r12, r13, r14, r15)

        self.used_regs = set()

        self.locVars = {}

        # Literal pool:
        self.constants = []
        self.literal_number = 0

    def make_call(self, vcall):
        # R0 is filled with return value, do not save it, it will conflict.
        # Now we now what variables are live
        live_regs = self.live_regs_over(vcall)

        # Caller save registers:
        for register in live_regs:
            yield Push(register)

        yield Call(vcall.function_name)

        # Restore caller save registers:
        for register in reversed(live_regs):
            yield Pop(register)

    def alloc_var(self, lvar, size):
        if lvar not in self.locVars:
            self.locVars[lvar] = self.stacksize
            self.stacksize = self.stacksize + size
        return self.locVars[lvar]

    def add_constant(self, value):
        """ Add constant literal to constant pool """
        for lab_name, val in self.constants:
            if value == val:
                return lab_name
        assert type(value) in [str, int, bytes], str(value)
        lab_name = '{}_literal_{}'.format(self.name, self.literal_number)
        self.literal_number += 1
        self.constants.append((lab_name, value))
        return lab_name

    def is_used(self, register):
        """ Check if a register is used by this frame """
        return register in self.used_regs

    def prologue(self):
        """ Returns prologue instruction sequence """
        # Label indication function:
        yield Label(self.name)

        yield Push(rbp)

        # Callee save registers:
        for reg in self.callee_save:
            if self.is_used(reg):
                yield Push(reg)

        # Reserve stack space
        if self.stacksize > 0:
            yield SubImm(rsp, self.stacksize)

        yield MovRegRm(rbp, RmReg(rsp))

    def epilogue(self):
        """ Return epilogue sequence for a frame. Adjust frame pointer
            and add constant pool
        """
        if self.stacksize > 0:
            yield AddImm(rsp, self.stacksize)

        # Pop save registers back:
        for reg in reversed(self.callee_save):
            if self.is_used(reg):
                yield Pop(reg)

        yield Pop(rbp)
        yield Ret()

        # Add final literal pool:
        for label, value in self.constants:
            yield Label(label)
            if isinstance(value, bytes):
                for byte in value:
                    yield Db(byte)
            else:  # pragma: no cover
                raise NotImplementedError('Constant of type {}'.format(value))
