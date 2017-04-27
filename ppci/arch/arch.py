""" Machine architecture description module """

import logging
import abc
from functools import lru_cache
from .registers import Register
from .stack import Frame
from .generic_instructions import VCall, RegisterUseDef
from .generic_instructions import VSaveRegisters, VRestoreRegisters
from .. import ir


class Architecture(metaclass=abc.ABCMeta):
    """ Base class for all targets """
    logger = logging.getLogger('arch')
    name = None
    desc = None
    option_names = ()

    def __init__(self, options=None, register_classes=()):
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
        self.register_classes = register_classes
        self.byte_sizes = {}
        self.byte_sizes['int'] = 4  # For front end!
        self.byte_sizes['ptr'] = 4  # For ir to dag
        self.byte_sizes['byte'] = 1
        self.byte_sizes['u8'] = 1
        self.FrameClass = Frame

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
        raise NotImplementedError()  # pragma: no cover

    def get_size(self, typ):
        """ Get type of ir type """
        if typ is ir.ptr:
            return self.byte_sizes['ptr']
        else:
            return {ir.i8: 1, ir.i16: 2, ir.i32: 4, ir.i64: 8}[typ]

    @property
    @lru_cache(maxsize=None)
    def value_classes(self):
        """ Get a mapping from ir-type to the proper register class """
        mapping = {}
        for register_class in self.register_classes:
            for ty in register_class.ir_types:
                mapping[ty] = register_class.typ
        return mapping

    def new_frame(self, frame_name, function):
        """ Create a new frame with name frame_name for an ir-function """
        frame = self.FrameClass(frame_name)
        return frame

    def move(self, dst, src):  # pragma: no cover
        """ Generate a move from src to dst """
        raise NotImplementedError('Implement this')

    @abc.abstractmethod
    def gen_prologue(self, frame):  # pragma: no cover
        """ Generate instructions for the epilogue of a frame """
        raise NotImplementedError('Implement this!')

    @abc.abstractmethod
    def gen_epilogue(self, frame):  # pragma: no cover
        """ Generate instructions for the epilogue of a frame """
        raise NotImplementedError('Implement this!')

    def between_blocks(self, frame):
        """ Generate any instructions here if needed between two blocks """
        return []

    def gen_vcall(self, value):
        """ Generate a sequence of instructions for a call to a label.
            The actual call instruction is not yet used until the end
            of the code generation at which time the live variables are
            known.
        """
        # TODO: migrate this function to instructionselector?

        if len(value) == 5:
            label, arg_types, res_type, args, res_var = value
        elif len(value) == 3:
            label, arg_types, args = value
            res_type, res_var = None, None
        else:  # pragma: no cover
            raise RuntimeError()

        vcall = VCall(label)

        # Create a placeholder to save caller saved registers:
        yield VSaveRegisters(vcall)

        # Setup parameters:
        for instr in self.gen_fill_arguments(arg_types, args):
            yield instr

        # Emit placeholder for later:
        yield vcall

        # TODO: if a return value is passed on the stack? What then?

        if res_var:
            # Get passed return value back:
            for instr in self.gen_extract_retval(res_type, res_var):
                yield instr

        # Re-adjust the stack pointer:
        for instr in self.gen_stack_cleanup(arg_types):
            yield instr

        # Create a placeholder to restore caller saved registers:
        yield VRestoreRegisters(vcall)

    def gen_call(self, frame, vcall):  # pragma: no cover
        """ Actual call instruction implementation.

        Implement this function for a new backend.

        """
        raise NotImplementedError('Implement this')

    def gen_save_registers(self, registers):  # pragma: no cover
        """ Generate a code sequence to save the specified registers.

        Implement this function for a new backend.

        Args:
            registers: An iterable of registers that is live over
                       the call.
        """
        raise NotImplementedError('Implement this')

    def gen_restore_registers(self, registers):  # pragma: no cover
        """ Generate a code sequence to restore the specified registers. """
        raise NotImplementedError('Implement this')

    def gen_fill_arguments(self, arg_types, args):  # pragma: no cover
        """ Generate instructions that fill the arguments.

        Arguments:
            arg_types: an iterable of ir-types of each argument
            args: an iterable of virtual registers where the arguments
                  must be loaded from.
        """
        arg_locs = self.determine_arg_locations(arg_types)

        for arg_loc, arg in zip(arg_locs, args):
            if isinstance(arg_loc, Register):
                yield self.move(arg_loc, arg)
            else:  # pragma: no cover
                raise NotImplementedError('Parameters in memory not impl')

        arg_regs = set(l for l in arg_locs if isinstance(l, Register))
        yield RegisterUseDef(uses=arg_regs)

    def gen_extract_arguments(self, arg_types, args):
        """ Generate code to extract arguments from the proper locations

        The default implementation tries to use registers and move
        instructions.

        Arguments:
            arg_types: an iterable of ir-types of the arguments
            args: an iterable of virtual registers in which the arguments
                  must be placed.
        """
        arg_locs = self.determine_arg_locations(arg_types)

        arg_regs = set(l for l in arg_locs if isinstance(l, Register))
        yield RegisterUseDef(defs=arg_regs)

        for arg_loc, arg in zip(arg_locs, args):
            if isinstance(arg_loc, Register):
                yield self.move(arg, arg_loc)
            else:  # pragma: no cover
                raise NotImplementedError('Parameters in memory not impl')

    def gen_fill_retval(self, retval_type, res_var):
        """ Generate a instructions to fill the return value.

        Override this function when needed.
        The basic implementation simply moves the result.
        """
        rv_loc = self.determine_rv_location(retval_type)
        assert isinstance(rv_loc, Register)
        yield self.move(rv_loc, res_var)
        yield RegisterUseDef(uses=(rv_loc,))

    def gen_extract_retval(self, retval_type, vreg):  # pragma: no cover
        """ Generate instructions to extract the return value.

        Arguments:
            retval_type: The ir-type of the return value
            vreg: The virtual register to move the return value into.
        """
        retval_loc = self.determine_rv_location(retval_type)
        assert isinstance(retval_loc, Register)
        yield RegisterUseDef(defs=(retval_loc,))
        yield self.move(vreg, retval_loc)

    def gen_stack_cleanup(self, arg_types):  # pragma: no cover
        """ This one is called after a function call to restore the stack.

        Override this function to fix the stack after a function call
        in which parameters were put on the stack.

        The default implementation does nothing.
        """
        return []

    @abc.abstractmethod
    def determine_arg_locations(self, arg_types):  # pragma: no cover
        """ Determine argument location for a given function """
        raise NotImplementedError('Implement this')

    @abc.abstractmethod
    def determine_rv_location(self, ret_type):  # pragma: no cover
        """ Determine the location of a return value of a function given the
        type of return value """
        raise NotImplementedError('Implement this')

    def get_reloc(self, name):
        """ Retrieve a relocation identified by a name """
        return self.isa.relocation_map[name]

    def get_runtime(self):  # pragma: no cover
        raise NotImplementedError('Implement this')

    @lru_cache(maxsize=30)
    def get_compiler_rt_lib(self):
        """ Gets the runtime for the compiler. Returns an object with the
        compiler runtime for this architecture """
        return self.get_runtime()

    runtime = property(get_compiler_rt_lib)
