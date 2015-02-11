"""
    Target independent code generator part. The target is provided when
    the generator is created.
"""

from .. import ir, irdag, irmach
from ..irutils import Verifier, split_block
from ..target import Target
from .registerallocator import RegisterAllocator
from ..binutils.outstream import MasterOutputStream, FunctionOutputStream
import logging


class CodeGenerator:
    """ Generic code generator.
    """
    def __init__(self, target):
        # TODO: schedule traces in better order.
        # This is optional!
        assert isinstance(target, Target), target
        self.logger = logging.getLogger('codegen')
        self.target = target
        self.dagger = irdag.Dagger()
        self.ins_sel = target.ins_sel
        self.register_allocator = RegisterAllocator()
        self.verifier = Verifier()
        self.dump_file = None

    def print(self, *args):
        if self.dump_file:
            print(*args, file=self.dump_file)

    def dump_dag(self, dags):
        self.print("Selection dag:")
        for dag in dags:
            self.print('Dag:')
            for root in dag:
                self.print("- {}".format(root))

    def dump_frame(self, frame):
        """ Dump frame to file for debug purposes """
        self.print("Frame:")
        self.print(frame)
        for ins in frame.instructions:
            self.print('$ {}'.format(ins.long_repr))

    def generate_function(self, irfunc, outs):
        """ Generate code for one function into a frame """
        self.logger.info('Generating {} code for {}'
                         .format(self.target, irfunc.name))

        self.print("========= Log for {} ==========".format(irfunc))
        self.print("Target: {}".format(self.target))
        # Writer().write_function(irfunc, f)

        instruction_list = []
        outs = MasterOutputStream([
            FunctionOutputStream(instruction_list.append),
            outs])

        # Create a frame for this function:
        frame = self.target.FrameClass(ir.label_name(irfunc))

        # Split too large basic blocks in smaller chunks (for literal pools):
        # TODO: fix arbitrary number of 500. This works for arm and thumb..
        for block in irfunc:
            max_block_len = 200
            while len(block) > max_block_len:
                self.logger.debug('{} too large, splitting up'.format(block))
                _, block = split_block(block, pos=max_block_len)

        # Create selection dag (directed acyclic graph):
        dag = self.dagger.make_dag(irfunc, frame)
        self.logger.debug('DAG created')
        self.dump_dag(dag)

        # Select instructions:
        self.ins_sel.munch_dag(dag, frame)
        self.logger.debug('Selected instructions')

        # Define arguments live at first instruction:
        ins0 = frame.instructions[0]
        in0def = []
        for idx, _ in enumerate(irfunc.arguments):
            arg_loc = frame.arg_loc(idx)
            if isinstance(arg_loc, irmach.VirtualRegister):
                in0def.append(arg_loc)
        ins0.dst = tuple(in0def)

        # Dump current state to file:
        self.print('Selected instructions')
        self.dump_frame(frame)

        # Do register allocation:
        self.register_allocator.allocFrame(frame)
        self.logger.debug('Registers allocated, now adding final glue')
        # TODO: Peep-hole here?

        for ins in frame.instructions:
            if frame.cfg.has_node(ins):
                nde = frame.cfg.get_node(ins)
                self.print('ins: {} {}'.format(ins, nde.longrepr))
        self.dump_frame(frame)

        # Add label and return and stack adjustment:
        frame.EntryExitGlue3()

        # Materialize the register allocated instructions into a stream of
        # real instructions.
        self.target.lower_frame_to_stream(frame, outs)
        self.logger.debug('Instructions materialized')

        for ins in instruction_list:
            self.print(ins)

        self.print("===============================")

    def generate(self, ircode, outs, dump_file=None):
        """ Generate code into output stream """
        assert isinstance(ircode, ir.Module)
        self.dump_file = dump_file

        # Generate code for global variables:
        outs.select_section('data')
        for var in ircode.Variables:
            self.target.emit_global(outs, ir.label_name(var), var.amount)

        # Generate code for functions:
        # Munch program into a bunch of frames. One frame per function.
        # Each frame has a flat list of abstract instructions.
        outs.select_section('code')
        for function in ircode.Functions:
            self.generate_function(function, outs)
