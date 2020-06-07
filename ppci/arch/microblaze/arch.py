""" The microblaze architecture """

from ... import ir
from ..arch import Architecture
from ..arch_info import ArchInfo, TypeInfo, Endianness
from ..generic_instructions import Label, RegisterUseDef, Alignment
from ..data_instructions import Db
from ..stack import StackLocation, FramePointerLocation
from ...binutils.assembler import BaseAssembler
from . import instructions
from . import registers


class MicroBlazeArch(Architecture):
    """ Microblaze architecture """

    name = "microblaze"

    def __init__(self, options=None):
        super().__init__(options=options)
        self.info = ArchInfo(
            type_infos={
                ir.i8: TypeInfo(1, 1),
                ir.u8: TypeInfo(1, 1),
                ir.i16: TypeInfo(2, 2),
                ir.u16: TypeInfo(2, 2),
                ir.i32: TypeInfo(4, 4),
                ir.u32: TypeInfo(4, 4),
                ir.f32: TypeInfo(4, 4),
                ir.f64: TypeInfo(8, 8),
                "int": ir.i32,
                "long": ir.i32,
                "ptr": ir.u32,
                ir.ptr: ir.u32,
            },
            endianness=Endianness.BIG,
            register_classes=registers.register_classes,
        )
        self.fp_location = FramePointerLocation.BOTTOM
        self.isa = instructions.isa
        self.assembler = BaseAssembler()
        self.assembler.gen_asm_parser(self.isa)

    def move(self, dst, src):
        if isinstance(dst, registers.MicroBlazeRegister):
            if isinstance(src, registers.MicroBlazeRegister):
                return instructions.mov(dst, src)
            else:
                raise NotImplementedError()
        else:
            raise NotImplementedError()

    def gen_prologue(self, frame):
        """ Returns prologue instruction sequence.

        """
        # Label indication function:
        yield Label(frame.name)

        # Determine stack size:
        stack_size = 4
        if frame.stacksize > 0:
            stack_size += round_up(frame.stacksize)

        # Determine callee save registers:
        saved_registers = []
        for register in self.get_callee_saved(frame):
            saved_registers.append((stack_size, register))
            stack_size += 4

        # Decrease stack pointer (R1)
        yield instructions.Addik(registers.R1, registers.R1, -stack_size)

        # Store return link:
        yield instructions.Swi(registers.R15, registers.R1, 0)

        # Save callee save registers:
        for offset, register in saved_registers:
            yield instructions.Swi(register, registers.R1, offset)

        # Setup frame pointer (R19):
        yield instructions.Addk(registers.R19, registers.R1, registers.R0)

    def gen_epilogue(self, frame):
        """ Return epilogue sequence for a frame.

        """
        # Determine stack size:
        stack_size = 4  # Start with 4?
        if frame.stacksize > 0:
            stack_size += round_up(frame.stacksize)

        # Determine callee save registers:
        saved_registers = []
        for register in self.get_callee_saved(frame):
            saved_registers.append((stack_size, register))
            stack_size += 4

        # Retrieve return link:
        yield instructions.Lwi(registers.R15, registers.R1, 0)

        # Restore callee saved registers:
        for offset, register in saved_registers:
            yield instructions.Lwi(register, registers.R1, offset)

        # Re-adjust stack pointer:
        yield instructions.Addik(registers.R1, registers.R1, stack_size)

        # Return:
        yield instructions.Rtsd(registers.R15, 8)
        yield instructions.nop()  # Fill delay slot.

        # Add final literal pool:
        for instruction in self.gen_litpool(frame):
            yield instruction
        yield Alignment(4)  # Align at 4 bytes

    def get_callee_saved(self, frame):
        saved_registers = []
        for register in registers.callee_saved:
            if register in frame.used_regs:
                saved_registers.append(register)
        return saved_registers

    def gen_litpool(self, frame):
        """ Generate instructions for literals """
        if frame.constants:
            # Align at 4 bytes
            yield Alignment(4)

            # Add constant literals:
            for label, value in frame.constants:
                yield Label(label)
                if isinstance(value, bytes):
                    for byte in value:
                        yield Db(byte)
                    yield Alignment(4)  # Align at 4 bytes
                else:  # pragma: no cover
                    raise NotImplementedError(
                        "Constant of type {}".format(value)
                    )

    def gen_function_enter(self, args):
        arg_types = [a[0] for a in args]
        arg_locs = self.determine_arg_locations(arg_types)

        arg_regs = set(
            l for l in arg_locs if isinstance(l, registers.MicroBlazeRegister)
        )
        yield RegisterUseDef(defs=arg_regs)

        for arg_loc, arg2 in zip(arg_locs, args):
            arg = arg2[1]
            if isinstance(arg_loc, registers.MicroBlazeRegister):
                yield self.move(arg, arg_loc)
            # elif isinstance(arg_loc, StackLocation):
            #     pass
            else:  # pragma: no cover
                raise NotImplementedError("Parameters in memory not impl")

    def gen_function_exit(self, rv):
        live_out = set()
        if rv:
            retval_loc = self.determine_rv_location(rv[0])
            yield self.move(retval_loc, rv[1])
            live_out.add(retval_loc)
        yield RegisterUseDef(uses=live_out)

    def gen_call(self, frame, label, args, rv):
        """ Generate proper calling sequence """
        # Copy arguments to proper locations:
        arg_types = [a[0] for a in args]
        arg_locs = self.determine_arg_locations(arg_types)
        arg_regs = []
        for arg_loc, arg2 in zip(arg_locs, args):
            arg = arg2[1]
            if isinstance(arg_loc, registers.MicroBlazeRegister):
                arg_regs.append(arg_loc)
                yield self.move(arg_loc, arg)
            else:
                raise NotImplementedError()
        yield RegisterUseDef(uses=arg_regs)

        # Emit call:
        if isinstance(label, registers.MicroBlazeRegister):
            yield instructions.Brald(
                registers.R15, label, clobbers=registers.caller_saved
            )
        else:
            yield instructions.Brlid_label(
                registers.R15, label, clobbers=registers.caller_saved
            )
        yield instructions.nop()  # Fill delay slot with nop:

        # Copy return value:
        if rv:
            retval_loc = self.determine_rv_location(rv[0])
            yield RegisterUseDef(defs=(retval_loc,))
            yield self.move(rv[1], retval_loc)

    def determine_arg_locations(self, arg_types):
        """ Use registers R5-R10 to pass arguments """
        locations = []
        regs = [
            registers.R5,
            registers.R6,
            registers.R7,
            registers.R8,
            registers.R9,
            registers.R10,
        ]
        offset = 0
        for arg_type in arg_types:
            if arg_type.is_blob:
                location = StackLocation(offset, arg_type.size)
                offset += arg_type.size
            else:
                if regs:
                    location = regs.pop(0)
                else:
                    arg_size = self.info.get_size(arg_type)
                    location = StackLocation(offset, arg_size)
                    offset += arg_size
            locations.append(location)
        return locations

    def determine_rv_location(self, ret_type):
        """ Return values in R3-R4 """
        return registers.R3

    def get_runtime(self):
        """ Compiles the runtime support for microblaze.

        It takes some c3 code.
        """
        # Circular import, but this is possible!
        from ...api import c3c
        from ..runtime import get_runtime_files

        c3_sources = get_runtime_files(["divsi3", "mulsi3"])
        obj = c3c(c3_sources, [], self)
        return obj


def round_up(s):
    return s + (4 - s % 4)
