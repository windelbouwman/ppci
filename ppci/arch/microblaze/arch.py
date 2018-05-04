""" The microblaze architecture """

from ... import ir
from ..arch import Architecture
from ..arch_info import ArchInfo, TypeInfo
from ..generic_instructions import Label
from ...binutils.assembler import BaseAssembler
from . import instructions
from . import registers


class MicroBlazeArch(Architecture):
    """ Microblaze architecture """
    name = 'microblaze'

    def __init__(self, options=None):
        super().__init__(options=options)
        self.info = ArchInfo(
            type_infos={
                ir.i8: TypeInfo(1, 1), ir.u8: TypeInfo(1, 1),
                ir.i16: TypeInfo(2, 2), ir.u16: TypeInfo(2, 2),
                ir.i32: TypeInfo(4, 4), ir.u32: TypeInfo(4, 4),
                'int': ir.i32, 'ptr': ir.u32, ir.ptr: ir.u32,
            },
            register_classes=registers.register_classes)
        self.isa = instructions.isa
        self.assembler = BaseAssembler()
        self.assembler.gen_asm_parser(self.isa)

    def gen_prologue(self, frame):
        """ Returns prologue instruction sequence.

        """
        # Label indication function:
        yield Label(frame.name)
        # TODO
        # Decrease stack pointer (R1)

        raise NotImplementedError()

    def gen_epilogue(self, frame):
        """ Return epilogue sequence for a frame.

        """
        raise NotImplementedError()

    def gen_function_enter(self, args):
        raise NotImplementedError()

    def gen_function_exit(self, rv):
        raise NotImplementedError()

    def gen_call(self, frame, label, args, rv):
        raise NotImplementedError()

    def determine_arg_locations(self, arg_types):
        raise NotImplementedError()

    def determine_rv_location(self, ret_type):
        raise NotImplementedError()
