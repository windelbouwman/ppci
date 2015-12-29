from ..target import Label, Alignment, Frame, VCall
from .instructions import dcd, AddSp, SubSp, Push, Pop, Mov2, Bl
from ..data_instructions import Db
from ..arm.registers import R0, R1, R2, R3, R4, R5, R6, R7, LR, PC, SP
from ..arm.registers import get_register


class ThumbFrame(Frame):
    """ Arm specific frame for functions. """
    def __init__(self, name):
        # We use r7 as frame pointer.
        super().__init__(name)
        # Registers usable by register allocator:
        self.regs = [R0, R1, R2, R3, R4, R5, R6]
        self.rv = R0
        self.p1 = R1
        self.p2 = R2
        self.p3 = R3
        self.p4 = R4
        self.fp = R7

        self.locVars = {}
        self.parMap = {}
        # Literal pool:
        self.constants = []
        self.literal_number = 0

    def move(self, dst, src):
        self.emit(Mov2(dst, src, ismove=True))

    def get_register(self, color):
        return get_register(color)

    def gen_call(self, label, args, res_var):
        """ Generate code for call sequence """

        # Copy args to correct positions:
        reg_uses = []
        for i, arg in enumerate(args):
            arg_loc = self.arg_loc(i)
            if type(arg_loc) is type(R0):
                reg_uses.append(arg_loc)
                self.move(arg_loc, arg)
            else:  # pragma: no cover
                raise NotImplementedError('Parameters in memory not impl')
        # Caller save registers:
        self.emit(
            VCall(label, extra_uses=reg_uses, extra_defs=[self.rv]))
        self.move(res_var, self.rv)

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
                yield dcd(value)
            elif isinstance(value, str):
                yield dcd(value)
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
