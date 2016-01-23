from ..target import Target, Label, VCall
from .instructions import LdrPseudo, isa, Mov2
from .registers import ArmRegister
from .registers import R0, R1, R2, R3, R4, R5, R6, R7, R8
from ...ir import i8, i32, ptr
from ..data_instructions import data_isa
from .frame import ArmFrame
from ...binutils.assembler import BaseAssembler
from ..arm.registers import register_range
from .instructions import dcd, RegisterSet


class ArmAssembler(BaseAssembler):
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


class ArmTarget(Target):
    """
        Arm machine class.
    """
    def __init__(self):
        super().__init__('arm')
        self.isa = isa + data_isa
        self.FrameClass = ArmFrame
        self.assembler = ArmAssembler(self)
        self.value_classes[i8] = ArmRegister
        self.value_classes[i32] = ArmRegister
        self.value_classes[ptr] = ArmRegister

    def get_runtime_src(self):
        """ Implement compiler runtime functions """
        # TODO: redesign this whole thing
        src = """
        __sdiv:
        ; Divide r1 by r2
        ; R4 is a work register.
        ; r0 is the quotient
        mov r0, 0       ; Initialize the result
        mov r3, 1

        mov r4, r2      ; mov divisor into temporary register.

        ; Blow up part: blow up divisor until it is larger than the divident.
        __sdiv_inc:
        cmp r4, r1      ; If r4 < r1, then, shift left once more.
        bls __sdiv_lsl
        b __sdiv_dec
        __sdiv_lsl:
        lsl r4, r4, r3
        b __sdiv_inc

        ; Repeatedly substract shifted versions of divisor
        __sdiv_dec:
        cmp r1, r4      ; Can we substract the current temp value?
        blt __sdiv_skip
        sub r1, r1, r4  ; Substract temp from divisor
        add r0, r0, 1   ; Add 1 to result
        __sdiv_skip:
        lsr r4, r4, r3  ; Shift right one
        lsl r0, r0, r3  ; Shift result left.
        __skip_check:
        cmp r4, r2      ; Is temp less than divisor?
        bgt __sdiv_dec  ; If so, repeat.

        mov pc, lr      ; Return from function.
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
            if isinstance(arg_loc, ArmRegister):
                yield self.move(arg_loc, arg)
            else:  # pragma: no cover
                raise NotImplementedError('Parameters in memory not impl')
        yield VCall(label, extra_uses=live_in, extra_defs=live_out)
        yield self.move(res_var, rv)

    def determine_arg_locations(self, arg_types, ret_type):
        """
            Given a set of argument types, determine location for argument
            ABI:
            pass arg1 in R1
            pass arg2 in R2
            pass arg3 in R3
            pass arg4 in R4
            return value in R0
        """
        l = []
        live_in = set()
        regs = [R1, R2, R3, R4]
        for a in arg_types:
            r = regs.pop(0)
            l.append(r)
            live_in.add(r)

        live_out = set()
        rv = R0
        live_out.add(rv)
        return l, tuple(live_in), rv, tuple(live_out)
