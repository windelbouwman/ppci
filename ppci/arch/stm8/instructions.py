""" Stm8 instructions """

from .registers import Stm8RegisterA, A
from .registers import Stm8RegisterX, Stm8RegisterXL, Stm8RegisterXH
from .registers import Stm8RegisterY, Stm8RegisterYL, Stm8RegisterYH
from .registers import Stm8RegisterSP, Stm8RegisterCC
from ..isa import Isa
from ..encoding import FixedPattern, Instruction, Operand, Syntax
from ..encoding import VariablePattern, Constructor
from ..token import bit_range, Token


class Stm8PrecodeToken(Token):
    class Info:
        precode = True
        size = 8

    precode = bit_range(0, 8)


class Stm8OpcodeToken(Token):
    class Info:
        size = 8

    opcode = bit_range(0, 8)
    position = bit_range(1, 4)


class Stm8ByteToken(Token):
    class Info:
        size = 8

    byte = bit_range(0, 8)


class Stm8WordToken(Token):
    class Info:
        size = 16
        endianness = 'big'

    word = bit_range(0, 16)


class Stm8Byte2Token(Token):
    class Info:
        size = 8

    byte2 = bit_range(0, 8)


class Stm8Word2Token(Token):
    class Info:
        size = 16
        endianness = 'big'

    word2 = bit_range(0, 16)


stm8_isa = Isa()


class Stm8Instruction(Instruction):
    isa = stm8_isa


def get_register_argument(name, mnemonic, read=True, write=False):
    return {'A': Operand(name, Stm8RegisterA, read=read, write=write),
            'X': Operand(name, Stm8RegisterX, read=read, write=write),
            'XL': Operand(name, Stm8RegisterXL, read=read, write=write),
            'XH': Operand(name, Stm8RegisterXH, read=read, write=write),
            'Y': Operand(name, Stm8RegisterY, read=read, write=write),
            'YL': Operand(name, Stm8RegisterYL, read=read, write=write),
            'YH': Operand(name, Stm8RegisterYH, read=read, write=write),
            'SP': Operand(name, Stm8RegisterSP, read=read, write=write),
            'CC': Operand(name, Stm8RegisterCC, read=read, write=write),
            None: None}.get(mnemonic, Operand(name, int))


def create_register_operand(register, read, write):
    argument = get_register_argument(
        register.lower(), register.upper(), read=read, write=write)
    return {'name': register.title(),
            register.lower(): argument,
            'syntax': [argument],
            'tokens': [],
            'patterns': []}


a_ro = create_register_operand('A', read=True, write=False)
a_wo = create_register_operand('A', read=False, write=True)
a_rw = create_register_operand('A', read=True, write=True)

x_ro = create_register_operand('X', read=True, write=False)
x_wo = create_register_operand('X', read=False, write=True)
x_rw = create_register_operand('X', read=True, write=True)

xl_ro = create_register_operand('XL', read=True, write=False)
xl_wo = create_register_operand('XL', read=False, write=True)
xl_rw = create_register_operand('XL', read=True, write=True)

xh_ro = create_register_operand('XH', read=True, write=False)
xh_wo = create_register_operand('XH', read=False, write=True)
xh_rw = create_register_operand('XH', read=True, write=True)

y_ro = create_register_operand('Y', read=True, write=False)
y_wo = create_register_operand('Y', read=False, write=True)
y_rw = create_register_operand('Y', read=True, write=True)

yl_ro = create_register_operand('YL', read=True, write=False)
yl_wo = create_register_operand('YL', read=False, write=True)
yl_rw = create_register_operand('YL', read=True, write=True)

yh_ro = create_register_operand('YH', read=True, write=False)
yh_wo = create_register_operand('YH', read=False, write=True)
yh_rw = create_register_operand('YH', read=True, write=True)

sp_ro = create_register_operand('SP', read=True, write=False)
sp_wo = create_register_operand('SP', read=False, write=True)
sp_rw = create_register_operand('SP', read=True, write=True)

cc_ro = create_register_operand('CC', read=True, write=False)
cc_wo = create_register_operand('CC', read=False, write=True)
cc_rw = create_register_operand('CC', read=True, write=True)


def create_memory_operand(immidiate=None,
                          address=None,
                          pointer=None,
                          index=None):
    name = 'Immidiate' if immidiate else ''
    name += immidiate.title() if immidiate else ''
    name += address.title() if address else pointer.title() if pointer else ''
    name += ('off' if index else 'mem') if address or pointer else ''
    name += index if index else ''

    argument_type = immidiate if immidiate else address if address else pointer

    argument = get_register_argument('argument', argument_type)
    index = get_register_argument('index', index)

    syntax = ['('] if index else []
    syntax += ['#'] if immidiate else []
    syntax += ['['] if pointer else []
    syntax += [argument] if argument else []
    syntax += [']'] if pointer else []
    syntax += [','] if argument and index else []
    syntax += [index] if index else []
    syntax += [')'] if index else []

    argument_token = {
        'byte': Stm8ByteToken, 'long': Stm8WordToken,
        'short': Stm8ByteToken, 'word': Stm8WordToken}
    tokens = [argument_token[argument_type]] \
        if argument_type in ('byte', 'long', 'short', 'word') else []

    argument_pattern = {
        'byte': 'byte', 'long': 'word', 'short': 'byte', 'word': 'word'}
    patterns = [VariablePattern(argument_pattern[argument_type], argument)] \
        if argument_type in ('byte', 'long', 'short', 'word') else []

    return {'name': name,
            'argument': argument,
            'index': index,
            'syntax': syntax,
            'tokens': tokens,
            'patterns': patterns}


byte = create_memory_operand(immidiate='byte')
word = create_memory_operand(immidiate='word')

shortmem = create_memory_operand(address='short')
longmem = create_memory_operand(address='long')

x_i = create_memory_operand(index='X')
y_i = create_memory_operand(index='Y')

shortoff_x = create_memory_operand(address='short', index='X')
longoff_x = create_memory_operand(address='long', index='X')

shortoff_y = create_memory_operand(address='short', index='Y')
longoff_y = create_memory_operand(address='long', index='Y')

shortoff_sp = create_memory_operand(address='short', index='SP')

shortptr = create_memory_operand(pointer='short')
longptr = create_memory_operand(pointer='long')

shortptr_x = create_memory_operand(pointer='short', index='X')
longptr_x = create_memory_operand(pointer='long', index='X')

shortptr_y = create_memory_operand(pointer='short', index='Y')
longptr_y = create_memory_operand(pointer='long', index='Y')


def create_bit_operand():
    position = Operand('position', int)
    return {'name': 'Bit',
            'position': position,
            'syntax': ['#', position],
            'tokens': [],
            'patterns': [VariablePattern('position', position)]}


bit = create_bit_operand()


def create_branch_operand():
    label = Operand('label', int)
    return {'name': 'Branch',
            'label': label,
            'syntax': [label],
            'tokens': [Stm8ByteToken],
            'patterns': [VariablePattern('byte', label)]}


branch = create_branch_operand()


def create_instruction(mnemonic,
                       opcode,
                       operands=(),
                       precode=None):
    name = mnemonic.title()
    syntax = [mnemonic] + ([' '] if operands else [])
    tokens = ([Stm8PrecodeToken] if precode else []) + [Stm8OpcodeToken]
    patterns = ([FixedPattern('precode', precode)] if precode else []) \
        + [FixedPattern('opcode', opcode)]
    members = {}

    for i in range(len(operands)):
        operand = dict(operands[i])
        name += operand.pop('name')
        syntax += [
            operand_syntax +
            ([','] if operand_syntax and i != (len(operands) - 1) else [])
            for operand_syntax in [operand.pop('syntax')]][0]
        tokens += operand.pop('tokens')
        patterns += operand.pop('patterns')
        members.update(operand)

    members.update({
        'syntax': Syntax(syntax), 'tokens': tokens, 'patterns': patterns})

    return type(name, (Stm8Instruction,), members)


class ASource(Constructor):
    a = Operand('a', Stm8RegisterA, read=True, write=True)
    syntax = Syntax([a])


class ByteSource(Constructor):
    v = Operand('v', int)
    patterns = {'byte': v}
    tokens = [Stm8ByteToken]
    syntax = Syntax(['#', v])


class LongMemSource(Constructor):
    v = Operand('v', int)
    patterns = {'word': v}
    tokens = [Stm8WordToken]
    syntax = Syntax([v])


class XSource(Constructor):
    x = Operand('x', Stm8RegisterX, read=True)
    syntax = Syntax(['(', x, ')'])


class LongOffsetXSource(Constructor):
    x = Operand('x', Stm8RegisterX, read=True)
    v = Operand('v', int)
    patterns = {'word': v}
    tokens = [Stm8WordToken]
    syntax = Syntax(['(', v, ',', ' ', x, ')'])


class YSource(Constructor):
    y = Operand('y', Stm8RegisterY, read=True)
    syntax = Syntax(['(', y, ')'])
    tokens = [Stm8PrecodeToken]
    patterns = {'precode': 0x90}


class LongOffsetYSource(Constructor):
    y = Operand('y', Stm8RegisterY, read=True)
    v = Operand('v', int)
    patterns = {'precode': 0x90, 'word': v}
    tokens = [Stm8PrecodeToken, Stm8WordToken]
    syntax = Syntax(['(', v, ',', ' ', y, ')'])


class ShortOffsetSp(Constructor):
    """ Memory at offset from SP """
    tokens = [Stm8ByteToken]
    v = Operand('v', int)
    syntax = Syntax(['(', v, ',', 'sp', ')'])
    patterns = {'byte': v}


# TODO: SbcAShortmem
# TODO: SbcAShortoffX

class Adc(Stm8Instruction):
    a = Operand('a', Stm8RegisterA, read=True, write=True)
    src = Operand(
        'src',
        {
            ByteSource: 0xA9,
            LongMemSource: 0xC9,
            XSource: 0xF9,
            LongOffsetXSource: 0xD9,
            ShortOffsetSp: 0x19,
            YSource: 0xF9,
            LongOffsetYSource: 0xD9,
        })
    syntax = Syntax(['adc', ' ', a, ',', ' ', src])
    tokens = [Stm8OpcodeToken]
    patterns = {'opcode': src}


# TODO: AdcAShortoffY
# TODO: AdcAShortptr
AdcALongptr = create_instruction(
    mnemonic='adc', operands=(a_rw, longptr), precode=0x72, opcode=0xC9)
# TODO: AdcAShortptrX
AdcALongptrX = create_instruction(
    mnemonic='adc', operands=(a_rw, longptr_x), precode=0x72, opcode=0xD9)
AdcAShortptrY = create_instruction(
    mnemonic='adc', operands=(a_rw, shortptr_y), precode=0x91, opcode=0xD9)


class Add(Stm8Instruction):
    """ Addition """
    a = Operand('a', Stm8RegisterA, read=True, write=True)
    src = Operand(
        'src',
        {
            ByteSource: 0xAB,
            LongMemSource: 0xCB,
            XSource: 0xFB,
            LongOffsetXSource: 0xDB,
            ShortOffsetSp: 0x1B,
            YSource: 0xFB,
            LongOffsetYSource: 0xDB,
        })
    syntax = Syntax(['add', ' ', a, ',', ' ', src])
    tokens = [Stm8OpcodeToken]
    patterns = {'opcode': src}


# TODO: AddAShortoffY
# TODO: AddAShortptr
AddALongptr = create_instruction(
    mnemonic='add', operands=(a_rw, longptr), precode=0x72, opcode=0xCB)
# TODO: AddAShortptrX
AddALongptrX = create_instruction(
    mnemonic='add', operands=(a_rw, longptr_x), precode=0x72, opcode=0xDB)
AddAShortptrY = create_instruction(
    mnemonic='add', operands=(a_rw, shortptr_y), precode=0x91, opcode=0xDB)


AddwXWord = create_instruction(
    mnemonic='addw', operands=(x_rw, word), opcode=0x1C)
AddwXLongmem = create_instruction(
    mnemonic='addw', operands=(x_rw, longmem), precode=0x72, opcode=0xBB)
AddwXShortoffSp = create_instruction(
    mnemonic='addw', operands=(x_rw, shortoff_sp), precode=0x72, opcode=0xFB)
AddwYWord = create_instruction(
    mnemonic='addw', operands=(y_rw, word), precode=0x72, opcode=0xA9)
AddwYLongmem = create_instruction(
    mnemonic='addw', operands=(y_rw, longmem), precode=0x72, opcode=0xB9)
AddwYShortoffSp = create_instruction(
    mnemonic='addw', operands=(y_rw, shortoff_sp), precode=0x72, opcode=0xF9)
AddwSpByte = create_instruction(
    mnemonic='addw', operands=(sp_rw, byte), opcode=0x5B)


class And(Stm8Instruction):
    """ Logical and """
    a = Operand('a', Stm8RegisterA, read=True, write=True)
    src = Operand(
        'src',
        {
            ByteSource: 0xA4,
            LongMemSource: 0xC4,
            XSource: 0xF4,
            LongOffsetXSource: 0xD4,
            ShortOffsetSp: 0x14,
            YSource: 0xF4,
            LongOffsetYSource: 0xD4,
        })
    syntax = Syntax(['and', ' ', a, ',', ' ', src])
    tokens = [Stm8OpcodeToken]
    patterns = {'opcode': src}


# TODO: AndAShortoffY
# TODO: AndAShortptr
AndALongptr = create_instruction(
    mnemonic='and', operands=(a_rw, longptr), precode=0x72, opcode=0xC4)
# TODO: AndAShortptrX
AndALongptrX = create_instruction(
    mnemonic='and', operands=(a_rw, longptr_x), precode=0x72, opcode=0xD4)
AndAShortptrY = create_instruction(
    mnemonic='and', operands=(a_rw, shortptr_y), precode=0x91, opcode=0xD4)


Bccm = create_instruction(
    mnemonic='bccm', operands=(longmem, bit), precode=0x90, opcode=0x11)


class Bcp(Stm8Instruction):
    """ Logical bit compare """
    a = Operand('a', Stm8RegisterA, read=True)
    src = Operand(
        'src',
        {
            ByteSource: 0xA5,
            LongMemSource: 0xC5,
            XSource: 0xF5,
            LongOffsetXSource: 0xD5,
            ShortOffsetSp: 0x15,
            YSource: 0xF5,
            LongOffsetYSource: 0xD5,
        })
    syntax = Syntax(['bcp', ' ', a, ',', ' ', src])
    tokens = [Stm8OpcodeToken]
    patterns = {'opcode': src}


# TODO: BcpAShortoffY
# TODO: BcpAShortptr
BcpALongptr = create_instruction(
    mnemonic='bcp', operands=(a_ro, longptr), precode=0x72, opcode=0xC5)
# TODO: BcpAShortptrX
BcpALongptrX = create_instruction(
    mnemonic='bcp', operands=(a_ro, longptr_x), precode=0x72, opcode=0xD5)
BcpAShortptrY = create_instruction(
    mnemonic='bcp', operands=(a_ro, shortptr_y), precode=0x91, opcode=0xD5)


Bcpl = create_instruction(
    mnemonic='bcpl', operands=(longmem, bit), precode=0x90, opcode=0x10)


Break = create_instruction(mnemonic='break', opcode=0x8B)


Bres = create_instruction(
    mnemonic='bres', operands=(longmem, bit), precode=0x72, opcode=0x11)


Bset = create_instruction(
    mnemonic='bset', operands=(longmem, bit), precode=0x72, opcode=0x10)


Btjf = create_instruction(
    mnemonic='btjf', operands=(longmem, bit, branch),
    precode=0x72, opcode=0x01)


Btjt = create_instruction(
    mnemonic='btjt', operands=(longmem, bit, branch),
    precode=0x72, opcode=0x00)


CallLongmem = create_instruction(
    mnemonic='call', operands=(longmem,), opcode=0xCD)
CallX = create_instruction(mnemonic='call', operands=(x_i,), opcode=0xFD)
# TODO: CallShortoffX
CallLongoffX = create_instruction(
    mnemonic='call', operands=(longoff_x,), opcode=0xDD)
CallY = create_instruction(
    mnemonic='call', operands=(y_i,), precode=0x90, opcode=0xFD)
# TODO: CallShortoffY
CallLongoffY = create_instruction(
    mnemonic='call', operands=(longoff_y,), precode=0x90, opcode=0xDD)
# TODO: CallShortptr
CallLongptr = create_instruction(
    mnemonic='call', operands=(longptr,), precode=0x72, opcode=0xCD)
# TODO: CallShortptrX
CallLongptrX = create_instruction(
    mnemonic='call', operands=(longptr_x,), precode=0x72, opcode=0xDD)
CallShortptrY = create_instruction(
    mnemonic='call', operands=(shortptr_y,), precode=0x91, opcode=0xDD)


Callr = create_instruction(mnemonic='callr', operands=(branch,), opcode=0xAD)


Ccf = create_instruction(mnemonic='ccf', opcode=0x8C)


class Clr(Stm8Instruction):
    """ Logical bit compare """
    src = Operand(
        'src',
        {
            ASource: 0x4F,
            XSource: 0x7F,
            ShortOffsetSp: 0x0F,
            YSource: 0x7F,
        })
    syntax = Syntax(['clr', ' ', src])
    tokens = [Stm8OpcodeToken]
    patterns = {'opcode': src}


# TODO: ClrShortmem
ClrLongmem = create_instruction(
    mnemonic='clr', operands=(longmem,), precode=0x72, opcode=0x5F)
# TODO: ClrShortoffX
ClrLongoffX = create_instruction(
    mnemonic='clr', operands=(longoff_x,), precode=0x72, opcode=0x4F)
# TODO: ClrShortoffY
ClrLongoffY = create_instruction(
    mnemonic='clr', operands=(longoff_y,), precode=0x90, opcode=0x4F)
# TODO: ClrShortptr
ClrLongptr = create_instruction(
    mnemonic='clr', operands=(longptr,), precode=0x72, opcode=0x3F)
# TODO: ClrShortptrX
ClrLongptrX = create_instruction(
    mnemonic='clr', operands=(longptr_x,), precode=0x72, opcode=0x6F)
ClrShortptrY = create_instruction(
    mnemonic='clr', operands=(shortptr_y,), precode=0x91, opcode=0x6F)


ClrwX = create_instruction(mnemonic='clrw', operands=(x_wo,), opcode=0x5F)
ClrwY = create_instruction(
    mnemonic='clrw', operands=(y_wo,), precode=0x90, opcode=0x5F)


class Cp(Stm8Instruction):
    """ Compare """
    a = Operand('a', Stm8RegisterA, read=True)
    src = Operand(
        'src',
        {
            ByteSource: 0xA1,
            LongMemSource: 0xC1,
            XSource: 0xF1,
            LongOffsetXSource: 0xD1,
            ShortOffsetSp: 0x11,
            YSource: 0xF1,
        })
    syntax = Syntax(['cp', ' ', a, ',', ' ', src])
    tokens = [Stm8OpcodeToken]
    patterns = {'opcode': src}


# TODO: CpAShortoffY
CpALongoffY = create_instruction(
    mnemonic='cp', operands=(a_ro, longoff_y), precode=0x90, opcode=0xD1)
# TODO: CpAShortptr
CpALongptr = create_instruction(
    mnemonic='cp', operands=(a_ro, longptr), precode=0x72, opcode=0xC1)
# TODO: CpAShortptrX
CpALongptrX = create_instruction(
    mnemonic='cp', operands=(a_ro, longptr_x), precode=0x72, opcode=0xD1)
CpAShortptrY = create_instruction(
    mnemonic='cp', operands=(a_ro, shortptr_y), precode=0x91, opcode=0xD1)


CpwXWord = create_instruction(
    mnemonic='cpw', operands=(x_ro, word), opcode=0xA3)
# TODO: CpwXShortmem
CpwXLongmem = create_instruction(
    mnemonic='cpw', operands=(x_ro, longmem), opcode=0xC3)
CpwXY = create_instruction(
    mnemonic='cpw', operands=(x_ro, y_i), precode=0x90, opcode=0xF3)
# TODO: CpwXShortoffY
CpwXLongoffY = create_instruction(
    mnemonic='cpw', operands=(x_ro, longoff_y), precode=0x90, opcode=0xD3)
CpwXShortoffSP = create_instruction(
    mnemonic='cpw', operands=(x_ro, shortoff_sp), opcode=0x13)
# TODO: CpwXShortptr
CpwXLongptr = create_instruction(
    mnemonic='cpw', operands=(x_ro, longptr), precode=0x72, opcode=0xC3)
CpwXShortptrY = create_instruction(
    mnemonic='cpw', operands=(x_ro, shortptr_y), precode=0x91, opcode=0xD3)

CpwYWord = create_instruction(
    mnemonic='cpw', operands=(y_ro, word), precode=0x90, opcode=0xA3)
# TODO: CpwYShortmem
CpwYLongmem = create_instruction(
    mnemonic='cpw', operands=(y_ro, longmem), precode=0x90, opcode=0xC3)
CpwYX = create_instruction(
    mnemonic='cpw', operands=(y_ro, x_i), opcode=0xF3)
# TODO: CpwYShortoffX
CpwYLongoffX = create_instruction(
    mnemonic='cpw', operands=(y_ro, longoff_x), opcode=0xD3)
CpwYShortptr = create_instruction(
    mnemonic='cpw', operands=(y_ro, shortptr), precode=0x91, opcode=0xC3)
# TODO: CpwYShortptrX
CpwYLongptrX = create_instruction(
    mnemonic='cpw', operands=(y_ro, longptr_x), precode=0x72, opcode=0xD3)


class Cpl(Stm8Instruction):
    """ Logical 1 complement """
    src = Operand(
        'src',
        {
            ASource: 0x43,
            XSource: 0x73,
            ShortOffsetSp: 0x03,
        })
    syntax = Syntax(['cpl', ' ', src])
    tokens = [Stm8OpcodeToken]
    patterns = {'opcode': src}


# TODO: CplShortmem
CplLongmem = create_instruction(
    mnemonic='cpl', operands=(longmem,), precode=0x72, opcode=0x53)
# TODO: CplShortoffX
CplLongoffX = create_instruction(
    mnemonic='cpl', operands=(longoff_x,), precode=0x72, opcode=0x43)
CplY = create_instruction(
    mnemonic='cpl', operands=(y_i,), precode=0x90, opcode=0x73)
# TODO: CplShortoffY
CplLongoffY = create_instruction(
    mnemonic='cpl', operands=(longoff_y,), precode=0x90, opcode=0x43)
# TODO: CplShortptr
CplLongptr = create_instruction(
    mnemonic='cpl', operands=(longptr,), precode=0x72, opcode=0x33)
# TODO: CplShortptrX
CplLongptrX = create_instruction(
    mnemonic='cpl', operands=(longptr_x,), precode=0x72, opcode=0x63)
CplShortptrY = create_instruction(
    mnemonic='cpl', operands=(shortptr_y,), precode=0x91, opcode=0x63)


CplwX = create_instruction(mnemonic='cplw', operands=(x_rw,), opcode=0x53)
CplwY = create_instruction(
    mnemonic='cplw', operands=(y_rw,), precode=0x90, opcode=0x53)


class Dec(Stm8Instruction):
    """ Decrement """
    src = Operand(
        'src',
        {
            ASource: 0x4A,
            XSource: 0x7A,
            ShortOffsetSp: 0x0A,
        })
    syntax = Syntax(['dec', ' ', src])
    tokens = [Stm8OpcodeToken]
    patterns = {'opcode': src}


# TODO: DecShortmem
DecLongmem = create_instruction(
    mnemonic='dec', operands=(longmem,), precode=0x72, opcode=0x5A)
# TODO: DecShortoffX
DecLongoffX = create_instruction(
    mnemonic='dec', operands=(longoff_x,), precode=0x72, opcode=0x4A)
DecY = create_instruction(
    mnemonic='dec', operands=(y_i,), precode=0x90, opcode=0x7A)
# TODO: DecShortoffY
DecLongoffY = create_instruction(
    mnemonic='dec', operands=(longoff_y,), precode=0x90, opcode=0x4A)
# TODO: DecShortptr
DecLongptr = create_instruction(
    mnemonic='dec', operands=(longptr,), precode=0x72, opcode=0x3A)
# TODO: DecShortptrX
DecLongptrX = create_instruction(
    mnemonic='dec', operands=(longptr_x,), precode=0x72, opcode=0x6A)
DecShortptrY = create_instruction(
    mnemonic='dec', operands=(shortptr_y,), precode=0x91, opcode=0x6A)


DecwX = create_instruction(mnemonic='decw', operands=(x_rw,), opcode=0x5A)
DecwY = create_instruction(
    mnemonic='decw', operands=(y_rw,), precode=0x90, opcode=0x5A)


DivXA = create_instruction(mnemonic='div', operands=(x_rw, a_rw), opcode=0x62)
DivYA = create_instruction(
    mnemonic='div', operands=(y_rw, a_rw), precode=0x90, opcode=0x62)


DivXY = create_instruction(mnemonic='div', operands=(x_rw, y_rw), opcode=0x65)


ExgAXl = create_instruction(
    mnemonic='exg', operands=(a_rw, xl_rw), opcode=0x41)
ExgAYl = create_instruction(
    mnemonic='exg', operands=(a_rw, yl_rw), opcode=0x61)
ExgYLongmem = create_instruction(
    mnemonic='exg', operands=(a_rw, longmem), opcode=0x31)


ExgwXY = create_instruction(
    mnemonic='exgw', operands=(x_rw, y_rw), opcode=0x51)


Halt = create_instruction(mnemonic='halt', opcode=0x8E)


class Inc(Stm8Instruction):
    """ Increment """
    src = Operand(
        'src',
        {
            ASource: 0x4C,
            XSource: 0x7C,
            ShortOffsetSp: 0x0C,
        })
    syntax = Syntax(['inc', ' ', src])
    tokens = [Stm8OpcodeToken]
    patterns = {'opcode': src}


# TODO: IncShortmem
IncLongmem = create_instruction(
    mnemonic='inc', operands=(longmem,), precode=0x72, opcode=0x5C)
# TODO: IncShortoffX
IncLongoffX = create_instruction(
    mnemonic='inc', operands=(longoff_x,), precode=0x72, opcode=0x4C)
IncY = create_instruction(
    mnemonic='inc', operands=(y_i,), precode=0x90, opcode=0x7C)
# TODO: IncShortoffY
IncLongoffY = create_instruction(
    mnemonic='inc', operands=(longoff_y,), precode=0x90, opcode=0x4C)
# TODO: IncShortptr
IncLongptr = create_instruction(
    mnemonic='inc', operands=(longptr,), precode=0x72, opcode=0x3C)
# TODO: IncShortptrX
IncLongptrX = create_instruction(
    mnemonic='inc', operands=(longptr_x,), precode=0x72, opcode=0x6C)
IncShortptrY = create_instruction(
    mnemonic='inc', operands=(shortptr_y,), precode=0x91, opcode=0x6C)


IncwX = create_instruction(mnemonic='incw', operands=(x_rw,), opcode=0x5C)
IncwY = create_instruction(
    mnemonic='incw', operands=(y_rw,), precode=0x90, opcode=0x5C)


# TODO: Add support for extended adresses.
Int = create_instruction(
    mnemonic='int', operands=(longmem,), precode=0x82, opcode=0x00)


Iret = create_instruction(mnemonic='iret', opcode=0x80)


JpALongmem = create_instruction(
    mnemonic='jp', operands=(longmem,), opcode=0xCC)
JpAX = create_instruction(mnemonic='jp', operands=(x_i,), opcode=0xFC)
# TODO: JpAShortoffX
JpALongoffX = create_instruction(
    mnemonic='jp', operands=(longoff_x,), opcode=0xDC)
JpAY = create_instruction(
    mnemonic='jp', operands=(y_i,), precode=0x90, opcode=0xFC)
# TODO: JpAShortoffY
JpALongoffY = create_instruction(
    mnemonic='jp', operands=(longoff_y,), precode=0x90, opcode=0xDC)
# TODO: JpAShortptr
JpALongptr = create_instruction(
    mnemonic='jp', operands=(longptr,), precode=0x72, opcode=0xCC)
# TODO: JpAShortptrX
JpALongptrX = create_instruction(
    mnemonic='jp', operands=(longptr_x,), precode=0x72, opcode=0xDC)
JpAShortptrY = create_instruction(
    mnemonic='jp', operands=(shortptr_y,), precode=0x91, opcode=0xDC)


Jra = create_instruction(mnemonic='jra', operands=(branch,), opcode=0x20)


Jrc = create_instruction(
    mnemonic='jrc', operands=(branch,), precode=None, opcode=0x25)
Jreq = create_instruction(
    mnemonic='jreq', operands=(branch,), precode=None, opcode=0x27)
Jrf = create_instruction(
    mnemonic='jrf', operands=(branch,), precode=None, opcode=0x21)
Jrh = create_instruction(
    mnemonic='jrh', operands=(branch,), precode=0x90, opcode=0x29)
Jrih = create_instruction(
    mnemonic='jrih', operands=(branch,), precode=0x90, opcode=0x2F)
Jril = create_instruction(
    mnemonic='jril', operands=(branch,), precode=0x90, opcode=0x2E)
Jrm = create_instruction(
    mnemonic='jrm', operands=(branch,), precode=0x90, opcode=0x2D)
Jrmi = create_instruction(
    mnemonic='jrmi', operands=(branch,), precode=None, opcode=0x2B)
Jrnc = create_instruction(
    mnemonic='jrnc', operands=(branch,), precode=None, opcode=0x24)
Jrne = create_instruction(
    mnemonic='jrne', operands=(branch,), precode=None, opcode=0x26)
Jrnh = create_instruction(
    mnemonic='jrnh', operands=(branch,), precode=0x90, opcode=0x28)
Jrnm = create_instruction(
    mnemonic='jrnm', operands=(branch,), precode=0x90, opcode=0x2C)
Jrnv = create_instruction(
    mnemonic='jrnv', operands=(branch,), precode=None, opcode=0x28)
Jrpl = create_instruction(
    mnemonic='jrpl', operands=(branch,), precode=None, opcode=0x2A)
Jrsge = create_instruction(
    mnemonic='jrsge', operands=(branch,), precode=None, opcode=0x2E)
Jrsgt = create_instruction(
    mnemonic='jrsgt', operands=(branch,), precode=None, opcode=0x2C)
Jrsle = create_instruction(
    mnemonic='jrsle', operands=(branch,), precode=None, opcode=0x2D)
Jrslt = create_instruction(
    mnemonic='jrslt', operands=(branch,), precode=None, opcode=0x2F)
Jrt = create_instruction(
    mnemonic='jrt', operands=(branch,), precode=None, opcode=0x20)
Jruge = create_instruction(
    mnemonic='jruge', operands=(branch,), precode=None, opcode=0x24)
Jrugt = create_instruction(
    mnemonic='jrugt', operands=(branch,), precode=None, opcode=0x22)
Jrule = create_instruction(
    mnemonic='jrule', operands=(branch,), precode=None, opcode=0x23)
Jrult = create_instruction(
    mnemonic='jrult', operands=(branch,), precode=None, opcode=0x25)
Jrv = create_instruction(
    mnemonic='jrv', operands=(branch,), precode=None, opcode=0x29)


class Ld(Stm8Instruction):
    """ Load """
    a = Operand('a', Stm8RegisterA, write=True)
    src = Operand(
        'src',
        {
            ByteSource: 0xA6,
            LongMemSource: 0xC6,
            XSource: 0xF6,
            LongOffsetXSource: 0xD6
        })
    syntax = Syntax(['ld', ' ', a, ',', ' ', src])
    tokens = [Stm8OpcodeToken]
    patterns = {'opcode': src}


LdAY = create_instruction(
    mnemonic='ld', operands=(a_wo, y_i), precode=0x90, opcode=0xF6)
# TODO: LdAShortoffY
LdALongoffY = create_instruction(
    mnemonic='ld', operands=(a_wo, longoff_y), precode=0x90, opcode=0xD6)
LdAShortoffSP = create_instruction(
    mnemonic='ld', operands=(a_wo, shortoff_sp), opcode=0x7B)
# TODO: LdAShortptr
LdALongptr = create_instruction(
    mnemonic='ld', operands=(a_wo, longptr), precode=0x72, opcode=0xC6)
# TODO: LdAShortptrX
LdALongptrX = create_instruction(
    mnemonic='ld', operands=(a_wo, longptr_x), precode=0x72, opcode=0xD6)
LdAShortptrY = create_instruction(
    mnemonic='ld', operands=(a_wo, shortptr_y), precode=0x91, opcode=0xD6)

LdByteA = create_instruction(
    mnemonic='ld', operands=(byte, a_ro), opcode=0xA7)
# TODO: LdShortmemA
LdLongmemA = create_instruction(
    mnemonic='ld', operands=(longmem, a_ro), opcode=0xC7)
LdXA = create_instruction(
    mnemonic='ld', operands=(x_i, a_ro), opcode=0xF7)
# TODO: LdShortoffXA
LdLongoffXA = create_instruction(
    mnemonic='ld', operands=(longoff_x, a_ro), opcode=0xD7)
LdYA = create_instruction(
    mnemonic='ld', operands=(y_i, a_ro), precode=0x90, opcode=0xF7)
# TODO: LdShortoffYA
LdLongoffYA = create_instruction(
    mnemonic='ld', operands=(longoff_y, a_ro), precode=0x90, opcode=0xD7)
LdShortoffSPA = create_instruction(
    mnemonic='ld', operands=(shortoff_sp, a_ro),               opcode=0x6B)
# TODO: LdShortptrA
LdLongptrA = create_instruction(
    mnemonic='ld', operands=(longptr, a_ro), precode=0x72, opcode=0xC7)
# TODO: LdShortptrXA
LdLongptrXA = create_instruction(
    mnemonic='ld', operands=(longptr_x, a_ro), precode=0x72, opcode=0xD7)
LdShortptrYA = create_instruction(
    mnemonic='ld', operands=(shortptr_y, a_ro), precode=0x91, opcode=0xD7)

MovXlA = create_instruction(
    mnemonic='ld', operands=(xl_wo, a_ro), precode=None, opcode=0x97)
MovAXl = create_instruction(
    mnemonic='ld', operands=(a_wo, xl_ro), precode=None, opcode=0x9F)
MovYlA = create_instruction(
    mnemonic='ld', operands=(yl_wo, a_ro), precode=0x90, opcode=0x97)
MovAYl = create_instruction(
    mnemonic='ld', operands=(a_wo, yl_ro), precode=0x90, opcode=0x9F)
MovXhA = create_instruction(
    mnemonic='ld', operands=(xh_wo, a_ro), precode=None, opcode=0x95)
MovAXh = create_instruction(
    mnemonic='ld', operands=(a_wo, xh_ro), precode=None, opcode=0x9E)
MovYhA = create_instruction(
    mnemonic='ld', operands=(yh_wo, a_ro), precode=0x90, opcode=0x95)
MovAYh = create_instruction(
    mnemonic='ld', operands=(a_wo, yh_ro), precode=0x90, opcode=0x9E)


LdwXWord = create_instruction(
    mnemonic='ldw', operands=(x_wo, word), opcode=0xAE)
# TODO: LdwXShortmem
LdwXLongmem = create_instruction(
    mnemonic='ldw', operands=(x_wo, longmem), opcode=0xCE)
LdwXX = create_instruction(mnemonic='ldw', operands=(x_wo, x_i), opcode=0xFE)
# TODO: LdwXShortoffX
LdwXLongoffX = create_instruction(
    mnemonic='ldw', operands=(x_wo, longoff_x), opcode=0xDE)
LdwXShortoffSP = create_instruction(
    mnemonic='ldw', operands=(x_wo, shortoff_sp), opcode=0x1E)
# TODO: LdwXShortptr
LdwXLongptr = create_instruction(
    mnemonic='ldw', operands=(x_wo, longptr), precode=0x72, opcode=0xCE)
# TODO: LdwXShortptrX
LdwXLongptrX = create_instruction(
    mnemonic='ldw', operands=(x_wo, longptr_x), precode=0x72, opcode=0xDE)

# TODO: LdwShortmemX
LdwLongmemX = create_instruction(
    mnemonic='ldw', operands=(longmem, x_ro), opcode=0xCF)
LdwXY = create_instruction(mnemonic='ldw', operands=(x_i, y_ro), opcode=0xFF)
# TODO: LdwShortoffXY
LdwLongoffXY = create_instruction(
    mnemonic='ldw', operands=(longoff_x, y_ro), opcode=0xDF)
LdwShortoffSPX = create_instruction(
    mnemonic='ldw', operands=(shortoff_sp, x_ro), opcode=0x1F)
# TODO: LdwShortptrX
LdwLongptrX = create_instruction(
    mnemonic='ldw', operands=(longptr, x_ro), precode=0x72, opcode=0xCF)
# TODO: LdwShortptrXY
LdwLongptrXY = create_instruction(
    mnemonic='ldw', operands=(longptr_x, y_ro), precode=0x72, opcode=0xDF)

LdwYWord = create_instruction(
    mnemonic='ldw', operands=(y_wo, word), precode=0x90, opcode=0xAE)
# TODO: LdwYShortmem
LdwYLongmem = create_instruction(
    mnemonic='ldw', operands=(y_wo, longmem), precode=0x90, opcode=0xCE)
LdwYY = create_instruction(
    mnemonic='ldw', operands=(y_wo, y_i), precode=0x90, opcode=0xFE)
# TODO: LdwYShortoffY
LdwYLongoffY = create_instruction(
    mnemonic='ldw', operands=(y_wo, longoff_y), precode=0x90, opcode=0xDE)
LdwYShortoffSP = create_instruction(
    mnemonic='ldw', operands=(y_wo, shortoff_sp), opcode=0x16)
LdwYShortptr = create_instruction(
    mnemonic='ldw', operands=(y_wo, shortptr), precode=0x91, opcode=0xCE)
LdwYShortptrY = create_instruction(
    mnemonic='ldw', operands=(y_wo, shortptr_y), precode=0x91, opcode=0xDE)

# TODO: LdwShortmemY
LdwLongmemY = create_instruction(
    mnemonic='ldw', operands=(longmem, y_ro), precode=0x90, opcode=0xCF)
LdwYX = create_instruction(
    mnemonic='ldw', operands=(y_i, x_ro), precode=0x90, opcode=0xFF)
# TODO: LdwShortoffYX
LdwLongoffYX = create_instruction(
    mnemonic='ldw', operands=(longoff_y, x_ro), precode=0x90, opcode=0xDF)
LdwShortoffSPY = create_instruction(
    mnemonic='ldw', operands=(shortoff_sp, y_ro), opcode=0x17)
LdwShortptrY = create_instruction(
    mnemonic='ldw', operands=(shortptr, y_ro), precode=0x91, opcode=0xCF)
LdwShortptrYX = create_instruction(
    mnemonic='ldw', operands=(shortptr_y, x_ro), precode=0x91, opcode=0xDF)

MovwXY = create_instruction(
    mnemonic='ldw', operands=(x_wo, y_ro), opcode=0x93)
MovwYX = create_instruction(
    mnemonic='ldw', operands=(y_wo, x_ro), precode=0x90, opcode=0x93)
MovwXSP = create_instruction(
    mnemonic='ldw', operands=(x_wo, sp_ro), opcode=0x96)
MovwSPX = create_instruction(
    mnemonic='ldw', operands=(sp_wo, x_ro), opcode=0x94)
MovwYSP = create_instruction(
    mnemonic='ldw', operands=(y_wo, sp_ro), precode=0x90, opcode=0x96)
MovwSPY = create_instruction(
    mnemonic='ldw', operands=(sp_wo, y_ro), precode=0x90, opcode=0x94)


class MovLongmemByte(Stm8Instruction):
    destination = Operand('destination', int)
    source = Operand('source', int)
    syntax = Syntax(['mov', ' ', destination, ',', '#', source])
    tokens = [Stm8OpcodeToken, Stm8ByteToken, Stm8WordToken]
    patterns = {'opcode': 0x35, 'byte': source, 'word': destination}


class MovLongmemLongmem(Stm8Instruction):
    destination = Operand('destination', int)
    source = Operand('source', int)
    syntax = Syntax(['mov', ' ', destination, ',', ' ', source])
    tokens = [Stm8OpcodeToken, Stm8Word2Token, Stm8WordToken]
    patterns = {'opcode': 0x55, 'word2': source, 'word': destination}


MulXA = create_instruction(
    mnemonic='mul', operands=(x_rw, a_ro), precode=None, opcode=0x42)
MulYA = create_instruction(
    mnemonic='mul', operands=(y_rw, a_ro), precode=0x90, opcode=0x42)


NegA = create_instruction(mnemonic='neg', operands=(a_rw,), opcode=0x40)
# TODO: NegShortmem
NegLongmem = create_instruction(
    mnemonic='neg', operands=(longmem,), precode=0x72, opcode=0x50)
NegX = create_instruction(mnemonic='neg', operands=(x_i,), opcode=0x70)
# TODO: NegShortoffX
NegLongoffX = create_instruction(
    mnemonic='neg', operands=(longoff_x,), precode=0x72, opcode=0x40)
NegY = create_instruction(
    mnemonic='neg', operands=(y_i,), precode=0x90, opcode=0x70)
# TODO: NegShortoffY
NegLongoffY = create_instruction(
    mnemonic='neg', operands=(longoff_y,), precode=0x90, opcode=0x40)
NegShortoffSP = create_instruction(
    mnemonic='neg', operands=(shortoff_sp,), opcode=0x00)
# TODO: NegShortptr
NegLongptr = create_instruction(
    mnemonic='neg', operands=(longptr,), precode=0x72, opcode=0x30)
# TODO: NegShortptrX
NegLongptrX = create_instruction(
    mnemonic='neg', operands=(longptr_x,), precode=0x72, opcode=0x60)
NegShortptrY = create_instruction(
    mnemonic='neg', operands=(shortptr_y,), precode=0x91, opcode=0x60)


NegwX = create_instruction(mnemonic='negw', operands=(x_rw,), opcode=0x50)
NegwY = create_instruction(
    mnemonic='negw', operands=(y_rw,), precode=0x90, opcode=0x50)


Nop = create_instruction(mnemonic='nop', opcode=0x9D)


class Or(Stm8Instruction):
    """ Logical or """
    a = Operand('a', Stm8RegisterA, read=True, write=True)
    src = Operand(
        'src',
        {
            ByteSource: 0xAA,
            LongMemSource: 0xCA,
            XSource: 0xFA,
            LongOffsetXSource: 0xDA,
            ShortOffsetSp: 0x1A,
        })
    syntax = Syntax(['or', ' ', a, ',', ' ', src])
    tokens = [Stm8OpcodeToken]
    patterns = {'opcode': src}


OrAY = create_instruction(
    mnemonic='or', operands=(a_rw, y_i), precode=0x90, opcode=0xFA)
# TODO: OrAShortoffY
OrALongoffY = create_instruction(
    mnemonic='or', operands=(a_rw, longoff_y), precode=0x90, opcode=0xDA)
# TODO: OrAShortptr
OrALongptr = create_instruction(
    mnemonic='or', operands=(a_rw, longptr), precode=0x72, opcode=0xCA)
# TODO: OrAShortptrX
OrALongptrX = create_instruction(
    mnemonic='or', operands=(a_rw, longptr_x), precode=0x72, opcode=0xDA)
OrAShortptrY = create_instruction(
    mnemonic='or', operands=(a_rw, shortptr_y), precode=0x91, opcode=0xDA)


PopA = create_instruction(mnemonic='pop', operands=(a_wo,), opcode=0x84)
PopCC = create_instruction(mnemonic='pop', operands=(cc_wo,), opcode=0x86)
PopLongmem = create_instruction(
    mnemonic='pop', operands=(longmem,), opcode=0x32)


PopwX = create_instruction(mnemonic='popw', operands=(x_wo,), opcode=0x85)
PopwY = create_instruction(
    mnemonic='popw', operands=(y_wo,), precode=0x90, opcode=0x85)


PushA = create_instruction(mnemonic='push', operands=(a_ro,), opcode=0x88)
PushCC = create_instruction(mnemonic='push', operands=(cc_ro,), opcode=0x8A)
PushByte = create_instruction(mnemonic='push', operands=(byte,), opcode=0x4B)
PushLongmem = create_instruction(
    mnemonic='push', operands=(longmem,), opcode=0x3B)


PushwX = create_instruction(mnemonic='pushw', operands=(x_ro,), opcode=0x89)
PushwY = create_instruction(
    mnemonic='pushw', operands=(y_ro,), precode=0x90, opcode=0x89)


Rcf = create_instruction(mnemonic='rcf', opcode=0x98)


class Ret(Stm8Instruction):
    """ Return from subroutine """
    syntax = Syntax(['ret'])
    tokens = [Stm8OpcodeToken]
    patterns = {'opcode': 0x81}


class Rim(Stm8Instruction):
    """ Reset interrupt mask / enable interrupt """
    syntax = Syntax(['rim'])
    tokens = [Stm8OpcodeToken]
    patterns = {'opcode': 0x9A}


class Rlc(Stm8Instruction):
    """ Rotate left logical through carry """
    src = Operand(
        'src',
        {
            ASource: 0x49,
            XSource: 0x79,
            ShortOffsetSp: 0x09,
        })
    syntax = Syntax(['rlc', ' ', src])
    tokens = [Stm8OpcodeToken]
    patterns = {'opcode': src}


# TODO: RlcShortmem
RlcLongmem = create_instruction(
    mnemonic='rlc', operands=(longmem,), precode=0x72, opcode=0x59)
# TODO: RlcShortoffX
RlcLongoffX = create_instruction(
    mnemonic='rlc', operands=(longoff_x,), precode=0x72, opcode=0x49)
RlcY = create_instruction(
    mnemonic='rlc', operands=(y_i,), precode=0x90, opcode=0x79)
# TODO: RlcShortoffY
RlcLongoffY = create_instruction(
    mnemonic='rlc', operands=(longoff_y,), precode=0x90, opcode=0x49)
# TODO: RlcShortptr
RlcLongptr = create_instruction(
    mnemonic='rlc', operands=(longptr,), precode=0x72, opcode=0x39)
# TODO: RlcShortptrX
RlcLongptrX = create_instruction(
    mnemonic='rlc', operands=(longptr_x,), precode=0x72, opcode=0x69)
RlcShortptrY = create_instruction(
    mnemonic='rlc', operands=(shortptr_y,), precode=0x91, opcode=0x69)


RlcwX = create_instruction(mnemonic='rlcw', operands=(x_rw,), opcode=0x59)
RlcwY = create_instruction(
    mnemonic='rlcw', operands=(y_rw,), precode=0x90, opcode=0x59)


RlwaXA = create_instruction(
    mnemonic='rlwa', operands=(x_rw, a_rw), opcode=0x02)
RlwaYA = create_instruction(
    mnemonic='rlwa', operands=(y_rw, a_rw), precode=0x90, opcode=0x02)


class Rrc(Stm8Instruction):
    """ Rotate right logical through carry """
    src = Operand(
        'src',
        {
            ASource: 0x46,
            XSource: 0x76,
            ShortOffsetSp: 0x06,
        })
    syntax = Syntax(['rrc', ' ', src])
    tokens = [Stm8OpcodeToken]
    patterns = {'opcode': src}


# TODO: RrcShortmem
RrcLongmem = create_instruction(
    mnemonic='rrc', operands=(longmem,), precode=0x72, opcode=0x56)
# TODO: RrcShortoffX
RrcLongoffX = create_instruction(
    mnemonic='rrc', operands=(longoff_x,), precode=0x72, opcode=0x46)
RrcY = create_instruction(
    mnemonic='rrc', operands=(y_i,), precode=0x90, opcode=0x76)
# TODO: RrcShortoffY
RrcLongoffY = create_instruction(
    mnemonic='rrc', operands=(longoff_y,), precode=0x90, opcode=0x46)
# TODO: RrcShortptr
RrcLongptr = create_instruction(
    mnemonic='rrc', operands=(longptr,), precode=0x72, opcode=0x36)
# TODO: RrcShortptrX
RrcLongptrX = create_instruction(
    mnemonic='rrc', operands=(longptr_x,), precode=0x72, opcode=0x66)
RrcShortptrY = create_instruction(
    mnemonic='rrc', operands=(shortptr_y,), precode=0x91, opcode=0x66)


RrcwX = create_instruction(mnemonic='rrcw', operands=(x_rw,), opcode=0x56)
RrcwY = create_instruction(
    mnemonic='rrcw', operands=(y_rw,), precode=0x90, opcode=0x56)


RrwaXA = create_instruction(
    mnemonic='rrwa', operands=(x_rw, a_rw), opcode=0x01)
RrwaYA = create_instruction(
    mnemonic='rrwa', operands=(y_rw, a_rw), precode=0x90, opcode=0x01)


Rvf = create_instruction(mnemonic='rvf', opcode=0x9C)


class Sbc(Stm8Instruction):
    """ Substract with carry / borrow """
    a = Operand('a', Stm8RegisterA, read=True, write=True)
    src = Operand(
        'src',
        {
            ByteSource: 0xA2,
            LongMemSource: 0xC2,
            XSource: 0xF2,
            LongOffsetXSource: 0xD2,
            ShortOffsetSp: 0x12,
        })
    syntax = Syntax(['sbc', ' ', a, ',', ' ', src])
    tokens = [Stm8OpcodeToken]
    patterns = {'opcode': src}


SbcAY = create_instruction(
    mnemonic='sbc', operands=(a_rw, y_i), precode=0x90, opcode=0xF2)
# TODO: SbcAShortoffY
SbcALongoffY = create_instruction(
    mnemonic='sbc', operands=(a_rw, longoff_y), precode=0x90, opcode=0xD2)
# TODO: SbcAShortptr
SbcALongptr = create_instruction(
    mnemonic='sbc', operands=(a_rw, longptr), precode=0x72, opcode=0xC2)
# TODO: SbcAShortptrX
SbcALongptrX = create_instruction(
    mnemonic='sbc', operands=(a_rw, longptr_x), precode=0x72, opcode=0xD2)
SbcAShortptrY = create_instruction(
    mnemonic='sbc', operands=(a_rw, shortptr_y), precode=0x91, opcode=0xD2)


Scf = create_instruction(mnemonic='scf', opcode=0x99)


Sim = create_instruction(mnemonic='sim', opcode=0x9B)


class Sll(Stm8Instruction):
    """ Shift left logical """
    src = Operand(
        'src',
        {
            ASource: 0x48,
            XSource: 0x78,
            ShortOffsetSp: 0x08,
        })
    syntax = Syntax(['sll', ' ', src])
    tokens = [Stm8OpcodeToken]
    patterns = {'opcode': src}


# TODO: SllShortmem
SllLongmem = create_instruction(
    mnemonic='sll', operands=(longmem,), precode=0x72, opcode=0x58)
# TODO: SllShortoffX
SllLongoffX = create_instruction(
    mnemonic='sll', operands=(longoff_x,), precode=0x72, opcode=0x48)
SllY = create_instruction(
    mnemonic='sll', operands=(y_i,), precode=0x90, opcode=0x78)
# TODO: SllShortoffY
SllLongoffY = create_instruction(
    mnemonic='sll', operands=(longoff_y,), precode=0x90, opcode=0x48)
# TODO: SllShortptr
SllLongptr = create_instruction(
    mnemonic='sll', operands=(longptr,), precode=0x72, opcode=0x38)
# TODO: SllShortptrX
SllLongptrX = create_instruction(
    mnemonic='sll', operands=(longptr_x,), precode=0x72, opcode=0x68)
SllShortptrY = create_instruction(
    mnemonic='sll', operands=(shortptr_y,), precode=0x91, opcode=0x68)


SllwX = create_instruction(mnemonic='sllw', operands=(x_rw,), opcode=0x58)
SllwY = create_instruction(
    mnemonic='sllw', operands=(y_rw,), precode=0x90, opcode=0x58)


class Sra(Stm8Instruction):
    """ Shift right arithmatic """
    src = Operand(
        'src',
        {
            ASource: 0x47,
            XSource: 0x77,
            ShortOffsetSp: 0x07,
        })
    syntax = Syntax(['sra', ' ', src])
    tokens = [Stm8OpcodeToken]
    patterns = {'opcode': src}


# TODO: SraShortmem
SraLongmem = create_instruction(
    mnemonic='sra', operands=(longmem,), precode=0x72, opcode=0x57)
# TODO: SraShortoffX
SraLongoffX = create_instruction(
    mnemonic='sra', operands=(longoff_x,), precode=0x72, opcode=0x47)
SraY = create_instruction(
    mnemonic='sra', operands=(y_i,), precode=0x90, opcode=0x77)
# TODO: SraShortoffY
SraLongoffY = create_instruction(
    mnemonic='sra', operands=(longoff_y,), precode=0x90, opcode=0x47)
# TODO: SraShortptr
SraLongptr = create_instruction(
    mnemonic='sra', operands=(longptr,), precode=0x72, opcode=0x37)
# TODO: SraShortptrX
SraLongptrX = create_instruction(
    mnemonic='sra', operands=(longptr_x,), precode=0x72, opcode=0x67)
SraShortptrY = create_instruction(
    mnemonic='sra', operands=(shortptr_y,), precode=0x91, opcode=0x67)


SrawX = create_instruction(mnemonic='sraw', operands=(x_rw,), opcode=0x57)
SrawY = create_instruction(
    mnemonic='sraw', operands=(y_rw,), precode=0x90, opcode=0x57)


class Srl(Stm8Instruction):
    """ Shift right logical """
    src = Operand(
        'src',
        {
            ASource: 0x44,
            XSource: 0x74,
            ShortOffsetSp: 0x04,
        })
    syntax = Syntax(['srl', ' ', src])
    tokens = [Stm8OpcodeToken]
    patterns = {'opcode': src}


# TODO: SrlShortmem
SrlLongmem = create_instruction(
    mnemonic='srl', operands=(longmem,), precode=0x72, opcode=0x54)
# TODO: SrlShortoffX
SrlLongoffX = create_instruction(
    mnemonic='srl', operands=(longoff_x,), precode=0x72, opcode=0x44)
SrlY = create_instruction(
    mnemonic='srl', operands=(y_i,), precode=0x90, opcode=0x74)
# TODO: SrlShortoffY
SrlLongoffY = create_instruction(
    mnemonic='srl', operands=(longoff_y,), precode=0x90, opcode=0x44)
# TODO: SrlShortptr
SrlLongptr = create_instruction(
    mnemonic='srl', operands=(longptr,), precode=0x72, opcode=0x34)
# TODO: SrlShortptrX
SrlLongptrX = create_instruction(
    mnemonic='srl', operands=(longptr_x,), precode=0x72, opcode=0x64)
SrlShortptrY = create_instruction(
    mnemonic='srl', operands=(shortptr_y,), precode=0x91, opcode=0x64)


SrlwX = create_instruction(mnemonic='srlw', operands=(x_rw,), opcode=0x54)
SrlwY = create_instruction(
    mnemonic='srlw', operands=(y_rw,), precode=0x90, opcode=0x54)


class Sub(Stm8Instruction):
    """ Substraction """
    a = Operand('a', Stm8RegisterA, read=True, write=True)
    src = Operand(
        'src',
        {
            ByteSource: 0xA0,
            LongMemSource: 0xC0,
            XSource: 0xF0,
            LongOffsetXSource: 0xD0,
            ShortOffsetSp: 0x10,
        })
    syntax = Syntax(['sub', ' ', a, ',', ' ', src])
    tokens = [Stm8OpcodeToken]
    patterns = {'opcode': src}


SubAY = create_instruction(
    mnemonic='sub', operands=(a_rw, y_i), precode=0x90, opcode=0xF0)
# TODO: SubAShortoffY
SubALongoffY = create_instruction(
    mnemonic='sub', operands=(a_rw, longoff_y), precode=0x90, opcode=0xD0)
# TODO: SubAShortptr
SubALongptr = create_instruction(
    mnemonic='sub', operands=(a_rw, longptr), precode=0x72, opcode=0xC0)
# TODO: SubAShortptrX
SubALongptrX = create_instruction(
    mnemonic='sub', operands=(a_rw, longptr_x), precode=0x72, opcode=0xD0)
SubAShortptrY = create_instruction(
    mnemonic='sub', operands=(a_rw, shortptr_y), precode=0x91, opcode=0xD0)


SubwXWord = create_instruction(
    mnemonic='subw', operands=(x_rw, word), opcode=0x1D)
SubwXLongmem = create_instruction(
    mnemonic='subw', operands=(x_rw, longmem), precode=0x72, opcode=0xB0)
SubwXShortoffSp = create_instruction(
    mnemonic='subw', operands=(x_rw, shortoff_sp), precode=0x72, opcode=0xF0)
SubwYWord = create_instruction(
    mnemonic='subw', operands=(y_rw, word), precode=0x72, opcode=0xA2)
SubwYLongmem = create_instruction(
    mnemonic='subw', operands=(y_rw, longmem), precode=0x72, opcode=0xB2)
SubwYShortoffSp = create_instruction(
    mnemonic='subw', operands=(y_rw, shortoff_sp), precode=0x72, opcode=0xF2)
SubwSpByte = create_instruction(
    mnemonic='subw', operands=(sp_rw, byte), opcode=0x52)


SwapA = create_instruction(mnemonic='swap', operands=(a_rw,), opcode=0x4E)
# TODO: SwapShortmem
SwapLongmem = create_instruction(
    mnemonic='swap', operands=(longmem,), precode=0x72, opcode=0x5E)
SwapX = create_instruction(mnemonic='swap', operands=(x_i,), opcode=0x7E)
# TODO: SwapShortoffX
SwapLongoffX = create_instruction(
    mnemonic='swap', operands=(longoff_x,), precode=0x72, opcode=0x4E)
SwapY = create_instruction(
    mnemonic='swap', operands=(y_i,), precode=0x90, opcode=0x7E)
# TODO: SwapShortoffY
SwapLongoffY = create_instruction(
    mnemonic='swap', operands=(longoff_y,), precode=0x90, opcode=0x4E)
SwapShortoffSP = create_instruction(
    mnemonic='swap', operands=(shortoff_sp,), opcode=0x0E)
# TODO: SwapShortptr
SwapLongptr = create_instruction(
    mnemonic='swap', operands=(longptr,), precode=0x72, opcode=0x3E)
# TODO: SwapShortptrX
SwapLongptrX = create_instruction(
    mnemonic='swap', operands=(longptr_x,), precode=0x72, opcode=0x6E)
SwapShortptrY = create_instruction(
    mnemonic='swap', operands=(shortptr_y,), precode=0x91, opcode=0x6E)


SwapwX = create_instruction(mnemonic='swapw', operands=(x_rw,), opcode=0x5E)
SwapwY = create_instruction(
    mnemonic='swapw', operands=(y_rw,), precode=0x90, opcode=0x5E)


TnzA = create_instruction(mnemonic='tnz', operands=(a_ro,), opcode=0x4D)
# TODO: TnzShortmem
TnzLongmem = create_instruction(
    mnemonic='tnz', operands=(longmem,), precode=0x72, opcode=0x5D)
TnzX = create_instruction(mnemonic='tnz', operands=(x_i,), opcode=0x7D)
# TODO: TnzShortoffX
TnzLongoffX = create_instruction(
    mnemonic='tnz', operands=(longoff_x,), precode=0x72, opcode=0x4D)
TnzY = create_instruction(
    mnemonic='tnz', operands=(y_i,), precode=0x90, opcode=0x7D)
# TODO: TnzShortoffY
TnzLongoffY = create_instruction(
    mnemonic='tnz', operands=(longoff_y,), precode=0x90, opcode=0x4D)
TnzShortoffSP = create_instruction(
    mnemonic='tnz', operands=(shortoff_sp,), opcode=0x0D)
# TODO: TnzShortptr
TnzLongptr = create_instruction(
    mnemonic='tnz', operands=(longptr,), precode=0x72, opcode=0x3D)
# TODO: TnzShortptrX
TnzLongptrX = create_instruction(
    mnemonic='tnz', operands=(longptr_x,), precode=0x72, opcode=0x6D)
TnzShortptrY = create_instruction(
    mnemonic='tnz', operands=(shortptr_y,), precode=0x91, opcode=0x6D)


TnzwX = create_instruction(mnemonic='tnzw', operands=(x_ro,), opcode=0x5D)
TnzwY = create_instruction(
    mnemonic='tnzw', operands=(y_ro,), precode=0x90, opcode=0x5D)


Trap = create_instruction(mnemonic='trap', opcode=0x83)


Wfe = create_instruction(mnemonic='wfe', precode=0x72, opcode=0x8F)


Wfi = create_instruction(mnemonic='wfi', opcode=0x8F)


class Xor(Stm8Instruction):
    """ Logical exclusive or """
    a = Operand('a', Stm8RegisterA, read=True, write=True)
    src = Operand(
        'src',
        {
            ByteSource: 0xA8,
            LongMemSource: 0xC8,
            XSource: 0xF8,
            LongOffsetXSource: 0xD8,
            ShortOffsetSp: 0x18,
        })
    syntax = Syntax(['xor', ' ', a, ',', ' ', src])
    tokens = [Stm8OpcodeToken]
    patterns = {'opcode': src}


XorAY = create_instruction(
    mnemonic='xor', operands=(a_rw, y_i), precode=0x90, opcode=0xF8)
# TODO: XorAShortoffY
XorALongoffY = create_instruction(
    mnemonic='xor', operands=(a_rw, longoff_y), precode=0x90, opcode=0xD8)
# TODO: XorAShortptr
XorALongptr = create_instruction(
    mnemonic='xor', operands=(a_rw, longptr), precode=0x72, opcode=0xC8)
# TODO: XorAShortptrX
XorALongptrX = create_instruction(
    mnemonic='xor', operands=(a_rw, longptr_x), precode=0x72, opcode=0xD8)
XorAShortptrY = create_instruction(
    mnemonic='xor', operands=(a_rw, shortptr_y), precode=0x91, opcode=0xD8)


@stm8_isa.pattern('a', 'CONSTU8', size=2, cycles=1, energy=1)
def pattern_const8(context, tree):
    context.emit(Ld(A, ByteSource(tree.value)))
    return A


@stm8_isa.pattern('a', 'ADDU8(a, CONSTU8)', size=2, cycles=1, energy=1)
def pattern_add8(context, tree, c0):
    context.emit(Add(A, ByteSource(tree[1].value)))
    return A


@stm8_isa.pattern('a', 'SUBU8(a, CONSTU8)', size=2, cycles=1, energy=1)
def pattern_sub8(context, tree, c0):
    context.emit(Sub(A, ByteSource(tree[1].value)))
    return A


@stm8_isa.pattern('a', 'ANDU8(a, CONSTU8)', size=2, cycles=1, energy=1)
def pattern_and8(context, tree, c0):
    context.emit(And(A, ByteSource(tree[1].value)))
    return A


@stm8_isa.pattern('a', 'ORU8(a, CONSTU8)', size=2, cycles=1, energy=1)
def pattern_or8(context, tree, c0):
    context.emit(Or(A, ByteSource(tree[1].value)))
    return A


@stm8_isa.pattern('a', 'XORU8(a, CONSTU8)', size=2, cycles=1, energy=1)
def pattern_xor8(context, tree, c0):
    context.emit(Xor(A, ByteSource(tree[1].value)))
    return A


@stm8_isa.pattern('a', 'LDRU8', size=2, cycles=1, energy=1)
def pattern_ldr8(context, tree):
    # TODO
    context.emit(Ld(A, LongMemSource(tree.value)))
    return A
