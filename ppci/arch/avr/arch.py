"""
    AVR architecture.
"""
import io
from ...ir import i8, i16, ptr
from ...binutils.assembler import BaseAssembler
from ..arch import Architecture, Label, Alignment, SectionInstruction
from ..data_instructions import data_isa
from ..data_instructions import Db
from .instructions import avr_isa
from .instructions import Push, Pop, Mov, Call, In, Movw, Ret
from .registers import AvrRegister
from .registers import AvrWordRegister
from .registers import r0, PC
from .registers import r8, r9, r10, r11, r12, r13, r14, r15
from .registers import r16, r17, r18, r19, r20, r21, r22, r23
from .registers import r24, r25, r26, r27, r28, r29, r30, r31, X, Y, Z
from .registers import r25r24
from .registers import get16reg, register_classes, gdb_registers


class AvrArch(Architecture):
    """ Avr architecture description. """
    name = 'avr'

    def __init__(self, options=None):
        super().__init__(options=options, register_classes=register_classes)
        self.isa = avr_isa + data_isa
        self.assembler = BaseAssembler()
        self.assembler.gen_asm_parser(self.isa)
        # TODO: make it possible to choose between 16 and 8 bit int type size
        # with an option -mint8 every integer is 8 bits wide.
        self.byte_sizes['int'] = 2
        self.byte_sizes['i16'] = 2
        self.byte_sizes['i8'] = 1
        self.byte_sizes['ptr'] = 2
        self.fp = Y
        self.gdb_registers = gdb_registers
        self.gdb_pc = PC

    def get_runtime(self):
        from ...api import asm
        asm_src = """
            __shr16:
                ; TODO
                ret
            __shl16:
                ; TODO!
                ret
        """
        return asm(io.StringIO(asm_src), self)

    def determine_arg_locations(self, arg_types):
        """ Given a set of argument types, determine location for argument """
        l = []
        live_in = set()
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
                r = get16reg(lo_reg.num)
                l.append(r)
                live_in.add(r)
            else:  # pragma: no cover
                raise NotImplementedError(str(s))
        return l, tuple(live_in)

    def determine_rv_location(self, ret_type):
        live_out = set()
        rv = r25r24
        live_out.add(r25r24)
        return rv, tuple(live_out)

    def gen_fill_arguments(self, arg_types, args, alives):
        """ Step 1 code for call sequence. This function moves arguments
            in the proper locations.
        """
        # Setup parameters:
        # TODO: variable return type
        arg_locs, tmp = self.determine_arg_locations(arg_types)
        alives.update(set(tmp))

        # Copy parameters:
        for arg_loc, arg in zip(arg_locs, args):
            # assert type(arg_loc) is type(arg)
            if isinstance(arg_loc, AvrRegister):
                yield self.move(arg_loc, arg)
            elif isinstance(arg_loc, AvrWordRegister):
                yield self.move(arg_loc, arg)
            else:  # pragma: no cover
                raise NotImplementedError('Parameters in memory not impl')

    def gen_copy_rv(self, res_type, res_var):
        # Copy return value:
        rv, live_out = self.determine_rv_location(res_type)
        if isinstance(res_var, AvrWordRegister):
            yield self.move(res_var, rv)
        else:  # pragma: no cover
            raise NotImplementedError('Parameters in memory not impl')

    def make_call(self, frame, vcall):
        """ Implement actual call and save / restore live registers """
        # Now we now what variables are live:
        live_registers = frame.live_regs_over(vcall)

        # Caller save registers:
        for register in live_registers:
            if isinstance(register, AvrWordRegister):
                yield Push(register.hi)
                yield Push(register.lo)
            else:
                yield Push(register)

        yield Call(vcall.function_name)

        # Restore caller save registers (in reverse order!):
        for register in reversed(live_registers):
            if isinstance(register, AvrWordRegister):
                yield Pop(register.lo)
                yield Pop(register.hi)
            else:
                yield Pop(register)

    def prologue(self, frame):
        """ Generate the prologue instruction sequence """
        # Label indication function:
        yield Label(frame.name)

        # Save previous frame pointer and fill it from the SP:
        yield Push(Y.lo)
        yield Push(Y.hi)

        # Save some registers:
        # TODO!
        self.logger.warning('Saving registers on prologue not impl')

        if frame.stacksize > 0:
            # Push N times to adjust stack:
            for _ in range(frame.stacksize):
                yield Push(r0)

        # Setup frame pointer:
        yield In(Y.lo, 0x3d)
        yield In(Y.hi, 0x3e)

    def epilogue(self, frame):
        """ Return epilogue sequence for a frame. Adjust frame pointer
            and add constant pool
        """
        if frame.stacksize > 0:
            # Pop x times to adjust stack:
            for _ in range(frame.stacksize):
                yield Pop(r0)

        yield Pop(Y.hi)
        yield Pop(Y.lo)
        yield Ret()

        # Add final literal pool:
        for instruction in self.litpool(frame):
            yield instruction
        yield Alignment(4)   # Align at 4 bytes

    def litpool(self, frame):
        """ Generate instruction for the current literals """
        # Align at 4 bytes

        if frame.constants:
            yield SectionInstruction('data')
            yield Alignment(4)

            # Add constant literals:
            while frame.constants:
                label, value = frame.constants.pop(0)
                yield Label(label)
                if isinstance(value, bytes):
                    for byte in value:
                        yield Db(byte)
                    yield Alignment(4)   # Align at 4 bytes
                else:  # pragma: no cover
                    raise NotImplementedError(
                        'Constant of type {}'.format(value))

            yield SectionInstruction('code')

    def between_blocks(self, frame):
        for instruction in self.litpool(frame):
            yield instruction

    def move(self, dst, src):
        """ Generate a move from src to dst """
        if isinstance(dst, AvrRegister) and isinstance(src, AvrRegister):
            return Mov(dst, src, ismove=True)
        elif isinstance(dst, AvrWordRegister) and \
                isinstance(src, AvrWordRegister):
            return Movw(dst, src, ismove=True)
        else:
            raise NotImplementedError()
