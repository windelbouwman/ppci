"""
    RISC-V architecture.
"""

import io
from ..arch import Architecture, Label, VCall
from .instructions import isa, Mov2
from .rvc_instructions import rvcisa
from .registers import RiscvRegister
from .registers import R0, LR, SP, R3, R4, R5, R6, R7, FP, R10, R11, R12, all_registers
from .registers import R13, R14, R15, R16, R17, R28, LR, get_register
from ...ir import i8, i32, ptr
from ..data_instructions import data_isa
from .frame import RiscvFrame
from ...binutils.assembler import BaseAssembler
from ..riscv.registers import register_range
from .instructions import dcd


class RiscvAssembler(BaseAssembler):
    def __init__(self):
        super().__init__()
        self.lit_pool = []
        self.lit_counter = 0

    def flush(self):
        if self.in_macro:
            raise Exception()
        while self.lit_pool:
            i = self.lit_pool.pop(0)
            self.emit(i)

    def add_literal(self, v):
        """ For use in the pseudo instruction LDR r0, =SOMESYM """
        # Invent some label for the literal and store it.
        assert type(v) is str
        self.lit_counter += 1
        label_name = "_lit_{}".format(self.lit_counter)
        self.lit_pool.append(Label(label_name))
        self.lit_pool.append(dcd(v))
        return label_name


class RiscvArch(Architecture):
    name = 'riscv'
    option_names = ('rvc',)

    def __init__(self, options=None):
        super().__init__(options=options)
        if self.has_option('rvc'):
            self.isa = isa + rvcisa + data_isa
        else:
            self.isa = isa + data_isa
        self.registers.extend(all_registers)
        self.FrameClass = RiscvFrame
        self.assembler = RiscvAssembler()
        self.assembler.gen_asm_parser(self.isa)
        self.value_classes[i8] = RiscvRegister
        self.value_classes[i32] = RiscvRegister
        self.value_classes[ptr] = RiscvRegister

    def get_runtime(self):
        """ Implement compiler runtime functions """
        from ...api import asm
        asm_src = """
        __sdiv:
        ; Divide x11 by x12
        ; x28 is a work register.
        ; x14 is the quotient
        mov x14, 0       ; Initialize the result
        mov x28, x12      ; mov divisor into temporary register.

        ; Blow up part: blow up divisor until it is larger than the divident.
        __sdiv_inc:
        blt x28 , x11,__sdiv_lsl ; If x28 < x11, then, shift left once more.
        j __sdiv_dec
        __sdiv_lsl:
        slli x28, x28, 1
        j __sdiv_inc

        ; Repeatedly substract shifted versions of divisor
        __sdiv_dec:
        blt x11, x28, __sdiv_skip
        sub x11, x11, x28  ; Substract temp from divisor
        add x14, x14, 1   ; Add 1 to result
        __sdiv_skip:
        srai x28, x28, 1  ; Shift right one
        slli x14, x14, 1  ; Shift result left.
        __skip_check:
        bgt  x28, x12, __sdiv_dec  ; Is temp less than divisor?, if so, repeat.

        mov x10, x14
        jalr x0,ra,0
        """
        return asm(io.StringIO(asm_src), self)

    def move(self, dst, src):
        """ Generate a move from src to dst """
        return Mov2(dst, src, ismove=True)

    def gen_call(self, label, arg_types, ret_type, args, res_var):
        """ Generate code for call sequence. This function saves registers
            and moves arguments in the proper locations.

        """
        # TODO: what ABI to use?
        arg_locs, live_in, rv, live_out = self.determine_arg_locations(
            arg_types, ret_type)

        # Setup parameters:
        for arg_loc, arg in zip(arg_locs, args):
            if isinstance(arg_loc, RiscvRegister):
                yield self.move(arg_loc, arg)
            else:  # pragma: no cover
                raise NotImplementedError('Parameters in memory not impl')
        yield VCall(label, extra_uses=live_in, extra_defs=live_out)
        yield self.move(res_var, rv)

    def get_register(self, color):
        return get_register(color)

    def determine_arg_locations(self, arg_types, ret_type):
        """
            Given a set of argument types, determine location for argument
            ABI:
            pass args in R10-R17
            return values in R10
        """
        l = []
        live_in = set()
        regs = [R11, R12, R13, R14, R15, R16, R17]
        for a in arg_types:
            r = regs.pop(0)
            l.append(r)
            live_in.add(r)
        live_out = set()
        rv = R10
        live_out.add(rv)
        return l, tuple(live_in), rv, tuple(live_out)
