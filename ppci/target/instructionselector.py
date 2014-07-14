from ppci import ir
from ppci.irmach import AbstractInstruction, Temp
from .basetarget import Label


def genTemps():
    n = 900
    while True:
        yield ir.Temp('t{}'.format(n))
        n = n + 1


class InstructionSelector:
    """
        Base instruction selector. This class must be overridden by
        backends.
    """
    def __init__(self):
        self.temps = genTemps()

    def newTmp(self):
        return self.temps.__next__()

    def munchFunction(self, f, frame):
        # Entry point for instruction selection
        assert isinstance(f, ir.Function)
        self.targets = {}
        # Enter a frame per function:
        self.frame = frame

        # First define labels:
        for bb in f.Blocks:
            itgt = AbstractInstruction(Label(ir.label_name(bb)))
            self.targets[bb] = itgt

        # Generate code for all blocks:
        for bb in f.Blocks:
            self.emit2(self.targets[bb])
            for i in bb.Instructions:
                self.munchStm(i)

        # Generate code for return statement:
        self.munchStm(ir.Move(self.frame.rv, f.return_value))

    def move(self, dst, src):
        raise NotImplementedError('Not target implemented')

    def emit(self, *args, **kwargs):
        """ Abstract instruction emitter """
        i = AbstractInstruction(*args, **kwargs)
        return self.emit2(i)

    def emit2(self, i):
        self.frame.instructions.append(i)
        return i

    def munchStm(self, s):
        """ Implement this in the target specific back-end """
        raise NotImplementedError()

    def munchExpr(self, e):
        """ Implement this in the target specific back-end """
        raise NotImplementedError()
