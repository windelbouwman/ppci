
from ...binutils.assembler import BaseAssembler
from ..arch import Architecture
from .instructions import core_isa
from .registers import register_classes


class XtensaArch(Architecture):
    name = 'xtensa'

    def __init__(self, options=None):
        super().__init__(options=options, register_classes=register_classes)
        self.isa = core_isa
        self.assembler = BaseAssembler()
        self.assembler.gen_asm_parser(self.isa)
