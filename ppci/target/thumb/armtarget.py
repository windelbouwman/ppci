from ..basetarget import Register, Instruction, Target, Label, Alignment
from .instructions import Add2, Sub, Sub3, Add3, Cmp, Lsl, Lsr, Orr, Add, Cmp2, Sub2, Mul, And
from .instructions import Dcd, Pop, Push, Yield, Mov2, Mov3
from .instructions import Ldr, Str2, Ldr2, Str1, Ldr1, Ldr3, Adr

from .frame import ArmFrame
from .arminstructionselector import ArmInstructionSelector
from .relocations import reloc_map
from ...assembler import BaseAssembler, AsmLexer

from .parser import Parser

""" ARM target description. """

# TODO: encode this in DSL (domain specific language)
# TBD: is this required?
# TODO: make a difference between armv7 and armv5?


class ThumbAssembler(BaseAssembler):
    def __init__(self, target):
        super().__init__(target)
        kws = [
            "repeat", "endrepeat", "section", "align",
            "r0", "r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8", "r9",
            "r10", "r11", "r12", "sp", "lr", "pc",
            "dcd", "yield",
            "nop", "mov", "cmp", "add", "sub", "mul",
            "lsl", "lsr", "orr", "and",
            "push", "pop", "b", "bl", "blt", "ble", "bgt", "beq",
            "bne", "bge", 'bw',
            "ldr", "str", "adr"
            ]
        self.lexer = AsmLexer(kws)
        self.parser = Parser()
        self.parser.assembler = self

    def select_section(self, name):
        self.flush()
        self.stream.select_section(name)


class ThumbTarget(Target):
    def __init__(self):
        super().__init__('thumb')
        self.ins_sel = ArmInstructionSelector()
        self.FrameClass = ArmFrame

        # Add lowering options:
        self.add_lowering(Str2, lambda im: Str2(im.src[1], im.src[0], im.others[0]))
        self.add_lowering(Ldr2, lambda im: Ldr2(im.dst[0], im.src[0], im.others[0]))
        self.add_lowering(Ldr3, lambda im: Ldr3(im.dst[0],  im.others[0]))
        self.add_lowering(Adr, lambda im: Adr(im.dst[0],  im.others[0]))
        self.add_lowering(Mov3, lambda im: Mov3(im.dst[0],  im.others[0]))
        self.add_lowering(Add2, lambda im: Add2(im.dst[0], im.src[0], im.others[0]))
        self.add_lowering(Sub2, lambda im: Sub2(im.dst[0], im.src[0], im.others[0]))
        self.add_lowering(Mov2, lambda im: Mov2(im.dst[0], im.src[0]))
        self.add_lowering(Add3, lambda im: Add3(im.dst[0], im.src[0], im.src[1]))
        self.add_lowering(Sub3, lambda im: Sub3(im.dst[0], im.src[0], im.src[1]))
        self.add_lowering(Mul, lambda im: Mul(im.src[0], im.dst[0]))
        self.add_lowering(And, lambda im: And(im.src[0], im.src[1]))
        self.add_lowering(Orr, lambda im: Orr(im.src[0], im.src[1]))
        self.add_lowering(Lsl, lambda im: Lsl(im.src[0], im.src[1]))
        self.add_lowering(Lsr, lambda im: Lsr(im.src[0], im.src[1]))
        self.add_lowering(Cmp, lambda im: Cmp(im.src[0], im.src[1]))

        self.assembler = ThumbAssembler(self)
        self.reloc_map = reloc_map

    def emit_global(self, outs, lname):
        outs.emit(Label(lname))
        outs.emit(Dcd(0))

