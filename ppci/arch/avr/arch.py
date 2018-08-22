""" AVR architecture.

See for good documentation about AVR ABI:

- https://gcc.gnu.org/wiki/avr-gcc

The stack grows downwards in AVR. The stack pointer points to the current
empty stack slot. This is somewhat confusing, because on other machines
the stack pointer points to the latests pushed byte.

The stack frame is layout as follows:

+----+-----------------------------+
| 90 | Incoming arguments          |
| 89 | for previous frame          |
+----+-----------------------------+
| 88 | return address              |
| 87 |                             |
+----+-----------------------------+
| 86 |                             |
| 85 | saved registers previous    |
| 84 | frame                       |
+----+-----------------------------+
| 83 |                             |
| 82 | stack for previous frame    |
| 81 |                             |
+----+-----------------------------+
| 80 |                             |
| 79 | Incoming arguments for      |
| 78 | current frame               |
+----+-----------------------------+
| 77 | return address              |
| 76 |                             |
+----+-----------------------------+
| 75 |                             |
| 74 | saved registers current     |
| 73 | frame                       |
+----+-----------------------------+
| 72 |                             |
| 71 |                             |
| 70 | Stack for the current frame |
| 69 |                             | <- pointed to by Y
+----+-----------------------------+
| 68 |                             | <- stack pointer

Stack grows
    ||
    \/

"""

import io
from ... import ir
from ...binutils.assembler import BaseAssembler
from ..arch import Architecture
from ..arch_info import ArchInfo, TypeInfo
from ..generic_instructions import Label, Alignment, SectionInstruction
from ..generic_instructions import RegisterUseDef
from ..data_instructions import data_isa
from ..data_instructions import Db
from ..runtime import get_runtime_files
from ..stack import FramePointerLocation
from . import registers, instructions
from .instructions import avr_isa
from .instructions import Push, Pop, Mov, Call, In, Movw, Ret, Adiw
from .registers import AvrRegister, Register
from .registers import AvrWordRegister
from .registers import r0, PC
from .registers import r8, r9, r10, r11, r12, r13, r14, r15
from .registers import r16, r17, r18, r19, r20, r21, r22, r23
from .registers import r24, r25, W, Y, Z
from .registers import caller_save, callee_save
from .registers import get16reg, register_classes, gdb_registers


class AvrArch(Architecture):
    """ Avr architecture description. """
    name = 'avr'

    def __init__(self, options=None):
        super().__init__(options=options)
        self.isa = avr_isa + data_isa
        self.assembler = BaseAssembler()
        self.assembler.gen_asm_parser(self.isa)
        # TODO: make it possible to choose between 16 and 8 bit int type size
        # with an option -mint8 every integer is 8 bits wide.
        self.info = ArchInfo(
            type_infos={
                ir.i8: TypeInfo(1, 1), ir.u8: TypeInfo(1, 1),
                ir.i16: TypeInfo(2, 2), ir.u16: TypeInfo(2, 2),
                'int': ir.i16, 'ptr': ir.u16
            },
            register_classes=register_classes)
        self.fp = Y
        self.fp_location = FramePointerLocation.BOTTOM
        self.gdb_registers = gdb_registers
        self.gdb_pc = PC
        self.caller_save = caller_save

    def get_runtime(self):
        from ...api import asm, c3c, link
        obj1 = asm(io.StringIO(asm_rt_src), self)
        c3_sources = get_runtime_files([
            'sdiv',
            'smul',
        ])
        obj2 = c3c(c3_sources, [], self)
        obj = link([obj1, obj2], partial_link=True)
        return obj

    def determine_arg_locations(self, arg_types):
        """ Given a set of argument types, determine location for argument """
        locations = []
        regs = [
            r25, r24, r23, r22, r21, r20, r19, r18, r17, r16, r15,
            r14, r13, r12, r11, r10, r9, r8]
        for a in arg_types:
            sizes = {
                ir.i8: 1, ir.u8: 1, ir.i16: 2, ir.u16: 2,
                ir.ptr: 2
            }
            s = sizes[a]

            # Round odd registers:
            if s % 2 == 1:
                regs.pop(0)

            # Determine register:
            if s == 1:
                r = regs.pop(0)
                locations.append(r)
            elif s == 2:
                regs.pop(0)
                lo_reg = regs.pop(0)
                r = get16reg(lo_reg.num)
                locations.append(r)
            else:  # pragma: no cover
                raise NotImplementedError(str(s))
        return locations

    def determine_rv_location(self, ret_type):
        rv = W
        return rv

    def expand_word_regs(self, registers):
        s = set()
        for register in registers:
            if isinstance(register, AvrWordRegister):
                s.add(register.hi)
                s.add(register.lo)
            else:
                s.add(register)
        return s

    def gen_prologue(self, frame):
        """ Generate the prologue instruction sequence. """
        # Label indication function:
        yield Label(frame.name)

        # Save some registers:
        used_regs = self.expand_word_regs(frame.used_regs)
        for register in callee_save:
            if register in used_regs:
                yield Push(register)

        if frame.stacksize > 0:
            # Save previous frame pointer and fill it from the SP:
            yield Push(Y.lo)
            yield Push(Y.hi)

            # Push N times to adjust stack:
            for _ in range(frame.stacksize):
                yield Push(r0)

            # Setup frame pointer:
            yield In(Y.lo, 0x3d)
            yield In(Y.hi, 0x3e)
            # ATTENTION: after push, the stackpointer points to the next empty
            # byte.
            # Increment entire Y by one to point to address frame+0:
            yield Adiw(Y, 1)

    def gen_epilogue(self, frame):
        """ Return epilogue sequence for a frame. Adjust frame pointer
            and add constant pool
        """
        if frame.stacksize > 0:
            # Pop x times to adjust stack:
            for _ in range(frame.stacksize):
                yield Pop(r0)

            yield Pop(Y.hi)
            yield Pop(Y.lo)

        # Restore registers:
        used_regs = self.expand_word_regs(frame.used_regs)
        for register in reversed(callee_save):
            if register in used_regs:
                yield Pop(register)

        yield Ret()

        # Add final literal pool:
        for instruction in self.litpool(frame):
            yield instruction
        yield Alignment(4)   # Align at 4 bytes

    def gen_call(self, frame, label, args, rv):
        arg_types = [a[0] for a in args]
        arg_locs = self.determine_arg_locations(arg_types)

        # Copy parameters:
        for arg_loc, arg2 in zip(arg_locs, args):
            arg = arg2[1]
            if isinstance(arg_loc, AvrRegister):
                yield self.move(arg_loc, arg)
            elif isinstance(arg_loc, AvrWordRegister):
                yield self.move(arg_loc, arg)
            else:  # pragma: no cover
                raise NotImplementedError('Parameters in memory not impl')

        arg_regs = set(l for l in arg_locs if isinstance(l, Register))
        yield RegisterUseDef(uses=arg_regs)

        if isinstance(label, AvrWordRegister):
            yield self.move(Z, label)
            # Call to function at Z
            # Divide Z by two, since PC is pointing to 16 bits words
            yield instructions.Lsr(registers.r31)
            yield instructions.Ror(registers.r30)
            yield instructions.Icall(clobbers=self.caller_save)
        else:
            yield Call(label, clobbers=self.caller_save)

        if rv:
            retval_loc = self.determine_rv_location(rv[0])

            yield RegisterUseDef(defs=(retval_loc,))

            if isinstance(rv[1], AvrWordRegister):
                yield self.move(rv[1], retval_loc)
            else:  # pragma: no cover
                raise NotImplementedError('Parameters in memory not impl')

    def gen_function_enter(self, args):
        """ Copy arguments into local temporaries and mark registers live """
        arg_types = [a[0] for a in args]
        arg_locs = self.determine_arg_locations(arg_types)
        arg_regs = set(l for l in arg_locs if isinstance(l, Register))
        yield RegisterUseDef(defs=arg_regs)

        # Copy parameters:
        for arg_loc, arg2 in zip(arg_locs, args):
            arg = arg2[1]
            if isinstance(arg_loc, Register):
                yield self.move(arg, arg_loc)
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
        else:  # pragma: no cover
            raise NotImplementedError()


asm_rt_src = """
; shift r25:r24 right by r22 bits
__shr16:
  push r16
  mov r16, r22
  cpi r16, 0
  breq __shr16_2
__shr16_1:
  lsr r25
  ror r24
  dec r16
  cpi r16, 0
  brne __shr16_1
__shr16_2:
  pop r16
  ret

; shift r25:r24 left by r22 bits
__shl16:
  push r16
  mov r16, r22
  cpi r16, 0
  breq __shl16_2
__shl16_1:
  add r24, r24
  adc r25, r25
  dec r16
  cpi r16, 0
  brne __shl16_1
__shl16_2:
  pop r16
  ret

"""
