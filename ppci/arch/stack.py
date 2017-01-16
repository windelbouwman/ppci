
""" This module contains all kind of classes to describe the stack """

from .encoding import Instruction
from .registers import Register
from .generic_instructions import Label


class StackLocation:
    """ A stack location can store data just like a register """
    def __init__(self):
        pass


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
        self.used_regs = set()
        self.temps = generate_temps()

        # Local stack:
        self.stacksize = 0

        # Literal pool:
        self.constants = []
        self.literal_number = 0

    def __repr__(self):
        return 'Frame {}'.format(self.name)

    def alloc(self, size):
        """ Allocate space on the stack frame and return the offset """
        # TODO: determine alignment!
        # TODO: grow down or up?
        offset = -size - self.stacksize
        self.stacksize += size
        return offset

    def new_name(self, salt):
        """ Generate a new unique name """
        name = '{}_{}_{}'.format(self.name, salt, self.literal_number)
        self.literal_number += 1
        return name

    def add_constant(self, value):
        """ Add constant literal to constant pool """
        for lab_name, val in self.constants:
            if value == val:
                return lab_name
        assert isinstance(value, (str, int, bytes)), str(value)
        lab_name = self.new_name('literal')
        self.constants.append((lab_name, value))
        return lab_name

    def is_used(self, register):
        """ Check if a register is used by this frame """
        return register in self.used_regs

    def live_regs_over(self, instruction):
        """ Determine what registers are live along an instruction.
        Useful to determine if registers must be saved when making a call """
        # print(self.cfg._map)
        # assert self.cfg.has_node(instruction)
        # fg_node = self.cfg.get_node(instruction)
        # print('live in and out', fg_node.live_in, fg_node.live_out)

        # Get register colors from interference graph:
        live_regs = []
        for tmp in (
                instruction.live_in & instruction.live_out) - instruction.kill:
            # print(tmp)
            n = self.ig.get_node(tmp)
            reg = n.reg
            live_regs.append(reg)
        # for tmp in instruction.used_registers:
        #    if tmp in live_regs:
        #        live_regs
        return live_regs

    def live_ranges(self, vreg):
        """ Determine the live range of some register """
        return self.cfg._live_ranges[vreg]

    def new_reg(self, cls, twain=""):
        """ Retrieve a new virtual register """
        tmp_name = self.temps.__next__() + twain
        assert issubclass(cls, Register)
        tmp = cls(tmp_name)
        return tmp

    def new_label(self):
        """ Generate a unique new label """
        return Label(self.new_name('label'))

    def emit(self, ins):
        """ Append an abstract instruction to the end of this frame """
        assert isinstance(ins, Instruction)
        self.instructions.append(ins)
        return ins

    def insert_code_before(self, instruction, code):
        """ Insert a code sequence before an instruction """
        pt = self.instructions.index(instruction)
        for idx, ins in enumerate(code):
            self.instructions.insert(idx + pt, ins)

    def insert_code_after(self, instruction, code):
        """ Insert a code sequence after an instruction """
        pt = self.instructions.index(instruction) + 1
        for idx, ins in enumerate(code):
            self.instructions.insert(idx + pt, ins)
