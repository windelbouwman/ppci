
from ...binutils.assembler import BaseAssembler
from ..arch import Architecture
from ..generic_instructions import Label
from ..data_instructions import data_isa
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
        yield instructions.Sw(-4, registers.r1, registers.r2)  # Save FP
        yield instructions.Addi(registers.r2, registers.r1, 0)  # setup FP

        # Adjust stack
        yield instructions.Addi(registers.r1, registers.r1, -20)

    def gen_epilogue(self, frame):
        """ Return epilogue sequence for a frame. """
        # Restore stack pointer:
        yield instructions.Ori(registers.r1, registers.r2, 0)
        yield instructions.Jr(registers.r9)

    def gen_save_registers(self, registers):
        if False:
            yield 1

    def gen_restore_registers(self, registers):
        if False:
            yield 1

    def gen_call(self, frame, vcall):
        yield instructions.Jal(vcall.function_name)

    def move(self, dst, src):
        """ Generate a move from src to dst """
        return instructions.mov(dst, src)
