""" Machine code generator.

The architecture is provided when the generator is created.
"""

import logging
from .. import ir
from ..irutils import Verifier, split_block
from ..arch.arch import Architecture, VCall, Label, Comment
from ..arch.arch import RegisterUseDef, VirtualInstruction, DebugData
from ..arch.arch import ArtificialInstruction
from ..arch.encoding import Instruction
from ..arch.data_instructions import Ds, Db
from ..binutils.debuginfo import DebugType, DebugLocation
from ..binutils.outstream import MasterOutputStream, FunctionOutputStream
from .irdag import SelectionGraphBuilder, make_label_name
from .instructionselector import InstructionSelector1
from .instructionscheduler import InstructionScheduler
from .registerallocator import GraphColoringRegisterAllocator


class CodeGenerator:
    """ Machine code generator """
    logger = logging.getLogger('codegen')

    def __init__(self, arch, debug_db, optimize_for='size'):
        assert isinstance(arch, Architecture), arch
        self.arch = arch
        self.debug_db = debug_db
        self.verifier = Verifier()
        self.sgraph_builder = SelectionGraphBuilder(arch, debug_db)
        weights_map = {
            'size': (10, 1, 1),
            'speed': (3, 10, 1),
            'co2': (1, 2, 10),
            'awesome': (13, 13, 13),
        }
        if optimize_for in weights_map:
            selection_weights = weights_map[optimize_for]
        else:
            selection_weights = (1, 1, 1)
        self.instruction_selector = InstructionSelector1(
            arch, self.sgraph_builder, debug_db,
            weights=selection_weights)
        self.instruction_scheduler = InstructionScheduler()
        self.register_allocator = GraphColoringRegisterAllocator(
            arch, self.instruction_selector, debug_db)

    def generate(
            self, ircode: ir.Module, output_stream, reporter, debug=False):
        """ Generate machine code from ir-code into output stream """
        assert isinstance(ircode, ir.Module)

        self.logger.info(
            'Generating %s code for module %s', str(self.arch), ircode.name)

        # Generate code for global variables:
        output_stream.select_section('data')
        for var in ircode.variables:
            label_name = make_label_name(var)
            # TODO: alignment?
            label = Label(label_name)
            output_stream.emit(label)
            if var.amount > 0:
                if var.value:
                    for byte in var.value:
                        output_stream.emit(Db(byte))
                else:
                    output_stream.emit(Ds(var.amount))
            else:  # pragma: no cover
                raise NotImplementedError()
            self.debug_db.map(var, label)
            if self.debug_db.contains(label) and debug:
                dv = self.debug_db.get(label)
                dv.address = label.name
                output_stream.emit(DebugData(dv))

        # Generate code for functions:
        # Munch program into a bunch of frames. One frame per function.
        # Each frame has a flat list of abstract instructions.
        output_stream.select_section('code')
        for function in ircode.functions:
            self.generate_function(
                function, output_stream, reporter, debug=debug)

        # Output debug type data:
        if debug:
            for di in self.debug_db.infos:
                if isinstance(di, DebugType):
                    # TODO: prevent this from being emitted twice in some way?
                    output_stream.emit(DebugData(di))

    def generate_function(
            self, ir_function, output_stream, reporter, debug=False):
        """ Generate code for one function into a frame """
        self.logger.info(
            'Generating %s code for function %s',
            str(self.arch), ir_function.name)

        reporter.heading(3, 'Log for {}'.format(ir_function))
        reporter.dump_ir(ir_function)

        # Split too large basic blocks in smaller chunks (for literal pools):
        # TODO: fix arbitrary number of 500. This works for arm and thumb..
        for block in ir_function:
            max_block_len = 200
            while len(block) > max_block_len:
                self.logger.debug('%s too large, splitting up', str(block))
                _, block = split_block(block, pos=max_block_len)

        # Create a frame for this function:
        frame_name = make_label_name(ir_function)
        frame = self.arch.new_frame(frame_name, ir_function)
        self.debug_db.map(ir_function, frame)

        # Select instructions and schedule them:
        self.select_and_schedule(ir_function, frame, reporter)

        # Define arguments live at first instruction:
        self.define_arguments_live(frame)

        reporter.dump_frame(frame)

        # Do register allocation:
        self.register_allocator.alloc_frame(frame)

        # TODO: Peep-hole here?
        # frame.instructions = [i for i in frame.instructions]

        reporter.dump_frame(frame)

        # Add label and return and stack adjustment:
        instruction_list = []
        output_stream = MasterOutputStream([
            FunctionOutputStream(instruction_list.append),
            output_stream])
        self.emit_frame_to_stream(frame, output_stream, debug=debug)

        # Emit function debug info:
        if self.debug_db.contains(frame) and debug:
            func_end_label = self.debug_db.new_label()
            output_stream.emit(Label(func_end_label))
            d = self.debug_db.get(frame)
            d.begin = frame_name
            d.end = func_end_label
            dd = DebugData(d)
            output_stream.emit(dd)

        reporter.dump_instructions(instruction_list)

    def select_and_schedule(self, ir_function, frame, reporter):
        """ Perform instruction selection and scheduling """
        self.logger.debug('Selecting instructions')

        tree_method = True
        if tree_method:
            self.instruction_selector.select(ir_function, frame, reporter)
        else:  # pragma: no cover
            raise NotImplementedError('TODO')
            # Build a graph:
            # self.sgraph_builder.build(ir_function, function_info)
            # reporter.message('Selection graph')
            # reporter.dump_sgraph(sgraph)

            # Schedule instructions:
            # self.instruction_scheduler.schedule(sgraph, frame)

    def emit_frame_to_stream(self, frame, output_stream, debug=False):
        """
            Add code for the prologue and the epilogue. Add a label, the
            return instruction and the stack pointer adjustment for the frame.
            At this point we know how much stack space must be reserved for
            locals and what registers should be saved.
        """
        # Materialize the register allocated instructions into a stream of
        # real instructions.
        self.logger.debug('Emitting instructions')

        debug_data = []

        # Prefix code:
        output_stream.emit_all(self.arch.gen_prologue(frame))

        for instruction in frame.instructions:
            assert isinstance(instruction, Instruction), str(instruction)

            # If the instruction has debug location, emit it here:
            if self.debug_db.contains(instruction) and debug:
                d = self.debug_db.get(instruction)
                assert isinstance(d, DebugLocation)
                if not d.address:
                    label_name = self.debug_db.new_label()
                    d.address = label_name
                    source_line = d.loc.get_source_line()
                    output_stream.emit(Comment(source_line))
                    output_stream.emit(Label(label_name))
                    debug_data.append(DebugData(d))

            if isinstance(instruction, VirtualInstruction):
                # Process virtual instructions
                if isinstance(instruction, VCall):
                    # We now know what variables are live at this point
                    # and possibly need to be saved.
                    output_stream.emit_all(
                        self.arch.make_call(frame, instruction))
                elif isinstance(instruction, RegisterUseDef):
                    pass
                elif isinstance(instruction, ArtificialInstruction):
                    output_stream.emit(instruction)
                else:  # pragma: no cover
                    raise NotImplementedError(str(instruction))
            else:
                # Real instructions:
                assert all(r.is_colored for r in instruction.registers)
                output_stream.emit(instruction)

        # Postfix code, like register restore and stack adjust:
        output_stream.emit_all(self.arch.gen_epilogue(frame))

        # Last but not least, emit debug infos:
        for dd in debug_data:
            output_stream.emit(dd)

        # Check if we know what variables are live
        for tmp in frame.ig.temp_map:
            if self.debug_db.contains(tmp):
                self.debug_db.get(tmp)
                # print(tmp, di)
                frame.live_ranges(tmp)
                # print('live ranges:', lr)

    def define_arguments_live(self, frame):
        """ Prepend a special instruction in front of the frame """
        ins0 = RegisterUseDef()
        frame.instructions.insert(0, ins0)
        for register in frame.live_in:
            ins0.add_def(register)

        ins2 = RegisterUseDef()
        frame.instructions.append(ins2)
        for register in frame.live_out:
            ins2.add_use(register)
