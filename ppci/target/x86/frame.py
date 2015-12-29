from ..target import Frame, Label, VCall
from .registers import rax, rbx, rcx, rdx, rbp, rsp
from .registers import r8, r9, r10, r11, r12, r13, r14, r15, X86Register
from .registers import rdi, rsi, get_register
from ..data_instructions import Db
from .instructions import MovRegRm, RmRegister, Push, Pop, SubImm, AddImm
from .instructions import Call, Ret


class X86Frame(Frame):
    """ X86 specific frame for functions.

        see also http://www.x86-64.org/documentation/abi.pdf

        ABI:
        pass arg1 in rax
        pass arg2 in rbx
        pass arg3 in rcx
        pass arg4 in rdx
        return value in rax

        rbp, rbx, r12, r13, r14 and r15 are callee save. The called function
        must save those. The other registers must be saved by the caller.
    """
    def __init__(self, name):
        super().__init__(name)
        # Allocatable registers:
        self.regs = [r8, r9, r10, r11, r14, r15]
        self.rv = rax
        self.p1 = rdi
        self.p2 = rsi
        self.p3 = rdx
        self.p4 = rcx
        self.p5 = r8
        self.p6 = r9
        self.fp = rbp

        self.callee_save = (rbx, r12, r13, r14, r15)

        self.register_classes[8] = X86Register
        self.register_classes[64] = X86Register

        self.used_regs = set()

        self.locVars = {}

        # Literal pool:
        self.constants = []
        self.literal_number = 0

    def gen_call(self, label, args, res_var):
        """ Generate code for call sequence. This function saves registers
            and moves arguments in the proper locations.
        """

        # Setup parameters:
        reg_uses = []
        for i, arg in enumerate(args):
            arg_loc = self.arg_loc(i)
            if isinstance(arg_loc, X86Register):
                reg_uses.append(arg_loc)
                self.move(arg_loc, arg)
            else:  # pragma: no cover
                raise NotImplementedError('Parameters in memory not impl')
        self.emit(
            VCall(label, extra_uses=reg_uses, extra_defs=[self.rv]))
        self.move(res_var, self.rv)

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

    def get_register(self, color):
        return get_register(color)

    def move(self, dst, src):
        """ Generate a move from src to dst """
        self.emit(MovRegRm(dst, RmRegister(src), ismove=True))

    def arg_loc(self, pos):
        """
            Gets the function parameter location in IR-code format.
        """
        if pos == 0:
            return self.p1
        elif pos == 1:
            return self.p2
        elif pos == 2:
            return self.p3
        elif pos == 3:
            return self.p4
        else:  # pragma: no cover
            raise NotImplementedError('No more than 4 parameters implemented')

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
        yield MovRegRm(rbp, RmRegister(rsp))

        # Callee save registers:
        for reg in self.callee_save:
            if self.is_used(reg):
                yield Push(reg)

        # Reserve stack space
        if self.stacksize > 0:
            yield SubImm(rsp, self.stacksize)

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
