from ..arch import Frame, Label, Alignment
from ..data_instructions import Db
from .registers import r4, r5, r6, r7, r8, r9, r10, r11, r12, r13, r14, r15
from .registers import r1
from .instructions import ret, push, call, pop, Add, Sub, ConstSrc, RegDst, mov
from ..data_instructions import Dw2


class Msp430Frame(Frame):
    """
        Frame class
    """
    def __init__(self, name, arg_locs, live_in, rv, live_out):
        super().__init__(name, arg_locs, live_in, rv, live_out)

        # Allocatable registers:
        self.regs = [r5, r6, r7, r8, r9, r10, r11, r13, r14, r15]
        # TODO: r12 is given as argument and is return value
        # so it is detected live falsely.

        self.callee_save = (r4, r5, r6, r7, r8, r9, r10)
        self.caller_save = (r11, r13, r14, r15)  # TODO: fix r12 reg!!

        self.fp = r4
        self.locVars = {}
        self.constants = []
        self.literal_number = 0

    def make_call(self, vcall):
        live_regs = self.live_regs_over(vcall)

        # Caller save registers:
        for register in live_regs:
            if register in self.caller_save:
                yield push(register)

        yield call(vcall.function_name)

        # Restore caller save registers:
        for register in reversed(live_regs):
            if register in self.caller_save:
                yield pop(register)

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
        assert isinstance(value, (str, bytes)), str(value)
        lab_name = '{}_literal_{}'.format(self.name, self.literal_number)
        self.literal_number += 1
        self.constants.append((lab_name, value))
        return lab_name

    def litpool(self):
        """ Generate instruction for the current literals """
        # Align at 2 bytes
        if self.constants:
            yield Alignment(2)

        # Add constant literals:
        while self.constants:
            label, value = self.constants.pop(0)
            yield Label(label)
            if isinstance(value, str):
                yield Dw2(value)
            elif isinstance(value, bytes):
                for byte in value:
                    yield Db(byte)
                yield Alignment(2)   # Align at 4 bytes
            else:  # pragma: no cover
                raise NotImplementedError('Constant of type {}'.format(value))

    def is_used(self, register):
        """ Check if a register is used by this frame """
        return True
        # TODO: implement a check here!
        return register in self.used_regs

    def prologue(self):
        """ Returns prologue instruction sequence """
        # Label indication function:
        yield Label(self.name)

        # Callee save registers:
        for reg in self.callee_save:
            if self.is_used(reg):
                yield push(reg)

        # Adjust stack:
        if self.stacksize:
            yield Sub(ConstSrc(self.stacksize), RegDst(r1))

        # Setup the frame pointer:
        yield mov(r1, r4)

    def epilogue(self):
        """ Return epilogue sequence for a frame. Adjust frame pointer
            and add constant pool
        """

        # Adjust stack:
        if self.stacksize:
            yield Add(ConstSrc(self.stacksize), RegDst(r1))

        # Pop save registers back:
        for reg in reversed(self.callee_save):
            if self.is_used(reg):
                yield pop(reg)

        # Return from function:
        yield ret()

        # Add final literal pool:
        for instruction in self.litpool():
            yield instruction
