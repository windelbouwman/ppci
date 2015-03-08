
"""
  This is the second intermediate representation.

  Instructions are selected and scheduled at this stage.
"""

from .target import Instruction


def generate_temps():
    n = 0
    while True:
        yield 'vreg{}'.format(n)
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
        self.temps = generate_temps()

    def __repr__(self):
        return 'Frame {}'.format(self.name)

    def new_virtual_register(self, cls, twain=""):
        """ Retrieve a new virtual register """
        tmp_name = self.temps.__next__() + twain
        tmp = cls(tmp_name)
        return tmp

    def emit(self, ins):
        """ Append an abstract instruction to the end of this frame """
        assert isinstance(ins, Instruction)
        self.instructions.append(ins)
        return ins

    def between_blocks(self):
        pass
