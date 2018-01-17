""" Define MIPS architecture """

from ... import ir
from ...binutils.assembler import BaseAssembler
from ..arch import Architecture
from ..arch_info import ArchInfo, TypeInfo
from ..generic_instructions import Label, Alignment, RegisterUseDef
from ..data_instructions import data_isa
from ..runtime import get_runtime_files
from . import instructions, registers


class MipsArch(Architecture):
    """ Mips architecture """
    name = 'mips'

    def __init__(self, options=None):
        super().__init__(options=options)
        self.info = ArchInfo(
            type_infos={
                ir.i8: TypeInfo(1, 1), ir.u8: TypeInfo(1, 1),
                ir.i16: TypeInfo(2, 2), ir.u16: TypeInfo(2, 2),
                ir.i32: TypeInfo(4, 4), ir.u32: TypeInfo(4, 4),
                ir.i64: TypeInfo(8, 4), ir.u64: TypeInfo(8, 4),
                'int': ir.i32, 'ptr': ir.u32
            }, register_classes=registers.register_classes)

        self.isa = instructions.isa + data_isa
        self.assembler = BaseAssembler()
        self.assembler.gen_asm_parser(self.isa)

    def get_runtime(self):
        """ Retrieve the runtime for this target """
        from ...api import c3c
        c3_sources = get_runtime_files([
            'divsi3',
            'mulsi3',
        ])
        obj = c3c(c3_sources, [], self)
        return obj

    def determine_arg_locations(self, arg_types):
        arg_locs = []
        int_regs = [
            registers.a0, registers.a1, registers.a2, registers.a3
        ]
        for arg_type in arg_types:
            # Determine register:
            if arg_type in [
                    ir.i8, ir.u8, ir.i16, ir.u16, ir.i32, ir.u32, ir.ptr]:
                reg = int_regs.pop(0)
            else:  # pragma: no cover
                raise NotImplementedError(str(arg_type))
            arg_locs.append(reg)
        return arg_locs

    def determine_rv_location(self, ret_type):
        """ return value in v0-v1 """
        if ret_type in [ir.i8, ir.u8, ir.i16, ir.u16, ir.i32, ir.u32, ir.ptr]:
            rv = registers.v0
        else:  # pragma: no cover
            raise NotImplementedError(str(ret_type))
        return rv

    def gen_prologue(self, frame):
        """ Returns prologue instruction sequence """

        # Label indication function:
        yield Alignment(4)
        yield Label(frame.name)

        yield instructions.Addi(registers.sp, registers.sp, -8)

        # First save return address (which is in a0):
        yield instructions.Sw(registers.lr, 4, registers.sp)

        # Save frame pointer:
        yield instructions.Sw(registers.fp, 0, registers.sp)

        # Reserve stack space
        if frame.stacksize > 0:
            # Prepare frame pointer:
            yield self.move(registers.fp, registers.sp)

            size = -round_up(frame.stacksize)
            yield instructions.Addi(registers.sp, registers.sp, size)

        # Callee save registers:
        for reg in registers.callee_save:
            if frame.is_used(reg):
                yield instructions.Push(reg)

    def gen_epilogue(self, frame):
        """ Return epilogue sequence """
        # Pop save registers back:
        for reg in reversed(registers.callee_save):
            if frame.is_used(reg):
                yield instructions.Pop(reg)

        if frame.stacksize > 0:
            size = round_up(frame.stacksize)
            yield instructions.Addi(registers.sp, registers.sp, size)

        yield instructions.Lw(registers.fp, 0, registers.sp)

        # Restore return address:
        yield instructions.Lw(registers.lr, 4, registers.sp)
        yield instructions.Addi(registers.sp, registers.sp, 8)

        # Return
        yield instructions.Jr(registers.lr)

    def gen_call(self, frame, label, args, rv):
        arg_types = [a[0] for a in args]
        arg_locs = self.determine_arg_locations(arg_types)

        arg_regs = []
        for arg_loc, arg2 in zip(arg_locs, args):
            arg = arg2[1]
            if isinstance(arg_loc, registers.MipsRegister):
                arg_regs.append(arg_loc)
                yield self.move(arg_loc, arg)
            else:  # pragma: no cover
                raise NotImplementedError('Parameters in memory not impl')

        yield RegisterUseDef(uses=arg_regs)

        if isinstance(label, registers.MipsRegister):
            yield instructions.Jalr(label, clobbers=registers.caller_save)
        else:
            yield instructions.Jal(label, clobbers=registers.caller_save)
        yield instructions.Nop()  # Delay slot = important

        if rv:
            retval_loc = self.determine_rv_location(rv[0])
            yield RegisterUseDef(defs=(retval_loc,))
            yield self.move(rv[1], retval_loc)

    def gen_function_enter(self, args):
        arg_types = [a[0] for a in args]
        arg_locs = self.determine_arg_locations(arg_types)

        arg_regs = set(l for l in arg_locs if isinstance(
            l, registers.MipsRegister))
        yield RegisterUseDef(defs=arg_regs)

        for arg_loc, arg2 in zip(arg_locs, args):
            arg = arg2[1]
            if isinstance(arg_loc, registers.MipsRegister):
                yield self.move(arg, arg_loc)
            else:  # pragma: no cover
                raise NotImplementedError('Parameters in memory not impl')

    def gen_function_exit(self, rv):
        live_out = set()
        if rv:
            retval_loc = self.determine_rv_location(rv[0])
            yield self.move(retval_loc, rv[1])
            live_out.add(retval_loc)
        yield RegisterUseDef(uses=live_out)

    def move(self, dst, src):
        return instructions.mov(dst, src)


def round_up(s):
    return s + (4 - s % 4)
