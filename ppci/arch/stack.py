
""" This module contains all kind of classes to describe the stack """

import enum
from .encoding import Instruction
from .registers import Register
from .generic_instructions import Label


class FramePointerLocation(enum.Enum):
    """ Define where the frame pointer is pointing to """
    TOP = 1
    BOTTOM = 2


class StackLocation:
    """ A stack location can store data just like a register """
    def __init__(self, offset: int, size: int):
        # self.frame = frame  # The frame in which this location lives
        self.offset = offset
        self.size = size

    def __repr__(self):
        return 'Stack[{} bytes at {}]'.format(self.size, self.offset)


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
    def __init__(
            self, name, debug_db=None, fp_location=FramePointerLocation.TOP):
        self.name = name
        self.debug_db = debug_db  # Eventual debug information
        self.fp_location = fp_location
        self.instructions = []
        self.used_regs = set()
        self.is_leaf = False  # TODO: detect leaf functions
        self.out_calls = []
        self.temps = generate_temps()

        # Local stack:
        self.stacksize = 0
        self.alignment = 1

        # Literal pool:
        self.constants = []
        self.literal_number = 0

    def __repr__(self):
        return 'Frame {}'.format(self.name)

    def alloc(self, size: int, alignment: int):
        """ Allocate space on the stack frame and return a stacklocation """
        # determine alignment of whole stack frame as maximum alignment
        self.alignment = max(self.alignment, alignment)

        # Calling alloc with 0 indicates a problem somewhere.
        if size == 0:
            raise ValueError('Trying to allocate 0 bytes')

        # grow down or up?
        if self.fp_location == FramePointerLocation.TOP:
            # Create a negative offset from framepointer:
            self.stacksize += size
            misalign = self.stacksize % alignment
            if misalign:
                self.stacksize = self.stacksize - misalign + alignment
            # When frame pointer is located at top of the stackframe,
            # the offset is negative:
            offset = -self.stacksize
        else:
            misalign = self.stacksize % alignment
            if misalign:
                self.stacksize += size - misalign
            offset = self.stacksize
            self.stacksize += size
        location = StackLocation(offset, size)
        return location

    def add_out_call(self, size):
        """ Record that we made a call out of this function.

        The size parameter determines how much bytes we needed to reserve
        on the stack to pass the arguments.
        """
        self.out_calls.append(size)

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
        """ Check if a register or one of its aliases is used by this frame.
        """
        return register in self.used_regs or \
            any(self.is_used(a) for a in register.aliases)

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
