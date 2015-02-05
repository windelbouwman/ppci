from ..basetarget import Label, Alignment
from ...irmach import AbstractInstruction, Frame, VirtualRegister
from .instructions import Dcd, Db, AddSp, SubSp, Push, Pop, Mov2, Bl
from ..arm.registers import R0, R1, R2, R3, R4, R5, R6, R7, LR, PC, SP


class ArmFrame(Frame):
    """ Arm specific frame for functions. """
    def __init__(self, name):
        # We use r7 as frame pointer.
        super().__init__(name)
        # Registers usable by register allocator:
        self.regs = [R0, R1, R2, R3, R4, R5, R6]
        self.rv = VirtualRegister('special_RV')
        self.p1 = VirtualRegister('special_P1')
        self.p2 = VirtualRegister('special_P2')
        self.p3 = VirtualRegister('special_P3')
        self.p4 = VirtualRegister('special_P4')
        self.fp = VirtualRegister('special_FP')
        # Pre-colored registers:
        self.tempMap = {}
        self.tempMap[self.rv] = R0
        self.tempMap[self.p1] = R1
        self.tempMap[self.p2] = R2
        self.tempMap[self.p3] = R3
        self.tempMap[self.p4] = R4
        self.tempMap[self.fp] = R7
        self.locVars = {}
        self.parMap = {}
        # Literal pool:
        self.constants = []
        self.literal_number = 0

    def move(self, dst, src):
        self.emit(Mov2, src=[src], dst=[dst], ismove=True)

    def gen_call(self, label, args, res_var):
        """ Generate code for call sequence """

        # Copy args to correct positions:
        reg_uses = []
        for i, arg in enumerate(args):
            arg_loc = self.arg_loc(i)
            if type(arg_loc) is VirtualRegister:
                reg_uses.append(arg_loc)
                self.move(arg_loc, arg)
            else:
                raise NotImplementedError('Parameters in memory not impl')
        # Caller save registers:
        self.emit(Push({R1, R2, R3, R4}))
        self.emit(Bl(label), src=reg_uses, dst=[self.rv])
        self.emit(Pop({R1, R2, R3, R4}))
        self.move(res_var, self.rv)

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

    def addConstant(self, value):
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
        pre = [
            Label(self.name),                     # Label indication function
            Push({LR, R7}),
            Push({R5, R6}),  # Callee save registers!
            ]
        if self.stacksize > 0:
            ssize = self.round_up(self.stacksize)

            # subSp cannot handle large numbers:
            while ssize > 0:
                if ssize < 128:
                    pre.append(SubSp(ssize))  # Reserve stack space
                    ssize -= ssize
                else:
                    pre.append(SubSp(128))  # Reserve stack space
                    ssize -= 128
        pre += [
            Mov2(R7, SP)                          # Setup frame pointer
            ]
        return pre

    def insert_litpool(self):
        """ Insert the literal pool at the current position """
        # Align at 4 bytes
        self.emit(Alignment(4))

        # Add constant literals:
        # TODO: pop constants from pool
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
        """ Return epilogue sequence for a frame. Adjust frame pointer and add
        constant pool """

        if self.stacksize > 0:
            ssize = self.round_up(self.stacksize)
            # subSp cannot handle large numbers:
            while ssize > 0:
                if ssize < 128:
                    self.emit(AddSp(ssize))
                    ssize -= ssize
                else:
                    self.emit(AddSp(128))
                    ssize -= 128
        self.emit(Pop({R5, R6}))  # Callee save registers!
        self.emit(Pop({PC, R7}))
        self.insert_litpool()  # Add final literal pool

    def EntryExitGlue3(self):
        """
            Add code for the prologue and the epilogue. Add a label, the
            return instruction and the stack pointer adjustment for the frame.
        """
        for index, ins in enumerate(self.prologue()):
            self.instructions.insert(index, AbstractInstruction(ins))

        # Postfix code (this uses the emit function):
        self.epilogue()
