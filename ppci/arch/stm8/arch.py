from ...binutils.assembler import BaseAssembler
from ..arch import Architecture
from .registers import A, X, Y
from .instructions import stm8_isa


class Stm8Arch(Architecture):
    ''' STM8 architecture description. '''
    name = 'stm8'

    def __init__(self, options=None):
        super().__init__(options=options, register_classes=[])
        self.isa = stm8_isa
        self.assembler = BaseAssembler()
        self.assembler.gen_asm_parser(self.isa)
        self.byte_sizes['ptr'] = 2
        self.byte_sizes['int'] = 2
        self.byte_sizes['i16'] = 2
        self.byte_sizes['u16'] = 2
        self.byte_sizes['i8'] = 1
        self.byte_sizes['u8'] = 1

    def determine_arg_locations(self, arg_types):
        ''' Calling convention in priority order:
        - Pointers in index registers;
        - 16-bit variables in index registers;
        - 8-bit variables in accumulator register first, afterwards in index
          registers.
        '''
        location = []
        live_in = set()
        accumulator_registers = [A]
        index_registers = [X, Y]

        # First check for pointers.
        for i in range(len(arg_types)):
            if arg_types[i].name in ('ptr'):
                if len(index_registers):
                    register = index_registers.pop()
                    location[i] = register
                    live_in[i] = register

        # Then check for 16-bit variables.
        for i in range(len(arg_types)):
            if arg_types[i].name in ('int', 'i16', 'u16'):
                if len(index_registers):
                    register = index_registers.pop()
                    location[i] = register
                    live_in[i] = register

        # Afterwards check for 8-bit variables.
        for i in range(len(arg_types)):
            if arg_types[i].name in ('i8', 'u8'):
                if len(accumulator_registers) or len(index_registers):
                    if len(accumulator_registers):
                        register = accumulator_registers.pop()
                    elif len(index_registers):
                        register = index_registers.pop()
                    location[i] = register
                    live_in[i] = register

        # Check for not implemented argument types.
        for arg_type in arg_types:
            if arg_type not in ('ptr', 'int', 'i16', 'u16', 'i8', 'u8'):
                raise NotImplementedError(
                    'Argument type {} not implemented'.format(arg_type))

        return location, tuple(live_in)

    def determine_rv_location(self, ret_type):
        live_out = set()
        if ret_type in ('i8', 'u8'):
            location = A
        elif ret_type in ('ptr', 'int', 'i16', 'u16'):
            location = X
        else:
            raise NotImplementedError(
                'Return type {} not implemented'.format(ret_type))
        live_out.add(location)
        return location, tuple(live_out)
