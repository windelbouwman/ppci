from ..arch import Label, Alignment, Frame
from .thumb_instructions import AddSp, SubSp, Push, Pop, Mov2, Bl
from ..data_instructions import Db, Dd, Dcd2
from .registers import R0, R1, R2, R3, R4, R5, R6, R7, LR, PC, SP


class ThumbFrame(Frame):
    """ Arm specific frame for functions. """
    def __init__(self, name, arg_locs, live_in, rv, live_out):
        super().__init__(name, arg_locs, live_in, rv, live_out)
        # Registers usable by register allocator:
        # We use r7 as frame pointer.
        self.regs = [R0, R1, R2, R3, R4, R5, R6]
        self.fp = R7

        self.locVars = {}
        self.parMap = {}
        # Literal pool:
        self.constants = []
        self.literal_number = 0

    def make_call(self, vcall):
        # Now we now what variables are live:
        live_regs = self.live_regs_over(vcall)
        register_set = set(live_regs)

        # Caller save registers:
        if register_set:
            yield Push(register_set)

        # Make the call:
        yield Bl(vcall.function_name)
        # R0 is filled with return value, do not save it, it will conflict.

        # Restore caller save registers:
        if register_set:
            yield Pop(register_set)

    def alloc_var(self, lvar, size):
        if lvar not in self.locVars:
            self.locVars[lvar] = self.stacksize
            self.stacksize = self.stacksize + size
        return self.locVars[lvar]

    def add_constant(self, value):
        """ Add a constant to this frame """
        # Check if the constant is already in this frame!
        for lab_name, val in self.constants:
            if value == val:
                return lab_name
        lab_name = '{}_literal_{}'.format(self.name, self.literal_number)
        self.literal_number += 1
        self.constants.append((lab_name, value))
        return lab_name

    def round_up(self, s):
        return s + (4 - s % 4)

    def prologue(self):
        """ Returns prologue instruction sequence """
        yield Label(self.name)  # Label indication function
        yield Push({LR, R7})
        yield Push({R5, R6})    # Callee save registers!
        if self.stacksize > 0:
            ssize = self.round_up(self.stacksize)

            # subSp cannot handle large numbers:
            while ssize > 0:
                if ssize < 128:
                    yield SubSp(ssize)  # Reserve stack space
                    ssize -= ssize
                else:
                    yield SubSp(128)  # Reserve stack space
                    ssize -= 128
        yield Mov2(R7, SP)                          # Setup frame pointer

    def insert_litpool(self):
        """ Insert the literal pool at the current position """
        # Align at 4 bytes
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
                raise NotImplementedError('{} not supported'.format(value))

    def between_blocks(self):
        for instruction in self.insert_litpool():
            self.emit(instruction)

    def epilogue(self):
        """ Return epilogue sequence for a frame. Adjust frame pointer and add
        constant pool """

        if self.stacksize > 0:
            ssize = self.round_up(self.stacksize)
            # subSp cannot handle large numbers:
            while ssize > 0:
                if ssize < 128:
                    yield AddSp(ssize)
                    ssize -= ssize
                else:
                    yield AddSp(128)
                    ssize -= 128
        yield Pop({R5, R6})  # Callee save registers!
        yield Pop({PC, R7})

        # Add final literal pool
        for instruction in self.insert_litpool():
            yield instruction
