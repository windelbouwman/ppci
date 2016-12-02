""" 6502 instructions """

from ..isa import Isa
from ..encoding import Instruction, Syntax, Operand
from ..token import Token, bit_range


isa = Isa()


class OpcodeToken(Token):
    size = 8
    opcode = bit_range(0, 8)


class ByteToken(Token):
    size = 8
    byte = bit_range(0, 8)


class Mcs6500Instruction(Instruction):
    isa = isa


class Immediate:
    imm = Operand('imm', int)
    syntax = Syntax(['#', imm])


class Absolute:
    imm = Operand('imm', int)
    syntax = Syntax([imm])


class Adc(Mcs6500Instruction):
    tokens = [OpcodeToken, ByteToken]
    imm = Operand('imm', int)
    syntax = Syntax(['adc', ' ', '#', imm])
    patterns = {'opcode': 0x69, 'byte': imm}


class And:
    """ And """
    pass


class Asl:
    pass


class Brk(Mcs6500Instruction):
    """ Force break """
    tokens = [OpcodeToken]
    syntax = Syntax(['brk'])
    patterns = {'opcode': 0}


class Clc(Mcs6500Instruction):
    """ Clear carry flag """
    tokens = [OpcodeToken]
    syntax = Syntax(['clc'])
    patterns = {'opcode': 0x18}


class Cld(Mcs6500Instruction):
    """ Clear decimal mode """
    tokens = [OpcodeToken]
    syntax = Syntax(['cld'])
    patterns = {'opcode': 0xd8}


class Cli(Mcs6500Instruction):
    """ Clear interrupt disable flag """
    tokens = [OpcodeToken]
    syntax = Syntax(['cli'])
    patterns = {'opcode': 0x58}


class Clv(Mcs6500Instruction):
    """ Clear overflow flag """
    tokens = [OpcodeToken]
    syntax = Syntax(['clv'])
    patterns = {'opcode': 0xb8}


class Dex(Mcs6500Instruction):
    """ Decrement index X by 1 """
    tokens = [OpcodeToken]
    syntax = Syntax(['dex'])
    patterns = {'opcode': 0xca}


class Dey(Mcs6500Instruction):
    """ Decrement index Y by 1 """
    tokens = [OpcodeToken]
    syntax = Syntax(['dey'])
    patterns = {'opcode': 0x88}


class Inx(Mcs6500Instruction):
    """ Increment index X by 1 """
    tokens = [OpcodeToken]
    syntax = Syntax(['inx'])
    patterns = {'opcode': 0xe8}


class Iny(Mcs6500Instruction):
    """ Increment index Y by 1 """
    tokens = [OpcodeToken]
    syntax = Syntax(['iny'])
    patterns = {'opcode': 0xc8}


class Nop(Mcs6500Instruction):
    """ No operation """
    tokens = [OpcodeToken]
    syntax = Syntax(['nop'])
    patterns = {'opcode': 0xea}


class Pha(Mcs6500Instruction):
    """ Push accumulator on stack """
    tokens = [OpcodeToken]
    syntax = Syntax(['pha'])
    patterns = {'opcode': 0x48}


class Php(Mcs6500Instruction):
    """ Push processor status on stack """
    tokens = [OpcodeToken]
    syntax = Syntax(['php'])
    patterns = {'opcode': 0x08}


class Pla(Mcs6500Instruction):
    """ Pull accumulator from stack """
    tokens = [OpcodeToken]
    syntax = Syntax(['pla'])
    patterns = {'opcode': 0x68}


class Plp(Mcs6500Instruction):
    """ Pull processor status from stack """
    tokens = [OpcodeToken]
    syntax = Syntax(['plp'])
    patterns = {'opcode': 0x28}


class Rti(Mcs6500Instruction):
    """ Return from interrupt """
    tokens = [OpcodeToken]
    syntax = Syntax(['rti'])
    patterns = {'opcode': 0x40}


class Rts(Mcs6500Instruction):
    """ Return from subroutine """
    tokens = [OpcodeToken]
    syntax = Syntax(['rts'])
    patterns = {'opcode': 0x60}


class Sec(Mcs6500Instruction):
    """ Set carry flag """
    tokens = [OpcodeToken]
    syntax = Syntax(['sec'])
    patterns = {'opcode': 0x38}


class Sed(Mcs6500Instruction):
    """ Set decimal flag """
    tokens = [OpcodeToken]
    syntax = Syntax(['sed'])
    patterns = {'opcode': 0xf8}


class Sei(Mcs6500Instruction):
    """ Set interrupt disable status """
    tokens = [OpcodeToken]
    syntax = Syntax(['sei'])
    patterns = {'opcode': 0x78}


class Tax(Mcs6500Instruction):
    """ Transfer accumulator to index X """
    tokens = [OpcodeToken]
    syntax = Syntax(['tax'])
    patterns = {'opcode': 0xaa}


class Tay(Mcs6500Instruction):
    """ Transfer accumulator to index Y """
    tokens = [OpcodeToken]
    syntax = Syntax(['tay'])
    patterns = {'opcode': 0xa8}


class Tsx(Mcs6500Instruction):
    """ Transfer stack pointer to index X """
    tokens = [OpcodeToken]
    syntax = Syntax(['tsx'])
    patterns = {'opcode': 0xba}


class Txa(Mcs6500Instruction):
    """ Transfer index X to accumulator """
    tokens = [OpcodeToken]
    syntax = Syntax(['txa'])
    patterns = {'opcode': 0x8a}


class Txs(Mcs6500Instruction):
    """ Transfer index X to stack register """
    tokens = [OpcodeToken]
    syntax = Syntax(['txs'])
    patterns = {'opcode': 0x9a}


class Tya(Mcs6500Instruction):
    """ Transfer index Y to accumulator """
    tokens = [OpcodeToken]
    syntax = Syntax(['tya'])
    patterns = {'opcode': 0x98}
