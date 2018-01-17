from ... import ir
from ...binutils.assembler import BaseAssembler
from ..arch import Architecture
from ..arch_info import ArchInfo, TypeInfo
from .registers import A, X, Y
from . import registers
from .instructions import stm8_isa


class Stm8Arch(Architecture):
    ''' STM8 architecture description. '''
    name = 'stm8'
    option_names = ('coolcc',)

    def __init__(self, options=None):
        super().__init__(options=options)
        self.isa = stm8_isa
        self.assembler = BaseAssembler()
        self.assembler.gen_asm_parser(self.isa)
        self.fp = registers.vrw4

        self.info = ArchInfo(
            type_infos={
                ir.i8: TypeInfo(1, 1), ir.u8: TypeInfo(1, 1),
                ir.i16: TypeInfo(2, 2), ir.u16: TypeInfo(2, 2),
                'int': ir.i16, 'ptr': ir.u16
            }, register_classes=registers.register_classes)

    def gen_prologue(self, frame):
        raise NotImplementedError()

    def gen_epilogue(self, frame):
        raise NotImplementedError()

    def gen_call(self, frame, label, args, rv):
        raise NotImplementedError()

    def gen_function_enter(self, args):
        raise NotImplementedError()

    def gen_function_exit(self, rv):
        raise NotImplementedError()

    def determine_arg_locations(self, arg_types):
        ''' Calling convention in priority order:

        - Pointers in index registers;
        - 16-bit variables in index registers;
        - 8-bit variables in accumulator register first, afterwards in index
          registers.

        '''
        location = []
        live_in = set()

        if self.has_option('coolcc'):
            # Better calling convention using more resisters

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
        else:
            # IAR-style calling convention:
            v8_registers = [
                registers.vrb8, registers.vrb9,
                registers.vrb10, registers.vrb11]
            v16_registers = [
                registers.vrw0, registers.vrw1,
                registers.vrw2, registers.vrw3]

            for arg_type in arg_types:
                if arg_type in (ir.ptr, ir.i16, ir.u16):
                    register = v16_registers.pop()
                elif arg_type in (ir.i8, ir.u8):
                    register = v8_registers.pop()
                else:
                    raise NotImplementedError(
                        'Argument type {} not implemented'.format(arg_type))
                location.append(register)
                live_in.add(register)

        return location, tuple(live_in)

    def determine_rv_location(self, ret_type):
        live_out = set()
        if ret_type in (ir.i8, ir.u8):
            location = registers.vrb0
        elif ret_type in (ir.ptr, ir.i16, ir.u16):
            location = registers.vrw0
        else:
            raise NotImplementedError(
                'Return type {} not implemented'.format(ret_type))
        live_out.add(location)
        return location, tuple(live_out)
