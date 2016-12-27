""" 6502 instructions

See for example: http://www.6502.org/tutorials/6502opcodes.html
"""


from ..isa import Isa
from ..encoding import Instruction, Syntax, Operand, Constructor, Relocation
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


@isa.register_relocation
class AbsRelocation(Relocation):
    token = WordToken
    field = 'word'
    name = 'abs16'

    def calc(self, sym_value, reloc_value):
        return sym_value


class Accumulator(Constructor):
    syntax = Syntax(['a'])


class Immediate(Constructor):
    """ Immediate value operand """
    imm = Operand('imm', int)
    syntax = Syntax(['#', imm])
    tokens = [ByteToken]
    patterns = {'byte': imm}


class AbsoluteLabel(Constructor):
    """ Absolute label """
    target = Operand('target', str)
    syntax = Syntax([target])
    tokens = [WordToken]

    def relocations(self):
        return [AbsRelocation(self.target)]


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


class Relative(Constructor):
    """ Relative """
    target = Operand('target', int)
    syntax = Syntax([target])
    tokens = [ByteToken]
    patterns = {'byte': target}


@isa.register_relocation
class RelativeRelocation(Relocation):
    token = ByteToken
    field = 'byte'
    name = 'rel8'

    def calc(self, sym_value, reloc_value):
        return sym_value - (reloc_value + 1)


class RelativeLabel(Constructor):
    """ Relative label """
    target = Operand('target', str)
    syntax = Syntax([target])
    tokens = [ByteToken]

    def relocations(self):
        return [RelativeRelocation(self.target)]


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


class Beq(Mcs6500Instruction):
    """ Branch on equal """
    tokens = [OpcodeToken]
    label = Operand('label', (Relative, RelativeLabel))
    syntax = Syntax(['beq', ' ', label])
    patterns = {'opcode': 0xF0}


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


class Bmi(Mcs6500Instruction):
    """ Branch on minus """
    tokens = [OpcodeToken]
    label = Operand('label', (Relative, RelativeLabel))
    syntax = Syntax(['bmi', ' ', label])
    patterns = {'opcode': 0x30}


class Bne(Mcs6500Instruction):
    """ Branch on not equal """
    tokens = [OpcodeToken]
    label = Operand('label', (Relative, RelativeLabel))
    syntax = Syntax(['bne', ' ', label])
    patterns = {'opcode': 0xD0}


class Bpl(Mcs6500Instruction):
    """ Branch on plus """
    tokens = [OpcodeToken]
    label = Operand('label', (Relative, RelativeLabel))
    syntax = Syntax(['bpl', ' ', label])
    patterns = {'opcode': 0x10}


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


class Cmp(Mcs6500Instruction):
    """ Compare accumulator """
    tokens = [OpcodeToken]
    op = Operand(
        'op',
        {
            Immediate: 0xC9,
            # TODO C5
            # TODO D5
            Absolute: 0xCD,
            AbsoluteX: 0xDD,
            AbsoluteY: 0xD9,
            IndirectX: 0xC1,
            IndirectY: 0xD1
        })
    syntax = Syntax(['cmp', ' ', op])
    patterns = {'opcode': op}


class Cpx(Mcs6500Instruction):
    """ Compare X register """
    tokens = [OpcodeToken]
    op = Operand(
        'op',
        {
            Immediate: 0xE0,
            # TODO E4
            Absolute: 0xEC,
        })
    syntax = Syntax(['cpx', ' ', op])
    patterns = {'opcode': op}


class Cpy(Mcs6500Instruction):
    """ Compare Y register """
    tokens = [OpcodeToken]
    op = Operand(
        'op',
        {
            Immediate: 0xC0,
            # TODO C4
            Absolute: 0xCC,
        })
    syntax = Syntax(['cpy', ' ', op])
    patterns = {'opcode': op}


class Dec(Mcs6500Instruction):
    """ Decrement memory """
    tokens = [OpcodeToken]
    op = Operand(
        'op',
        {
            # TODO C6
            # TODO D6
            Absolute: 0xCE,
            AbsoluteX: 0xDE,
        })
    syntax = Syntax(['dec', ' ', op])
    patterns = {'opcode': op}


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


class Eor(Mcs6500Instruction):
    """ Bitwise exclusive or """
    tokens = [OpcodeToken]
    op = Operand(
        'op',
        {
            Immediate: 0x49,
            # TODO 45
            # TODO 55
            Absolute: 0x4D,
            AbsoluteX: 0x5D,
            AbsoluteY: 0x59,
            IndirectX: 0x41,
            IndirectY: 0x51,
        })
    syntax = Syntax(['eor', ' ', op])
    patterns = {'opcode': op}


class Inc(Mcs6500Instruction):
    """ Increment memory """
    tokens = [OpcodeToken]
    op = Operand(
        'op',
        {
            # TODO E6
            # TODO F6
            Absolute: 0xEE,
            AbsoluteX: 0xFE,
        })
    syntax = Syntax(['inc', ' ', op])
    patterns = {'opcode': op}


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


class Jmp(Mcs6500Instruction):
    """ Jump """
    tokens = [OpcodeToken]
    label = Operand(
        'label',
        {
            Absolute: 0x4C,
            AbsoluteLabel: 0x4C,
            # TODO: 6C
        })
    syntax = Syntax(['jmp', ' ', label])
    patterns = {'opcode': label}


class Jsr(Mcs6500Instruction):
    """ Jump to subroutine """
    tokens = [OpcodeToken]
    label = Operand('label', (Absolute, AbsoluteLabel))
    syntax = Syntax(['jsr', ' ', label])
    patterns = {'opcode': 0x20}


class Lda(Mcs6500Instruction):
    """ Load accumulator """
    tokens = [OpcodeToken]
    op = Operand(
        'op',
        {
            Immediate: 0xA9,
            # TODO A5
            # TODO B5
            Absolute: 0xAD,
            AbsoluteX: 0xBD,
            AbsoluteY: 0xB9,
            IndirectX: 0xA1,
            IndirectY: 0xB1
        })
    syntax = Syntax(['lda', ' ', op])
    patterns = {'opcode': op}


class Ldx(Mcs6500Instruction):
    """ Load X register """
    tokens = [OpcodeToken]
    op = Operand(
        'op',
        {
            Immediate: 0xA2,
            # TODO A6
            # TODO B6
            Absolute: 0xAE,
            AbsoluteY: 0xBE,
        })
    syntax = Syntax(['ldx', ' ', op])
    patterns = {'opcode': op}


class Ldy(Mcs6500Instruction):
    """ Load Y register """
    tokens = [OpcodeToken]
    op = Operand(
        'op',
        {
            Immediate: 0xA0,
            # TODO A4
            # TODO B4
            Absolute: 0xAC,
            AbsoluteX: 0xBC,
        })
    syntax = Syntax(['ldy', ' ', op])
    patterns = {'opcode': op}


class Lsr(Mcs6500Instruction):
    """ Logical shift right """
    tokens = [OpcodeToken]
    op = Operand(
        'op',
        {
            Accumulator: 0x4A,
            # TODO 46
            # TODO 56
            Absolute: 0x4E,
            AbsoluteX: 0x5E
        })
    syntax = Syntax(['lsr', ' ', op])
    patterns = {'opcode': op}


class Ora(Mcs6500Instruction):
    """ Bitwise or with accumulator """
    tokens = [OpcodeToken]
    op = Operand(
        'op',
        {
            Immediate: 0x09,
            # TODO 05
            # TODO 15
            Absolute: 0x0D,
            AbsoluteX: 0x1D,
            AbsoluteY: 0x19,
            IndirectX: 0x01,
            IndirectY: 0x11,
        })
    syntax = Syntax(['ora', ' ', op])
    patterns = {'opcode': op}


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


class Rol(Mcs6500Instruction):
    """ Rotate left """
    tokens = [OpcodeToken]
    op = Operand(
        'op',
        {
            Accumulator: 0x2A,
            # TODO 26
            # TODO 36
            Absolute: 0x2E,
            AbsoluteX: 0x3E
        })
    syntax = Syntax(['rol', ' ', op])
    patterns = {'opcode': op}


class Ror(Mcs6500Instruction):
    """ Rotate right """
    tokens = [OpcodeToken]
    op = Operand(
        'op',
        {
            Accumulator: 0x6A,
            # TODO 66
            # TODO 76
            Absolute: 0x6E,
            AbsoluteX: 0x7E
        })
    syntax = Syntax(['ror', ' ', op])
    patterns = {'opcode': op}


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


class Sta(Mcs6500Instruction):
    """ Store accumulator """
    tokens = [OpcodeToken]
    op = Operand(
        'op',
        {
            # TODO 85
            # TODO 95
            Absolute: 0x8D,
            AbsoluteX: 0x9D,
            AbsoluteY: 0x99,
            IndirectX: 0x81,
            IndirectY: 0x91
        })
    syntax = Syntax(['sta', ' ', op])
    patterns = {'opcode': op}


class Stx(Mcs6500Instruction):
    """ Store X register """
    tokens = [OpcodeToken]
    op = Operand(
        'op',
        {
            # TODO 86
            # TODO 96
            Absolute: 0x8E,
        })
    syntax = Syntax(['stx', ' ', op])
    patterns = {'opcode': op}


class Sty(Mcs6500Instruction):
    """ Store Y register """
    tokens = [OpcodeToken]
    op = Operand(
        'op',
        {
            # TODO 84
            # TODO 94
            Absolute: 0x8C,
        })
    syntax = Syntax(['sty', ' ', op])
    patterns = {'opcode': op}


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
