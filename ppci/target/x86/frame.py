from ..target import Frame, Label, Alignment
from .registers import rax, rbx, rcx, rdx, rbp, r9, r10, r11, X86Register
from ..data_instructions import Db
from .instructions import Mov2, RmRegister


class X86Frame(Frame):
    """ Arm specific frame for functions.

        ABI:
        pass arg1 in R1
        pass arg2 in R2
        pass arg3 in R3
        pass arg4 in R4
        return value in R0
        R5 and above are callee save (the function that is called
    """
    def __init__(self, name):
        super().__init__(name)
        # Allocatable registers:
        self.regs = [r9, r10, r11]
        self.rv = rax
        self.p1 = rax
        self.p2 = rbx
        self.p3 = rcx
        self.p4 = rdx
        self.fp = rbp

        self.locVars = {}

        # Literal pool:
        self.constants = []
        self.literal_number = 0

    def new_virtual_register(self, twain=""):
        """ Retrieve a new virtual register """
        return super().new_virtual_register(X86Register, twain=twain)

    def gen_call(self, label, args, res_var):
        """ Generate code for call sequence. This function saves registers
            and moves arguments in the proper locations.

        """
        # TODO: what ABI to use?

        # Caller save registers:
        # R0 is filled with return value, do not save it, it will conflict.
        self.emit(Push(RegisterSet({R1, R2, R3, R4})))

        # Setup parameters:
        reg_uses = []
        for i, arg in enumerate(args):
            arg_loc = self.arg_loc(i)
            if isinstance(arg_loc, ArmRegister):
                reg_uses.append(arg_loc)
                self.move(arg_loc, arg)
            else:  # pragma: no cover
                raise NotImplementedError('Parameters in memory not impl')
        self.emit(Bl(label, extra_uses=reg_uses, extra_defs=[self.rv]))
        self.emit(Pop(RegisterSet({R1, R2, R3, R4})))
        self.move(res_var, self.rv)

        # Restore caller save registers:

    def move(self, dst, src):
        """ Generate a move from src to dst """
        self.emit(Mov2(dst, RmRegister(src), ismove=True))

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
        yield Push(RegisterSet({LR, R11}))
        # Callee save registers:
        yield Push(RegisterSet({R5, R6, R7, R8, R9, R10}))
        if self.stacksize > 0:
            yield Sub(SP, SP, self.stacksize)  # Reserve stack space
        yield Mov(R11, SP)                 # Setup frame pointer

    def litpool(self):
        """ Generate instruction for the current literals """
        # Align at 4 bytes
        if self.constants:
            yield Alignment(4)

        # Add constant literals:
        while self.constants:
            label, value = self.constants.pop(0)
            yield Label(label)
            if isinstance(value, int) or isinstance(value, str):
                yield dcd(value)
            elif isinstance(value, bytes):
                for byte in value:
                    yield Db(byte)
                yield Alignment(4)   # Align at 4 bytes
            else:  # pragma: no cover
                raise NotImplementedError('Constant of type {}'.format(value))

    def between_blocks(self):
        for ins in self.litpool():
            self.emit(ins)

    def epilogue(self):
        """ Return epilogue sequence for a frame. Adjust frame pointer
            and add constant pool
        """
        if self.stacksize > 0:
            yield Add(SP, SP, self.stacksize)
        yield Pop(RegisterSet({R5, R6, R7, R8, R9, R10}))
        yield Pop(RegisterSet({PC, R11}), extra_uses=[self.rv])
        # Add final literal pool:
        for instruction in self.litpool():
            yield instruction
        yield Alignment(4)   # Align at 4 bytes
