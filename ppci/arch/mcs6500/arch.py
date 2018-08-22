from ... import ir
from ..arch import Architecture
from ..arch_info import ArchInfo, TypeInfo
from ..generic_instructions import Label
from ..data_instructions import data_isa
from ...binutils.assembler import BaseAssembler
from .instructions import isa
from . import registers, instructions


class Mcs6500Arch(Architecture):
    """ 6502 architectur """
    name = 'mcs6500'

    def __init__(self, options=None):
        super().__init__(options=options)
        self.isa = isa + data_isa
        self.assembler = BaseAssembler()
        self.assembler.gen_asm_parser(self.isa)
        self.info = ArchInfo(
            type_infos={
                ir.i8: TypeInfo(1, 1), ir.u8: TypeInfo(1, 1),
                ir.i16: TypeInfo(2, 2), ir.u16: TypeInfo(2, 2),
                'int': ir.i16, 'ptr': ir.u16
            }, register_classes=registers.register_classes)

    def gen_prologue(self, frame):
        # Label indication function:
        yield Label(frame.name)

    def gen_epilogue(self, frame):
        yield instructions.Rts()

    def gen_call(self, label, args, rv):
        # Put arguments on stack?
        yield instructions.Jsr(instructions.AbsoluteLabel(label))
        # Clean stack?

    def gen_function_enter(self, args):
        # Fetch arguments from stack?
        return []

    def gen_function_exit(self, rv):
        # Put return value into place.
        return []
        raise NotImplementedError()

    def determine_arg_locations(self, arg_types):
        """ """
        # TODO: what ABI to use?

        locations = []
        live_in = set()
        for r in arg_types:
            print(r)
            locations.append(registers.A)

        return locations, tuple(live_in)

    def determine_rv_location(self, ret_type):
        live_out = set()
        rv = registers.A
        live_out.add(rv)
        return rv, tuple(live_out)
