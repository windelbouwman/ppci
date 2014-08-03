from ... import ir, same_dir
from ppci.irmach import AbstractInstruction as makeIns
from ppci import pyburg
from ..basetarget import Nop
from ..instructionselector import InstructionSelector
from .instructions import Orr, Lsl, Str2, Ldr2, Ldr3
from .instructions import B, Bl, Bgt, Blt, Beq, Bne
from .instructions import Mov2, Mov3
from .instructions import Cmp, Sub2, Mul

# Import BURG spec for arm:
spec_file = same_dir(__file__, 'arm.brg')
arm_matcher = pyburg.load_as_module(spec_file)


class ArmMatcher(arm_matcher.Matcher):
    """ Matcher that derives from a burg spec generated matcher """
    def __init__(self, selector):
        super().__init__()
        self.newTmp = selector.newTmp
        self.emit = selector.emit
        self.selector = selector


class ArmInstructionSelector(InstructionSelector):
    """ Instruction selector for the arm architecture """
    def __init__(self):
        super().__init__()
        self.matcher = ArmMatcher(self)

    def munchCall(self, e):
        """ Generate code for call sequence """
        # Move arguments into proper locations:
        reguses = []
        self.emit(Bl(e.f), src=reguses, dst=[self.frame.rv])
        # d = self.newTmp()
        # self.move(d, self.frame.rv)

    def munchStm(self, s):
        if isinstance(s, ir.Terminator):
            pass
        elif isinstance(s, ir.Move) and isinstance(s.dst, ir.Temp):
            val = self.munchExpr(s.src)
            dreg = s.dst
            self.move(dreg, val)
        elif isinstance(s, ir.Exp):
            # Generate expression code and discard the result.
            x = self.munchExpr(s.e)
            self.emit(Nop(), src=[x])
        else:
            raise NotImplementedError('Stmt --> {}'.format(s))

    def move(self, dst, src):
        self.emit(Mov2, src=[src], dst=[dst], ismove=True)
