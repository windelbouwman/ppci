import logging
from .isa import Instruction, Register
from .data_instructions import Ds
from ..ir import i8, i16, i32, i64, ptr


class Target:
    """ Base class for all targets """
    def __init__(self, name, desc=''):
        logging.getLogger('target').debug('Creating {} target'.format(name))
        self.name = name
        self.desc = desc
        self.registers = []
        self.byte_sizes = {}
        self.byte_sizes['int'] = 4  # For front end!
        self.byte_sizes['ptr'] = 4  # For ir to dag
        self.byte_sizes['byte'] = 1
        self.value_classes = {}

    def __repr__(self):
        return '{}-target'.format(self.name)

    def get_reg_class(self, bitsize=None, ty=None):
        """ Look for a register class """
        if bitsize:
            ty = {8: i8, 16: i16, 32: i32, 64: i64}[bitsize]
        if ty:
            return self.value_classes[ty]
        raise NotImplementedError()

    def get_size(self, ty):
        """ Get type of ir type """
        if ty is ptr:
            return self.byte_sizes['ptr']
        else:
            return {i8: 1, i16: 2, i32: 4, i64: 8}[ty]

    def get_reloc(self, name):
        """ Retrieve a relocation identified by a name """
        return self.isa.relocation_map[name]

    def emit_global(self, outs, lname, amount):
        # TODO: alignment?
        outs.emit(Label(lname))
        if amount > 0:
            outs.emit(Ds(amount))
        else:  # pragma: no cover
            raise NotImplementedError()

    def get_runtime_src(self):
        return ''


class Nop(Instruction):
    """ Instruction that does nothing and has zero size """
    def encode(self):
        return bytes()

    def __repr__(self):
        return 'NOP'


class VirtualInstruction(Instruction):
    """
        Virtual instructions are instructions used during code generation
        and can never be encoded into a stream.
    """
    def encode(self):
        raise RuntimeError('Cannot encode virtual instruction')


class RegisterUseDef(VirtualInstruction):
    """ Magic instruction that can be used to define and use registers """
    def __repr__(self):
        return 'VUseDef'

    def add_use(self, reg):
        self.extra_uses.append(reg)

    def add_uses(self, uses):
        for use in uses:
            self.add_use(use)

    def add_def(self, reg):
        self.extra_defs.append(reg)

    def add_defs(self, defs):
        for df in defs:
            self.add_def(df)


class VCall(VirtualInstruction):
    def __init__(self, function_name, **kwargs):
        super().__init__(**kwargs)
        self.function_name = function_name

    def __repr__(self):
        return 'VCALL {}'.format(self.function_name)


class PseudoInstruction(Instruction):
    def __init__(self):
        super().__init__()

    def encode(self):
        return bytes()


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
    def __init__(self, name, arg_locs, live_in, rv, live_out):
        self.name = name
        self.arg_locs = arg_locs
        self.live_in = live_in
        self.rv = rv
        self.live_out = live_out
        self.instructions = []
        self.stacksize = 0
        self.temps = generate_temps()
        self.register_classes = {}

    def __repr__(self):
        return 'Frame {}'.format(self.name)

    def live_regs_over(self, instruction):
        """ Determine what registers are live along an instruction.
        Useful to determine if registers must be saved when making a call """
        # print(self.cfg._map)
        # assert self.cfg.has_node(instruction)
        # fg_node = self.cfg.get_node(instruction)
        # print('live in and out', fg_node.live_in, fg_node.live_out)

        # Get register colors from interference graph:
        live_regs = []
        for tmp in instruction.live_in & instruction.live_out:
            # print(tmp)
            n = self.ig.get_node(tmp)
            live_regs.append(self.get_register(n.color))
        return live_regs

    def get_register(self, color):
        raise NotImplementedError('get_register')

    def new_reg(self, cls, twain=""):
        """ Retrieve a new virtual register """
        tmp_name = self.temps.__next__() + twain
        assert issubclass(cls, Register)
        # cls = self.register_classes[bit_size]
        tmp = cls(tmp_name)
        return tmp

    def emit(self, ins):
        """ Append an abstract instruction to the end of this frame """
        assert isinstance(ins, Instruction)
        self.instructions.append(ins)
        return ins

    def between_blocks(self):
        pass
