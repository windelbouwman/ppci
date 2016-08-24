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


def create_instruction(mnemonic,
                       opcode,
                       destination=None,
                       read=False,
                       write=False,
                       immidiate=None,
                       address=None,
                       pointer=None,
                       index=None,
                       bit=False,
                       branch=False,
                       precode=None):
    assert(isinstance(mnemonic, str))
    assert(opcode in range(0x00, 0xFF))
    assert(not (immidiate and (address or pointer)))
    assert(not (address and pointer))

    argument_type = immidiate if immidiate else address if address else pointer

    destination = get_register_argument('destination', destination, read,      write)
    argument    =     register_argument('argument',    int) if argument_type else None
    position    =     register_argument('position',    int) if bit else None
    label       =     register_argument('label',       str) if branch else None
    index       = get_register_argument('index',       index,       read=True, write=False)

    syntax  = [mnemonic]
    syntax += [' '] if destination or argument_type or index else []
    syntax += [destination] if destination else []
    syntax += [','] if destination and (argument_type or index) else []
    syntax += ['('] if index else []
    syntax += ['#'] if immidiate else []
    syntax += ['['] if pointer else []
    syntax += [argument] if argument_type else []
    syntax += [']'] if pointer else []
    syntax += [','] if argument_type and index else []
    syntax += [index] if index else []
    syntax += [')'] if index else []
    syntax += [','] if bit else []
    syntax += ['#'] if bit else []
    syntax += [position] if bit else []
    syntax += [','] if branch else []
    syntax += [label] if branch else []

    argument_token = {'byte':Stm8ByteToken, 'long':Stm8WordToken, 'short':Stm8ByteToken, 'word':Stm8WordToken}
    tokens  = [Stm8PrecodeToken] if precode else []
    tokens += [Stm8OpcodeToken]
    tokens += [argument_token[argument_type]] if argument_type else []
    tokens += [Stm8ByteToken] if branch else []

    argument_pattern = {'byte':'byte', 'long':'word', 'short':'byte', 'word':'word'}
    patterns  = [FixedPattern('precode', precode)] if precode else []
    patterns += [FixedPattern('opcode', opcode)]
    patterns += [VariablePattern('position', position)] if bit else []
    patterns += [VariablePattern(argument_pattern[argument_type], argument)] if argument_type else []

    return type(mnemonic.title(), (Stm8Instruction,), {'destination': destination,
                                                       'argument'   : argument,
                                                       'index'      : index,
                                                       'position'   : position,
                                                       'label'      : label,
                                                       'syntax'     : Syntax(syntax),
                                                       'tokens'     : tokens,
                                                       'patterns'   : patterns})



AdcAByte       = create_instruction(mnemonic='adc', destination='A', read=True, write=True, immidiate='byte',                         opcode=0xA9)
# TODO: AdcAShortmem
AdcALongmem    = create_instruction(mnemonic='adc', destination='A', read=True, write=True, address='long',                           opcode=0xC9)
AdcAX          = create_instruction(mnemonic='adc', destination='A', read=True, write=True,                  index='X',               opcode=0xF9)
# TODO: AdcAShortoffX
AdcALongoffX   = create_instruction(mnemonic='adc', destination='A', read=True, write=True, address='long',  index='X',               opcode=0xD9)
AdcAY          = create_instruction(mnemonic='adc', destination='A', read=True, write=True,                  index='Y', precode=0x90, opcode=0xF9)
# TODO: AdcAShortoffY
AdcALongoffY   = create_instruction(mnemonic='adc', destination='A', read=True, write=True, address='long',  index='Y', precode=0x90, opcode=0xD9)
AdcAShortoffSP = create_instruction(mnemonic='adc', destination='A', read=True, write=True, address='short', index='SP',              opcode=0x19)
# TODO: AdcAShortptr
AdcALongptr    = create_instruction(mnemonic='adc', destination='A', read=True, write=True, pointer='long',             precode=0x72, opcode=0xC9)
# TODO: AdcAShortptrX
AdcALongptrX   = create_instruction(mnemonic='adc', destination='A', read=True, write=True, pointer='long',  index='X', precode=0x72, opcode=0xD9)
AdcAShortptrY  = create_instruction(mnemonic='adc', destination='A', read=True, write=True, pointer='short', index='Y', precode=0x91, opcode=0xD9)


AddAByte       = create_instruction(mnemonic='add', destination='A', read=True, write=True, immidiate='byte',                         opcode=0xAB)
# TODO: AddAShortmem
AddALongmem    = create_instruction(mnemonic='add', destination='A', read=True, write=True, address='long',                           opcode=0xCB)
AddAX          = create_instruction(mnemonic='add', destination='A', read=True, write=True,                  index='X',               opcode=0xFB)
# TODO: AddAShortoffX
AddALongoffX   = create_instruction(mnemonic='add', destination='A', read=True, write=True, address='long',  index='X',               opcode=0xDB)
AddAY          = create_instruction(mnemonic='add', destination='A', read=True, write=True,                  index='Y', precode=0x90, opcode=0xFB)
# TODO: AddAShortoffY
AddALongoffY   = create_instruction(mnemonic='add', destination='A', read=True, write=True, address='long',  index='Y', precode=0x90, opcode=0xDB)
AddAShortoffSP = create_instruction(mnemonic='add', destination='A', read=True, write=True, address='short', index='SP',              opcode=0x1B)
# TODO: AddAShortptr
AddALongptr    = create_instruction(mnemonic='add', destination='A', read=True, write=True, pointer='long',             precode=0x72, opcode=0xCB)
# TODO: AddAShortptrX
AddALongptrX   = create_instruction(mnemonic='add', destination='A', read=True, write=True, pointer='long',  index='X', precode=0x72, opcode=0xDB)
AddAShortptrY  = create_instruction(mnemonic='add', destination='A', read=True, write=True, pointer='short', index='Y', precode=0x91, opcode=0xDB)


AddwXWord       = create_instruction(mnemonic='addw', destination='X',  read=True, write=True, immidiate='word',                          opcode=0x1C)
AddwXLongmem    = create_instruction(mnemonic='addw', destination='X',  read=True, write=True, address='long',              precode=0x72, opcode=0xBB)
AddwXShortoffSp = create_instruction(mnemonic='addw', destination='X',  read=True, write=True, address='short', index='SP', precode=0x72, opcode=0xFB)
AddwYWord       = create_instruction(mnemonic='addw', destination='Y',  read=True, write=True, immidiate='word',            precode=0x72, opcode=0xA9)
AddwXLongmem    = create_instruction(mnemonic='addw', destination='Y',  read=True, write=True, address='long',              precode=0x72, opcode=0xB9)
AddwXShortoffSp = create_instruction(mnemonic='addw', destination='Y',  read=True, write=True, address='short', index='SP', precode=0x72, opcode=0xF9)
AddwSpByte      = create_instruction(mnemonic='addw', destination='SP', read=True, write=True, immidiate='byte',                          opcode=0x5B)


AndAByte       = create_instruction(mnemonic='and', destination='A', read=True, write=True, immidiate='byte',                         opcode=0xA4)
# TODO: AndAShortmem
AndALongmem    = create_instruction(mnemonic='and', destination='A', read=True, write=True, address='long',                           opcode=0xC4)
AndAX          = create_instruction(mnemonic='and', destination='A', read=True, write=True,                  index='X',               opcode=0xF4)
# TODO: AndAShortoffX
AndALongoffX   = create_instruction(mnemonic='and', destination='A', read=True, write=True, address='long',  index='X',               opcode=0xD4)
AndAY          = create_instruction(mnemonic='and', destination='A', read=True, write=True,                  index='Y', precode=0x90, opcode=0xF4)
# TODO: AndAShortoffY
AndALongoffY   = create_instruction(mnemonic='and', destination='A', read=True, write=True, address='long',  index='Y', precode=0x90, opcode=0xD4)
AndAShortoffSP = create_instruction(mnemonic='and', destination='A', read=True, write=True, address='short', index='SP',              opcode=0x14)
# TODO: AndAShortptr
AndALongptr    = create_instruction(mnemonic='and', destination='A', read=True, write=True, pointer='long',             precode=0x72, opcode=0xC4)
# TODO: AndAShortptrX
AndALongptrX   = create_instruction(mnemonic='and', destination='A', read=True, write=True, pointer='long',  index='X', precode=0x72, opcode=0xD4)
AndAShortptrY  = create_instruction(mnemonic='and', destination='A', read=True, write=True, pointer='short', index='Y', precode=0x91, opcode=0xD4)


#Bccm = create_bit_instruction(mnemonic='bccm', address='long', precode=0x90, opcode=0x11)
Bccm = create_instruction(mnemonic='bccm', address='long', bit=True, precode=0x90, opcode=0x11)


BcpAByte       = create_instruction(mnemonic='bcp', destination='A', read=True, immidiate='byte',                         opcode=0xA5)
# TODO: BcpAShortmem
BcpALongmem    = create_instruction(mnemonic='bcp', destination='A', read=True, address='long',                           opcode=0xC5)
BcpAX          = create_instruction(mnemonic='bcp', destination='A', read=True,                  index='X',               opcode=0xF5)
# TODO: BcpAShortoffX
BcpALongoffX   = create_instruction(mnemonic='bcp', destination='A', read=True, address='long',  index='X',               opcode=0xD5)
BcpAY          = create_instruction(mnemonic='bcp', destination='A', read=True,                  index='Y', precode=0x90, opcode=0xF5)
# TODO: BcpAShortoffY
BcpALongoffY   = create_instruction(mnemonic='bcp', destination='A', read=True, address='long',  index='Y', precode=0x90, opcode=0xD5)
BcpAShortoffSP = create_instruction(mnemonic='bcp', destination='A', read=True, address='short', index='SP',              opcode=0x15)
# TODO: BcpAShortptr
BcpALongptr    = create_instruction(mnemonic='bcp', destination='A', read=True, pointer='long',             precode=0x72, opcode=0xC5)
# TODO: BcpAShortptrX
BcpALongptrX   = create_instruction(mnemonic='bcp', destination='A', read=True, pointer='long',  index='X', precode=0x72, opcode=0xD5)
BcpAShortptrY  = create_instruction(mnemonic='bcp', destination='A', read=True, pointer='short', index='Y', precode=0x91, opcode=0xD5)


Bcpl = create_instruction(mnemonic='bcpl', address='long', bit=True, precode=0x90, opcode=0x10)


Break = create_instruction(mnemonic='break', opcode=0x8B)


Bres = create_instruction(mnemonic='bres', address='long', bit=True, precode=0x72, opcode=0x11)


Bset = create_instruction(mnemonic='bset', address='long', bit=True, precode=0x72, opcode=0x10)


Btjf = create_instruction(mnemonic='btjf', address='long', bit=True, branch=True, precode=0x72, opcode=0x01)


Btjt = create_instruction(mnemonic='btjt', address='long', bit=True, branch=True, precode=0x72, opcode=0x00)


CallLongmem   = create_instruction(mnemonic='call', address='long',                           opcode=0xCD)
CallX         = create_instruction(mnemonic='call',                  index='X',               opcode=0xFD)
# TODO: CallShortoffX
CallLongoffX  = create_instruction(mnemonic='call', address='long',  index='X',               opcode=0xDD)
CallY         = create_instruction(mnemonic='call',                  index='Y', precode=0x90, opcode=0xFD)
# TODO: CallShortoffY
CallLongoffY  = create_instruction(mnemonic='call', address='long',  index='Y', precode=0x90, opcode=0xDD)
# TODO: CallShortptr
CallLongptr   = create_instruction(mnemonic='call', pointer='long',             precode=0x72, opcode=0xCD)
# TODO: CallShortptrX
CallLongptrX  = create_instruction(mnemonic='call', pointer='long',  index='X', precode=0x72, opcode=0xDD)
CallShortptrY = create_instruction(mnemonic='call', pointer='short', index='Y', precode=0x91, opcode=0xDD)


Callr = create_instruction(mnemonic='callr', address='short', opcode=0xAD) # Truely this is an relative instruction, but the ST assembly syntax is like an direct addressing instruction.


Ccf = create_instruction(mnemonic='ccf', opcode=0x8C)


ClrA          = create_instruction(mnemonic='clr', destination='A', write=True,               opcode=0x4F)
# TODO: ClrShortmem
ClrLongmem    = create_instruction(mnemonic='clr', address='long',              precode=0x72, opcode=0x5F)
ClrX          = create_instruction(mnemonic='clr',                  index='X',                opcode=0x7F)
# TODO: ClrShortoffX
ClrLongoffX   = create_instruction(mnemonic='clr', address='long',  index='X',  precode=0x72, opcode=0x4F)
ClrY          = create_instruction(mnemonic='clr',                  index='Y',  precode=0x90, opcode=0x7F)
# TODO: ClrShortoffY
ClrLongoffY   = create_instruction(mnemonic='clr', address='long',  index='Y',  precode=0x90, opcode=0x4F)
ClrShortoffSP = create_instruction(mnemonic='clr', address='short', index='SP',               opcode=0x0F)
# TODO: ClrShortptr
ClrLongptr    = create_instruction(mnemonic='clr', pointer='long',              precode=0x72, opcode=0x3F)
# TODO: ClrShortptrX
ClrLongptrX   = create_instruction(mnemonic='clr', pointer='long',  index='X',  precode=0x72, opcode=0x6F)
ClrShortptrY  = create_instruction(mnemonic='clr', pointer='short', index='Y',  precode=0x91, opcode=0x6F)


ClrwX = create_instruction(mnemonic='clrw', destination='X', write=True,               opcode=0x5F)
ClrwY = create_instruction(mnemonic='clrw', destination='Y', write=True, precode=0x90, opcode=0x5F)


CpAByte       = create_instruction(mnemonic='cp', destination='A', read=True, immidiate='byte',                         opcode=0xA1)
# TODO: CpAShortmem
CpALongmem    = create_instruction(mnemonic='cp', destination='A', read=True, address='long',                           opcode=0xC1)
CpAX          = create_instruction(mnemonic='cp', destination='A', read=True,                  index='X',               opcode=0xF1)
# TODO: CpAShortoffX
CpALongoffX   = create_instruction(mnemonic='cp', destination='A', read=True, address='long',  index='X',               opcode=0xD1)
CpAY          = create_instruction(mnemonic='cp', destination='A', read=True,                  index='Y', precode=0x90, opcode=0xF1)
# TODO: CpAShortoffY
CpALongoffY   = create_instruction(mnemonic='cp', destination='A', read=True, address='long',  index='Y', precode=0x90, opcode=0xD1)
CpAShortoffSP = create_instruction(mnemonic='cp', destination='A', read=True, address='short', index='SP',              opcode=0x11)
# TODO: CpAShortptr
CpALongptr    = create_instruction(mnemonic='cp', destination='A', read=True, pointer='long',             precode=0x72, opcode=0xC1)
# TODO: CpAShortptrX
CpALongptrX   = create_instruction(mnemonic='cp', destination='A', read=True, pointer='long',  index='X', precode=0x72, opcode=0xD1)
CpAShortptrY  = create_instruction(mnemonic='cp', destination='A', read=True, pointer='short', index='Y', precode=0x91, opcode=0xD1)


CpwXWord       = create_instruction(mnemonic='cpw', destination='X', read=True, immidiate='word',                         opcode=0xA3)
# TODO: CpwXShortmem
CpwXLongmem    = create_instruction(mnemonic='cpw', destination='X', read=True, address='long',                           opcode=0xC3)
CpwXY          = create_instruction(mnemonic='cpw', destination='X', read=True,                  index='Y', precode=0x90, opcode=0xF3)
# TODO: CpwXShortoffY
CpwXLongoffY   = create_instruction(mnemonic='cpw', destination='X', read=True, address='long',  index='Y', precode=0x90, opcode=0xD3)
CpwXShortoffSP = create_instruction(mnemonic='cpw', destination='X', read=True, address='short', index='SP',              opcode=0x13)
# TODO: CpwXShortptr
CpwXLongptr    = create_instruction(mnemonic='cpw', destination='X', read=True, pointer='long',             precode=0x72, opcode=0xC3)
CpwXShortptrY  = create_instruction(mnemonic='cpw', destination='X', read=True, pointer='short', index='Y', precode=0x91, opcode=0xD3)

CpwYWord       = create_instruction(mnemonic='cpw', destination='Y', read=True, immidiate='word',           precode=0x90, opcode=0xA3)
# TODO: CpwYShortmem
CpwYLongmem    = create_instruction(mnemonic='cpw', destination='Y', read=True, address='long',            precode=0x90, opcode=0xC3)
CpwYX          = create_instruction(mnemonic='cpw', destination='Y', read=True,                  index='X',               opcode=0xF3)
# TODO: CpwYShortoffX
CpwYLongoffX   = create_instruction(mnemonic='cpw', destination='Y', read=True, address='long',  index='X',               opcode=0xD3)
CpwYShortptr   = create_instruction(mnemonic='cpw', destination='Y', read=True, pointer='short',            precode=0x91, opcode=0xC3)
# TODO: CpwYShortptrX
CpwYLongptrX   = create_instruction(mnemonic='cpw', destination='Y', read=True, pointer='long',  index='X', precode=0x72, opcode=0xD3)


CplA          = create_instruction(mnemonic='cpl', destination='A', write=True,               opcode=0x43)
# TODO: CplShortmem
CplLongmem    = create_instruction(mnemonic='cpl', address='long',              precode=0x72, opcode=0x53)
CplX          = create_instruction(mnemonic='cpl',                  index='X',                opcode=0x73)
# TODO: CplShortoffX
CplLongoffX   = create_instruction(mnemonic='cpl', address='long',  index='X',  precode=0x72, opcode=0x43)
CplY          = create_instruction(mnemonic='cpl',                  index='Y',  precode=0x90, opcode=0x73)
# TODO: CplShortoffY
CplLongoffY   = create_instruction(mnemonic='cpl', address='long',  index='Y',  precode=0x90, opcode=0x43)
CplShortoffSP = create_instruction(mnemonic='cpl', address='short', index='SP',               opcode=0x03)
# TODO: CplShortptr
CplLongptr    = create_instruction(mnemonic='cpl', pointer='long',              precode=0x72, opcode=0x33)
# TODO: CplShortptrX
CplLongptrX   = create_instruction(mnemonic='cpl', pointer='long',  index='X',  precode=0x72, opcode=0x63)
CplShortptrY  = create_instruction(mnemonic='cpl', pointer='short', index='Y',  precode=0x91, opcode=0x63)


CplwX = create_instruction(mnemonic='cplw', destination='X', write=True,               opcode=0x53)
CplwY = create_instruction(mnemonic='cplw', destination='Y', write=True, precode=0x90, opcode=0x53)


Nop = create_instruction(mnemonic='nop', opcode=0x9D)
