""" 6502 instructions

See for example: http://www.6502.org/tutorials/6502opcodes.html
"""


from ..isa import Isa
from ..encoding import Instruction, Syntax, Operand, Constructor
from ..token import Token, bit_range


isa = Isa()


class OpcodeToken(Token):
    size = 8
    opcode = bit_range(0, 8)


class ByteToken(Token):
    size = 8
    byte = bit_range(0, 8)


class WordToken(Token):
    size = 16
    word = bit_range(0, 16)


class Mcs6500Instruction(Instruction):
    isa = isa


class Accumulator(Constructor):
    syntax = Syntax(['a'])


class Immediate(Constructor):
    """ Immediate value operand """
    imm = Operand('imm', int)
    syntax = Syntax(['#', imm])
    tokens = [ByteToken]
    patterns = {'byte': imm}


class Absolute(Constructor):
    """ Absolute 16-bit address """
    imm = Operand('imm', int)
    syntax = Syntax([imm])
    tokens = [WordToken]
    patterns = {'word': imm}


class AbsoluteX(Constructor):
    imm = Operand('imm', int)
    syntax = Syntax([imm, ',', 'x'])
    tokens = [WordToken]
    patterns = {'word': imm}


class AbsoluteY(Constructor):
    imm = Operand('imm', int)
    syntax = Syntax([imm, ',', 'y'])
    tokens = [WordToken]
    patterns = {'word': imm}


class IndirectX(Constructor):
    imm = Operand('imm', int)
    syntax = Syntax(['(', imm, ',', 'x', ')'])
    tokens = [ByteToken]
    patterns = {'byte': imm}


class IndirectY(Constructor):
    imm = Operand('imm', int)
    syntax = Syntax(['(', imm, ')', ',', 'y'])
    tokens = [ByteToken]
    patterns = {'byte': imm}


class Adc(Mcs6500Instruction):
    """ Add with carry """
    tokens = [OpcodeToken]
    op = Operand(
        'op',
        {
            Immediate: 0x69,
            # TODO 65
            # TODO 75
            Absolute: 0x6D,
            AbsoluteX: 0x7D,
            AbsoluteY: 0x79,
            IndirectX: 0x61,
            IndirectY: 0x71
        })
    syntax = Syntax(['adc', ' ', op])
    patterns = {'opcode': op}


class And(Mcs6500Instruction):
    """ Bitwise and """
    tokens = [OpcodeToken]
    op = Operand(
        'op',
        {
            Immediate: 0x29,
            # TODO 25
            # TODO 35
            Absolute: 0x2D,
            AbsoluteX: 0x3D,
            AbsoluteY: 0x39,
            IndirectX: 0x21,
            IndirectY: 0x31
        })
    syntax = Syntax(['and', ' ', op])
    patterns = {'opcode': op}


class Asl(Mcs6500Instruction):
    """ Arithmatic shift left """
    tokens = [OpcodeToken]
    op = Operand(
        'op',
        {
            Accumulator: 0x0A,
            # TODO 06
            # TODO 16
            Absolute: 0x0E,
            AbsoluteX: 0x1E
        })
    syntax = Syntax(['asl', ' ', op])
    patterns = {'opcode': op}


class Bit(Mcs6500Instruction):
    """ Test bits """
    tokens = [OpcodeToken]
    op = Operand(
        'op',
        {
            # TODO 24
            Absolute: 0x2C,
        })
    syntax = Syntax(['bit', ' ', op])
    patterns = {'opcode': op}


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


class Sbc(Mcs6500Instruction):
    """ Substract with carry """
    tokens = [OpcodeToken]
    op = Operand(
        'op',
        {
            Immediate: 0xE9,
            # TODO E5
            # TODO F5
            Absolute: 0xED,
            AbsoluteX: 0xFD,
            AbsoluteY: 0xF9,
            IndirectX: 0xE1,
            IndirectY: 0xF1
        })
    syntax = Syntax(['sbc', ' ', op])
    patterns = {'opcode': op}


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
