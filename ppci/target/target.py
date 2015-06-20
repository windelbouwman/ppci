import logging
from .isa import Instruction


class Target:
    """ Base class for all targets """
    def __init__(self, name, desc=''):
        logging.getLogger('target').debug('Creating {} target'.format(name))
        self.name = name
        self.desc = desc
        self.registers = []
        self.byte_sizes = {'int': 4}  # For front end!
        self.byte_sizes['byte'] = 1

    def __repr__(self):
        return '{}-target'.format(self.name)

    def get_reloc(self, name):
        """ Retrieve a relocation identified by a name """
        return self.isa.relocation_map[name]

    def lower_frame_to_stream(self, frame, outs):
        """ Lower instructions from frame to output stream """
        for ins in frame.instructions:
            assert isinstance(ins, Instruction)
            assert ins.is_colored, str(ins)
            outs.emit(ins)


class Nop(Instruction):
    """ Instruction that does nothing and has zero size """
    def encode(self):
        return bytes()

    def __repr__(self):
        return 'NOP'


class RegisterUseDef(Nop):
    """ Magic instruction that can be used to define and use registers """
    def __init__(self):
        super().__init__()
        self._src = set()
        self._dst = set()

    def add_use(self, reg):
        self._src.add(reg)

    def add_uses(self, uses):
        for u in uses:
            self.add_use(u)

    def add_def(self, reg):
        self._dst.add(reg)

    def add_defs(self, defs):
        for d in defs:
            self.add_def(d)


class PseudoInstruction(Instruction):
    pass


class Label(PseudoInstruction):
    def __init__(self, name):
        super().__init__()
        self.name = name

    def __repr__(self):
        return '{}:'.format(self.name)

    def symbols(self):
        return [self.name]


class Comment(PseudoInstruction):
    """ Comment instruction. Does nothing, only contains comments """
    def __init__(self, txt):
        super().__init__()
        self.txt = txt

    def __repr__(self):
        return '; {}'.format(self.txt)


class Alignment(PseudoInstruction):
    """ Instruction to indicate alignment. Encodes to nothing, but is
        used in the linker to enforce multiple of x byte alignment
    """
    def __init__(self, a):
        super().__init__()
        self.align = a

    def __repr__(self):
        return 'ALIGN({})'.format(self.align)


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
