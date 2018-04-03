""" Machine architecture description module """

import abc
import logging
from functools import lru_cache
from .stack import Frame, FramePointerLocation
from .asm_printer import AsmPrinter
from .. import ir


# Idea: create several types of architectures.
# One for real machines, one for virtual machines
class MachineArchitecture(metaclass=abc.ABCMeta):
    logger = logging.getLogger('arch')
    name = None
    desc = None
    option_names = ()

    def __init__(self):
        self.info = None
        self.fp_location = FramePointerLocation.TOP

    def new_frame(self, frame_name, function):
        """ Create a new frame with name frame_name for an ir-function """
        frame = Frame(frame_name, fp_location=self.fp_location)
        return frame

    def get_reg_class(self, bitsize=None, ty=None):
        """ Look for a register class """
        if bitsize:
            ty = {8: ir.i8, 16: ir.i16, 32: ir.i32, 64: ir.i64}[bitsize]
        if ty:
            return self.info.value_classes[ty]
        raise NotImplementedError()  # pragma: no cover


class VirtualMachineArchitecture(MachineArchitecture):
    """ Virtual machine architecture. """
    pass


class Architecture(MachineArchitecture):
    """ Base class for all targets """

    def __init__(self, options=None):
        """ Create a new machine instance.

        Arguments:
            options: a tuple with which options to enable.
        """
        super().__init__()
        self.logger.debug('Creating %s arch', self.name)
        self.option_settings = {o: False for o in self.option_names}
        if options:
            assert isinstance(options, tuple)
            for option_name in options:
                assert option_name in self.option_names
                self.option_settings[option_name] = True
        self.asm_printer = AsmPrinter()

    def has_option(self, name):
        """ Check for an option setting selected """
        return self.option_settings[name]

    def __repr__(self):
        opstring = ''
        for n in self.option_names:
            if self.option_settings[n]:
                opstring += ':' + n
        return '{}{}-arch'.format(self.name, opstring)

    def make_id_str(self):
        """ Return a string uniquely identifying this machine """
        options = [n for n, v in self.option_settings.items() if v]
        return ':'.join([self.name] + options)

    def get_size(self, typ):
        """ Get type of ir type """
        return self.info.get_size(typ)

    def move(self, dst, src):  # pragma: no cover
        """ Generate a move from src to dst """
        raise NotImplementedError('Implement this')

    @abc.abstractmethod
    def gen_prologue(self, frame):  # pragma: no cover
        """ Generate instructions for the epilogue of a frame.

        Arguments:
            frame: the function frame for which to create a prologue
        """
        raise NotImplementedError('Implement this!')

    @abc.abstractmethod
    def gen_epilogue(self, frame):  # pragma: no cover
        """ Generate instructions for the epilogue of a frame.

        Arguments:
            frame: the function frame for which to create a prologue
        """
        raise NotImplementedError('Implement this!')

    @abc.abstractmethod
    def gen_call(self, frame, label, args, rv):  # pragma: no cover
        """ Generate instructions for a function call. """
        raise NotImplementedError('Implement this!')

    @abc.abstractmethod
    def gen_function_enter(self, args):  # pragma: no cover
        """ Generate code to extract arguments from the proper locations

        The default implementation tries to use registers and move
        instructions.

        Arguments:
            args: an iterable of virtual registers in which the arguments
                  must be placed.
        """
        raise NotImplementedError('Implement me!')

    @abc.abstractmethod
    def gen_function_exit(self, rv):  # pragma: no cover
        raise NotImplementedError('Implement me!')

    def between_blocks(self, frame):
        """ Generate any instructions here if needed between two blocks """
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

    def get_runtime(self):
        """ Create an object with an optional runtime. """
        import io
        from ..api import asm
        asm_src = ''
        return asm(io.StringIO(asm_src), self)

    @lru_cache(maxsize=30)
    def get_compiler_rt_lib(self):
        """ Gets the runtime for the compiler. Returns an object with the
        compiler runtime for this architecture """
        return self.get_runtime()

    runtime = property(get_compiler_rt_lib)
