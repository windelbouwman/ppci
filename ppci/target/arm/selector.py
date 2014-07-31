from ... import ir, same_dir
from ppci.irmach import AbstractInstruction as makeIns
from ppci.ir2tree import makeTree
from .instructions import Str1, Mov2
from .instructions import B, Bl, Blt, Bgt, Beq, Bne, Cmp2, Ble, Bge
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

    def munchExpr(self, e):
        # Use BURG system here:
        t = makeTree(e)
        return self.matcher.gen(t)

    def munchCall(self, e):
        """ Generate code for call sequence """
        # Move arguments into proper locations:
        reguses = []
        for i, a in enumerate(e.arguments):
            loc = self.frame.argLoc(i)
            m = ir.Move(loc, a)
            self.munchStm(m)
            if isinstance(loc, ir.Temp):
                reguses.append(loc)
        self.emit(Bl(e.f), src=reguses, dst=[self.frame.rv])
        d = self.newTmp()
        self.move(d, self.frame.rv)
        return d

    def munchStm(self, s):
        if isinstance(s, ir.Terminator):
            pass
        elif isinstance(s, ir.Move) and isinstance(s.dst, ir.Mem) and \
            isinstance(s.dst.e, ir.Binop) and s.dst.e.operation == '+' and \
            isinstance(s.dst.e.b, ir.Const):
            a = self.munchExpr(s.dst.e.a)
            val = self.munchExpr(s.src)
            c = s.dst.e.b.value
            self.emit(Str1, others=[c], src=[a, val])
        elif isinstance(s, ir.Move) and isinstance(s.dst, ir.Mem):
            memloc = self.munchExpr(s.dst.e)
            val = self.munchExpr(s.src)
            self.emit(Str1, others=[0], src=[memloc, val])
        elif isinstance(s, ir.Move) and isinstance(s.dst, ir.Temp):
            val = self.munchExpr(s.src)
            dreg = s.dst
            self.move(dreg, val)
        elif isinstance(s, ir.Exp):
            # Generate expression code and discard the result.
            x = self.munchExpr(s.e)
            self.emit(Nop(), src=[x])
        elif isinstance(s, ir.Jump):
            tgt = self.targets[s.target]
            self.emit(B(ir.label_name(s.target)), jumps=[tgt])
        elif isinstance(s, ir.CJump):
            a = self.munchExpr(s.a)
            b = self.munchExpr(s.b)
            self.emit(Cmp2, src=[a, b])
            ntgt = self.targets[s.lab_no]
            ytgt = self.targets[s.lab_yes]
            jmp_ins = makeIns(B(ir.label_name(s.lab_no)), jumps=[ntgt])
            opnames = {'<': Blt, '>':Bgt, '==':Beq, '!=':Bne, '>=':Bge}
            op = opnames[s.cond](ir.label_name(s.lab_yes))
            self.emit(op, jumps=[ytgt, jmp_ins])  # Explicitely add fallthrough
            self.emit2(jmp_ins)
        else:
            raise NotImplementedError('Stmt --> {}'.format(s))

    def move(self, dst, src):
        self.emit(Mov2, src=[src], dst=[dst], ismove=True)
