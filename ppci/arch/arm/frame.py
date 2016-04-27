from ..arch import Label, Alignment
from ..arch import Frame
from .instructions import Add2, Sub2, Push, Pop, Mov2, Bl, NoShift
from ..data_instructions import Db, Dd, Dcd2
from .instructions import RegisterSet
from .registers import R0, R1, R2, R3, R4, R5, R6, R7, R8
from .registers import R9, R10, R11, LR, PC, SP, ArmRegister


class ArmFrame(Frame):
    """ Arm specific frame for functions.

        R5 and above are callee save (the function that is called
    """
    def __init__(self, name, arg_locs, live_in, rv, live_out):
        super().__init__(name, arg_locs, live_in, rv, live_out)
        # Allocatable registers:
        self.regs = [R0, R1, R2, R3, R4, R5, R6, R7]
        self.fp = R11

        self.locVars = {}

        # Literal pool:
        self.constants = []
        self.literal_number = 0

    def new_virtual_register(self, twain=""):
        """ Retrieve a new virtual register """
        return super().new_virtual_register(ArmRegister, twain=twain)

    def make_call(self, vcall):
        """ Implement actual call and save / restore live registers """
        # R0 is filled with return value, do not save it, it will conflict.
        # Now we now what variables are live:
        live_regs = self.live_regs_over(vcall)
        register_set = set(live_regs)

        # Caller save registers:
        if register_set:
            yield Push(RegisterSet(register_set))

        yield Bl(vcall.function_name)

        # Restore caller save registers:
        if register_set:
            yield Pop(RegisterSet(register_set))

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
            yield Sub2(SP, SP, self.stacksize)  # Reserve stack space
        yield Mov2(R11, SP, NoShift())                 # Setup frame pointer

    def litpool(self):
        """ Generate instruction for the current literals """
        # Align at 4 bytes
        if self.constants:
            yield Alignment(4)

        # Add constant literals:
        while self.constants:
            label, value = self.constants.pop(0)
            yield Label(label)
            if isinstance(value, int):
                yield Dd(value)
            elif isinstance(value, str):
                yield Dcd2(value)
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
            yield Add2(SP, SP, self.stacksize)
        yield Pop(RegisterSet({R5, R6, R7, R8, R9, R10}))
        yield Pop(RegisterSet({PC, R11}), extra_uses=[self.rv])
        # Add final literal pool:
        for instruction in self.litpool():
            yield instruction
        yield Alignment(4)   # Align at 4 bytes
