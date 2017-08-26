from ..generic_instructions import SectionInstruction
from ..asm_printer import AsmPrinter


class RiscvAsmPrinter(AsmPrinter):
    """ Riscv specific assembly printer """
    def print_instruction(self, instruction):
        if isinstance(instruction, SectionInstruction):
            return '.section {}'.format(instruction.name)
        else:
            return str(instruction)
