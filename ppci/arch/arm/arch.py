"""
    ARM architecture definition.
"""
import io
from ...ir import i8, i32, ptr
from ...binutils.assembler import BaseAssembler
from ..arch import Architecture, Label, Alignment
from ..data_instructions import Db, Dd, Dcd2, data_isa
from ..registers import RegisterClass
from .registers import ArmRegister, register_range, LowArmRegister, RegisterSet
from .registers import R0, R1, R2, R3, R4, all_registers
from .registers import R5, R6, R7, R8
from .registers import R9, R10, R11, LR, PC, SP
from .arm_instructions import LdrPseudo, arm_isa
from .thumb_instructions import thumb_isa
from . import thumb_instructions
from . import arm_instructions


class ArmArch(Architecture):
    """ Arm machine class. """
    name = 'arm'
    option_names = ('thumb', 'jazelle', 'neon', 'vfpv1', 'vfpv2')

    def __init__(self, options=None):
        super().__init__(options=options, register_classes=[])
        if self.has_option('thumb'):
            self.assembler = ThumbAssembler()
            self.isa = thumb_isa + data_isa
            # We use r7 as frame pointer (in case of thumb ;)):
            self.fp = R7

            # Registers usable by register allocator:
            self.register_classes = [
                RegisterClass(
                    'loreg', [i8, i32, ptr], LowArmRegister,
                    [R0, R1, R2, R3, R4, R5, R6, R7])
                ]
        else:
            self.isa = arm_isa + data_isa
            self.assembler = ArmAssembler()
            self.fp = R11

            # Registers usable by register allocator:
            self.register_classes = [
                RegisterClass(
                    'loreg', [], LowArmRegister,
                    [R0, R1, R2, R3, R4, R5, R6, R7]),
                RegisterClass(
                    'reg', [i8, i32, ptr], ArmRegister,
                    [R0, R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11])
                ]
        self.assembler.gen_asm_parser(self.isa)
        self.registers.extend(all_registers)
        self.gdb_registers = all_registers

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
            return arm_instructions.Mov2(
                dst, src, arm_instructions.NoShift(), ismove=True)

    def make_call(self, frame, vcall):
        """ Implement actual call and save / restore live registers """
        # Now we now what variables are live:
        live_regs = frame.live_regs_over(vcall)
        register_set = set(live_regs)

        if self.has_option('thumb'):
            # Caller save registers:
            if register_set:
                yield thumb_instructions.Push(register_set)

            # Make the call:
            yield thumb_instructions.Bl(vcall.function_name)
            # R0 is filled with return value, do not save it, it will conflict.

            # Restore caller save registers:
            if register_set:
                yield thumb_instructions.Pop(register_set)
        else:
            # Caller save registers:
            if register_set:
                yield arm_instructions.Push(RegisterSet(register_set))

            yield arm_instructions.Bl(vcall.function_name)

            # Restore caller save registers:
            if register_set:
                yield arm_instructions.Pop(RegisterSet(register_set))

    def gen_prologue(self, frame):
        """ Returns prologue instruction sequence """
        # Label indication function:
        yield Label(frame.name)

        if self.has_option('thumb'):
            yield thumb_instructions.Push({LR, R7})
        else:
            yield arm_instructions.Push(RegisterSet({LR, R11}))

        # Callee save registers:
        if self.has_option('thumb'):
            yield thumb_instructions.Push({R5, R6})
        else:
            yield arm_instructions.Push(RegisterSet({R5, R6, R7, R8, R9, R10}))

        if frame.stacksize:
            if self.has_option('thumb'):
                ssize = round_up(frame.stacksize)

                # Reserve stack space:
                # subSp cannot handle large numbers:
                while ssize > 0:
                    inc = min(124, ssize)
                    yield thumb_instructions.SubSp(inc)
                    ssize -= inc
            else:
                yield arm_instructions.Sub2(SP, SP, frame.stacksize)

        # Setup frame pointer:
        if self.has_option('thumb'):
            yield thumb_instructions.Mov2(R7, SP)
        else:
            yield arm_instructions.Mov2(R11, SP, arm_instructions.NoShift())

    def gen_epilogue(self, frame):
        """ Return epilogue sequence for a frame.

        Adjust frame pointer and add constant pool. """

        if frame.stacksize > 0:
            if self.has_option('thumb'):
                ssize = round_up(frame.stacksize)
                # subSp cannot handle large numbers:
                while ssize > 0:
                    inc = min(124, ssize)
                    yield thumb_instructions.AddSp(inc)
                    ssize -= inc
            else:
                yield arm_instructions.Add2(SP, SP, frame.stacksize)

        # Callee save registers:
        if self.has_option('thumb'):
            yield thumb_instructions.Pop({R5, R6})
            yield thumb_instructions.Pop({PC, R7})
        else:
            yield arm_instructions.Pop(RegisterSet({R5, R6, R7, R8, R9, R10}))
            yield arm_instructions.Pop(
                RegisterSet({PC, R11}), extra_uses=[frame.rv])

        # Add final literal pool
        for instruction in self.litpool(frame):
            yield instruction

        if not self.has_option('thumb'):
            yield Alignment(4)   # Align at 4 bytes

    def litpool(self, frame):
        """ Generate instruction for the current literals """
        # Align at 4 bytes
        if frame.constants:
            yield Alignment(4)

        # Add constant literals:
        while frame.constants:
            label, value = frame.constants.pop(0)
            yield Label(label)
            if isinstance(value, int):
                yield Dd(value)
            elif isinstance(value, str):
                yield Dcd2(value)
            elif isinstance(value, bytes):
                for byte in value:
                    yield Db(byte)
                yield Alignment(4)   # Align at 4 bytes
            else:  # pragma: no cover
                raise NotImplementedError('Constant of type {}'.format(value))

    def between_blocks(self, frame):
        for instruction in self.litpool(frame):
            yield instruction

    def gen_fill_arguments(self, arg_types, args, alives):
        # Setup parameters:
        arg_locs, _ = self.determine_arg_locations(arg_types)
        for arg_loc, arg in zip(arg_locs, args):
            if isinstance(arg_loc, ArmRegister):
                yield self.move(arg_loc, arg)
                alives.add(arg_loc)
            else:  # pragma: no cover
                raise NotImplementedError('Parameters in memory not impl')

    def determine_arg_locations(self, arg_types):
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

        return l, tuple(live_in)

    def determine_rv_location(self, ret_type):
        live_out = set()
        rv = R0
        live_out.add(rv)
        return rv, tuple(live_out)


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
        reg_nt = '$reg_cls_armregister$'
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
            'reg_or_range', [reg_nt], lambda rhs: RegisterSet([rhs[0]]))
        self.add_rule(
            'reg_or_range',
            [reg_nt, '-', reg_nt],
            lambda rhs: RegisterSet(register_range(rhs[0], rhs[2])))

        # Ldr pseudo instruction:
        # TODO: fix the add_literal other way:
        self.add_rule(
            'instruction',
            ['ldr', reg_nt, ',', '=', 'ID'],
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
        reg_nt = '$reg_cls_armregister$'
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

        self.add_rule('reg_or_range', [reg_nt], lambda rhs: set([rhs[0]]))
        self.add_rule(
            'reg_or_range',
            [reg_nt, '-', reg_nt], lambda rhs: register_range(rhs[0], rhs[2]))


def round_up(s):
    return s + (4 - s % 4)


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
