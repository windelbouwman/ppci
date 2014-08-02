from ... import ir, same_dir
from .instructions import Mov2
from .instructions import Bl
from ppci import pyburg
from ..basetarget import Nop
from ..instructionselector import InstructionSelector

# Import BURG spec for arm:
spec_file = same_dir(__file__, 'arm.brg')
arm_matcher = pyburg.load_as_module(spec_file)


class ArmMatcher(arm_matcher.Matcher):
    """ Matcher that derives from a burg spec generated matcher """
    def __init__(self, selector):
        super().__init__()
        self.selector = selector
        self.newTmp = selector.newTmp
        self.emit = selector.emit


class ArmInstructionSelector(InstructionSelector):
    """ Instruction selector for the arm architecture """
    def __init__(self):
        super().__init__()
        self.matcher = ArmMatcher(self)

    def munchCall(self, e):
        """ Generate code for call sequence """
        reguses = []
        self.emit(Bl(e.f), src=reguses, dst=[self.frame.rv])
        # d = self.newTmp()
        # self.move(d, self.frame.rv)
        # return d

    def move(self, dst, src):
        self.emit(Mov2, src=[src], dst=[dst], ismove=True)
