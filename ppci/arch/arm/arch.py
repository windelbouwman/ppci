""" ARM architecture definition. """
import io
from ... import ir
from ...binutils.assembler import BaseAssembler
from ..arch import Architecture
from ..arch_info import ArchInfo, TypeInfo
from ..generic_instructions import Label, Alignment, RegisterUseDef
from ..data_instructions import Db, Dd, Dcd2, data_isa
from ..registers import RegisterClass
from ..stack import StackLocation
from .registers import ArmRegister, register_range, LowArmRegister, RegisterSet
from .registers import R0, R1, R2, R3, R4, all_registers
from .registers import R5, R6, R7, R8
from .registers import R9, R10, R11, LR, PC, SP
from .arm_instructions import LdrPseudo, arm_isa
from .thumb_instructions import thumb_isa
from . import thumb_instructions
from . import arm_instructions


class ArmCallingConvention:
    pass


class ArmArch(Architecture):
    """ Arm machine class. """
    name = 'arm'
    option_names = ('thumb', 'jazelle', 'neon', 'vfpv1', 'vfpv2')

    def __init__(self, options=None):
        super().__init__(options=options)
        if self.has_option('thumb'):
            self.assembler = ThumbAssembler()
            self.isa = thumb_isa + data_isa
            # We use r7 as frame pointer (in case of thumb ;)):
            self.fp = R7
            self.callee_save = (R5, R6)

            # Registers usable by register allocator:
            register_classes = [
                RegisterClass(
                    'loreg',
                    [ir.i8, ir.i32, ir.ptr, ir.u8, ir.u32, ir.i16, ir.u16],
                    LowArmRegister,
                    [R0, R1, R2, R3, R4, R5, R6, R7])
                ]
        else:
            self.isa = arm_isa + data_isa
            self.assembler = ArmAssembler()
            self.fp = R11
            self.callee_save = (R5, R6, R7, R8, R9, R10)

            # Registers usable by register allocator:
            register_classes = [
                RegisterClass(
                    'loreg', [], LowArmRegister,
                    [R0, R1, R2, R3, R4, R5, R6, R7]),
                RegisterClass(
                    'reg',
                    [ir.i8, ir.i32, ir.u8, ir.u32, ir.i16, ir.u16, ir.ptr],
                    ArmRegister,
                    [R0, R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11])
                ]
        self.assembler.gen_asm_parser(self.isa)
        self.gdb_registers = all_registers
        self.gdb_pc = PC

        self.info = ArchInfo(
            type_infos={
                ir.i8: TypeInfo(1, 1), ir.u8: TypeInfo(1, 1),
                ir.i16: TypeInfo(2, 2), ir.u16: TypeInfo(2, 2),
                ir.i32: TypeInfo(4, 4), ir.u32: TypeInfo(4, 4),
                'int': ir.i32, 'ptr': ir.u32, ir.ptr: ir.u32,
            },
            register_classes=register_classes)

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

    def gen_prologue(self, frame):
        """ Returns prologue instruction sequence.

        Reserve stack for this calling frame for:

          - local variables
          - save registers
          - parameters to called functions
        """
        # Label indication function:
        yield Label(frame.name)

        # Save the link register and the frame pointer:
        if self.has_option('thumb'):
            yield thumb_instructions.Push({LR, R7})
        else:
            yield arm_instructions.Push(RegisterSet({LR, R11}))

        # Setup frame pointer:
        if self.has_option('thumb'):
            yield thumb_instructions.Mov2(R7, SP)
        else:
            yield arm_instructions.Mov2(R11, SP, arm_instructions.NoShift())

        # Reserve stack for this calling frame for:
        # 1. local variables
        # 2. save registers
        # 3. parameters to called functions
        if frame.stacksize:
            ssize = round_up(frame.stacksize)
            if self.has_option('thumb'):

                # Reserve stack space:
                # subSp cannot handle large numbers:
                while ssize > 0:
                    inc = min(124, ssize)
                    yield thumb_instructions.SubSp(inc)
                    ssize -= inc
            else:
                yield arm_instructions.SubImm(SP, SP, ssize)

        # Callee save registers:
        callee_save = {r for r in self.callee_save if r in frame.used_regs}
        if callee_save:
            if self.has_option('thumb'):
                yield thumb_instructions.Push(callee_save)
            else:
                yield arm_instructions.Push(RegisterSet(callee_save))

        # Allocate space for outgoing calls:
        extras = max(frame.out_calls) if frame.out_calls else 0
        if extras:
            ssize = round_up(extras)
            if self.has_option('thumb'):
                raise NotImplementedError()
            else:
                yield arm_instructions.SubImm(SP, SP, ssize)

    def gen_epilogue(self, frame):
        """ Return epilogue sequence for a frame.

        Adjust frame pointer and add constant pool.

        Also free up space on stack for:

          - Space for parameters passed to called functions.
          - Space for save registers
          - Space for local variables
        """

        # Free space for outgoing calls:
        extras = max(frame.out_calls) if frame.out_calls else 0
        if extras:
            ssize = round_up(extras)
            if self.has_option('thumb'):
                raise NotImplementedError()
            else:
                yield arm_instructions.AddImm(SP, SP, ssize)

        # Callee save registers:
        callee_save = {r for r in self.callee_save if r in frame.used_regs}
        if callee_save:
            if self.has_option('thumb'):
                yield thumb_instructions.Pop(callee_save)
            else:
                yield arm_instructions.Pop(RegisterSet(callee_save))

        if frame.stacksize > 0:
            ssize = round_up(frame.stacksize)
            if self.has_option('thumb'):
                # subSp cannot handle large numbers:
                while ssize > 0:
                    inc = min(124, ssize)
                    yield thumb_instructions.AddSp(inc)
                    ssize -= inc
            else:
                yield arm_instructions.AddImm(SP, SP, ssize)

        if self.has_option('thumb'):
            yield thumb_instructions.Pop({PC, R7})
        else:
            yield arm_instructions.Pop(RegisterSet({PC, R11}))

        # Add final literal pool
        for instruction in self.litpool(frame):
            yield instruction

        if not self.has_option('thumb'):
            yield Alignment(4)   # Align at 4 bytes

    def gen_arm_memcpy(self, p1, p2, v3, size):
        # Called before register allocation
        # Major crappy memcpy, can be improved!
        for idx in range(size):
            yield arm_instructions.Ldrb(v3, p2, idx)
            yield arm_instructions.Strb(v3, p1, idx)
            # TODO: yield the below from time to time for really big stuff:
            # yield arm_instructions.AddImm(p1, 1)
            # yield arm_instructions.AddImm(p2, 1)

    def gen_call(self, frame, label, args, rv):
        arg_types = [a[0] for a in args]
        arg_locs = self.determine_arg_locations(arg_types)

        arg_regs = []
        stack_size = 0
        for arg_loc, arg2 in zip(arg_locs, args):
            arg = arg2[1]
            if isinstance(arg_loc, ArmRegister):
                arg_regs.append(arg_loc)
                yield self.move(arg_loc, arg)
            elif isinstance(arg_loc, StackLocation):
                stack_size += arg_loc.size
                if isinstance(arg, ArmRegister):
                    # Store register on stack:
                    if self.has_option('thumb'):
                        yield thumb_instructions.Str1(arg, SP, arg_loc.offset)
                    else:
                        yield arm_instructions.Str1(arg, SP, arg_loc.offset)
                elif isinstance(arg, StackLocation):
                    if self.has_option('thumb'):
                        raise NotImplementedError()
                    else:
                        # Generate memcpy now:
                        # print(arg2, arg_loc)
                        assert arg.size == arg_loc.size
                        # Now start a copy routine to copy some stack:
                        p1 = frame.new_reg(ArmRegister)
                        p2 = frame.new_reg(ArmRegister)
                        v3 = frame.new_reg(ArmRegister)

                        # Destination location:
                        # Remember that the LR and FP are pushed in between
                        # So hence -8:
                        yield arm_instructions.AddImm(
                            p1, SP, arg_loc.offset - 8)
                        # Source location:
                        yield arm_instructions.SubImm(
                            p2, self.fp, -arg.offset)
                        for instruction in self.gen_arm_memcpy(
                                p1, p2, v3, arg.size):
                            yield instruction

                else:  # pragma: no cover
                    raise NotImplementedError(str(arg))
            else:  # pragma: no cover
                raise NotImplementedError('Parameters in memory not impl')

        # Record that certain amount of stack is required:
        frame.add_out_call(stack_size)

        yield RegisterUseDef(uses=arg_regs)

        clobbers = [R0, R1, R2, R3, R4]
        if self.has_option('thumb'):
            if isinstance(label, ArmRegister):
                # Ensure thumb mode!
                yield thumb_instructions.AddImm(label, label, 1)
                yield thumb_instructions.Blx(label, clobbers=clobbers)
            else:
                yield thumb_instructions.Bl(label, clobbers=clobbers)
        else:
            if isinstance(label, ArmRegister):
                yield arm_instructions.Blx(label, clobbers=clobbers)
            else:
                yield arm_instructions.Bl(label, clobbers=clobbers)

        if rv:
            retval_loc = self.determine_rv_location(rv[0])
            yield RegisterUseDef(defs=(retval_loc,))
            yield self.move(rv[1], retval_loc)

    def gen_function_enter(self, args):
        arg_types = [a[0] for a in args]
        arg_locs = self.determine_arg_locations(arg_types)

        arg_regs = set(l for l in arg_locs if isinstance(l, ArmRegister))
        yield RegisterUseDef(defs=arg_regs)

        for arg_loc, arg2 in zip(arg_locs, args):
            arg = arg2[1]
            if isinstance(arg_loc, ArmRegister):
                yield self.move(arg, arg_loc)
            elif isinstance(arg_loc, StackLocation):
                pass
            else:  # pragma: no cover
                raise NotImplementedError('Parameters in memory not impl')

    def gen_function_exit(self, rv):
        live_out = set()
        if rv:
            retval_loc = self.determine_rv_location(rv[0])
            yield self.move(retval_loc, rv[1])
            live_out.add(retval_loc)
        yield RegisterUseDef(uses=live_out)

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
        locations = []
        regs = [R1, R2, R3, R4]
        offset = 8
        for arg_ty in arg_types:
            if arg_ty.is_blob:
                r = StackLocation(offset, arg_ty.size)
                offset += arg_ty.size
            else:
                # Pass non-blob values in registers if possible:
                if regs:
                    r = regs.pop(0)
                else:
                    arg_size = self.info.get_size(arg_ty)
                    r = StackLocation(offset, arg_size)
                    offset += arg_size
            locations.append(r)
        return locations

    def determine_rv_location(self, ret_type):
        rv = R0
        return rv


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
        assert isinstance(v, str)
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
   push {r4}
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

   pop {r4}
   mov pc, lr         ; Return from function.
"""
