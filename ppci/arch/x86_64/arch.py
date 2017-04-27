""" X86-64 architecture description.

X86 specific frame for functions.

  rbp, rbx, r12, r13, r14 and r15 are callee save. The called function
  must save those. The other registers must be saved by the caller.

See also:
http://eli.thegreenplace.net/2011/09/06/stack-frame-layout-on-x86-64

"""

import io
from ... import ir
from ..arch import Architecture
from ..generic_instructions import Label, RegisterUseDef
from ..stack import StackLocation
from ..cc import CallingConvention
from ..registers import Register
from ...binutils.assembler import BaseAssembler
from ..data_instructions import data_isa
from ..data_instructions import Db
from .instructions import MovRegRm, RmReg, MovRegRm8, RmReg8, RmMemDisp, isa
from .instructions import Push, Pop, SubImm, AddImm, MovsxRegRm
from .instructions import Call, Ret
from .x87_instructions import x87_isa
from .sse2_instructions import sse1_isa, sse2_isa, Movss, RmXmmReg
from .sse2_instructions import PushXmm, PopXmm
from .registers import rax, rcx, rdx, r8, r9, rdi, rsi
from .registers import register_classes
from .registers import X86Register, LowRegister, XmmRegister
from .registers import rbx, rbp, rsp, al
from .registers import r12, r13, r14, r15
from . import registers


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
        super().__init__(options=options, register_classes=register_classes)
        self.byte_sizes['int'] = 8  # For front end!
        self.byte_sizes['ptr'] = 8  # For front end!
        self.isa = isa + data_isa + sse1_isa + sse2_isa
        if self.has_option('x87'):
            # TODO: implement x87 isa also!
            self.isa = self.isa + x87_isa
        self.assembler = BaseAssembler()
        self.assembler.gen_asm_parser(self.isa)
        self.callee_save = (rbx, r12, r13, r14, r15)
        self.stack_grows_down = True

    def move(self, dst, src):
        """ Generate a move from src to dst """
        if isinstance(dst, LowRegister) and isinstance(src, LowRegister):
            return MovRegRm8(dst, RmReg8(src), ismove=True)
        elif isinstance(dst, LowRegister) and isinstance(src, X86Register):
            raise NotImplementedError()  # pragma: no cover
        elif isinstance(dst, X86Register) and isinstance(src, LowRegister):
            raise NotImplementedError()  # pragma: no cover
        elif isinstance(dst, X86Register) and isinstance(src, X86Register):
            return MovRegRm(dst, RmReg(src), ismove=True)
        elif isinstance(dst, XmmRegister) and isinstance(src, XmmRegister):
            return Movss(dst, RmXmmReg(src), ismove=True)
        else:
            raise NotImplementedError()  # pragma: no cover

    def push(self, register):
        if isinstance(register, registers.XmmRegister):
            return PushXmm(register)
        else:
            return Push(register)

    def pop(self, register):
        if isinstance(register, registers.XmmRegister):
            return PopXmm(register)
        else:
            return Pop(register)

    def get_runtime(self):
        from ...api import asm
        asm_src = ''
        return asm(io.StringIO(asm_src), self)

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
        """
        arg_locs = []
        if self.has_option('wincc'):
            # Windows calling convention:
            int_regs = [rcx, rdx, r8, r9]
            float_regs = [
                registers.xmm0, registers.xmm1, registers.xmm2,
                registers.xmm3]
        else:
            # Sys V ABI calling convention:
            int_regs = [rdi, rsi, rdx, rcx, r8, r9]
            float_regs = [
                registers.xmm0, registers.xmm1, registers.xmm2,
                registers.xmm3, registers.xmm4, registers.xmm5,
                registers.xmm6, registers.xmm7]

        for arg_type in arg_types:
            # Determine register:
            if arg_type in [ir.i8, ir.i64, ir.u8, ir.u64, ir.ptr]:
                if int_regs:
                    reg = int_regs.pop(0)
                else:
                    # We need stack location!
                    reg = StackLocation()
            elif arg_type in [ir.f32, ir.f64]:
                reg = float_regs.pop(0)
            else:  # pragma: no cover
                raise NotImplementedError(str(arg_type))
            arg_locs.append(reg)

        return arg_locs

    def determine_rv_location(self, ret_type):
        """ return value in rax or xmm0 """
        if ret_type in [ir.i8, ir.i64, ir.u8, ir.u64, ir.ptr]:
            rv = rax
        elif ret_type in [ir.f32, ir.f64]:
            rv = registers.xmm0
        else:  # pragma: no cover
            raise NotImplementedError(str(ret_type))
        return rv

    def gen_fill_arguments(self, arg_types, args):
        """ This function moves arguments in the proper locations. """
        arg_locs = self.determine_arg_locations(arg_types)
        push_ops = []

        # Setup parameters:
        for arg_loc, arg in zip(arg_locs, args):
            if isinstance(arg_loc, X86Register):
                if isinstance(arg, X86Register):
                    yield self.move(arg_loc, arg)
                elif isinstance(arg, LowRegister):
                    # Upcast to char!
                    yield self.move(al, arg)
                    yield MovsxRegRm(rax, RmReg8(al))
                    yield self.move(arg_loc, rax)
                else:  # pragma: no cover
                    raise NotImplementedError()
            elif isinstance(arg_loc, XmmRegister):
                yield self.move(arg_loc, arg)
            elif isinstance(arg_loc, StackLocation):
                push_ops.append(Push(arg))
            else:  # pragma: no cover
                raise NotImplementedError('Parameters in memory not impl')

        # Push arguments in reverse order:
        for ins in reversed(push_ops):
            yield ins

        # Mark all dedicated registers as used:
        arg_regs = set(l for l in arg_locs if isinstance(l, Register))
        yield RegisterUseDef(uses=arg_regs)

    def gen_extract_arguments(self, arg_types, args):
        """ Generate code to extract arguments from the proper locations """
        arg_locs = self.determine_arg_locations(arg_types)

        arg_regs = set(l for l in arg_locs if isinstance(l, Register))
        yield RegisterUseDef(defs=arg_regs)

        stack_offset = 0
        for arg_loc, arg in zip(arg_locs, args):
            if isinstance(arg_loc, X86Register):
                if isinstance(arg, X86Register):
                    yield self.move(arg, arg_loc)
                elif isinstance(arg, LowRegister):
                    # Extract character part:
                    yield self.move(rax, arg_loc)
                    yield RegisterUseDef(uses=(rax,), defs=(al,))
                    yield self.move(arg, al)
                else:  # pragma: no cover
                    raise NotImplementedError()
            elif isinstance(arg_loc, XmmRegister):
                yield self.move(arg, arg_loc)
            elif isinstance(arg_loc, StackLocation):
                yield MovRegRm(arg, RmMemDisp(rbp, stack_offset + 16))
                stack_offset += 8
            else:  # pragma: no cover
                raise NotImplementedError('Parameters in memory not impl')

    def gen_stack_cleanup(self, arg_types):
        arg_locs = self.determine_arg_locations(arg_types)
        stack_slots = sum(isinstance(l, StackLocation) for l in arg_locs)
        if stack_slots:
            yield AddImm(rsp, stack_slots * 8)

    def gen_fill_retval(self, retval_type, retval_vreg):
        """ Fill the dedicated place with a return value """
        retval_loc = self.determine_rv_location(retval_type)
        yield self.move(retval_loc, retval_vreg)
        yield RegisterUseDef(uses=(retval_loc,))

    def gen_extract_retval(self, retval_type, rv):
        retval_loc = self.determine_rv_location(retval_type)
        yield RegisterUseDef(defs=(retval_loc,))
        yield self.move(rv, retval_loc)

    def gen_save_registers(self, registers):
        """ If registers must be saved, this is the time! """
        # Caller save registers:
        for register in registers:
            if register not in [rsp, rbp]:
                yield self.push(register)

    def gen_restore_registers(self, registers):
        """ If registers were saved, restore them """
        # Restore caller save registers:
        for register in reversed(registers):
            # TODO: determine caller saved?
            if register not in [rsp, rbp]:
                yield self.pop(register)

    def gen_call(self, frame, vcall):
        # R0 is filled with return value, do not save it, it will conflict.
        # Now we now what variables are live

        yield Call(vcall.function_name)

    def gen_prologue(self, frame):
        """ Returns prologue instruction sequence """
        # Label indication function:
        yield Label(frame.name)

        # Save rbp:
        yield self.push(rbp)

        # Setup frame pointer:
        yield MovRegRm(rbp, RmReg(rsp))

        # Reserve stack space
        if frame.stacksize > 0:
            yield SubImm(rsp, frame.stacksize)

        # Callee save registers:
        for reg in self.callee_save:
            if frame.is_used(reg):
                yield self.push(reg)

    def gen_epilogue(self, frame):
        """ Return epilogue sequence for a frame. Adjust frame pointer
            and add constant pool
        """
        # Pop save registers back:
        for reg in reversed(self.callee_save):
            if frame.is_used(reg):
                yield self.pop(reg)

        # Give free stack space:
        if frame.stacksize > 0:
            yield AddImm(rsp, frame.stacksize)

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
