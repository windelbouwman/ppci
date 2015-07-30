from ..target import Frame
from .registers import r10, r11, r12, r13, r14, r15, Msp430Register
from .instructions import ret


class Msp430Frame(Frame):
    """
        ABI:
        pass arg1 in R11
        pass arg2 in R12
        return value in R10
    """
    def __init__(self, name):
        # We use r7 as frame pointer.
        super().__init__(name)

        self.rv = r10
        self.p1 = r11
        self.p2 = r12
        self.p3 = r13
        self.p4 = r14
        self.fp = r15
        self.locVars = {}

    def gen_call(self, label, args, res_var):
        # Caller save registers:
        # R0 is filled with return value, do not save it, it will conflict.
        self.emit(Push(r6))
        self.emit(Call(label))
        self.emit(Pop(r6))

    def new_virtual_register(self, twain=""):
        """ Retrieve a new virtual register """
        return super().new_virtual_register(Msp430Register, twain=twain)

    def alloc_var(self, lvar, size):
        if lvar not in self.locVars:
            self.locVars[lvar] = self.stacksize
            self.stacksize = self.stacksize + size
        return self.locVars[lvar]

    def epilogue(self):
        """ Return epilogue sequence for a frame. Adjust frame pointer
            and add constant pool
        """
        self.emit(ret())

    def arg_loc(self, pos):
        """ Gets the function parameter location. """
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
