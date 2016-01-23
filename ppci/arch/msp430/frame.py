from ..target import Frame, Label, Alignment
from ..data_instructions import Db, Dw
from .registers import r4, r5, r6, r7, r8, r9, r10, r11, r12, r13, r14, r15
from .registers import Msp430Register, get_register
from .instructions import ret, push, call, pop, Dcd2


class Msp430Frame(Frame):
    """
        ABI:
        pass arg1 in R11
        pass arg2 in R12
        return value in R10
    """
    def __init__(self, name, arg_locs, live_in, rv, live_out):
        super().__init__(name, arg_locs, live_in, rv, live_out)

        # Allocatable registers:
        self.regs = [r4, r5, r6, r7, r8, r9, r10, r11, r12, r13, r14]

        self.fp = r15
        self.locVars = {}
        self.constants = []
        self.literal_number = 0

    def make_call(self, vcall):
        # TODO: calling convention!
        live_regs = self.live_regs_over(vcall)

        # Caller save registers:
        for register in live_regs:
            yield push(register)

        yield call(vcall.function_name)

        # Restore caller save registers:
        for register in reversed(live_regs):
            yield pop(register)

    def get_register(self, color):
        return get_register(color)

    def new_virtual_register(self, twain=""):
        """ Retrieve a new virtual register """
        return super().new_virtual_register(Msp430Register, twain=twain)

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

    def litpool(self):
        """ Generate instruction for the current literals """
        # Align at 2 bytes
        if self.constants:
            yield Alignment(2)

        # Add constant literals:
        while self.constants:
            label, value = self.constants.pop(0)
            yield Label(label)
            if isinstance(value, int):
                yield Dw(value)
            elif isinstance(value, str):
                yield Dcd2(value)
            elif isinstance(value, bytes):
                for byte in value:
                    yield Db(byte)
                yield Alignment(2)   # Align at 4 bytes
            else:  # pragma: no cover
                raise NotImplementedError('Constant of type {}'.format(value))

    def prologue(self):
        """ Returns prologue instruction sequence """
        # Label indication function:
        yield Label(self.name)

    def epilogue(self):
        """ Return epilogue sequence for a frame. Adjust frame pointer
            and add constant pool
        """
        yield ret()
        # Add final literal pool:
        for instruction in self.litpool():
            yield instruction
