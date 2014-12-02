from ..basetarget import Label, Alignment
from ...irmach import AbstractInstruction, Frame, VirtualRegister
from .instructions import Dcd, Add, Sub, Push, Pop, Mov, Db, Mov2, Bl, RegisterSet
from .registers import R0, R1, R2, R3, R4, R5, R6, R7, R8
from .registers import R9, R10, R11, LR, PC, SP


class ArmFrame(Frame):
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
        # We use r7 as frame pointer.
        super().__init__(name)
        # Allocatable registers:
        self.regs = [R0, R1, R2, R3, R4, R5, R6, R7]
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
            if type(arg_loc) is VirtualRegister:
                reg_uses.append(arg_loc)
                self.move(arg_loc, arg)
            else:
                raise NotImplementedError('Parameters in memory not impl')
        self.emit(Bl(label), src=reg_uses, dst=[self.rv])
        self.emit(Pop(RegisterSet({R1, R2, R3, R4})))
        self.move(res_var, self.rv)

        # Restore caller save registers:

    def move(self, dst, src):
        """ Generate a move from src to dst """
        self.emit(Mov2, src=[src], dst=[dst], ismove=True)

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
        assert type(value) in [str, int, bytes], str(value)
        lab_name = '{}_literal_{}'.format(self.name, self.literal_number)
        self.literal_number += 1
        self.constants.append((lab_name, value))
        return lab_name

    def prologue(self):
        """ Returns prologue instruction sequence """
        pre = [
            # Label indication function:
            Label(self.name),
            Push(RegisterSet({LR, R11})),
            Push(RegisterSet({R5, R6, R7, R8, R9, R10})),  # Callee save registers!
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
            elif isinstance(v, str):
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
        self.emit(Pop(RegisterSet({R5, R6, R7, R8, R9, R10})))
        self.emit(Pop(RegisterSet({PC, R11})))
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
