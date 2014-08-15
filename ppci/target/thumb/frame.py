from ..basetarget import Label, Alignment, LabelAddress
from ...irmach import AbstractInstruction, Frame, VirtualRegister
from .instructions import Dcd, Db, AddSp, SubSp, Push, Pop, Mov2
from ..arm.registers import R0, R1, R2, R3, R4, R5, R6, R7, LR, PC, SP


class ArmFrame(Frame):
    """ Arm specific frame for functions. """
    def __init__(self, name):
        # We use r7 as frame pointer.
        super().__init__(name)
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

    def addConstant(self, value):
        lab_name = '{}_literal_{}'.format(self.name, len(self.constants))
        self.constants.append((lab_name, value))
        return lab_name

    def prologue(self):
        """ Returns prologue instruction sequence """
        pre = [
            Label(self.name),                     # Label indication function
            Push({LR, R7})
            ]
        if self.stacksize > 0:
            pre.append(SubSp(self.stacksize))  # Reserve stack space
        pre += [
            Mov2(R7, SP)                          # Setup frame pointer
            ]
        return pre

    def epilogue(self):
        """ Return epilogue sequence for a frame. Adjust frame pointer and add constant pool """
        post = []
        if self.stacksize > 0:
            post.append(AddSp(self.stacksize))
        post += [
            Pop({PC, R7}),
            Alignment(4)   # Align at 4 bytes
            ]

        # Add constant literals:
        for ln, v in self.constants:
            if isinstance(v, int):
                post.extend([Label(ln), Dcd(v)])
            elif isinstance(v, LabelAddress):
                post.extend([Label(ln), Dcd(v)])
            elif isinstance(v, bytes):
                post.append(Label(ln))
                for c in v:
                    post.append(Db(c))
                post.append(Alignment(4))   # Align at 4 bytes
            else:
                raise Exception('Constant of type {} not supported'.format(v))
        return post

    def EntryExitGlue3(self):
        """
            Add code for the prologue and the epilogue. Add a label, the
            return instruction and the stack pointer adjustment for the frame.
        """
        for index, ins in enumerate(self.prologue()):
            self.instructions.insert(index, AbstractInstruction(ins))

        # Postfix code:
        for ins in self.epilogue():
            self.instructions.append(AbstractInstruction(ins))
