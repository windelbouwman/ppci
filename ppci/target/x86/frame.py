from ..target import Frame, Label
from .registers import rax, rbx, rcx, rdx, rbp, rsp
from .registers import r8, r9, r10, r11, r12, r13, r14, r15, X86Register
from .registers import rdi, rsi
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
        self.regs = [r8, r9, r10, r11, r13, r14]
        self.rv = rax
        self.p1 = rdi
        self.p2 = rsi
        self.p3 = rdx
        self.p4 = rcx
        self.p5 = r8
        self.p6 = r9
        self.fp = rbp

        self.register_classes[8] = X86Register
        self.register_classes[64] = X86Register

        self.locVars = {}

        # Literal pool:
        self.constants = []
        self.literal_number = 0

    def gen_call(self, label, args, res_var):
        """ Generate code for call sequence. This function saves registers
            and moves arguments in the proper locations.

        """
        # Caller save registers:
        # R0 is filled with return value, do not save it, it will conflict.

        # Setup parameters:
        reg_uses = []
        for i, arg in enumerate(args):
            arg_loc = self.arg_loc(i)
            if isinstance(arg_loc, X86Register):
                reg_uses.append(arg_loc)
                self.move(arg_loc, arg)
            else:  # pragma: no cover
                raise NotImplementedError('Parameters in memory not impl')
        self.emit(Call(label, extra_uses=reg_uses, extra_defs=[self.rv]))
        self.move(res_var, self.rv)

        # Restore caller save registers:

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

    def prologue(self):
        """ Returns prologue instruction sequence """
        # Label indication function:
        yield Label(self.name)
        yield Push(rbp)
        yield Push(rbx)
        yield Push(r12)
        yield Push(r13)
        yield Push(r14)
        yield Push(r15)
        # Callee save registers:
        # TODO
        if self.stacksize > 0:
            yield SubImm(rsp, self.stacksize)  # Reserve stack space
        # yield Mov(R11, SP)                 # Setup frame pointer

    def epilogue(self):
        """ Return epilogue sequence for a frame. Adjust frame pointer
            and add constant pool
        """
        if self.stacksize > 0:
            yield AddImm(rsp, self.stacksize)
        # Pop save registers back:
        yield Pop(r15)
        yield Pop(r14)
        yield Pop(r13)
        yield Pop(r12)
        yield Pop(rbx)
        yield Pop(rbp)
        yield Ret()
        # Add final literal pool:
