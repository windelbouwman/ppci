from .. import ir
from ..irutils import Verifier
from ..target import Target
from .canon import make as canonicalize
from .registerallocator import RegisterAllocator
import logging


class CodeGenerator:
    """ Generic code generator """
    def __init__(self, target):
        # TODO: schedule traces in better order.
        # This is optional!
        assert isinstance(target, Target), target
        self.logger = logging.getLogger('codegen')
        self.target = target
        self.ins_sel = target.ins_sel
        self.ra = RegisterAllocator()
        self.verifier = Verifier()

    def generate_function(self, irfunc, outs):
        """ Generate code for one function into a frame """
        self.logger.debug('Generating code for {}'.format(irfunc.name))
        # Create a frame for this function:
        frame = self.target.FrameClass(ir.label_name(irfunc))

        # Canonicalize the intermediate language:
        canonicalize(irfunc, frame)
        self.logger.debug('after canonicalize', extra={'irfunc': irfunc})
        self.verifier.verify_function(irfunc)

        # Select instructions:
        self.ins_sel.munchFunction(irfunc, frame)
        self.logger.debug('Selected instructions', extra={'ppci_frame': frame})

        # Do register allocation:
        self.ra.allocFrame(frame)
        self.logger.debug('Registers allocated, now adding final glue')
        # TODO: Peep-hole here?

        # Add label and return and stack adjustment:
        frame.EntryExitGlue3()

        # Materialize the register allocated instructions into a stream of
        # real instructions.
        self.target.lower_frame_to_stream(frame, outs)
        self.logger.debug('Instructions materialized')
        return frame

    def generate(self, ircode, outs):
        """ Generate code into output stream """
        assert isinstance(ircode, ir.Module)

        # Generate code for global variables:
        outs.select_section('data')
        for global_variable in ircode.Variables:
            self.target.emit_global(outs, ir.label_name(global_variable))

        # Generate code for functions:
        # Munch program into a bunch of frames. One frame per function.
        # Each frame has a flat list of abstract instructions.
        # Generate code for all functions:
        outs.select_section('code')
        frames = [self.generate_function(f, outs) for f in ircode.Functions]
        return frames
