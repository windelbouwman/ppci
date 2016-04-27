"""
    ARM architecture definition.
"""
import io
from ..arch import Architecture, Label, VCall
from ...ir import i8, i32, ptr
from ...binutils.assembler import BaseAssembler
from .registers import ArmRegister, register_range, Reg8Op, RegisterSet
from .registers import R0, R1, R2, R3, R4, all_registers, get_register
from .instructions import LdrPseudo, arm_isa
from .thumb_instructions import thumb_isa
from . import thumb_instructions
from . import instructions
from ..data_instructions import data_isa, Dcd2
from .frame import ArmFrame
from .thumb_frame import ThumbFrame


class ArmAssembler(BaseAssembler):
    """ Assembler for the arm instruction set """
    def __init__(self):
        super().__init__()
        # self.parser.assembler = self
        self.add_extra_rules()

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
        assert not self.in_macro
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
        self.lit_pool.append(Dcd2(v))
        return label_name


class ThumbAssembler(BaseAssembler):
    def __init__(self):
        super().__init__()
        self.parser.assembler = self
        self.add_extra_rules()

    def add_extra_rules(self):
        # Implement register list syntaxis:
        self.typ2nt[set] = 'reg_list'
        self.add_rule(
            'reg_list', ['{', 'reg_list_inner', '}'], lambda rhs: rhs[1])
        self.add_rule('reg_list_inner', ['reg_or_range'], lambda rhs: rhs[0])

        # For a left right parser, or right left parser, this is important:
        self.add_rule(
            'reg_list_inner',
            ['reg_list_inner', ',', 'reg_or_range'],
            lambda rhs: rhs[0] | rhs[2])
        # self.add_rule(
        # 'reg_list_inner',
        # ['reg_or_range', ',', 'reg_list_inner'], lambda rhs: rhs[0] | rhs[2])

        self.add_rule('reg_or_range', ['reg'], lambda rhs: set([rhs[0]]))
        self.add_rule(
            'reg_or_range',
            ['reg', '-', 'reg'], lambda rhs: register_range(rhs[0], rhs[2]))


class ArmArch(Architecture):
    """ Arm machine class. """
    name = 'arm'
    option_names = ('thumb', 'jazelle', 'neon', 'vfpv1', 'vfpv2')

    def __init__(self, options=None):
        super().__init__(options=options)
        if self.has_option('thumb'):
            self.assembler = ThumbAssembler()
            self.isa = thumb_isa + data_isa
            self.FrameClass = ThumbFrame
        else:
            self.isa = arm_isa + data_isa
            self.assembler = ArmAssembler()
            self.FrameClass = ArmFrame
        self.assembler.gen_asm_parser(self.isa)
        self.registers.extend(all_registers)
        self.value_classes[i32] = Reg8Op
        self.value_classes[i8] = Reg8Op
        self.value_classes[ptr] = Reg8Op

    def get_runtime(self):
        """ Implement compiler runtime functions """
        from ...api import asm
        if self.has_option('thumb'):
            asm_src = ''
        else:
            asm_src = ARM_ASM_RT
        return asm(io.StringIO(asm_src), self)

    def move(self, dst, src):
        """ Generate a move from src to dst """
        if self.has_option('thumb'):
            return thumb_instructions.Mov2(dst, src, ismove=True)
        else:
            return instructions.Mov2(
                dst, src, instructions.NoShift(), ismove=True)

    def get_register(self, color):
        return get_register(color)

    def gen_call(self, label, arg_types, ret_type, args, res_var):
        """ Generate code for call sequence. This function saves registers
            and moves arguments in the proper locations.
        """
        arg_locs, live_in, rv, live_out = \
            self.determine_arg_locations(arg_types, ret_type)

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
        # TODO: what ABI to use?
        # Perhaps follow the arm ABI spec?
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


ARM_ASM_RT = """
__sdiv:
   ; Divide r1 by r2
   ; R4 is a work register.
   ; r0 is the quotient
   mov r4, r2         ; mov divisor into temporary register.

   ; Blow up divisor until it is larger than the divident.
   cmp r4, r1, lsr 1  ; If r4 < r1, then, shift left once more.
__sdiv_inc:
   movls r4, r4, lsl 1
   cmp r4, r1, lsr 1
   bls __sdiv_inc
   mov r0, 0          ; Initialize the result
                      ; Repeatedly substract shifted divisor
__sdiv_dec:
   cmp r1, r4         ; Can we substract the current temp value?
   subcs r1, r1, r4   ; Substract temp from divisor if carry
   adc r0, r0, r0     ; double (shift left) and add carry
   mov r4, r4, lsr 1  ; Shift right one
   cmp r4, r2         ; Is temp less than divisor?
   bhs __sdiv_dec     ; If so, repeat.

   mov pc, lr         ; Return from function.
"""
