""" X86-64 architecture description.

X86 specific frame for functions.

  rbp, rbx, r12, r13, r14 and r15 are callee save. The called function
  must save those. The other registers must be saved by the caller.

See also:
http://eli.thegreenplace.net/2011/09/06/stack-frame-layout-on-x86-64

Calling conventions

- Passing a struct by value is done by placing the structure on the stack.

- Returning a complex data type by value is done by implicitly setting the
  first argument of the function to a memory address where the value should
  be copied.

- The end of input arguments must always be aligned on a 16 byte boundary.
  This means rsp + 8 is aligned on 16 bytes when entering a function.
"""

from ... import ir
from ..arch import Architecture
from ..arch_info import ArchInfo, TypeInfo
from ..generic_instructions import Label, RegisterUseDef
from ..stack import StackLocation
from ..cc import CallingConvention
from ..registers import Register
from ...binutils.assembler import BaseAssembler
from ..data_instructions import data_isa
from ..data_instructions import Db
from .instructions import bits64, RmReg64, MovRegRm8, RmReg8, RmMemDisp, isa
from .instructions import Push, Pop, SubImm, AddImm, MovsxReg64Rm8
from .instructions import Call, Ret, bits16, RmReg16, bits32, RmReg32
from .x87_instructions import x87_isa
from .sse2_instructions import sse1_isa, sse2_isa, Movss, Movsd
from .sse2_instructions import RmXmmRegSingle, RmXmmRegDouble
from .sse2_instructions import PushXmm, PopXmm
from .registers import rax, rcx, rdi, rsi
from .registers import register_classes, caller_save, callee_save
from .registers import Register64, XmmRegister
from .registers import rbp, rsp, al
from . import instructions, registers


# TODO: Use something like the below?
class WindowsCallingConvention(CallingConvention):
    """ Windows calling convention """
    name = 'wincc'
    int_regs = [registers.rcx, registers.rdx, registers.r8, registers.r9]
    float_regs = [
        registers.xmm0, registers.xmm1, registers.xmm2,
        registers.xmm3]


class LinuxCallingConvention(CallingConvention):
    """ Sys V ABI calling convention

    Given a set of argument types, determine locations
    the first arguments go into registers. The others on the stack.

    see also http://www.x86-64.org/documentation/abi.pdf

    ABI:
    p1 = rdi
    p2 = rsi
    p3 = rdx
    p4 = rcx
    p5 = r8
    p6 = r9

    floating point values are passed in xmm0, xmm1, xmm2, xmm3, etc..

    return value in rax

    self.rv = rax
    """
    name = 'sysv'
    locs = (
        ([ir.i8, ir.i16, ir.i32, ir.i64, ir.u8, ir.u64, ir.ptr],
         [registers.rdi, registers.rsi, registers.rdx,
          registers.rcx, registers.r8, registers.r9]),
        ([ir.f32, ir.f64],
         [registers.xmm0, registers.xmm1, registers.xmm2,
          registers.xmm3, registers.xmm4, registers.xmm5,
          registers.xmm6, registers.xmm7]))


class X86_64Arch(Architecture):
    """ x86_64 architecture """
    name = 'x86_64'
    option_names = ('sse2', 'sse3', 'x87', 'wincc')

    def __init__(self, options=None):
        super().__init__(options=options)
        self.info = ArchInfo(
            type_infos={
                ir.i8: TypeInfo(1, 1), ir.u8: TypeInfo(1, 1),
                ir.i16: TypeInfo(2, 2), ir.u16: TypeInfo(2, 2),
                ir.i32: TypeInfo(4, 4), ir.u32: TypeInfo(4, 4),
                ir.i64: TypeInfo(8, 8), ir.u64: TypeInfo(8, 8),
                'int': ir.i64, 'ptr': ir.u64, ir.ptr: ir.u64,
            }, register_classes=register_classes)

        self.isa = isa + data_isa + sse1_isa + sse2_isa
        if self.has_option('x87'):
            # TODO: implement x87 isa also!
            self.isa = self.isa + x87_isa
        self.assembler = BaseAssembler()
        self.assembler.gen_asm_parser(self.isa)
        self.stack_grows_down = True
        self.gdb_registers = registers.full_registers

    def move(self, dst, src):
        """ Generate a move from src to dst """
        if isinstance(dst, registers.Register8) and \
                isinstance(src, registers.Register8):
            return MovRegRm8(dst, RmReg8(src), ismove=True)
        elif isinstance(dst, registers.Register16) and \
                isinstance(src, registers.Register16):
            return bits16.MovRegRm(dst, RmReg16(src), ismove=True)
        elif isinstance(dst, registers.Register32) and \
                isinstance(src, registers.Register32):
            return bits32.MovRegRm(dst, RmReg32(src), ismove=True)
        elif isinstance(dst, registers.Register64) and \
                isinstance(src, registers.Register16):
            return instructions.MovsxRegRm16(dst, RmReg16(src), ismove=True)
        elif isinstance(dst, registers.Register16) and \
                isinstance(src, registers.Register64):
            # return instructions.MovsxRegRm16(dst, RmReg16(src), ismove=True)
            raise NotImplementedError()  # pragma: no cover
        elif isinstance(dst, registers.Register8) and \
                isinstance(src, registers.Register64):
            raise NotImplementedError()  # pragma: no cover
        elif isinstance(dst, Register64) and \
                isinstance(src, registers.Register8):
            raise NotImplementedError()  # pragma: no cover
        elif isinstance(dst, registers.Register64) and \
                isinstance(src, registers.Register64):
            return bits64.MovRegRm(dst, RmReg64(src), ismove=True)
        elif isinstance(dst, XmmRegister) and isinstance(src, XmmRegister):
            return Movsd(dst, RmXmmRegDouble(src), ismove=True)
        elif isinstance(dst, registers.XmmRegisterSingle) and \
                isinstance(src, registers.XmmRegisterSingle):
            return Movss(dst, RmXmmRegSingle(src), ismove=True)
        else:  # pragma: no cover
            raise NotImplementedError(str(type(dst))+str(type(src)))

    def gen_memcpy(self, dst, src, count):
        """ Generate a memcpy action """
        # Destination pointer:
        yield instructions.Lea(rdi, dst)

        # Source pointer:
        yield instructions.Lea(rsi, src)

        yield instructions.MovImm(rcx, count)     # Byte count
        yield instructions.Rep()
        yield RegisterUseDef(uses=(rcx,))
        yield instructions.Movsb()

        # for x in
        # Memcopy action!
        # yield mov(rdi, arg)
        # yield mov(rsi, arg_loc)
        # yield mov(rcx, arg_loc.size)
        # yield rep()
        # yield movsb()
        # raise NotImplementedError()

    @staticmethod
    def push(register):
        if isinstance(register, registers.XmmRegister):
            return PushXmm(register)
        else:
            return Push(register)

    @staticmethod
    def pop(register):
        if isinstance(register, registers.XmmRegister):
            return PopXmm(register)
        else:
            return Pop(register)

    def determine_arg_locations(self, arg_types):
        """ Given a set of argument types, determine locations
            the first arguments go into registers. The others on the stack.

        see also http://www.x86-64.org/documentation/abi.pdf

        ABI:
        p1 = rdi
        p2 = rsi
        p3 = rdx
        p4 = rcx
        p5 = r8
        p6 = r9

        floating point values are passed in xmm0, xmm1, xmm2, xmm3, etc..

        return value in rax

        self.rv = rax

        On windows a different scheme is used:
        integers are passed in rcx, rdx, r8 and r9
        floats are passed in xmm0, xmm1, xmm2 and xmm3

        These examples show how it works:

        func(int a, double b, int c, float d)
        // a in rcx, b in xmm1, c in r8 and d in xmm3
        """
        arg_locs = []
        if self.has_option('wincc'):
            # Windows calling convention:
            int_regs = [
                (registers.rcx, registers.ecx),
                (registers.rdx, registers.edx),
                (registers.r8, registers.r8d),
                (registers.r9, registers.r9d),
            ]
            float_regs = [
                (registers.xmm0_single, registers.xmm0),
                (registers.xmm1_single, registers.xmm1),
                (registers.xmm2_single, registers.xmm2),
                (registers.xmm3_single, registers.xmm3),
            ]
        else:
            # Sys V ABI calling convention:
            int_regs = [
                (registers.rdi, registers.edi),
                (registers.rsi, registers.esi),
                (registers.rdx, registers.edx),
                (registers.rcx, registers.ecx),
                (registers.r8, registers.r8d),
                (registers.r9, registers.r9d),
            ]
            float_regs = [
                (registers.xmm0_single, registers.xmm0),
                (registers.xmm1_single, registers.xmm1),
                (registers.xmm2_single, registers.xmm2),
                (registers.xmm3_single, registers.xmm3),
                (registers.xmm4_single, registers.xmm4),
                (registers.xmm5_single, registers.xmm5),
                (registers.xmm6_single, registers.xmm6),
                (registers.xmm7_single, registers.xmm7),
            ]

        offset = 16
        for arg_type in arg_types:
            # Determine register:
            if arg_type in [
                    ir.i8, ir.i64, ir.u8, ir.u64,
                    ir.i16, ir.u16,
                    ir.i32, ir.u32,  # TODO: maybe use eax and friends?
                    ir.ptr]:
                if int_regs:
                    if arg_type in [ir.i32, ir.u32]:
                        reg = int_regs.pop(0)[1]
                    else:
                        reg = int_regs.pop(0)[0]

                    if self.has_option('wincc'):
                        float_regs.pop(0)
                else:
                    # We need stack location!
                    # arg_size = self.info.get_size(arg_type)
                    arg_size = 8  # All integers are passed in 8 byte memory
                    reg = StackLocation(offset, arg_size)
                    offset += arg_size
            elif arg_type in [ir.f32, ir.f64]:
                if float_regs:
                    if arg_type is ir.f32:
                        reg = float_regs.pop(0)[0]
                    else:
                        reg = float_regs.pop(0)[1]

                    if self.has_option('wincc'):
                        int_regs.pop(0)
                else:
                    # We need stack location!
                    arg_size = self.info.get_size(arg_type)
                    reg = StackLocation(offset, arg_size)
                    offset += arg_size
            elif isinstance(arg_type, ir.BlobDataTyp):
                reg = StackLocation(offset, arg_type.size)
                offset += arg_type.size
            else:  # pragma: no cover
                raise NotImplementedError(str(arg_type))
            arg_locs.append(reg)

        return arg_locs

    def determine_rv_location(self, ret_type):
        """ return value in rax or xmm0 """
        if ret_type in [ir.i64, ir.u64, ir.ptr]:
            rv = registers.rax
        elif ret_type in [ir.i32, ir.u32]:
            rv = registers.eax
        elif ret_type in [ir.i16, ir.u16]:
            rv = registers.ax
        elif ret_type in [ir.i8, ir.u8]:
            rv = registers.al
        elif ret_type is ir.f64:
            rv = registers.xmm0
        elif ret_type is ir.f32:
            rv = registers.xmm0_single
        else:  # pragma: no cover
            raise NotImplementedError(str(ret_type))
        return rv

    def gen_function_enter(self, args):
        """ Copy arguments into local temporaries and mark registers live """
        arg_types = [a[0] for a in args]
        arg_locs = self.determine_arg_locations(arg_types)
        arg_regs = set(l for l in arg_locs if isinstance(l, Register))
        yield RegisterUseDef(defs=arg_regs)

        stack_offset = 0
        cps = []
        for arg_loc, arg2 in zip(arg_locs, args):
            arg = arg2[1]
            if isinstance(arg_loc, registers.Register64):
                if isinstance(arg, registers.Register64):
                    yield self.move(arg, arg_loc)
                elif isinstance(arg, registers.Register8):
                    # Extract character part:
                    yield self.move(rax, arg_loc)
                    yield RegisterUseDef(uses=(rax,), defs=(al,))
                    yield self.move(arg, al)
                elif isinstance(arg, registers.Register16):
                    # Extract character part:
                    yield self.move(rax, arg_loc)
                    yield RegisterUseDef(uses=(rax,), defs=(registers.ax,))
                    yield self.move(arg, registers.ax)
                elif isinstance(arg, registers.Register32):
                    # Extract character part:
                    yield self.move(rax, arg_loc)
                    yield RegisterUseDef(uses=(rax,), defs=(registers.eax,))
                    yield self.move(arg, registers.eax)
                else:  # pragma: no cover
                    raise NotImplementedError(str(type(arg)))
            elif isinstance(arg_loc, registers.Register32):
                if isinstance(arg, registers.Register32):
                    yield self.move(arg, arg_loc)
                else:  # pragma: no cover
                    raise NotImplementedError(str(type(arg)))
            elif isinstance(arg_loc, registers.XmmRegister):
                yield self.move(arg, arg_loc)
            elif isinstance(arg_loc, registers.XmmRegisterSingle):
                yield self.move(arg, arg_loc)
            elif isinstance(arg_loc, StackLocation):
                if isinstance(arg, registers.Register64):
                    yield bits64.MovRegRm(
                        arg, RmMemDisp(rbp, stack_offset + 16))
                    stack_offset += arg_loc.size
                elif isinstance(arg, registers.Register32):
                    yield bits32.MovRegRm(
                        arg, RmMemDisp(rbp, stack_offset + 16))
                    stack_offset += arg_loc.size
                elif isinstance(arg, StackLocation):
                    # Store memcpy action for later:
                    # cps.append((arg.offset, stack_offset, arg.size))
                    raise NotImplementedError()
                    stack_offset += arg.size
                else:  # pragma: no cover
                    raise NotImplementedError()
            else:  # pragma: no cover
                raise NotImplementedError('Parameters in memory not impl')

        for dst, src, count in cps:
            for instruction in self.gen_memcpy(dst, src, count):
                yield instruction

    def gen_function_exit(self, rv):
        live_out = set()
        if rv:
            if rv[1]:
                retval_loc = self.determine_rv_location(rv[0])
                yield self.move(retval_loc, rv[1])
                live_out.add(retval_loc)
        yield RegisterUseDef(uses=live_out)

    def gen_call(self, frame, label, args, rv):
        # def gen_fill_arguments(self, arg_types, args):
        """ This function moves arguments in the proper locations. """
        arg_types = [a[0] for a in args]
        arg_locs = self.determine_arg_locations(arg_types)
        push_regs = []

        # Setup parameters:
        for arg_loc, arg2 in zip(arg_locs, args):
            arg = arg2[1]
            if isinstance(arg_loc, registers.Register64):
                if isinstance(arg, registers.Register64):
                    yield self.move(arg_loc, arg)
                elif isinstance(arg, registers.Register8):
                    # Upcast to char!
                    yield self.move(al, arg)
                    yield MovsxReg64Rm8(rax, RmReg8(al))
                    yield self.move(arg_loc, rax)
                elif isinstance(arg, registers.Register16):
                    # Upcast char!
                    yield self.move(registers.ax, arg)
                    yield instructions.MovsxRegRm16(
                        rax, RmReg16(registers.ax))
                    yield self.move(arg_loc, rax)
                else:  # pragma: no cover
                    raise NotImplementedError()
            elif isinstance(arg_loc, registers.Register32):
                if isinstance(arg, registers.Register32):
                    yield self.move(arg_loc, arg)
                else:  # pragma: no cover
                    raise NotImplementedError()
            elif isinstance(arg_loc, registers.XmmRegisterDouble):
                assert isinstance(arg, registers.XmmRegisterDouble)
                yield self.move(arg_loc, arg)
            elif isinstance(arg_loc, registers.XmmRegisterSingle):
                assert isinstance(arg, registers.XmmRegisterSingle)
                yield self.move(arg_loc, arg)
            elif isinstance(arg_loc, StackLocation):
                if isinstance(arg, Register):
                    push_regs.append(arg)
                elif isinstance(arg, StackLocation):
                    raise NotImplementedError(str(arg))
                    # memcpy(a, b, 100)
                else:  # pragma: no cover
                    raise NotImplementedError(str(arg))
            else:  # pragma: no cover
                raise NotImplementedError('Parameters in memory not impl')

        # Pre align stack to 16 bytes:
        stack_size = len(push_regs) * 8
        if stack_size % 16 != 0:
            extra_padding = stack_size % 16
            yield SubImm(rsp, extra_padding)
            stack_size += extra_padding

        # Push arguments in reverse order:
        for push_reg in reversed(push_regs):
            if isinstance(push_reg, registers.Register64):
                yield Push(push_reg)
            elif isinstance(push_reg, registers.Register32):
                yield self.move(registers.eax, push_reg)
                yield RegisterUseDef(
                    uses=(registers.eax,), defs=(registers.rax,))
                yield Push(rax)
            else:  # pragma: no cover
                raise NotImplementedError(str(push_reg))

        wincc = self.has_option('wincc')

        # If windows, reserve space for rcx, rdx, r8 and r9:
        if wincc:
            yield SubImm(rsp, 32)
            stack_size += 32

        # Mark all dedicated registers as used:
        arg_regs = set(l for l in arg_locs if isinstance(l, Register))
        yield RegisterUseDef(uses=arg_regs)

        if isinstance(label, Register64):
            # Call to register pointer
            yield instructions.CallReg(label, clobbers=caller_save)
        else:
            yield Call(label, clobbers=caller_save)

        if rv:
            retval_loc = self.determine_rv_location(rv[0])
            yield RegisterUseDef(defs=(retval_loc,))
            yield self.move(rv[1], retval_loc)

        if stack_size:
            yield AddImm(rsp, stack_size)

    def gen_prologue(self, frame):
        """ Returns prologue instruction sequence """
        # Label indication function:
        yield Label(frame.name)

        # Save rbp:
        yield self.push(rbp)

        # Setup frame pointer:
        yield bits64.MovRegRm(rbp, RmReg64(rsp))

        # Callee save registers:
        saved_registers = [reg for reg in callee_save if frame.is_used(reg)]

        # Determine how much space already was taken:
        saved_size = sum(r.bitsize // 8 for r in saved_registers)

        # Reserve stack space
        if frame.stacksize > 0:
            stack_size = round_up16(frame.stacksize, saved_size)
            yield SubImm(rsp, stack_size)
        elif saved_size % 16 != 0:
            yield SubImm(rsp, saved_size % 16)

        # TODO: align stackframe and saved registers on 16 bytes.

        for reg in saved_registers:
            yield self.push(reg)

    def gen_epilogue(self, frame):
        """ Return epilogue sequence for a frame. Adjust frame pointer
            and add constant pool
        """
        saved_registers = [reg for reg in callee_save if frame.is_used(reg)]
        saved_size = sum(r.bitsize // 8 for r in saved_registers)

        # Pop save registers back:
        for reg in reversed(saved_registers):
            yield self.pop(reg)

        # Give free stack space:
        if frame.stacksize > 0:
            stack_size = round_up16(frame.stacksize, saved_size)
            yield AddImm(rsp, stack_size)
        elif saved_size % 16 != 0:
            yield AddImm(rsp, saved_size % 16)

        # Restore rbp:
        yield self.pop(rbp)
        yield Ret()

        # Add final literal pool:
        for label, value in frame.constants:
            yield Label(label)
            if isinstance(value, bytes):
                for byte in value:
                    yield Db(byte)
            else:  # pragma: no cover
                raise NotImplementedError('Constant of type {}'.format(value))


def round_up16(s, already_taken):
    total = s + already_taken
    return s + (16 - total % 16)
