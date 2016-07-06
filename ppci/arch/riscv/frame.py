from ..arch import Label, Alignment, Frame
from .instructions import dcd, Addi, Subi, Mov, Bl, Sw, Lw, Blr
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
        self.callee_save = () #(LR, FP, R9, R18, R19, R20, R21 ,R22, R23 ,R24, R25, R26, R27)

    def new_virtual_register(self, twain=""):
        """ Retrieve a new virtual register """
        return super().new_virtual_register(RiscvRegister, twain=twain)

    def prologue(self):
        """ Returns prologue instruction sequence """
        # Label indication function:
        yield Label(self.name)
        # Callee save registers:
        i = 0
        for register in self.callee_save:
            yield Sw(register, i, SP)
            i-= 4
        Addi(SP, SP, i)
        if self.stacksize > 0:
            yield Subi(SP, SP, self.stacksize)  # Reserve stack space
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
            yield Addi(SP, SP, self.stacksize)
        # Callee saved registers:
        i = 0
        for register in reversed(self.callee_save):
            i+= 4
            yield Lw(register, i, SP)
        Addi(SP, SP, i)
        yield(Blr(R0, LR, 0))
        # Add final literal pool:
        for instruction in self.litpool():
            yield instruction
        yield Alignment(4)   # Align at 4 bytes
