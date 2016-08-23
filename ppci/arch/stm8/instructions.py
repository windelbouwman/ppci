from .registers import Stm8RegisterA, Stm8RegisterX, Stm8RegisterY, Stm8RegisterSP
from ..isa import Isa
from ..encoding import FixedPattern, Instruction, register_argument, Syntax, VariablePattern
from ..token import bit, bit_range, Token



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



def get_register_argument(name, mnemonic, read, write):
    if mnemonic == 'A':
        return register_argument(name, Stm8RegisterA, read=read, write=write)
    elif mnemonic == 'X':
        return register_argument(name, Stm8RegisterX, read=read, write=write)
    elif mnemonic == 'Y':
        return register_argument(name, Stm8RegisterY, read=read, write=write)
    elif mnemonic == 'SP':
        return register_argument(name, Stm8RegisterSP, read=read, write=write)
    else:
        return None


#def create_inherent_instruction(mnemonic, opcode, destination=None, read=False, write=False):
#    destination = get_register_argument('destination', destination, read, write)
#
#    syntax = Syntax([mnemonic] + ([' ', destination] if destination else []))
#
#    tokens = [Stm8OpcodeToken]
#
#    patterns = [FixedPattern('opcode', opcode)]
#
#    members = {'destination': destination, 'syntax': syntax, 'tokens': tokens, 'patterns': patterns}
#    return type(mnemonic.title(), (Stm8Instruction,), members)


def create_immidiate_instruction(mnemonic, immidiate, opcode, destination=None, read=False, write=False, precode=None):
    immidiate_type = immidiate

    destination = get_register_argument('destination', destination, read, write)
    immidiate_argument = register_argument('immidiate', int)

    syntax = Syntax([mnemonic, ' '] + ([destination, ','] if destination else []) + ['#', immidiate_argument])

    tokens = ([Stm8PrecodeToken] if precode else []) + [Stm8OpcodeToken] + ([Stm8ByteToken] if immidiate_type == 'byte' else [Stm8WordToken] if immidiate_type == 'word' else [])

    patterns = ([FixedPattern('precode', precode)] if precode else []) + [FixedPattern('opcode', opcode)] +([VariablePattern('byte', immidiate_argument)] if immidiate_type == 'byte' else [VariablePattern('word', immidiate_argument)] if immidiate_type == 'word' else [])

    members = {'destination': destination, 'immidiate': immidiate_argument, 'syntax': syntax, 'tokens': tokens, 'patterns': patterns}
    return type(mnemonic.title(), (Stm8Instruction,), members)


def create_direct_instruction(mnemonic, opcode, destination=None, read=False, write=False, address=None, index=None, precode=None):
    address_type = address

    destination = get_register_argument('destination', destination, read, write)
    address_argument = register_argument('address', int)
    index = get_register_argument('index', index, read=True, write=False)

    syntax = Syntax([mnemonic] + ([' '] if destination or address_type or index else []) + ([destination] if destination else []) + ([','] if destination and (address_type or index) else []) + (['('] if index else []) + ([address_argument] if address_type else []) + ([','] if address_type and index else []) + ([index, ')'] if index else []))

    tokens = ([Stm8PrecodeToken] if precode else []) + [Stm8OpcodeToken] + ([Stm8ByteToken] if address_type == 'short' else [Stm8WordToken] if address_type == 'long' else [])

    patterns = ([FixedPattern('precode', precode)] if precode else []) + [FixedPattern('opcode', opcode)] +([VariablePattern('byte', address_argument)] if address_type == 'short' else [VariablePattern('word', address_argument)] if address_type == 'long' else [])

    members = {'destination': destination, 'address': address_argument, 'index': index, 'syntax': syntax, 'tokens': tokens, 'patterns': patterns}
    return type(mnemonic.title(), (Stm8Instruction,), members)


def create_indirect_instruction(mnemonic, address, opcode, destination=None, read=False, write=False, index=None, precode=None):
    address_type = address

    destination = get_register_argument('destination', destination, read, write)
    address_argument = register_argument('address', int)
    index = get_register_argument('index', index, read=True, write=False)

    syntax = Syntax([mnemonic, ' '] + ([destination] if destination else []) + ([','] if destination and (address_type or index) else []) + (['('] if index else []) + ['[', address_argument, ']'] + ([','] if index else []) + ([index, ')'] if index else []))

    tokens = ([Stm8PrecodeToken] if precode else []) + [Stm8OpcodeToken] + ([Stm8ByteToken] if address_type == 'short' else [Stm8WordToken] if address_type == 'long' else [])

    patterns = ([FixedPattern('precode', precode)] if precode else []) + [FixedPattern('opcode', opcode)] +([VariablePattern('byte', address_argument)] if address_type == 'short' else [VariablePattern('word', address_argument)] if address_type == 'long' else [])

    members = {'destination': destination, 'address': address_argument, 'index': index, 'syntax': syntax, 'tokens': tokens, 'patterns': patterns}
    return type(mnemonic.title(), (Stm8Instruction,), members)


def create_bit_instruction(mnemonic, opcode, address=None, branch=False, precode=None):
    # TODO: Relocation of branch destination.
    address_type = address

    address_argument = register_argument('address', int)
    position = register_argument('position', int)
    label = register_argument('label', str) if branch else None

    syntax = Syntax([mnemonic, ' ', address_argument, ',', '#', position] + ([',', label] if branch else []))

    tokens = ([Stm8PrecodeToken] if precode else []) + [Stm8OpcodeToken] + ([Stm8WordToken] if address_type == 'long' else []) + ([Stm8ByteToken] if branch else [])

    patterns = ([FixedPattern('precode', precode)] if precode else []) + [FixedPattern('opcode', opcode), VariablePattern('position', position)] + ([VariablePattern('word', address_argument)] if address_type == 'long' else [])

    members = {'address': address_argument, 'position': position, 'label': label, 'syntax': syntax, 'tokens': tokens, 'patterns': patterns}
    return type(mnemonic.title(), (Stm8Instruction,), members)



AdcAByte       = create_immidiate_instruction(mnemonic='adc', destination='A', read=True, write=True, immidiate='byte',                         opcode=0xA9)
# TODO: AdcAShortmem
AdcALongmem    = create_direct_instruction(   mnemonic='adc', destination='A', read=True, write=True, address='long',                           opcode=0xC9)
AdcAX          = create_direct_instruction(   mnemonic='adc', destination='A', read=True, write=True,                  index='X',               opcode=0xF9)
# TODO: AdcAShortoffX
AdcALongoffX   = create_direct_instruction(   mnemonic='adc', destination='A', read=True, write=True, address='long',  index='X',               opcode=0xD9)
AdcAY          = create_direct_instruction(   mnemonic='adc', destination='A', read=True, write=True,                  index='Y', precode=0x90, opcode=0xF9)
# TODO: AdcAShortoffY
AdcALongoffY   = create_direct_instruction(   mnemonic='adc', destination='A', read=True, write=True, address='long',  index='Y', precode=0x90, opcode=0xD9)
AdcAShortoffSP = create_direct_instruction(   mnemonic='adc', destination='A', read=True, write=True, address='short', index='SP',              opcode=0x19)
# TODO: AdcAShortptr
AdcALongptr    = create_indirect_instruction( mnemonic='adc', destination='A', read=True, write=True, address='long',             precode=0x72, opcode=0xC9)
# TODO: AdcAShortptrX
AdcALongptrX   = create_indirect_instruction( mnemonic='adc', destination='A', read=True, write=True, address='long',  index='X', precode=0x72, opcode=0xD9)
AdcAShortptrY  = create_indirect_instruction( mnemonic='adc', destination='A', read=True, write=True, address='short', index='Y', precode=0x91, opcode=0xD9)


AddAByte       = create_immidiate_instruction(mnemonic='add', destination='A', read=True, write=True, immidiate='byte',                         opcode=0xAB)
# TODO: AddAShortmem
AddALongmem    = create_direct_instruction(   mnemonic='add', destination='A', read=True, write=True, address='long',                           opcode=0xCB)
AddAX          = create_direct_instruction(   mnemonic='add', destination='A', read=True, write=True,                  index='X',               opcode=0xFB)
# TODO: AddAShortoffX
AddALongoffX   = create_direct_instruction(   mnemonic='add', destination='A', read=True, write=True, address='long',  index='X',               opcode=0xDB)
AddAY          = create_direct_instruction(   mnemonic='add', destination='A', read=True, write=True,                  index='Y', precode=0x90, opcode=0xFB)
# TODO: AddAShortoffY
AddALongoffY   = create_direct_instruction(   mnemonic='add', destination='A', read=True, write=True, address='long',  index='Y', precode=0x90, opcode=0xDB)
AddAShortoffSP = create_direct_instruction(   mnemonic='add', destination='A', read=True, write=True, address='short', index='SP',              opcode=0x1B)
# TODO: AddAShortptr
AddALongptr    = create_indirect_instruction( mnemonic='add', destination='A', read=True, write=True, address='long',             precode=0x72, opcode=0xCB)
# TODO: AddAShortptrX
AddALongptrX   = create_indirect_instruction( mnemonic='add', destination='A', read=True, write=True, address='long',  index='X', precode=0x72, opcode=0xDB)
AddAShortptrY  = create_indirect_instruction( mnemonic='add', destination='A', read=True, write=True, address='short', index='Y', precode=0x91, opcode=0xDB)


AddwXWord       = create_immidiate_instruction(mnemonic='addw', destination='X',  read=True, write=True, immidiate='word',                          opcode=0x1C)
AddwXLongmem    = create_direct_instruction(   mnemonic='addw', destination='X',  read=True, write=True, address='long',              precode=0x72, opcode=0xBB)
AddwXShortoffSp = create_direct_instruction(   mnemonic='addw', destination='X',  read=True, write=True, address='short', index='SP', precode=0x72, opcode=0xFB)
AddwYWord       = create_immidiate_instruction(mnemonic='addw', destination='Y',  read=True, write=True, immidiate='word',            precode=0x72, opcode=0xA9)
AddwXLongmem    = create_direct_instruction(   mnemonic='addw', destination='Y',  read=True, write=True, address='long',              precode=0x72, opcode=0xB9)
AddwXShortoffSp = create_direct_instruction(   mnemonic='addw', destination='Y',  read=True, write=True, address='short', index='SP', precode=0x72, opcode=0xF9)
AddwSpByte      = create_immidiate_instruction(mnemonic='addw', destination='SP', read=True, write=True, immidiate='byte',                          opcode=0x5B)


AndAByte       = create_immidiate_instruction(mnemonic='and', destination='A', read=True, write=True, immidiate='byte',                         opcode=0xA4)
# TODO: AndAShortmem
AndALongmem    = create_direct_instruction(   mnemonic='and', destination='A', read=True, write=True, address='long',                           opcode=0xC4)
AndAX          = create_direct_instruction(   mnemonic='and', destination='A', read=True, write=True,                  index='X',               opcode=0xF4)
# TODO: AndAShortoffX
AndALongoffX   = create_direct_instruction(   mnemonic='and', destination='A', read=True, write=True, address='long',  index='X',               opcode=0xD4)
AndAY          = create_direct_instruction(   mnemonic='and', destination='A', read=True, write=True,                  index='Y', precode=0x90, opcode=0xF4)
# TODO: AndAShortoffY
AndALongoffY   = create_direct_instruction(   mnemonic='and', destination='A', read=True, write=True, address='long',  index='Y', precode=0x90, opcode=0xD4)
AndAShortoffSP = create_direct_instruction(   mnemonic='and', destination='A', read=True, write=True, address='short', index='SP',              opcode=0x14)
# TODO: AndAShortptr
AndALongptr    = create_indirect_instruction( mnemonic='and', destination='A', read=True, write=True, address='long',             precode=0x72, opcode=0xC4)
# TODO: AndAShortptrX
AndALongptrX   = create_indirect_instruction( mnemonic='and', destination='A', read=True, write=True, address='long',  index='X', precode=0x72, opcode=0xD4)
AndAShortptrY  = create_indirect_instruction( mnemonic='and', destination='A', read=True, write=True, address='short', index='Y', precode=0x91, opcode=0xD4)


Bccm = create_bit_instruction(mnemonic='bccm', address='long', precode=0x90, opcode=0x11)


BcpAByte       = create_immidiate_instruction(mnemonic='bcp', destination='A', read=True, immidiate='byte',                         opcode=0xA5)
# TODO: BcpAShortmem
BcpALongmem    = create_direct_instruction(   mnemonic='bcp', destination='A', read=True, address='long',                           opcode=0xC5)
BcpAX          = create_direct_instruction(   mnemonic='bcp', destination='A', read=True,                  index='X',               opcode=0xF5)
# TODO: BcpAShortoffX
BcpALongoffX   = create_direct_instruction(   mnemonic='bcp', destination='A', read=True, address='long',  index='X',               opcode=0xD5)
BcpAY          = create_direct_instruction(   mnemonic='bcp', destination='A', read=True,                  index='Y', precode=0x90, opcode=0xF5)
# TODO: BcpAShortoffY
BcpALongoffY   = create_direct_instruction(   mnemonic='bcp', destination='A', read=True, address='long',  index='Y', precode=0x90, opcode=0xD5)
BcpAShortoffSP = create_direct_instruction(   mnemonic='bcp', destination='A', read=True, address='short', index='SP',              opcode=0x15)
# TODO: BcpAShortptr
BcpALongptr    = create_indirect_instruction( mnemonic='bcp', destination='A', read=True, address='long',             precode=0x72, opcode=0xC5)
# TODO: BcpAShortptrX
BcpALongptrX   = create_indirect_instruction( mnemonic='bcp', destination='A', read=True, address='long',  index='X', precode=0x72, opcode=0xD5)
BcpAShortptrY  = create_indirect_instruction( mnemonic='bcp', destination='A', read=True, address='short', index='Y', precode=0x91, opcode=0xD5)


Bcpl = create_bit_instruction(mnemonic='bcpl', address='long', precode=0x90, opcode=0x10)


Break = create_direct_instruction(mnemonic='break', opcode=0x8B)


Bres = create_bit_instruction(mnemonic='bres', address='long', precode=0x72, opcode=0x11)


Bset = create_bit_instruction(mnemonic='bset', address='long', precode=0x72, opcode=0x10)


Btjf = create_bit_instruction(mnemonic='btjf', address='long', branch=True, precode=0x72, opcode=0x01)


Btjt = create_bit_instruction(mnemonic='btjt', address='long', branch=True, precode=0x72, opcode=0x00)


CallLongmem   = create_direct_instruction(  mnemonic='call', address='long',                           opcode=0xCD)
CallX         = create_direct_instruction(  mnemonic='call',                  index='X',               opcode=0xFD)
# TODO: CallShortoffX
CallLongoffX  = create_direct_instruction(  mnemonic='call', address='long',  index='X',               opcode=0xDD)
CallY         = create_direct_instruction(  mnemonic='call',                  index='Y', precode=0x90, opcode=0xFD)
# TODO: CallShortoffY
CallLongoffY  = create_direct_instruction(  mnemonic='call', address='long',  index='Y', precode=0x90, opcode=0xDD)
# TODO: CallShortptr
CallLongptr   = create_indirect_instruction(mnemonic='call', address='long',             precode=0x72, opcode=0xCD)
# TODO: CallShortptrX
CallLongptrX  = create_indirect_instruction(mnemonic='call', address='long',  index='X', precode=0x72, opcode=0xDD)
CallShortptrY = create_indirect_instruction(mnemonic='call', address='short', index='Y', precode=0x91, opcode=0xDD)


Callr = create_direct_instruction(mnemonic='callr', address='short', opcode=0xAD) # Truely this is an relative instruction, but the ST assembly syntax is like an direct instruction.


Ccf = create_direct_instruction(mnemonic='ccf', opcode=0x8C)


ClrA          = create_direct_instruction(  mnemonic='clr', destination='A', write=True,               opcode=0x4F)
# TODO: ClrShortmem
ClrLongmem    = create_direct_instruction(  mnemonic='clr', address='long',              precode=0x72, opcode=0x5F)
ClrX          = create_direct_instruction(  mnemonic='clr',                  index='X',                opcode=0x7F)
# TODO: ClrShortoffX
ClrLongoffX   = create_direct_instruction(  mnemonic='clr', address='long',  index='X',  precode=0x72, opcode=0x4F)
ClrY          = create_direct_instruction(  mnemonic='clr',                  index='Y',  precode=0x90, opcode=0x7F)
# TODO: ClrShortoffY
ClrLongoffY   = create_direct_instruction(  mnemonic='clr', address='long',  index='Y',  precode=0x90, opcode=0x4F)
ClrShortoffSP = create_direct_instruction(  mnemonic='clr', address='short', index='SP',               opcode=0x0F)
# TODO: ClrShortptr
ClrLongptr    = create_indirect_instruction(mnemonic='clr', address='long',              precode=0x72, opcode=0x3F)
# TODO: ClrShortptrX
ClrLongptrX   = create_indirect_instruction(mnemonic='clr', address='long',  index='X',  precode=0x72, opcode=0x6F)
ClrShortptrY  = create_indirect_instruction(mnemonic='clr', address='short', index='Y',  precode=0x91, opcode=0x6F)


ClrwX = create_direct_instruction(mnemonic='clrw', destination='X', write=True,               opcode=0x5F)
ClrwY = create_direct_instruction(mnemonic='clrw', destination='Y', write=True, precode=0x90, opcode=0x5F)


CpAByte       = create_immidiate_instruction(mnemonic='cp', destination='A', read=True, immidiate='byte',                         opcode=0xA1)
# TODO: CpAShortmem
CpALongmem    = create_direct_instruction(   mnemonic='cp', destination='A', read=True, address='long',                           opcode=0xC1)
CpAX          = create_direct_instruction(   mnemonic='cp', destination='A', read=True,                  index='X',               opcode=0xF1)
# TODO: CpAShortoffX
CpALongoffX   = create_direct_instruction(   mnemonic='cp', destination='A', read=True, address='long',  index='X',               opcode=0xD1)
CpAY          = create_direct_instruction(   mnemonic='cp', destination='A', read=True,                  index='Y', precode=0x90, opcode=0xF1)
# TODO: CpAShortoffY
CpALongoffY   = create_direct_instruction(   mnemonic='cp', destination='A', read=True, address='long',  index='Y', precode=0x90, opcode=0xD1)
CpAShortoffSP = create_direct_instruction(   mnemonic='cp', destination='A', read=True, address='short', index='SP',              opcode=0x11)
# TODO: CpAShortptr
CpALongptr    = create_indirect_instruction( mnemonic='cp', destination='A', read=True, address='long',             precode=0x72, opcode=0xC1)
# TODO: CpAShortptrX
CpALongptrX   = create_indirect_instruction( mnemonic='cp', destination='A', read=True, address='long',  index='X', precode=0x72, opcode=0xD1)
CpAShortptrY  = create_indirect_instruction( mnemonic='cp', destination='A', read=True, address='short', index='Y', precode=0x91, opcode=0xD1)


CpwXWord       = create_immidiate_instruction(mnemonic='cpw', destination='X', read=True, immidiate='word',                         opcode=0xA3)
# TODO: CpwXShortmem
CpwXLongmem    = create_direct_instruction(   mnemonic='cpw', destination='X', read=True, address='long',                           opcode=0xC3)
CpwXY          = create_direct_instruction(   mnemonic='cpw', destination='X', read=True,                  index='Y', precode=0x90, opcode=0xF3)
# TODO: CpwXShortoffY
CpwXLongoffY   = create_direct_instruction(   mnemonic='cpw', destination='X', read=True, address='long',  index='Y', precode=0x90, opcode=0xD3)
CpwXShortoffSP = create_direct_instruction(   mnemonic='cpw', destination='X', read=True, address='short', index='SP',              opcode=0x13)
# TODO: CpwXShortptr
CpwXLongptr    = create_indirect_instruction( mnemonic='cpw', destination='X', read=True, address='long',             precode=0x72, opcode=0xC3)
CpwXShortptrY  = create_indirect_instruction( mnemonic='cpw', destination='X', read=True, address='short', index='Y', precode=0x91, opcode=0xD3)

CpwYWord       = create_immidiate_instruction(mnemonic='cpw', destination='Y', read=True, immidiate='word',           precode=0x90, opcode=0xA3)
# TODO: CpwYShortmem
CpwYLongmem    = create_direct_instruction(   mnemonic='cpw', destination='Y', read=True, address='long',            precode=0x90, opcode=0xC3)
CpwYX          = create_direct_instruction(   mnemonic='cpw', destination='Y', read=True,                  index='X',               opcode=0xF3)
# TODO: CpwYShortoffX
CpwYLongoffX   = create_direct_instruction(   mnemonic='cpw', destination='Y', read=True, address='long',  index='X',               opcode=0xD3)
CpwYShortptr   = create_indirect_instruction( mnemonic='cpw', destination='Y', read=True, address='short',            precode=0x91, opcode=0xC3)
# TODO: CpwYShortptrX
CpwYLongptrX   = create_indirect_instruction( mnemonic='cpw', destination='Y', read=True, address='long',  index='X', precode=0x72, opcode=0xD3)


CplA          = create_direct_instruction(  mnemonic='cpl', destination='A', write=True,               opcode=0x43)
# TODO: CplShortmem
CplLongmem    = create_direct_instruction(  mnemonic='cpl', address='long',              precode=0x72, opcode=0x53)
CplX          = create_direct_instruction(  mnemonic='cpl',                  index='X',                opcode=0x73)
# TODO: CplShortoffX
CplLongoffX   = create_direct_instruction(  mnemonic='cpl', address='long',  index='X',  precode=0x72, opcode=0x43)
CplY          = create_direct_instruction(  mnemonic='cpl',                  index='Y',  precode=0x90, opcode=0x73)
# TODO: CplShortoffY
CplLongoffY   = create_direct_instruction(  mnemonic='cpl', address='long',  index='Y',  precode=0x90, opcode=0x43)
CplShortoffSP = create_direct_instruction(  mnemonic='cpl', address='short', index='SP',               opcode=0x03)
# TODO: CplShortptr
CplLongptr    = create_indirect_instruction(mnemonic='cpl', address='long',              precode=0x72, opcode=0x33)
# TODO: CplShortptrX
CplLongptrX   = create_indirect_instruction(mnemonic='cpl', address='long',  index='X',  precode=0x72, opcode=0x63)
CplShortptrY  = create_indirect_instruction(mnemonic='cpl', address='short', index='Y',  precode=0x91, opcode=0x63)


CplwX = create_direct_instruction(mnemonic='cplw', destination='X', write=True,               opcode=0x53)
CplwY = create_direct_instruction(mnemonic='cplw', destination='Y', write=True, precode=0x90, opcode=0x53)


Nop = create_direct_instruction(mnemonic='nop', opcode=0x9D)
