
"""
  Abstract assembly language instructions.

  This is the second intermediate representation.

  Instructions are selected and scheduled at this stage.
"""

from .target import Instruction


def genTemps():
    n = 0
    while True:
        yield VirtualRegister('vreg{}'.format(n))
        n = n + 1


class Frame:
    """
        Activation record abstraction. This class contains a flattened
        function. Instructions are selected and scheduled at this stage.
        Frames differ per machine. The only thing left to do for a frame
        is register allocation.
    """
    def __init__(self, name):
        self.name = name
        self.instructions = []
        self.stacksize = 0
        self.temps = genTemps()

    def __repr__(self):
        return 'Frame {}'.format(self.name)

    def new_virtual_register(self, twain=""):
        """ Retrieve a new virtual register """
        tmp = self.temps.__next__()
        tmp.name += twain
        return tmp

    def emit(self, *args, **kwargs):
        """ Append an abstract instruction to the end of this frame """
        if len(args) == 1 and type(args[0]) is AbstractInstruction:
            i = args[0]
        else:
            i = AbstractInstruction(*args, **kwargs)
        self.instructions.append(i)
        return i

    def between_blocks(self):
        pass


class VirtualRegister:
    """ Infinite register value """
    def __init__(self, name):
        # TODO: have some value type here?
        self.name = name

    def __repr__(self):
        return self.name


class AbstractInstruction:
    """
        Abstract machine instruction class. This is a very simple
        abstraction of machine instructions.
    """
    __slots__ = [
        'assem', 'ops', 'src', 'dst', 'jumps', 'others', 'ismove',
        'gen', 'kill', 'live_out', 'live_in']

    def __init__(self, cls, ops=(), src=(), dst=(), jumps=(), others=(),
                 ismove=False):
        assert isinstance(cls, type) or isinstance(cls, Instruction), str(cls) + str(type(cls))
        self.assem = cls
        self.ops = tuple(ops)
        self.src = tuple(src)
        self.dst = tuple(dst)
        self.jumps = tuple(jumps)
        self.others = tuple(others)
        self.ismove = ismove

        # Check src and dst to be virtual registers:
        if isinstance(cls, type):
            assert all(isinstance(u, VirtualRegister) for u in self.src)

    def __repr__(self):
        """ Substitutes source, dst and labels in the string """
        if isinstance(self.assem, Instruction):
            cn = str(self.assem)
        else:
            cn = self.assem.__name__
        return cn

    @property
    def long_repr(self):
        if hasattr(self, 'live_out'):
            lo = self.live_out
        else:
            lo = 'None'
        if hasattr(self, 'live_in'):
            li = self.live_in
        else:
            li = 'None'
        return '{:25}, def={:20}, use={:20}, other={:20}, jumps={:20}, live_out={:40}, live_in={:40}'.format(
            str(self), str(self.dst), str(self.src), str(self.others),
            str(self.jumps), str(lo), str(li))
