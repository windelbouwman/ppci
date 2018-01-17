""" Open risc 1K architecture """

from ... import ir
from ...binutils.assembler import BaseAssembler
from ..arch import Architecture
from ..arch_info import ArchInfo, TypeInfo, Endianness
from ..generic_instructions import Label, Alignment, SectionInstruction
from ..generic_instructions import RegisterUseDef
from ..data_instructions import data_isa, Db
from .isa import orbis32
from . import instructions, registers


class Or1kArch(Architecture):
    """ Open risc architecture.

    ABI:
    r0 -> zero
    r1 -> stack pointer
    r2 -> frame pointer
    r3 -> parameter 0
    r4 -> parameter 1
    r5 -> parameter 2
    r6 -> parameter 3
    r7 -> parameter 4
    r8 -> parameter 6
    r9 -> link address (return address for functions)
    r11 -> return value

    """
    name = 'or1k'

    def __init__(self, options=None):
        super().__init__(options=options)
        # TODO: extend with architecture options like vector and 64 bit
        self.isa = orbis32 + data_isa
        self.assembler = BaseAssembler()
        self.assembler.gen_asm_parser(self.isa)

        self.info = ArchInfo(
            type_infos={
                ir.i8: TypeInfo(1, 1), ir.u8: TypeInfo(1, 1),
                ir.i16: TypeInfo(2, 2), ir.u16: TypeInfo(2, 2),
                ir.i32: TypeInfo(4, 4), ir.u32: TypeInfo(4, 4),
                'int': ir.i32, 'ptr': ir.u32,
            },
            endianness=Endianness.BIG,
            register_classes=registers.register_classes)

        self.gdb_registers = registers.gdb_registers
        self.gdb_pc = registers.PC

    def determine_arg_locations(self, arg_types):
        """ Given a set of argument types, determine location for argument """
        l = []
        regs = [
            registers.r3, registers.r4, registers.r5, registers.r6,
            registers.r7, registers.r8]
        for a in arg_types:
            r = regs.pop(0)
            l.append(r)
        return l

    def determine_rv_location(self, ret_type):
        return registers.r11

    def gen_prologue(self, frame):
        """ Generate the prologue instruction sequence """
        # Label indication function:
        yield Label(frame.name)

        # Save frame pointer:
        yield instructions.Sw(-8, registers.r1, registers.r2)

        # setup frame pointer:
        yield instructions.Addi(
            registers.r2, registers.r1, instructions.Immediate(0))

        # Save link register:
        yield instructions.Sw(-4, registers.r2, registers.r9)

        # Save callee save registers:
        saved_registers_space = 0
        for register in registers.callee_save:
            if register in frame.used_regs:
                saved_registers_space += 4
                offset = -8 - frame.stacksize - saved_registers_space
                yield instructions.Sw(offset, registers.r2, register)

        assert saved_registers_space <= len(frame.used_regs) * 4

        # Adjust stack
        stack_size = 8 + frame.stacksize + len(frame.used_regs) * 4
        yield instructions.Addi(
            registers.r1, registers.r1, instructions.Immediate(-stack_size))

    def gen_epilogue(self, frame):
        """ Return epilogue sequence for a frame. """
        # Restore stack pointer:
        yield instructions.Ori(
            registers.r1, registers.r2, instructions.Immediate(0))

        # Restore callee saved registers:
        saved_registers_space = 0
        for register in registers.callee_save:
            if register in frame.used_regs:
                saved_registers_space += 4
                offset = -8 - frame.stacksize - saved_registers_space
                yield instructions.Lwz(register, offset, registers.r1)

        # Restore frame pointer:
        yield instructions.Lwz(registers.r2, -8, registers.r1)

        # Restore link register:
        yield instructions.Lwz(registers.r9, -4, registers.r1)

        # Return:
        yield instructions.Jr(registers.r9)

        # Fill delay slot:
        yield instructions.Nop(0)

        # Add final literal pool:
        for instruction in self.litpool(frame):
            yield instruction
        yield Alignment(4)   # Align at 4 bytes

    def gen_call(self, frame, label, args, rv):
        arg_types = [a[0] for a in args]
        arg_locs = self.determine_arg_locations(arg_types)

        arg_regs = []
        for arg_loc, arg2 in zip(arg_locs, args):
            arg = arg2[1]
            if isinstance(arg_loc, registers.Or1kRegister):
                arg_regs.append(arg_loc)
                yield self.move(arg_loc, arg)
            else:  # pragma: no cover
                raise NotImplementedError('Parameters in memory not impl')

        yield RegisterUseDef(uses=arg_regs)

        if isinstance(label, registers.Or1kRegister):
            yield instructions.Jalr(label, clobbers=registers.caller_save)
        else:
            yield instructions.Jal(label, clobbers=registers.caller_save)
        # Fill delay slot:
        yield instructions.Nop(0)

        if rv:
            retval_loc = self.determine_rv_location(rv[0])
            yield RegisterUseDef(defs=(retval_loc,))
            yield self.move(rv[1], retval_loc)

    def gen_function_enter(self, args):
        arg_types = [a[0] for a in args]
        arg_locs = self.determine_arg_locations(arg_types)

        arg_regs = set(l for l in arg_locs if isinstance(
            l, registers.Or1kRegister))
        yield RegisterUseDef(defs=arg_regs)

        for arg_loc, arg2 in zip(arg_locs, args):
            arg = arg2[1]
            if isinstance(arg_loc, registers.Or1kRegister):
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

    def litpool(self, frame):
        """ Generate instructions for literals """
        if frame.constants:
            # Align at 4 bytes
            yield SectionInstruction('rodata')
            yield Alignment(4)

            # Add constant literals:
            for label, value in frame.constants:
                yield Label(label)
                if isinstance(value, bytes):
                    for byte in value:
                        yield Db(byte)
                    yield Alignment(4)   # Align at 4 bytes
                else:  # pragma: no cover
                    raise NotImplementedError(
                        'Constant of type {}'.format(value))

            yield SectionInstruction('code')

    def move(self, dst, src):
        """ Generate a move from src to dst """
        return instructions.mov(dst, src)
