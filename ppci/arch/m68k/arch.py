""" M68000 architecture.

Calling convention:
- Arguments are pushed on stack.
- return value in d0

"""

from ... import ir
from ...binutils.assembler import BaseAssembler
from ..arch import Architecture
from ..arch_info import ArchInfo, TypeInfo, Endianness
from ..data_instructions import data_isa
from ..generic_instructions import Label
from ..generic_instructions import RegisterUseDef
from ..stack import StackLocation
from . import registers, instructions


class M68kArch(Architecture):
    name = "m68k"

    def __init__(self, options=None):
        super().__init__(options=options)
        self.isa = instructions.m68k_isa + data_isa
        self.assembler = BaseAssembler()
        self.assembler.gen_asm_parser(self.isa)
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
            },
            endianness=Endianness.BIG,
            register_classes=registers.register_classes,
        )

    def gen_prologue(self, frame):
        """ Generate the prologue instruction sequence """
        # Label indication function:
        yield Label(frame.name)

    def gen_epilogue(self, frame):
        """ Return epilogue sequence for a frame. """
        yield instructions.Rts()

    def determine_arg_locations(self, arg_types):
        """ Determine argument locations.
        """
        locations = []
        offset = 0
        for arg_type in arg_types:
            arg_size = self.info.get_size(arg_type)
            location = StackLocation(offset, arg_size)
            offset += arg_size
            locations.append(location)
        return locations

    def determine_rv_location(self, ret_type):
        return registers.D0

    def gen_function_enter(self, args):
        arg_types = [a[0] for a in args]
        arg_locs = self.determine_arg_locations(arg_types)

        for arg_loc, arg2 in zip(arg_locs, args):
            arg = arg2[1]
            if isinstance(arg_loc, StackLocation):
                yield self.move(arg, arg_loc)
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
        arg_types = [a[0] for a in args]
        arg_locs = self.determine_arg_locations(arg_types)

        arg_regs = []
        for arg_loc, arg2 in zip(arg_locs, args):
            arg = arg2[1]
            if isinstance(arg_loc, registers.DataRegister):
                arg_regs.append(arg_loc)
                yield self.move(arg_loc, arg)
            else:  # pragma: no cover
                raise NotImplementedError("Parameters in memory not impl")

        if isinstance(label, registers.AddressRegister):
            yield instructions.Jalr(label, clobbers=registers.caller_save)
        else:
            assert isinstance(label, str)
            yield instructions.Bsr(label, clobbers=registers.caller_save)

        if rv:
            retval_loc = self.determine_rv_location(rv[0])
            yield RegisterUseDef(defs=(retval_loc,))
            yield self.move(rv[1], retval_loc)

    def move(self, dst, src):
        """ Generate a move from src to dst """
        if isinstance(dst, registers.DataRegister):
            if isinstance(src, registers.DataRegister):
                return instructions.Movel(
                    instructions.DataRegEa(src), instructions.DataRegDstEa(dst)
                )
            elif isinstance(src, StackLocation):
                if src.size == 4:
                    # TODO: what is the stack pointer register?
                    return instructions.Movel(
                        instructions.AddressOffsetEa(src.offset, registers.A0),
                        instructions.DataRegDstEa(dst),
                    )
                else:
                    raise NotImplementedError()
            else:
                raise NotImplementedError()
        else:
            raise NotImplementedError()
