
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

    def new_virtual_register(self):
        """ Retrieve a new virtual register """
        return self.temps.__next__()

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
        return 'vreg_{}'.format(self.name)


class AbstractInstruction:
    """
        Abstract machine instruction class. This is a very simple
        abstraction of machine instructions.
    """
    def __init__(self, cls, ops=(), src=(), dst=(), jumps=(), others=(),
                 ismove=False):
        assert type(cls) is type or isinstance(cls, Instruction), str(cls)
        self.assem = cls
        self.ops = tuple(ops)
        self.src = tuple(src)
        self.dst = tuple(dst)
        self.jumps = tuple(jumps)
        self.others = tuple(others)
        self.ismove = ismove

    def __gt__(self, other):
        """ To make the class fit for sorting """
        # TODO: make this nicer..
        return str(self) > str(other)

    def __repr__(self):
        """ Substitutes source, dst and labels in the string """
        if isinstance(self.assem, Instruction):
            x = str(self.assem)
        else:
            cn = self.assem.__name__
            x = '{}, def={}, use={}, other={}'
            x = x.format(cn, self.dst, self.src, self.others)
        return x
