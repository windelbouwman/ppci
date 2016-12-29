""" RISC-V architecture. """

import io
from ..arch import Architecture, Label, Alignment
from .instructions import isa
from .rvc_instructions import rvcisa
from .registers import RiscvRegister, gdb_registers, all_registers
from .registers import R0, LR, SP, FP
from .registers import R10, R11, R12
from .registers import R13, R14, R15, R16, R17
from .registers import PC
from .registers import R9, R18, R19
from .registers import R20, R21, R22, R23, R24, R25, R26, R27
from ... import ir
from ..registers import RegisterClass
from ..data_instructions import data_isa, Db
from ...binutils.assembler import BaseAssembler
from .instructions import dcd, Addi, Subi, Movr, Bl, Sw, Lw, Blr, Mov
from .rvc_instructions import CSwsp, CLwsp, CJal, CJr


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
            self.store = CSwsp
            self.load = CLwsp
        else:
            self.isa = isa + data_isa
            self.store = Sw
            self.load = Lw
        self.registers.extend(all_registers)
        self.gdb_registers = gdb_registers
        self.gdb_pc = PC
        self.assembler = RiscvAssembler()
        self.assembler.gen_asm_parser(self.isa)

        # Allocatable registers:
        self.register_classes = [
            RegisterClass(
                'reg', [ir.i8, ir.i32, ir.ptr, ir.u8, ir.u32], RiscvRegister,
                [R9, R10, R11, R12, R13, R14, R15, R16, R17, R18, R19, R20,
                 R21, R22, R23, R24, R25, R26, R27])
            ]
        self.fp = FP
        self.callee_save = ()
        # (LR, FP, R9, R18, R19, R20, R21 ,R22, R23 ,R24, R25, R26, R27)

    def branch(self, reg, lab):
        if self.has_option('rvc'):
            return CJal(lab)
        else:
            return Bl(reg, lab)

    def get_runtime(self):
        """ Implement compiler runtime functions """
        from ...api import asm
        asm_src = """
        __sdiv:
        ; Divide x11 by x12
        ; x13 is a work register.
        ; x10 is the quotient

        mov x10, x0     ; Initialize the result
        mov x13, 1      ; mov divisor into temporary register.

        ; Blow up part: blow up divisor until it is larger than the divident.
        __shiftl:
        bge x12, x11, __cont1
        slli x12, x12, 1
        slli x13, x13, 1
        j __shiftl

        ; Repeatedly substract shifted versions of divisor
        __cont1:
        beq x13, x0, __exit
        blt x11, x12, __skip
        sub x11, x11, x12
        or x10, x10, x13
        __skip:
        srli x12, x12, 1
        srli x13, x13, 1
        j __cont1

        __exit:
        jalr x0,ra,0
        """
        return asm(io.StringIO(asm_src), self)

    def move(self, dst, src):
        """ Generate a move from src to dst """
        return Movr(dst, src, ismove=True)

    def gen_fill_arguments(self, arg_types, args, live):
        """ This function moves arguments in the proper locations.
        """
        arg_locs, live_in = self.determine_arg_locations(arg_types)
        live.update(set(live_in))

        # Setup parameters:
        for arg_loc, arg in zip(arg_locs, args):
            if isinstance(arg_loc, RiscvRegister):
                yield self.move(arg_loc, arg)
            else:  # pragma: no cover
                raise NotImplementedError('Parameters in memory not impl')

    def make_call(self, frame, vcall):
        """ Implement actual call and save / restore live registers """
        # Now we now what variables are live:
        live_regs = frame.live_regs_over(vcall)

        # Caller save registers:
        i = (len(live_regs)+1)*4
        yield Subi(SP, SP, i)
        i -= 4
        for register in live_regs:
            yield self.store(register, i, SP)
            i -= 4
        yield self.store(LR, i, SP)

        yield self.branch(LR, vcall.function_name)

        # Restore caller save registers:
        i = 0
        yield self.load(LR, i, SP)
        for register in reversed(live_regs):
            i += 4
            yield self.load(register, i, SP)
        i += 4
        yield Addi(SP, SP, i)

    def determine_arg_locations(self, arg_types):
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
        return l, tuple(live_in)

    def determine_rv_location(self, ret_type):
        live_out = set()
        rv = R10
        live_out.add(rv)
        return rv, tuple(live_out)

    def gen_prologue(self, frame):
        """ Returns prologue instruction sequence """
        # Label indication function:
        yield Label(frame.name)
        # Callee save registers:
        i = 0
        for register in self.callee_save:
            yield Sw(register, i, SP)
            i -= 4
        Addi(SP, SP, i)
        if frame.stacksize > 0:
            ssize = round_up(frame.stacksize)
            yield Subi(SP, SP, ssize)     # Reserve stack space
        yield Mov(FP, SP)                 # Setup frame pointer

    def litpool(self, frame):
        """ Generate instruction for the current literals """
        # Align at 4 bytes
        if frame.constants:
            yield Alignment(4)

        # Add constant literals:
        while frame.constants:
            label, value = frame.constants.pop(0)
            yield Label(label)
            if isinstance(value, int) or isinstance(value, str):
                yield dcd(value)
            elif isinstance(value, bytes):
                for byte in value:
                    yield Db(byte)
                yield Alignment(4)   # Align at 4 bytes
            else:  # pragma: no cover
                raise NotImplementedError('Constant of type {}'.format(value))

    def between_blocks(self, frame):
        for ins in self.litpool(frame):
            yield ins

    def gen_epilogue(self, frame):
        """ Return epilogue sequence for a frame. Adjust frame pointer
            and add constant pool
        """
        if frame.stacksize > 0:
            ssize = round_up(frame.stacksize)
            yield Addi(SP, SP, ssize)
        # Callee saved registers:
        i = 0
        for register in reversed(self.callee_save):
            i += 4
            yield Lw(register, i, SP)
        Addi(SP, SP, i)

        if self.has_option('rvc'):
            yield(CJr(LR))
        else:
            yield(Blr(R0, LR, 0))

        # Add final literal pool:
        for instruction in self.litpool(frame):
            yield instruction
        yield Alignment(4)   # Align at 4 bytes


def round_up(s):
    return s + (4 - s % 4)
