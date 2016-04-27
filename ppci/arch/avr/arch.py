"""
    AVR architecture.
"""
import io
from ..arch import Architecture, Label
from ..arch import Alignment
from ..arch import Frame, VCall
from ...ir import i8, i16, ptr
from ...binutils.assembler import BaseAssembler
from ..data_instructions import data_isa
from ..data_instructions import Db
from .instructions import avr_isa
from .instructions import Push, Pop, Mov, Call, In
from .registers import AvrRegister, AvrPseudo16Register
from .registers import r0, r1, r2, r3, r4, r5, r6, r7
from .registers import r8, r9, r10, r11, r12, r13, r14, r15
from .registers import r16, r17, r18, r19, r20, r21, r22, r23
from .registers import r24, r25, X, Y, Z
from .registers import get_register


class AvrArch(Architecture):
    """
        Check this site for good info:
        - https://gcc.gnu.org/wiki/avr-gcc
    """
    name = 'avr'

    def __init__(self, options=None):
        super().__init__(options=options)
        self.isa = avr_isa + data_isa
        self.FrameClass = AvrFrame
        self.assembler = BaseAssembler()
        self.assembler.gen_asm_parser(self.isa)
        # TODO: make it possible to choose between 16 and 8 bit int type size
        self.byte_sizes['int'] = 2
        self.byte_sizes['i16'] = 2
        self.byte_sizes['i8'] = 1
        self.byte_sizes['ptr'] = 2
        self.value_classes[i8] = AvrRegister
        self.value_classes[i16] = AvrPseudo16Register
        self.value_classes[ptr] = AvrPseudo16Register

    def get_runtime(self):
        from ...api import asm
        asm_src = """
            __shr16:
                ; TODO
                ret
            __shl16:
                ret
        """
        return asm(io.StringIO(asm_src), self)

    def get_register(self, color):
        return get_register(color)

    def determine_arg_locations(self, arg_types, ret_type):
        """ Given a set of argument types, determine location for argument """
        l = []
        live_in = set()
        live_out = set()
        rv = AvrPseudo16Register('ret_val', r25, r24)
        regs = [
            r25, r24, r23, r22, r21, r20, r19, r18, r17, r16, r15,
            r14, r13, r12, r11, r10, r9, r8]
        for a in arg_types:
            s = self.byte_sizes[a.name]

            # Round odd registers:
            if s % 2 == 1:
                regs.pop(0)

            # Determine register:
            if s == 1:
                r = regs.pop(0)
                l.append(r)
                live_in.add(r)
            elif s == 2:
                hi_reg = regs.pop(0)
                lo_reg = regs.pop(0)
                reg_name = '{}_{}'.format(hi_reg.name, lo_reg.name)
                r = AvrPseudo16Register(reg_name, hi_reg, lo_reg)
                l.append(r)
                live_in.add(hi_reg)
                live_in.add(lo_reg)
            else:  # pragma: no cover
                raise NotImplementedError(str(s))
        return l, tuple(live_in), rv, tuple(live_out)

    def gen_call(self, label, arg_types, ret_type, args, res_var):
        """ Step 1 code for call sequence. This function moves arguments
            in the proper locations.
        """
        # Setup parameters:
        # TODO: variable return type
        arg_locs, live_in, rv, live_out = self.determine_arg_locations(arg_types, ret_type)

        # Copy parameters:
        for arg_loc, arg in zip(arg_locs, args):
            assert type(arg_loc) is type(arg)
            if isinstance(arg_loc, AvrRegister):
                yield self.move(arg_loc, arg)
            elif isinstance(arg_loc, AvrPseudo16Register):
                yield self.move(arg_loc.hi, arg.hi)
                yield self.move(arg_loc.lo, arg.lo)
            else:  # pragma: no cover
                raise NotImplementedError('Parameters in memory not impl')

        # Emit call placeholder:
        yield VCall(label, extra_uses=live_in, extra_defs=live_out)

        # Copy return value:
        if isinstance(res_var, AvrPseudo16Register):
            yield self.move(res_var.lo, rv.lo)
            yield self.move(res_var.hi, rv.hi)
        else:  # pragma: no cover
            raise NotImplementedError('Parameters in memory not impl')

    def move(self, dst, src):
        """ Generate a move from src to dst """
        return Mov(dst, src, ismove=True)


class AvrFrame(Frame):
    def __init__(self, name, arg_locs, live_in, rv, live_out):
        super().__init__(name, arg_locs, live_in, rv, live_out)
        # Allocatable registers:
        # TODO: the registers are not always possible, for example:
        # ldi r16, 0xaa
        self.regs = [
            r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12, r13, r14,
            r15, r16, r17, r18, r19, r20, r21, r22, r23, r24, r25]
        # r27, r28, r29, r30, r31]
        self.fp = Y

        self.locVars = {}

        # Literal pool:
        self.constants = []
        self.literal_number = 0

    def make_call(self, vcall):
        """ Implement actual call and save / restore live registers """
        # Now we now what variables are live:
        live_registers = self.live_regs_over(vcall)

        # Caller save registers:
        for register in live_registers:
            yield Push(register)

        yield Call(vcall.function_name)

        # Restore caller save registers:
        for register in reversed(live_registers):
            yield Pop(register)

    def alloc_var(self, lvar, size):
        if lvar not in self.locVars:
            self.locVars[lvar] = self.stacksize
            self.stacksize = self.stacksize + size
        return self.locVars[lvar]

    def add_constant(self, value):
        """ Add constant literal to constant pool """
        for lab_name, val in self.constants:
            if value == val:
                return lab_name
        assert type(value) in [str, int, bytes], str(value)
        lab_name = '{}_literal_{}'.format(self.name, self.literal_number)
        self.literal_number += 1
        self.constants.append((lab_name, value))
        return lab_name

    def prologue(self):
        """ Generate the prologue instruction sequence """
        # Label indication function:
        yield Label(self.name)

        # Save previous frame pointer and fill it from the SP:
        yield Push(Y.lo)
        yield Push(Y.hi)
        yield In(Y.lo, 0x3d)
        yield In(Y.hi, 0x3e)

        if self.stacksize > 0:
            # Push N times to adjust stack:
            for _ in range(self.stacksize):
                yield Push(r0)

        # yield Mov(R11, SP)                 # Setup frame pointer

    def litpool(self):
        """ Generate instruction for the current literals """
        # Align at 4 bytes
        if self.constants:
            yield Alignment(4)

        # Add constant literals:
        while self.constants:
            label, value = self.constants.pop(0)
            yield Label(label)
            if isinstance(value, bytes):
                for byte in value:
                    yield Db(byte)
                yield Alignment(4)   # Align at 4 bytes
            else:  # pragma: no cover
                raise NotImplementedError('Constant of type {}'.format(value))

    def between_blocks(self):
        for ins in self.litpool():
            self.emit(ins)

    def epilogue(self):
        """ Return epilogue sequence for a frame. Adjust frame pointer
            and add constant pool
        """
        if self.stacksize > 0:
            # Pop x times to adjust stack:
            for _ in range(self.stacksize):
                yield Pop(r0)

        yield Pop(Y.hi)
        yield Pop(Y.lo)

        # Add final literal pool:
        for instruction in self.litpool():
            yield instruction
        yield Alignment(4)   # Align at 4 bytes
