
from ...binutils.assembler import BaseAssembler
from ..arch import Architecture
from ..generic_instructions import Label, Alignment, SectionInstruction
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
        super().__init__(
            options=options, register_classes=registers.register_classes)
        # TODO: extend with architecture options like vector and 64 bit
        self.isa = orbis32 + data_isa
        self.assembler = BaseAssembler()
        self.assembler.gen_asm_parser(self.isa)
        self.byte_sizes['int'] = 4
        self.byte_sizes['ptr'] = 4
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

    def gen_save_registers(self, frame, regs):
        """ Save caller saved registers """
        # Save registers at end of frame
        offset = -8 - frame.stacksize - len(frame.used_regs) * 4
        for register in regs:
            if register in registers.caller_save:
                yield instructions.Sw(offset, registers.r2, register)
                offset += 4

    def gen_restore_registers(self, frame, regs):
        """ Restore caller saved registers """
        offset = -8 - frame.stacksize - len(frame.used_regs) * 4
        for register in regs:
            if register in registers.caller_save:
                yield instructions.Lwz(register, offset, registers.r2)
                offset += 4

    def gen_call(self, frame, vcall):
        yield instructions.Jal(vcall.function_name)

        # Fill delay slot:
        yield instructions.Nop(0)

    def move(self, dst, src):
        """ Generate a move from src to dst """
        return instructions.mov(dst, src)
