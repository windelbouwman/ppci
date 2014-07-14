
"""
  Abstract assembly language instructions.

  This is the second intermediate representation.

  Instructions are selected and scheduled at this stage.
"""

from .target import Instruction


class Frame:
    """
        Activation record abstraction. This class contains a flattened
        function. Instructions are selected and scheduled at this stage.
        Frames differ per machine.
    """
    def __init__(self, name):
        self.name = name
        self.instructions = []
        self.stacksize = 0

    def __repr__(self):
        return 'Frame {}'.format(self.name)


class Temp:
    """ Infinite register value """
    def __init__(self, name):
        self.name = name


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
