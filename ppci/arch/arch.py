import logging
from functools import lru_cache
from .isa import Instruction, Register
from .. import ir


class Architecture:
    """ Base class for all targets """
    logger = logging.getLogger('arch')
    name = None
    desc = None
    option_names = ()

    def __init__(self, options=None):
        """
            Create a new machine instance with possibly some extra machine
            options.

            options is a tuple with which options to enable.
        """
        self.logger.debug('Creating %s arch', self.name)
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
        return '{}-arch'.format(self.name)

    def make_id_str(self):
        """ Return a string uniquely identifying this machine """
        options = [n for n, v in self.option_settings.items() if v]
        return ':'.join([self.name] + options)

    def get_reg_class(self, bitsize=None, ty=None):
        """ Look for a register class """
        if bitsize:
            ty = {8: ir.i8, 16: ir.i16, 32: ir.i32, 64: ir.i64}[bitsize]
        if ty:
            return self.value_classes[ty]
        raise NotImplementedError()

    def get_size(self, typ):
        """ Get type of ir type """
        if typ is ir.ptr:
            return self.byte_sizes['ptr']
        else:
            return {ir.i8: 1, ir.i16: 2, ir.i32: 4, ir.i64: 8}[typ]

    def new_frame(self, frame_name, function):
        """ Create a new frame with name frame_name for an ir-function """
        arg_types = [arg.ty for arg in function.arguments]
        arg_locs, live_in = self.determine_arg_locations(arg_types)
        if isinstance(function, ir.Function):
            rv, live_out = self.determine_rv_location(function.return_ty)
        else:
            rv = None
            live_out = set()
        frame = self.FrameClass(
            frame_name, arg_locs, live_in, rv, live_out)

        # TODO: change this:
        frame.get_register = self.get_register
        return frame

    def get_register(self, color):
        raise NotImplementedError('get_register')

    def move(self, dst, src):
        """ Generate a move from src to dst """
        raise NotImplementedError('Implement this')

    def gen_call(self, value):
        """ Generate a sequence of instructions for a call to a label.
            The actual call instruction is not yet used until the end
            of the code generation at which time the live variables are
            known.
        """
        if len(value) == 5:
            label, arg_types, res_type, args, res_var = value
            # Setup parameters:
            live_in = set()
            for instr in self.gen_fill_arguments(arg_types, args, live_in):
                yield instr
            rv, live_out = self.determine_rv_location(res_type)
            yield VCall(label, extra_uses=live_in, extra_defs=live_out)
            for instr in self.gen_copy_rv(res_type, res_var):
                yield instr
        elif len(value) == 3:
            label, arg_types, args = value
            live_in = set()
            for instr in self.gen_fill_arguments(arg_types, args, live_in):
                yield instr
            yield VCall(label, extra_uses=live_in)
        else:
            raise RuntimeError()

    def make_call(self, frame, vcall):
        """ Actual call instruction implementation """
        raise NotImplementedError('Implement this')

    def gen_fill_arguments(self, arg_types, args, live):
        """ Generate a sequence of instructions that puts the arguments of
        a function to the right place. """
        raise NotImplementedError('Implement this')

    def gen_copy_rv(self, res_type, res_var):
        """ Generate a sequence of instructions for copying the result of a
        function to the correct variable. Override this function when needed.
        The basic implementation simply moves the result.
        """
        rv, live_out = self.determine_rv_location(res_type)
        yield self.move(res_var, rv)

    def determine_arg_locations(self, arg_types):
        """ Determine argument location for a given function """
        raise NotImplementedError('Implement this')

    def determine_rv_location(self, ret_type):
        """ Determine the location of a return value of a function given the
        type of return value """
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
        self.temps = generate_temps()

        # Local stack:
        self.stacksize = 0
        self.locVars = {}

        # Literal pool:
        self.constants = []
        self.literal_number = 0

    def __repr__(self):
        return 'Frame {}'.format(self.name)

    def alloc_var(self, lvar, size):
        if lvar not in self.locVars:
            self.locVars[lvar] = self.stacksize
            self.stacksize = self.stacksize + size
        return self.locVars[lvar]

    def add_constant(self, value):
        """ Add constant literal to constant pool """
        for lab_name, val in self.constants:
            if value == val:
                return lab_name
        assert isinstance(value, (str, int, bytes)), str(value)
        lab_name = '{}_literal_{}'.format(self.name, self.literal_number)
        self.literal_number += 1
        self.constants.append((lab_name, value))
        return lab_name

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

    def live_ranges(self, vreg):
        """ Determine the live range of some register """
        return self.cfg._live_ranges[vreg]

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

    def prologue(self):  # pragma: no cover
        raise NotImplementedError('Implement this!')

    def epilogue(self):  # pragma: no cover
        raise NotImplementedError('Implement this!')
