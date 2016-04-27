from ..arch import Label, Alignment, Frame
from .instructions import dcd, Add, Sub, Mov, Mov2, Bl, Sw, Lw, Blr
from ..data_instructions import Db
from .registers import R0, LR, SP, FP
from .registers import R9, R18, R19, R20, R21, R22, R23, R24, R25, R26, R27
from .registers import RiscvRegister


class RiscvFrame(Frame):
    """ Riscv specific frame for functions.

        R5 and above are callee save (the function that is called
    """
    def __init__(self, name, arg_locs, live_in, rv, live_out):
        super().__init__(name, arg_locs, live_in, rv, live_out)
        # Allocatable registers:
        self.regs = [R9, R18, R19, R20, R21, R22, R23, R24, R25, R26, R27]
        self.fp = FP
        self.callee_save = () #(LR, FP, R9, R18, R19, R20, R21 ,R22, R23 ,R24, R25, R26, R27)

        self.locVars = {}

        # Literal pool:
        self.constants = []
        self.literal_number = 0

    def new_virtual_register(self, twain=""):
        """ Retrieve a new virtual register """
        return super().new_virtual_register(RiscvRegister, twain=twain)

    def make_call(self, vcall):
        """ Implement actual call and save / restore live registers """
        # Now we now what variables are live:
        live_regs = self.live_regs_over(vcall)
        # Caller save registers:
        i = 0
        for register in live_regs:
            yield Sw(SP, register, i)
            i-= 4
        yield Sw(SP, LR, i)
        i-=4
        yield Add(SP, SP, i)

        yield Bl(LR, vcall.function_name)

        # Restore caller save registers:
        
        i = 0
        i+= 4
        yield Lw(LR, SP, i)
        for register in reversed(live_regs):
            i+= 4
            yield Lw(register, SP, i)
        
        yield Add(SP, SP, i)

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
        # Callee save registers:
        i = 0
        for register in self.callee_save:
            yield Sw(SP,register,i)
            i-= 4
        Add(SP, SP, i)
        if self.stacksize > 0:
            yield Sub(SP, SP, self.stacksize)  # Reserve stack space
        yield Mov(FP, SP)                 # Setup frame pointer

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
        # Callee saved registers:
        i = 0
        for register in reversed(self.callee_save):
            i+= 4
            yield Lw(register, SP, i)
        Add(SP, SP, i)
        yield(Blr(R0, LR, 0))
        # Add final literal pool:
        for instruction in self.litpool():
            yield instruction
        yield Alignment(4)   # Align at 4 bytes
