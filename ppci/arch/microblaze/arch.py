""" The microblaze architecture """

from ... import ir
from ..arch import Architecture
from ..arch_info import ArchInfo, TypeInfo
from ..generic_instructions import Label, RegisterUseDef
from ..stack import StackLocation
from ...binutils.assembler import BaseAssembler
from . import instructions
from . import registers


class MicroBlazeArch(Architecture):
    """ Microblaze architecture """
    name = 'microblaze'

    def __init__(self, options=None):
        super().__init__(options=options)
        self.info = ArchInfo(
            type_infos={
                ir.i8: TypeInfo(1, 1), ir.u8: TypeInfo(1, 1),
                ir.i16: TypeInfo(2, 2), ir.u16: TypeInfo(2, 2),
                ir.i32: TypeInfo(4, 4), ir.u32: TypeInfo(4, 4),
                'int': ir.i32, 'ptr': ir.u32, ir.ptr: ir.u32,
            },
            register_classes=registers.register_classes)
        self.isa = instructions.isa
        self.assembler = BaseAssembler()
        self.assembler.gen_asm_parser(self.isa)

    def gen_prologue(self, frame):
        """ Returns prologue instruction sequence.

        """
        # Label indication function:
        yield Label(frame.name)
        # TODO
        # Decrease stack pointer (R1)

        raise NotImplementedError()

    def gen_epilogue(self, frame):
        """ Return epilogue sequence for a frame.

        """
        raise NotImplementedError()

    def gen_function_enter(self, args):
        arg_types = [a[0] for a in args]
        arg_locs = self.determine_arg_locations(arg_types)

        arg_regs = set(
            l for l in arg_locs
            if isinstance(l, registers.MicroBlazeRegister))
        yield RegisterUseDef(defs=arg_regs)

        for arg_loc, arg2 in zip(arg_locs, args):
            arg = arg2[1]
            if isinstance(arg_loc, registers.MicroBlazeRegister):
                yield self.move(arg, arg_loc)
            # elif isinstance(arg_loc, StackLocation):
            #     pass
            else:  # pragma: no cover
                raise NotImplementedError('Parameters in memory not impl')

    def gen_function_exit(self, rv):
        live_out = set()
        if rv:
            retval_loc = self.determine_rv_location(rv[0])
            yield self.move(retval_loc, rv[1])
            live_out.add(retval_loc)
        yield RegisterUseDef(uses=live_out)

    def gen_call(self, frame, label, args, rv):
        raise NotImplementedError()

    def determine_arg_locations(self, arg_types):
        """ Use registers R5-R10 to pass arguments """
        locations = []
        regs = [
            registers.R5, registers.R6, registers.R7, registers.R8,
            registers.R9, registers.R10
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
