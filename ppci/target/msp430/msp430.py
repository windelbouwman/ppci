import struct
import types
from ..basetarget import Register, Instruction, Target
from ppci import CompilerError
from .registers import r10, r11, r12, r13, r14, r15
from .instructions import Reti, Mov, Add, isa
from ...assembler import BaseAssembler


# Create the target class (singleton):

class Msp430Assembler(BaseAssembler):
    def __init__(self, target):
        super().__init__(target)

        # Registers:
        self.add_keyword('r10')
        self.add_keyword('r11')
        self.add_keyword('r12')
        self.add_keyword('r13')
        self.add_keyword('r14')
        self.add_keyword('r15')
        self.add_rule('reg', ['r10'], lambda rhs: r10)
        self.add_rule('reg', ['r11'], lambda rhs: r11)
        self.add_rule('reg', ['r12'], lambda rhs: r12)
        self.add_rule('reg', ['r13'], lambda rhs: r13)
        self.add_rule('reg', ['r14'], lambda rhs: r14)
        self.add_rule('reg', ['r15'], lambda rhs: r15)

        # Instructions rules:
        self.add_keyword('mov')
        self.add_instruction(['mov', 'reg', ',', 'reg'],
            lambda rhs: Mov(rhs[1], rhs[3]))
        self.add_instruction(['mov', 'imm16', ',', 'reg'],
            lambda rhs: Mov(rhs[1], rhs[3]))

        self.add_keyword('add')
        self.add_instruction(['add', 'reg', ',', 'reg'],
            lambda rhs: Add(rhs[1], rhs[3]))

        self.add_keyword('reti')
        self.gen_asm_parser(isa)


class Msp430Target(Target):
    def __init__(self):
        super().__init__('msp430')

        self.assembler = Msp430Assembler(self)

        self.registers.append(r10)
        self.registers.append(r11)
        self.registers.append(r12)
        self.registers.append(r13)
        self.registers.append(r14)
        self.registers.append(r15)

