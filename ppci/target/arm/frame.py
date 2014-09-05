from ..basetarget import Label, Alignment, LabelAddress
from ...irmach import AbstractInstruction, Frame, VirtualRegister
from .instructions import Dcd, Add, Sub, Push, Pop, Mov, Db
from .registers import R0, R1, R2, R3, R4, R5, R6, R7, R8
from .registers import R9, R10, R11, LR, PC, SP


class ArmFrame(Frame):
    """ Arm specific frame for functions. """
    def __init__(self, name):
        # We use r7 as frame pointer.
        super().__init__(name)
        self.regs = [R0, R1, R2, R3, R4, R5, R6, R7, R8]
        self.rv = VirtualRegister('special_RV')
        self.p1 = VirtualRegister('special_P1')
        self.p2 = VirtualRegister('special_P2')
        self.p3 = VirtualRegister('special_P3')
        self.p4 = VirtualRegister('special_P4')
        self.fp = VirtualRegister('special_FP')

        # Output of the register allocator goes in here:
        self.tempMap = {}
        # Pre-colored registers:
        self.tempMap[self.rv] = R0
        self.tempMap[self.p1] = R1
        self.tempMap[self.p2] = R2
        self.tempMap[self.p3] = R3
        self.tempMap[self.p4] = R4
        self.tempMap[self.fp] = R11
        self.locVars = {}
        # Literal pool:
        self.constants = []
        self.literal_number = 0

    def argLoc(self, pos):
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
        else:
            raise NotImplementedError('No more than 4 parameters implemented')

    def allocVar(self, lvar, size):
        if lvar not in self.locVars:
            self.locVars[lvar] = self.stacksize
            self.stacksize = self.stacksize + size
        return self.locVars[lvar]

    def add_constant(self, value):
        """ Add constant literal to constant pool """
        for lab_name, val in self.constants:
            if value == val:
                return lab_name
        lab_name = '{}_literal_{}'.format(self.name, self.literal_number)
        self.literal_number += 1
        self.constants.append((lab_name, value))
        return lab_name

    def prologue(self):
        """ Returns prologue instruction sequence """
        pre = [
            Label(self.name),                     # Label indication function
            Push({LR, R11}),
            Sub(SP, SP, self.stacksize),  # Reserve stack space
            Mov(R11, SP)                          # Setup frame pointer
            ]
        return pre

    def insert_litpool(self):
        """ Insert the literal pool at the current position """
        # Align at 4 bytes
        self.emit(Alignment(4))
        # Add constant literals:
        while self.constants:
            ln, v = self.constants.pop(0)
            if isinstance(v, int):
                self.emit(Label(ln))
                self.emit(Dcd(v))
            elif isinstance(v, LabelAddress):
                self.emit(Label(ln))
                self.emit(Dcd(v))
            elif isinstance(v, bytes):
                self.emit(Label(ln))
                for c in v:
                    self.emit(Db(c))
                self.emit(Alignment(4))   # Align at 4 bytes
            else:
                raise Exception('Constant of type {} not supported'.format(v))

    def between_blocks(self):
        self.insert_litpool()

    def epilogue(self):
        """ Return epilogue sequence for a frame. Adjust frame pointer
            and add constant pool
        """
        self.emit(Add(SP, SP, self.stacksize))
        self.emit(Pop({PC, R11}))
        self.insert_litpool()  # Add final literal pool
        self.emit(Alignment(4))   # Align at 4 bytes

    def EntryExitGlue3(self):
        """
            Add code for the prologue and the epilogue. Add a label, the
            return instruction and the stack pointer adjustment for the frame.
        """
        for index, ins in enumerate(self.prologue()):
            self.instructions.insert(index, AbstractInstruction(ins))

        # Postfix code:
        self.epilogue()
