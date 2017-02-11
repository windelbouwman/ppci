from ..arch import Architecture
from ...binutils.assembler import BaseAssembler
from .instructions import isa
from . import registers


class Mcs6500Arch(Architecture):
    """ 6502 architectur """
    name = 'mcs6500'

    def __init__(self, options=None):
        super().__init__(options=options)
        self.isa = isa
        self.assembler = BaseAssembler()
        self.assembler.gen_asm_parser(isa)

    def gen_prologue(self, frame):
        pass

    def gen_epilogue(self, frame):
        pass

    def determine_arg_locations(self, arg_types):
        """ """
        # TODO: what ABI to use?

        l = []
        live_in = set()
        for r in arg_types:
            print(r)
            l.append(registers.A)

        return l, tuple(live_in)

    def determine_rv_location(self, ret_type):
        live_out = set()
        rv = registers.A
        live_out.add(rv)
        return rv, tuple(live_out)
