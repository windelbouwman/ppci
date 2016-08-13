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



def generate_instruction(name,
                         inherent=None,
                         a=None,
                         a_byte=None,
                         a_shortmem=None,
                         a_longmem=None,
                         a_x=None,
                         a_shortoff_x=None,
                         a_longoff_x=None,
                         a_y=None,
                         a_shortoff_y=None,
                         a_longoff_y=None,
                         a_shortoff_sp=None,
                         a_shortptr=None,
                         a_longptr=None,
                         a_shortptr_x=None,
                         a_longptr_x=None,
                         a_shortptr_y=None):

    class_name = 'Stm8' + name.title()

    if inherent != None:
        tokens = [Stm8OpcodeToken]
        syntax = Syntax([name])
        patterns = [FixedPattern('opcode', inherent)]
        members = {'tokens': tokens, 'syntax': syntax, 'patterns': patterns}
        type(class_name, (Stm8Instruction,), members)

    if a != None:
        tokens = [Stm8OpcodeToken]
        destination = register_argument('destination', Stm8RegisterA, read=True, write=True)
        syntax = Syntax([name, destination])
        patterns = [FixedPattern('opcode', a)]
        members = {'tokens': tokens, 'destination': destination, 'syntax': syntax, 'patterns': patterns}
        type(class_name + 'A', (Stm8Instruction,), members)

    if a_byte != None:
        tokens = [Stm8OpcodeToken, Stm8ByteToken]
        destination = register_argument('destination', Stm8RegisterA, read=True, write=True)
        value = register_argument('value', int)
        syntax = Syntax([name, destination, ',', '#', value])
        patterns = [FixedPattern('opcode', a_byte), VariablePattern('byte', value)]
        members = {'tokens': tokens, 'destination': destination, 'value': value,'syntax': syntax, 'patterns': patterns}
        type(class_name + 'AByte', (Stm8Instruction,), members)

#    TODO: Enable shortmem when assembler can distinguish between short and long address size.
#    if a_shortmem != None:
#        tokens = [Stm8OpcodeToken, Stm8ByteToken]
#        destination = register_argument('destination', Stm8RegisterA, read=True, write=True)
#        address = register_argument('address', int)
#        syntax = Syntax([name, destination, ',', address])
#        patterns = [FixedPattern('opcode', a_shortmem), VariablePattern('byte', address)]
#        members = {'tokens': tokens, 'destination': destination, 'address': address,'syntax': syntax, 'patterns': patterns}
#        type(class_name + 'AShortmem', (Stm8Instruction,), members)

    if a_longmem != None:
        tokens = [Stm8OpcodeToken, Stm8WordToken]
        destination = register_argument('destination', Stm8RegisterA, read=True, write=True)
        address = register_argument('address', int)
        syntax = Syntax([name, destination, ',', address])
        patterns = [FixedPattern('opcode', a_longmem), VariablePattern('word', address)]
        members = {'tokens': tokens, 'destination': destination, 'address': address,'syntax': syntax, 'patterns': patterns}
        type(class_name + 'ALongmem', (Stm8Instruction,), members)

    if a_x != None:
        tokens = [Stm8OpcodeToken]
        destination = register_argument('destination', Stm8RegisterA, read=True, write=True)
        address = register_argument('address', Stm8RegisterX, read=True)
        syntax = Syntax([name, destination, ',', '(', address, ')'])
        patterns = [FixedPattern('opcode', a_x)]
        members = {'tokens': tokens, 'destination': destination, 'address': address, 'syntax': syntax, 'patterns': patterns}
        type(class_name + 'AX', (Stm8Instruction,), members)

    if a_longoff_x != None:
        tokens = [Stm8OpcodeToken, Stm8WordToken]
        destination = register_argument('destination', Stm8RegisterA, read=True, write=True)
        offset = register_argument('offset', int)
        address = register_argument('address', Stm8RegisterX, read=True)
        syntax = Syntax([name, destination, ',', '(', offset, ',', address, ')'])
        patterns = [FixedPattern('opcode', a_longoff_x), VariablePattern('word', offset)]
        members = {'tokens': tokens, 'destination': destination, 'offset': offset, 'address': address, 'syntax': syntax, 'patterns': patterns}
        type(class_name + 'ALongoffX', (Stm8Instruction,), members)

    if a_y != None:
        tokens = [Stm8PrecodeToken, Stm8OpcodeToken]
        destination = register_argument('destination', Stm8RegisterA, read=True, write=True)
        address = register_argument('address', Stm8RegisterY, read=True)
        syntax = Syntax([name, destination, ',', '(', address, ')'])
        patterns = [FixedPattern('precode', 0x90), FixedPattern('opcode', a_y)]
        members = {'tokens': tokens, 'destination': destination, 'address': address, 'syntax': syntax, 'patterns': patterns}
        type(class_name + 'AY', (Stm8Instruction,), members)

    if a_longoff_y != None:
        tokens = [Stm8PrecodeToken, Stm8OpcodeToken, Stm8WordToken]
        destination = register_argument('destination', Stm8RegisterA, read=True, write=True)
        offset = register_argument('offset', int)
        address = register_argument('address', Stm8RegisterY, read=True)
        syntax = Syntax([name, destination, ',', '(', offset, ',', address, ')'])
        patterns = [FixedPattern('precode', 0x90), FixedPattern('opcode', a_longoff_y), VariablePattern('word', offset)]
        members = {'tokens': tokens, 'destination': destination, 'offset': offset, 'address': address, 'syntax': syntax, 'patterns': patterns}
        type(class_name + 'ALongoffY', (Stm8Instruction,), members)

    if a_shortoff_sp != None:
        tokens = [Stm8OpcodeToken, Stm8ByteToken]
        destination = register_argument('destination', Stm8RegisterA, read=True, write=True)
        offset = register_argument('offset', int)
        address = register_argument('address', Stm8RegisterSP, read=True)
        syntax = Syntax([name, destination, ',', '(', offset, ',', address, ')'])
        patterns = [FixedPattern('opcode', a_shortoff_sp), VariablePattern('byte', offset)]
        members = {'tokens': tokens, 'destination': destination, 'offset': offset, 'address': address, 'syntax': syntax, 'patterns': patterns}
        type(class_name + 'AShortoffSP', (Stm8Instruction,), members)

    if a_longptr != None:
        tokens = [Stm8PrecodeToken, Stm8OpcodeToken, Stm8WordToken]
        destination = register_argument('destination', Stm8RegisterA, read=True, write=True)
        pointer = register_argument('pointer', int)
        syntax = Syntax([name, destination, ',', '[', pointer, ']']) # TODO: add pointer size specifier '.w'.
        patterns = [FixedPattern('precode', 0x72), FixedPattern('opcode', a_longptr), VariablePattern('word', pointer)]
        members = {'tokens': tokens, 'destination': destination, 'pointer': pointer, 'syntax': syntax, 'patterns': patterns}
        type(class_name + 'ALongptr', (Stm8Instruction,), members)

    if a_longptr_x != None:
        tokens = [Stm8PrecodeToken, Stm8OpcodeToken, Stm8WordToken]
        destination = register_argument('destination', Stm8RegisterA, read=True, write=True)
        pointer = register_argument('pointer', int)
        offset = register_argument('offset', Stm8RegisterX, read=True)
        syntax = Syntax([name, destination, ',', '(', '[', pointer, ']', ',', offset, ')']) # TODO: add pointer size specifier '.w'.
        patterns = [FixedPattern('precode', 0x72), FixedPattern('opcode', a_longptr_x), VariablePattern('word', pointer)]
        members = {'tokens': tokens, 'destination': destination, 'pointer': pointer, 'offset': offset, 'syntax': syntax, 'patterns': patterns}
        type(class_name + 'ALongptrX', (Stm8Instruction,), members)

    if a_shortptr_y != None:
        tokens = [Stm8PrecodeToken, Stm8OpcodeToken, Stm8ByteToken]
        destination = register_argument('destination', Stm8RegisterA, read=True, write=True)
        pointer = register_argument('pointer', int)
        offset = register_argument('offset', Stm8RegisterY, read=True)
        syntax = Syntax([name, destination, ',', '(', '[', pointer, ']', ',', offset, ')']) # TODO: add pointer size specifier '.w'.
        patterns = [FixedPattern('precode', 0x91), FixedPattern('opcode', a_shortptr_y), VariablePattern('byte', pointer)]
        members = {'tokens': tokens, 'destination': destination, 'pointer': pointer, 'offset': offset, 'syntax': syntax, 'patterns': patterns}
        type(class_name + 'AShortptrY', (Stm8Instruction,), members)



def generate_instructions():
    generate_instruction('adc', a_byte=0xA9, a_shortmem=0xB9, a_longmem=0xC9, a_x=0xF9, a_shortoff_x=0xE9, a_longoff_x=0xD9, a_y=0xF9, a_shortoff_y=0xE9, a_longoff_y=0xD9, a_shortoff_sp=0x19, a_shortptr=0xC9, a_longptr=0xC9, a_shortptr_x=0xD9, a_longptr_x=0xD9, a_shortptr_y=0xD9)
    generate_instruction('nop', 0x9D)



generate_instructions()
