from .registers import Stm8RegisterA, Stm8RegisterX, Stm8RegisterY, Stm8RegisterSP
from ..isa import Isa
from ..encoding import FixedPattern, Instruction, register_argument, Syntax, VariablePattern
from ..token import bit_range, Token



class Stm8PrecodeToken(Token):
    precode = bit_range(0, 8)

    def __init__(self):
        super().__init__(8, fmt='>B')


class Stm8OpcodeToken(Token):
    opcode = bit_range(0, 8)
    position = bit_range(1, 4)

    def __init__(self):
        super().__init__(8, fmt='>B')


class Stm8ByteToken(Token):
    byte = bit_range(0, 8)

    def __init__(self):
        super().__init__(8, fmt='>B')


class Stm8WordToken(Token):
    word = bit_range(0, 16)

    def __init__(self):
        super().__init__(16, fmt='>H')



stm8_isa = Isa()


class Stm8Instruction(Instruction):
    isa = stm8_isa



def get_register_argument(name, mnemonic, read=True, write=False):
    if mnemonic == 'A':
        return register_argument(name, Stm8RegisterA, read=read, write=write)
    elif mnemonic == 'X':
        return register_argument(name, Stm8RegisterX, read=read, write=write)
    elif mnemonic == 'Y':
        return register_argument(name, Stm8RegisterY, read=read, write=write)
    elif mnemonic == 'SP':
        return register_argument(name, Stm8RegisterSP, read=read, write=write)
    elif mnemonic == 'label':
        return register_argument(name, str)
    elif mnemonic:
        return register_argument(name, int)
    else:
        return None



def create_register_operand(register, read, write):
    argument = get_register_argument(register.lower(), register.upper(), read=read, write=write)
    return {'name'          : register.title(),
            register.lower(): argument,
            'syntax'        : [argument],
            'tokens'        : [],
            'patterns'      : []}


a_ro = create_register_operand('A', read=True , write=False)
a_wo = create_register_operand('A', read=False, write=True )
a_rw = create_register_operand('A', read=True , write=True )

x_ro = create_register_operand('X', read=True , write=False)
x_wo = create_register_operand('X', read=False, write=True )
x_rw = create_register_operand('X', read=True , write=True )

y_ro = create_register_operand('Y', read=True , write=False)
y_wo = create_register_operand('Y', read=False, write=True )
y_rw = create_register_operand('Y', read=True , write=True )

sp_ro = create_register_operand('SP', read=True , write=False)
sp_wo = create_register_operand('SP', read=False, write=True )
sp_rw = create_register_operand('SP', read=True , write=True )


def create_memory_operand(immidiate=None,
                          address=None,
                          pointer=None,
                          index=None):
    name  = 'Immidiate' if immidiate else ''
    name += immidiate.title() if immidiate else ''
    name += address.title() if address else pointer.title() if pointer else ''
    name += ('off' if index else 'mem') if address or pointer else ''
    name += index if index else ''

    argument_type = immidiate if immidiate else address if address else pointer

    argument    = get_register_argument('argument', argument_type)
    index       = get_register_argument('index',    index)

    syntax  = ['('] if index else []
    syntax += ['#'] if immidiate else []
    syntax += ['['] if pointer else []
    syntax += [argument] if argument else []
    syntax += [']'] if pointer else []
    syntax += [','] if argument and index else []
    syntax += [index] if index else []
    syntax += [')'] if index else []

    argument_token = {'byte':Stm8ByteToken, 'long':Stm8WordToken, 'short':Stm8ByteToken, 'word':Stm8WordToken}
    tokens = [argument_token[argument_type]] if argument_type in ('byte', 'long', 'short', 'word') else []

    argument_pattern = {'byte':'byte', 'long':'word', 'short':'byte', 'word':'word'}
    patterns = [VariablePattern(argument_pattern[argument_type], argument)] if argument_type in ('byte', 'long', 'short', 'word') else []

    return {'name'    : name,
            'argument': argument,
            'index'   : index,
            'syntax'  : syntax,
            'tokens'  : tokens,
            'patterns': patterns}


byte = create_memory_operand(immidiate='byte')
word = create_memory_operand(immidiate='word')

shortmem = create_memory_operand(address='short')
longmem  = create_memory_operand(address='long' )

x_i = create_memory_operand(index='X')
y_i = create_memory_operand(index='Y')

shortoff_x = create_memory_operand(address='short', index='X')
longoff_x  = create_memory_operand(address='long' , index='X')

shortoff_y = create_memory_operand(address='short', index='Y')
longoff_y  = create_memory_operand(address='long' , index='Y')

shortoff_sp = create_memory_operand(address='short', index='SP')

shortptr = create_memory_operand(pointer='short')
longptr  = create_memory_operand(pointer='long' )

shortptr_x = create_memory_operand(pointer='short', index='X')
longptr_x  = create_memory_operand(pointer='long' , index='X')

shortptr_y = create_memory_operand(pointer='short', index='Y')
longptr_y  = create_memory_operand(pointer='long' , index='Y')


def create_bit_operand():
    position = register_argument('position', int)
    return {'name'    : 'Bit',
            'position': position,
            'syntax'  : ['#', position],
            'tokens'  : [],
            'patterns': [VariablePattern('position', position)]}


bit = create_bit_operand()


def create_branch_operand():
    label = register_argument('label', str)
    return {'name'    : 'Bit',
            'label'   : label,
            'syntax'  : [label],
            'tokens'  : [Stm8ByteToken],
            'patterns': []}


branch = create_branch_operand()



def create_instruction(mnemonic,
                       opcode,
                       operands=(),
                       precode=None):
    name     = mnemonic.title()
    syntax   = [mnemonic] + ([' '] if operands else [])
    tokens   = ([Stm8PrecodeToken] if precode else []) + [Stm8OpcodeToken]
    patterns = ([FixedPattern('precode', precode)] if precode else []) + [FixedPattern('opcode', opcode)]
    members  = {}

    for i in range(len(operands)):
        operand = dict(operands[i])
        name     += operand.pop('name')
        syntax   += [operand_syntax + ([','] if operand_syntax and i != (len(operands) - 1) else []) for operand_syntax in [operand.pop('syntax')]][0]
        tokens   += operand.pop('tokens')
        patterns += operand.pop('patterns')
        members.update(operand)

    members.update({'syntax': Syntax(syntax), 'tokens': tokens, 'patterns': patterns})

    return type(name, (Stm8Instruction,), members)



AdcAByte       = create_instruction(mnemonic='adc', operands=(a_rw, byte       ),               opcode=0xA9)
# TODO: AdcAShortmem
AdcALongmem    = create_instruction(mnemonic='adc', operands=(a_rw, longmem    ),               opcode=0xC9)
AdcAX          = create_instruction(mnemonic='adc', operands=(a_rw, x_i        ),               opcode=0xF9)
# TODO: AdcAShortoffX
AdcALongoffX   = create_instruction(mnemonic='adc', operands=(a_rw, longoff_x  ),               opcode=0xD9)
AdcAY          = create_instruction(mnemonic='adc', operands=(a_rw, y_i        ), precode=0x90, opcode=0xF9)
# TODO: AdcAShortoffY
AdcALongoffY   = create_instruction(mnemonic='adc', operands=(a_rw, longoff_y  ), precode=0x90, opcode=0xD9)
AdcAShortoffSP = create_instruction(mnemonic='adc', operands=(a_rw, shortoff_sp),               opcode=0x19)
# TODO: AdcAShortptr
AdcALongptr    = create_instruction(mnemonic='adc', operands=(a_rw, longptr    ), precode=0x72, opcode=0xC9)
# TODO: AdcAShortptrX
AdcALongptrX   = create_instruction(mnemonic='adc', operands=(a_rw, longptr_x  ), precode=0x72, opcode=0xD9)
AdcAShortptrY  = create_instruction(mnemonic='adc', operands=(a_rw, shortptr_y ), precode=0x91, opcode=0xD9)


AddAByte       = create_instruction(mnemonic='add', operands=(a_rw, byte       ),               opcode=0xAB)
# TODO: AddAShortmem
AddALongmem    = create_instruction(mnemonic='add', operands=(a_rw, longmem    ),               opcode=0xCB)
AddAX          = create_instruction(mnemonic='add', operands=(a_rw, x_i        ),               opcode=0xFB)
# TODO: AddAShortoffX
AddALongoffX   = create_instruction(mnemonic='add', operands=(a_rw, longoff_x  ),               opcode=0xDB)
AddAY          = create_instruction(mnemonic='add', operands=(a_rw, y_i        ), precode=0x90, opcode=0xFB)
# TODO: AddAShortoffY
AddALongoffY   = create_instruction(mnemonic='add', operands=(a_rw, longoff_y  ), precode=0x90, opcode=0xDB)
AddAShortoffSP = create_instruction(mnemonic='add', operands=(a_rw, shortoff_sp),               opcode=0x1B)
# TODO: AddAShortptr
AddALongptr    = create_instruction(mnemonic='add', operands=(a_rw, longptr    ), precode=0x72, opcode=0xCB)
# TODO: AddAShortptrX
AddALongptrX   = create_instruction(mnemonic='add', operands=(a_rw, longptr_x  ), precode=0x72, opcode=0xDB)
AddAShortptrY  = create_instruction(mnemonic='add', operands=(a_rw, shortptr_y ), precode=0x91, opcode=0xDB)


AddwXWord       = create_instruction(mnemonic='addw', operands=(x_rw , word       ),               opcode=0x1C)
AddwXLongmem    = create_instruction(mnemonic='addw', operands=(x_rw , longmem    ), precode=0x72, opcode=0xBB)
AddwXShortoffSp = create_instruction(mnemonic='addw', operands=(x_rw , shortoff_sp), precode=0x72, opcode=0xFB)
AddwYWord       = create_instruction(mnemonic='addw', operands=(y_rw , word       ), precode=0x72, opcode=0xA9)
AddwYLongmem    = create_instruction(mnemonic='addw', operands=(y_rw , longmem    ), precode=0x72, opcode=0xB9)
AddwYShortoffSp = create_instruction(mnemonic='addw', operands=(y_rw , shortoff_sp), precode=0x72, opcode=0xF9)
AddwSpByte      = create_instruction(mnemonic='addw', operands=(sp_rw, byte       ),               opcode=0x5B)


AndAByte       = create_instruction(mnemonic='and', operands=(a_rw, byte       ),               opcode=0xA4)
# TODO: AndAShortmem
AndALongmem    = create_instruction(mnemonic='and', operands=(a_rw, longmem    ),               opcode=0xC4)
AndAX          = create_instruction(mnemonic='and', operands=(a_rw, x_i        ),               opcode=0xF4)
# TODO: AndAShortoffX
AndALongoffX   = create_instruction(mnemonic='and', operands=(a_rw, longoff_x  ),               opcode=0xD4)
AndAY          = create_instruction(mnemonic='and', operands=(a_rw, y_i        ), precode=0x90, opcode=0xF4)
# TODO: AndAShortoffY
AndALongoffY   = create_instruction(mnemonic='and', operands=(a_rw, longoff_y  ), precode=0x90, opcode=0xD4)
AndAShortoffSP = create_instruction(mnemonic='and', operands=(a_rw, shortoff_sp),               opcode=0x14)
# TODO: AndAShortptr
AndALongptr    = create_instruction(mnemonic='and', operands=(a_rw, longptr    ), precode=0x72, opcode=0xC4)
# TODO: AndAShortptrX
AndALongptrX   = create_instruction(mnemonic='and', operands=(a_rw, longptr_x  ), precode=0x72, opcode=0xD4)
AndAShortptrY  = create_instruction(mnemonic='and', operands=(a_rw, shortptr_y ), precode=0x91, opcode=0xD4)


Bccm = create_instruction(mnemonic='bccm', operands=(longmem, bit), precode=0x90, opcode=0x11)


BcpAByte       = create_instruction(mnemonic='bcp', operands=(a_ro, byte       ),               opcode=0xA5)
# TODO: BcpAShortmem
BcpALongmem    = create_instruction(mnemonic='bcp', operands=(a_ro, longmem    ),               opcode=0xC5)
BcpAX          = create_instruction(mnemonic='bcp', operands=(a_ro, x_i        ),               opcode=0xF5)
# TODO: BcpAShortoffX
BcpALongoffX   = create_instruction(mnemonic='bcp', operands=(a_ro, longoff_x  ),               opcode=0xD5)
BcpAY          = create_instruction(mnemonic='bcp', operands=(a_ro, y_i        ), precode=0x90, opcode=0xF5)
# TODO: BcpAShortoffY
BcpALongoffY   = create_instruction(mnemonic='bcp', operands=(a_ro, longoff_y  ), precode=0x90, opcode=0xD5)
BcpAShortoffSP = create_instruction(mnemonic='bcp', operands=(a_ro, shortoff_sp),               opcode=0x15)
# TODO: BcpAShortptr
BcpALongptr    = create_instruction(mnemonic='bcp', operands=(a_ro, longptr    ), precode=0x72, opcode=0xC5)
# TODO: BcpAShortptrX
BcpALongptrX   = create_instruction(mnemonic='bcp', operands=(a_ro, longptr_x  ), precode=0x72, opcode=0xD5)
BcpAShortptrY  = create_instruction(mnemonic='bcp', operands=(a_ro, shortptr_y ), precode=0x91, opcode=0xD5)


Bcpl = create_instruction(mnemonic='bcpl', operands=(longmem, bit), precode=0x90, opcode=0x10)


Break = create_instruction(mnemonic='break', opcode=0x8B)


Bres = create_instruction(mnemonic='bres', operands=(longmem, bit), precode=0x72, opcode=0x11)


Bset = create_instruction(mnemonic='bset', operands=(longmem, bit), precode=0x72, opcode=0x10)


Btjf = create_instruction(mnemonic='btjf', operands=(longmem, bit, branch), precode=0x72, opcode=0x01)


Btjt = create_instruction(mnemonic='btjt', operands=(longmem, bit, branch), precode=0x72, opcode=0x00)


CallLongmem   = create_instruction(mnemonic='call', operands=(longmem   ,),               opcode=0xCD)
CallX         = create_instruction(mnemonic='call', operands=(x_i       ,),               opcode=0xFD)
# TODO: CallShortoffX
CallLongoffX  = create_instruction(mnemonic='call', operands=(longoff_x ,),               opcode=0xDD)
CallY         = create_instruction(mnemonic='call', operands=(y_i       ,), precode=0x90, opcode=0xFD)
# TODO: CallShortoffY
CallLongoffY  = create_instruction(mnemonic='call', operands=(longoff_y ,), precode=0x90, opcode=0xDD)
# TODO: CallShortptr
CallLongptr   = create_instruction(mnemonic='call', operands=(longptr   ,), precode=0x72, opcode=0xCD)
# TODO: CallShortptrX
CallLongptrX  = create_instruction(mnemonic='call', operands=(longptr_x ,), precode=0x72, opcode=0xDD)
CallShortptrY = create_instruction(mnemonic='call', operands=(shortptr_y,), precode=0x91, opcode=0xDD)


Callr = create_instruction(mnemonic='callr', operands=(shortmem,), opcode=0xAD)


Ccf = create_instruction(mnemonic='ccf', opcode=0x8C)


ClrA          = create_instruction(mnemonic='clr', operands=(a_wo       ,),               opcode=0x4F)
# TODO: ClrShortmem
ClrLongmem    = create_instruction(mnemonic='clr', operands=(longmem    ,), precode=0x72, opcode=0x5F)
ClrX          = create_instruction(mnemonic='clr', operands=(x_i        ,),               opcode=0x7F)
# TODO: ClrShortoffX
ClrLongoffX   = create_instruction(mnemonic='clr', operands=(longoff_x  ,), precode=0x72, opcode=0x4F)
ClrY          = create_instruction(mnemonic='clr', operands=(y_i        ,), precode=0x90, opcode=0x7F)
# TODO: ClrShortoffY
ClrLongoffY   = create_instruction(mnemonic='clr', operands=(longoff_y  ,), precode=0x90, opcode=0x4F)
ClrShortoffSP = create_instruction(mnemonic='clr', operands=(shortoff_sp,),               opcode=0x0F)
# TODO: ClrShortptr
ClrLongptr    = create_instruction(mnemonic='clr', operands=(longptr    ,), precode=0x72, opcode=0x3F)
# TODO: ClrShortptrX
ClrLongptrX   = create_instruction(mnemonic='clr', operands=(longptr_x  ,), precode=0x72, opcode=0x6F)
ClrShortptrY  = create_instruction(mnemonic='clr', operands=(shortptr_y ,), precode=0x91, opcode=0x6F)


ClrwX = create_instruction(mnemonic='clrw', operands=(x_wo,),               opcode=0x5F)
ClrwY = create_instruction(mnemonic='clrw', operands=(y_wo,), precode=0x90, opcode=0x5F)


CpAByte       = create_instruction(mnemonic='cp', operands=(a_ro, byte       ),               opcode=0xA1)
# TODO: CpAShortmem
CpALongmem    = create_instruction(mnemonic='cp', operands=(a_ro, longmem    ),               opcode=0xC1)
CpAX          = create_instruction(mnemonic='cp', operands=(a_ro, x_i        ),               opcode=0xF1)
# TODO: CpAShortoffX
CpALongoffX   = create_instruction(mnemonic='cp', operands=(a_ro, longoff_x  ),               opcode=0xD1)
CpAY          = create_instruction(mnemonic='cp', operands=(a_ro, y_i        ), precode=0x90, opcode=0xF1)
# TODO: CpAShortoffY
CpALongoffY   = create_instruction(mnemonic='cp', operands=(a_ro, longoff_y  ), precode=0x90, opcode=0xD1)
CpAShortoffSP = create_instruction(mnemonic='cp', operands=(a_ro, shortoff_sp),               opcode=0x11)
# TODO: CpAShortptr
CpALongptr    = create_instruction(mnemonic='cp', operands=(a_ro, longptr    ), precode=0x72, opcode=0xC1)
# TODO: CpAShortptrX
CpALongptrX   = create_instruction(mnemonic='cp', operands=(a_ro, longptr_x  ), precode=0x72, opcode=0xD1)
CpAShortptrY  = create_instruction(mnemonic='cp', operands=(a_ro, shortptr_y ), precode=0x91, opcode=0xD1)


CpwXWord       = create_instruction(mnemonic='cpw', operands=(x_ro, word       ),               opcode=0xA3)
# TODO: CpwXShortmem
CpwXLongmem    = create_instruction(mnemonic='cpw', operands=(x_ro, longmem    ),               opcode=0xC3)
CpwXY          = create_instruction(mnemonic='cpw', operands=(x_ro, y_i        ), precode=0x90, opcode=0xF3)
# TODO: CpwXShortoffY
CpwXLongoffY   = create_instruction(mnemonic='cpw', operands=(x_ro, longoff_y  ), precode=0x90, opcode=0xD3)
CpwXShortoffSP = create_instruction(mnemonic='cpw', operands=(x_ro, shortoff_sp),               opcode=0x13)
# TODO: CpwXShortptr
CpwXLongptr    = create_instruction(mnemonic='cpw', operands=(x_ro, longptr    ), precode=0x72, opcode=0xC3)
CpwXShortptrY  = create_instruction(mnemonic='cpw', operands=(x_ro, shortptr_y ), precode=0x91, opcode=0xD3)

CpwYWord       = create_instruction(mnemonic='cpw', operands=(y_ro, word     ), precode=0x90, opcode=0xA3)
# TODO: CpwYShortmem
CpwYLongmem    = create_instruction(mnemonic='cpw', operands=(y_ro, longmem  ), precode=0x90, opcode=0xC3)
CpwYX          = create_instruction(mnemonic='cpw', operands=(y_ro, x_i      ),               opcode=0xF3)
# TODO: CpwYShortoffX
CpwYLongoffX   = create_instruction(mnemonic='cpw', operands=(y_ro, longoff_x),               opcode=0xD3)
CpwYShortptr   = create_instruction(mnemonic='cpw', operands=(y_ro, shortptr ), precode=0x91, opcode=0xC3)
# TODO: CpwYShortptrX
CpwYLongptrX   = create_instruction(mnemonic='cpw', operands=(y_ro, longptr_x), precode=0x72, opcode=0xD3)


CplA          = create_instruction(mnemonic='cpl', operands=(a_rw       ,),               opcode=0x43)
# TODO: CplShortmem
CplLongmem    = create_instruction(mnemonic='cpl', operands=(longmem    ,), precode=0x72, opcode=0x53)
CplX          = create_instruction(mnemonic='cpl', operands=(x_i        ,),               opcode=0x73)
# TODO: CplShortoffX
CplLongoffX   = create_instruction(mnemonic='cpl', operands=(longoff_x  ,), precode=0x72, opcode=0x43)
CplY          = create_instruction(mnemonic='cpl', operands=(y_i        ,), precode=0x90, opcode=0x73)
# TODO: CplShortoffY
CplLongoffY   = create_instruction(mnemonic='cpl', operands=(longoff_y  ,), precode=0x90, opcode=0x43)
CplShortoffSP = create_instruction(mnemonic='cpl', operands=(shortoff_sp,),               opcode=0x03)
# TODO: CplShortptr
CplLongptr    = create_instruction(mnemonic='cpl', operands=(longptr    ,), precode=0x72, opcode=0x33)
# TODO: CplShortptrX
CplLongptrX   = create_instruction(mnemonic='cpl', operands=(longptr_x  ,), precode=0x72, opcode=0x63)
CplShortptrY  = create_instruction(mnemonic='cpl', operands=(shortptr_y ,), precode=0x91, opcode=0x63)


CplwX = create_instruction(mnemonic='cplw', operands=(x_rw,),               opcode=0x53)
CplwY = create_instruction(mnemonic='cplw', operands=(y_rw,), precode=0x90, opcode=0x53)


DecA          = create_instruction(mnemonic='dec', operands=(a_rw       ,),               opcode=0x4A)
# TODO: DecShortmem
DecLongmem    = create_instruction(mnemonic='dec', operands=(longmem    ,), precode=0x72, opcode=0x5A)
DecX          = create_instruction(mnemonic='dec', operands=(x_i        ,),               opcode=0x7A)
# TODO: DecShortoffX
DecLongoffX   = create_instruction(mnemonic='dec', operands=(longoff_x  ,), precode=0x72, opcode=0x4A)
DecY          = create_instruction(mnemonic='dec', operands=(y_i        ,), precode=0x90, opcode=0x7A)
# TODO: DecShortoffY
DecLongoffY   = create_instruction(mnemonic='dec', operands=(longoff_y  ,), precode=0x90, opcode=0x4A)
DecShortoffSP = create_instruction(mnemonic='dec', operands=(shortoff_sp,),               opcode=0x0A)
# TODO: DecShortptr
DecLongptr    = create_instruction(mnemonic='dec', operands=(longptr    ,), precode=0x72, opcode=0x3A)
# TODO: DecShortptrX
DecLongptrX   = create_instruction(mnemonic='dec', operands=(longptr_x  ,), precode=0x72, opcode=0x6A)
DecShortptrY  = create_instruction(mnemonic='dec', operands=(shortptr_y ,), precode=0x91, opcode=0x6A)


DecwX = create_instruction(mnemonic='decw', operands=(x_rw,),               opcode=0x5A)
DecwY = create_instruction(mnemonic='decw', operands=(y_rw,), precode=0x90, opcode=0x5A)


DivXA = create_instruction(mnemonic='div', operands=(x_rw, a_rw),               opcode=0x62)
DivYA = create_instruction(mnemonic='div', operands=(y_rw, a_rw), precode=0x90, opcode=0x62)


DivXY = create_instruction(mnemonic='div', operands=(x_rw, y_rw), opcode=0x65)


Nop = create_instruction(mnemonic='nop', opcode=0x9D)
