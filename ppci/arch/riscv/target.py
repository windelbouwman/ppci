

from ..target import Target, Label, VCall
from .instructions import LdrPseudo, isa, Mov2
from .registers import RiscvRegister
from .registers import R0, LR, SP, R3, R4, R5, R6, R7, FP, R10, R11, R12, R13, R14, R28
from ...ir import i8, i32, ptr
from ..data_instructions import data_isa
from .frame import RiscvFrame
from ...binutils.assembler import BaseAssembler
from ..riscv.registers import register_range
from .instructions import dcd, RegisterSet


class RiscvAssembler(BaseAssembler):
    def __init__(self, target):
        super().__init__(target)
        self.parser.assembler = self
        self.add_extra_rules()
        self.gen_asm_parser()

        self.lit_pool = []
        self.lit_counter = 0

    def add_extra_rules(self):
        # Implement register list syntaxis:
        self.typ2nt[RegisterSet] = 'reg_list'
        self.add_rule(
            'reg_list', ['{', 'reg_list_inner', '}'], lambda rhs: rhs[1])
        self.add_rule('reg_list_inner', ['reg_or_range'], lambda rhs: rhs[0])

        # self.add_rule(
        #    'reg_list_inner',
        #    ['reg_or_range', ',', 'reg_list_inner'],
        #    lambda rhs: RegisterSet(rhs[0] | rhs[2]))
        self.add_rule(
            'reg_list_inner',
            ['reg_list_inner', ',', 'reg_or_range'],
            lambda rhs: RegisterSet(rhs[0] | rhs[2]))

        self.add_rule(
            'reg_or_range', ['reg'], lambda rhs: RegisterSet([rhs[0]]))
        self.add_rule(
            'reg_or_range',
            ['reg', '-', 'reg'],
            lambda rhs: RegisterSet(register_range(rhs[0], rhs[2])))

        # Ldr pseudo instruction:
        # TODO: fix the add_literal other way:
        self.add_rule(
            'instruction',
            ['ldr', 'reg', ',', '=', 'ID'],
            lambda rhs: LdrPseudo(rhs[1], rhs[4].val, self.add_literal))

    def flush(self):
        if self.inMacro:
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


class RiscvTarget(Target):
    def __init__(self):
        super().__init__('riscv')
        self.isa = isa + data_isa
        self.FrameClass = RiscvFrame
        self.assembler = RiscvAssembler(self)
        self.value_classes[i8] = RiscvRegister
        self.value_classes[i32] = RiscvRegister
        self.value_classes[ptr] = RiscvRegister

    def get_runtime_src(self):
        """ Implement compiler runtime functions """
        # TODO: redesign this whole thing
        src = """
        __sdiv:
        ; Divide r10 by r11
        ; R28 is a work register.
        ; r14 is the quotient
        mov r14, 0       ; Initialize the result
        mov r28, r11      ; mov divisor into temporary register.

        ; Blow up part: blow up divisor until it is larger than the divident.
        __sdiv_inc:
        ;cmp r4, r10      ; If r4 < r1, then, shift left once more.
        blt r28 ,sp,__sdiv_lsl
        j __sdiv_dec
        __sdiv_lsl:
        slli r28, r28, 1
        j __sdiv_inc

        ; Repeatedly substract shifted versions of divisor
        __sdiv_dec:
        ;cmp sp, r4      ; Can we substract the current temp value?
        blt sp,r28,__sdiv_skip
        sub sp, sp, r28  ; Substract temp from divisor
        add r14, r14, 1   ; Add 1 to result
        __sdiv_skip:
        srli r28, r28, 1  ; Shift right one
        slli r14, r14, 1  ; Shift result left.
        __skip_check:
        ;cmp r4, sp      ; Is temp less than divisor?
        bgt  r28,sp,__sdiv_dec  ; If so, repeat.

        ;mov pc, lr      ; Return from function.
        
        jalr r0,lr,0
        """
        return src

    def move(self, dst, src):
        """ Generate a move from src to dst """
        return Mov2(dst, src, ismove=True)

    def gen_call(self, label, arg_types, ret_type, args, res_var):
        """ Generate code for call sequence. This function saves registers
            and moves arguments in the proper locations.

        """
        # TODO: what ABI to use?
        arg_locs, live_in, rv, live_out = self.determine_arg_locations(arg_types, ret_type)

        # Setup parameters:
        for arg_loc, arg in zip(arg_locs, args):
            if isinstance(arg_loc, RiscvRegister):
                yield self.move(arg_loc, arg)
            else:  # pragma: no cover
                raise NotImplementedError('Parameters in memory not impl')
        yield VCall(label, extra_uses=live_in, extra_defs=live_out)
        yield self.move(res_var, rv)

    def determine_arg_locations(self, arg_types, ret_type):
        """
            Given a set of argument types, determine location for argument
            ABI:
            pass arg1 in R10
            pass arg2 in R11
            pass arg3 in R12
            pass arg4 in R13
            return value in R14
        """
        l = []
        live_in = set()
        regs = [R10, R11, R12, R13]
        for a in arg_types:
            r = regs.pop(0)
            l.append(r)
            live_in.add(r)

        live_out = set()
        rv = R14
        live_out.add(rv)
        return l, tuple(live_in), rv, tuple(live_out)
