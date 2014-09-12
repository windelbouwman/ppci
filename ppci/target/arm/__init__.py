
from ..basetarget import Target, Label
from .instructions import LdrPseudo
from .selector import ArmInstructionSelector
from .frame import ArmFrame
from ...assembler import BaseAssembler, AsmLexer
from .parser import Parser

from ..arm.registers import R0, R1, R2, R3, R4, R5, R6, R7
from ..arm.registers import R8, R9, R10, R11, R12, SP, LR, PC
from ..arm.registers import register_range

from .instructions import Dcd, Mov, Mov1, Add, Add2, Sub, Orr1, Mul, Mov2
from .instructions import Add1, Mul1
from .instructions import Lsr1, Lsl1, And1, Sub1
from .instructions import B, Bl, Ble, Bgt, Beq, Blt, Cmp, Cmp2
from .instructions import Push, Pop, Str, Ldr, Ldr3, Str1, Ldr1, Adr
from .instructions import Mcr, Mrc
from .relocations import reloc_map


class ArmAssembler(BaseAssembler):
    def __init__(self, target):
        super().__init__(target)

        kws = [
                "repeat", "endrepeat", "section",
                "r0", "r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8", "r9", "r10", "r11", "r12", "sp", "lr", "pc",
                "dcd",
                "nop", "mov", "cmp", "add", "sub", "mul",
                "lsl", "lsr", "orr", "and",
                "push", "pop", "b", "bl", "blt", "ble", "bgt", "beq",
                "ldr", "str", "adr",
                "c0", "c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8", "c9", "c10", "c11", "c12", "c13", "c14", "c15",
                "p8", "p9", "p10", "p11", "p12", "p13", "p14", "p15",
                "mcr", "mrc"
              ]
        self.lexer = AsmLexer(kws)
        self.parser = Parser()
        self.parser.assembler = self
        # self.parser = Parser(self.target.asm_keywords, self.target.assembler_rules, self.emit)

        self.lit_pool = []
        self.lit_counter = 0
        self.inMacro = False

    def prepare(self):
        self.inMacro = False

    def begin_repeat(self, count):
        assert not self.inMacro
        self.inMacro = True
        self.rep_count = count
        self.recording = []

    def end_repeat(self):
        assert self.inMacro
        self.inMacro = False
        for rec in self.recording * self.rep_count:
            self.emit(*rec)

    def emit(self, *args):
        if self.inMacro:
            self.recording.append(args)
        else:
            super().emit(*args)

    def select_section(self, name):
        self.flush()
        self.stream.select_section(name)

    def flush(self):
        if self.inMacro:
            raise Exception()
        while self.lit_pool:
            i = self.lit_pool.pop(0)
            self.emit(i)

    def add_literal(self, v):
        """ For use in the pseudo instruction LDR r0, =SOMESYM """
        # Invent some label for the literal and store it.
        self.lit_counter += 1
        label_name = "_lit_{}".format(self.lit_counter)
        self.lit_pool.append(Label(label_name))
        self.lit_pool.append(Dcd(v))
        return label_name


class ArmTarget(Target):
    def __init__(self):
        super().__init__('arm')
        self.ins_sel = ArmInstructionSelector()
        self.FrameClass = ArmFrame
        self.assembler = ArmAssembler(self)

        self.add_lowering(Ldr3, lambda im: Ldr3(im.dst[0], im.others[0]))
        self.add_lowering(Str1, lambda im: Str1(im.src[1], im.src[0], im.others[0]))
        self.add_lowering(Ldr1, lambda im: Ldr1(im.dst[0], im.src[0], im.others[0]))
        self.add_lowering(Adr, lambda im: Adr(im.dst[0], im.others[0]))
        self.add_lowering(Mov2, lambda im: Mov2(im.dst[0], im.src[0]))
        self.add_lowering(Cmp2, lambda im: Cmp2(im.src[0], im.src[1]))
        self.add_lowering(Add1, lambda im: Add1(im.dst[0], im.src[0], im.src[1]))
        self.add_lowering(Add2, lambda im: Add2(im.dst[0], im.src[0], im.others[0]))
        self.add_lowering(Sub1, lambda im: Sub1(im.dst[0], im.src[0], im.src[1]))
        self.add_lowering(Mul1, lambda im: Mul1(im.dst[0], im.src[0], im.src[1]))
        self.add_lowering(Lsr1, lambda im: Lsr1(im.dst[0], im.src[0], im.src[1]))
        self.add_lowering(And1, lambda im: And1(im.dst[0], im.src[0], im.src[1]))
        self.add_lowering(Mov1, lambda im: Mov1(im.dst[0], im.others[0]))

        self.reloc_map = reloc_map

    def emit_global(self, outs, lname):
        outs.emit(Label(lname))
        outs.emit(Dcd(0))

