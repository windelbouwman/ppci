""" Xtensa architecture """

from ... import ir
from ...binutils.assembler import BaseAssembler
from ..arch import Architecture
from ..arch_info import ArchInfo, TypeInfo
from ..generic_instructions import Label, Alignment, RegisterUseDef
from ..data_instructions import Db, Dd, Dcd2, data_isa
from ..runtime import get_runtime_files
from .registers import register_classes
from . import registers
from . import instructions


class XtensaArch(Architecture):
    """ Xtensa architecture implementation. """
    name = 'xtensa'

    def __init__(self, options=None):
        super().__init__(options=options)
        self.isa = instructions.core_isa + data_isa
        self.assembler = BaseAssembler()
        self.assembler.gen_asm_parser(self.isa)
        self.fp = registers.a15  # The frame pointer in call0 abi mode

        self.info = ArchInfo(
            type_infos={
                ir.i8: TypeInfo(1, 1), ir.u8: TypeInfo(1, 1),
                ir.i16: TypeInfo(2, 2), ir.u16: TypeInfo(2, 2),
                ir.i32: TypeInfo(4, 4), ir.u32: TypeInfo(4, 4),
                'int': ir.i32, 'ptr': ir.u32
            }, register_classes=register_classes)

        # TODO: a15 is also callee save
        self.callee_save = registers.callee_save
        self.caller_save = registers.caller_save

    def move(self, dst, src):
        """ Generate a move from src to dst """
        return instructions.Mov(dst, src, ismove=True)

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
            registers.a2, registers.a3, registers.a4, registers.a5,
            registers.a6]
        for arg_type in arg_types:
            # Determine register:
            if arg_type in [ir.i8, ir.u8, ir.i32, ir.u32, ir.ptr]:
                reg = int_regs.pop(0)
            else:  # pragma: no cover
                raise NotImplementedError(str(arg_type))
            arg_locs.append(reg)
        return arg_locs

    def determine_rv_location(self, ret_type):
        """ return value in a2 """
        # TODO: what is the frame pointer??
        if ret_type in [ir.i8, ir.u8, ir.i32, ir.u32, ir.ptr]:
            rv = registers.a2
        else:  # pragma: no cover
            raise NotImplementedError(str(ret_type))
        return rv

    def gen_prologue(self, frame):
        """ Returns prologue instruction sequence """
        # Literal pool must reside before function!
        for label, value in frame.constants:
            yield Alignment(4)
            yield Label(label)
            if isinstance(value, bytes):
                for byte in value:
                    yield Db(byte)
            elif isinstance(value, int):
                yield Dd(value)
            elif isinstance(value, str):
                yield Dcd2(value)
            else:  # pragma: no cover
                raise NotImplementedError('Constant {}'.format(value))

        # Label indication function:
        yield Alignment(4)  # Must be 32 bit aligned for call0 instruction
        yield Label(frame.name)

        # First save return address (which is in a0):
        yield instructions.Push(registers.a0)

        # Save frame pointer:
        yield instructions.Push(self.fp)

        # Reserve stack space
        if frame.stacksize > 0:
            # Prepare frame pointer:
            yield self.move(self.fp, registers.a1)

            size = -round_up(frame.stacksize)
            yield instructions.Addi(registers.a1, registers.a1, size)

        # Callee save registers:
        for reg in self.callee_save:
            if frame.is_used(reg):
                yield instructions.Push(reg)

    def gen_epilogue(self, frame):
        """ Return epilogue sequence """
        # Pop save registers back:
        for reg in reversed(self.callee_save):
            if frame.is_used(reg):
                yield instructions.Pop(reg)

        if frame.stacksize > 0:
            size = round_up(frame.stacksize)
            yield instructions.Addi(registers.a1, registers.a1, size)

        yield instructions.Pop(self.fp)

        # Restore return address:
        yield instructions.Pop(registers.a0)

        # Return
        yield instructions.Ret()

    def gen_call(self, frame, label, args, rv):
        arg_types = [a[0] for a in args]
        arg_locs = self.determine_arg_locations(arg_types)

        arg_regs = []
        for arg_loc, arg2 in zip(arg_locs, args):
            arg = arg2[1]
            if isinstance(arg_loc, registers.AddressRegister):
                arg_regs.append(arg_loc)
                yield self.move(arg_loc, arg)
            else:  # pragma: no cover
                raise NotImplementedError('Parameters in memory not impl')

        yield RegisterUseDef(uses=arg_regs)

        if isinstance(label, registers.AddressRegister):
            yield instructions.Callx0(label, clobbers=self.caller_save)
        else:
            yield instructions.Call0(label, clobbers=self.caller_save)

        if rv:
            retval_loc = self.determine_rv_location(rv[0])
            yield RegisterUseDef(defs=(retval_loc,))
            yield self.move(rv[1], retval_loc)

    def gen_function_enter(self, args):
        arg_types = [a[0] for a in args]
        arg_locs = self.determine_arg_locations(arg_types)

        arg_regs = set(l for l in arg_locs if isinstance(
            l, registers.AddressRegister))
        yield RegisterUseDef(defs=arg_regs)

        for arg_loc, arg2 in zip(arg_locs, args):
            arg = arg2[1]
            if isinstance(arg_loc, registers.AddressRegister):
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


def round_up(s):
    if s % 4:
        return s + (4 - s % 4)
    else:
        return s
