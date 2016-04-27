import logging
from functools import lru_cache
from .isa import Instruction, Register
from ..ir import i8, i16, i32, i64, ptr


class Architecture:
    """ Base class for all targets """
    name = None
    desc = None
    option_names = ()

    def __init__(self, options=None):
        """
            Create a new machine instance with possibly some extra machine
            options.

            options is a tuple with which options to enable.
        """
        logging.getLogger('target').debug('Creating %s target', self.name)
        self.option_settings = {o: False for o in self.option_names}
        if options:
            assert isinstance(options, tuple)
            for option_name in options:
                assert option_name in self.option_names
                self.option_settings[option_name] = True
        self.registers = []
        self.byte_sizes = {}
        self.byte_sizes['int'] = 4  # For front end!
        self.byte_sizes['ptr'] = 4  # For ir to dag
        self.byte_sizes['byte'] = 1
        self.value_classes = {}

    def has_option(self, name):
        """ Check for an option setting selected """
        return self.option_settings[name]

    def __repr__(self):
        return '{}-target'.format(self.name)

    def make_id_str(self):
        """ Return a string uniquely identifying this machine """
        options = [n for n, v in self.option_settings.items() if v]
        return ':'.join([self.name] + options)

    def get_reg_class(self, bitsize=None, ty=None):
        """ Look for a register class """
        if bitsize:
            ty = {8: i8, 16: i16, 32: i32, 64: i64}[bitsize]
        if ty:
            return self.value_classes[ty]
        raise NotImplementedError()

    def get_size(self, typ):
        """ Get type of ir type """
        if typ is ptr:
            return self.byte_sizes['ptr']
        else:
            return {i8: 1, i16: 2, i32: 4, i64: 8}[typ]

    def new_frame(self, frame_name, function):
        """ Create a new frame with name frame_name for an ir-function """
        arg_types = [arg.ty for arg in function.arguments]
        arg_locs, live_in, rv, live_out = \
            self.determine_arg_locations(arg_types, None)
        frame = self.FrameClass(
            frame_name, arg_locs, live_in, rv, live_out)

        # TODO: change this:
        frame.get_register = self.get_register
        return frame

    def get_register(self, color):
        raise NotImplementedError('get_register')

    def determine_arg_locations(self, arg_types, ret_type):
        """ Determine argument location for a given function """
        raise NotImplementedError('Implement this')

    def get_reloc(self, name):
        """ Retrieve a relocation identified by a name """
        return self.isa.relocation_map[name]

    def get_runtime(self):
        raise NotImplementedError('Implement this')

    @lru_cache(maxsize=30)
    def get_compiler_rt_lib(self):
        """ Gets the runtime for the compiler. Returns an object with the
        compiler runtime for this architecture """
        return self.get_runtime()

    runtime = property(get_compiler_rt_lib)


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
    """
        An instruction call before register allocation. After register
        allocation, this instruction is replaced by the correct calling
        sequence for a function.
    """
    def __init__(self, function_name, **kwargs):
        super().__init__(**kwargs)
        self.function_name = function_name

    def __repr__(self):
        return 'VCALL {}'.format(self.function_name)


class PseudoInstruction(Instruction):
    """
        Pseudo instructions can be emitted into a stream, but are not real
        machine instructions. They are instructions like comments, labels
        and debug information alike information.
    """
    def __init__(self):
        super().__init__()

    def encode(self):
        return bytes()


class Label(PseudoInstruction):
    """ Assembly language label instruction """
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


class DebugData(PseudoInstruction):
    """
        Carrier instruction of debug information.
    """
    def __init__(self, data):
        super().__init__()
        self.data = data

    def __repr__(self):
        return '.debug_data( {} )'.format(self.data)


# TODO: deprecated:
class DebugLocation222(PseudoInstruction):
    """ Debug location """
    def __init__(self, filename, row, col):
        super().__init__()
        self.filename = filename
        self.row = row
        self.col = col

    def __repr__(self):
        return 'debug_loc({},{},{})'.format(self.filename, self.row, self.col)


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
