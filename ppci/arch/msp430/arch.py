""" MSP430 architecture description. """

import io
from ...binutils.assembler import BaseAssembler
from ...utils.reporting import complete_report
from ...utils.reporting import DummyReportGenerator
from ..arch import Architecture, Label, Alignment
from ..data_instructions import Db, Dw2, data_isa
from .registers import r10, r11, r12, r13, r14, r15, Msp430Register
from .registers import r4, r5, r6, r7, r8, r9
from .registers import r1, register_classes
from .instructions import isa, mov, Ret, Pop
from .instructions import push, call, Add, Sub, ConstSrc, RegDst


class Msp430Arch(Architecture):
    """ Texas Instruments msp430 target architecture """
    name = 'msp430'

    def __init__(self, options=None):
        super().__init__(options=options, register_classes=register_classes)
        self.byte_sizes['int'] = 2
        self.byte_sizes['ptr'] = 2
        self.isa = isa + data_isa
        self.assembler = BaseAssembler()
        self.assembler.gen_asm_parser(self.isa)

        # Allocatable registers:
        self.fp = r4
        self.callee_save = (r4, r5, r6, r7, r8, r9, r10)
        self.caller_save = (r11, r13, r14, r15)  # TODO: fix r12 reg!!
        # TODO: r12 is given as argument and is return value
        # so it is detected live falsely.

    def move(self, dst, src):
        """ Generate a move from src to dst """
        return mov(src, dst)

    def gen_fill_arguments(self, arg_types, args, live):
        """ This function moves arguments in the proper locations.
        """
        arg_locs, _ = self.determine_arg_locations(arg_types)

        # Setup parameters:
        for arg_loc, arg in zip(arg_locs, args):
            if isinstance(arg_loc, Msp430Register):
                yield self.move(arg_loc, arg)
                live.add(arg_loc)
            else:  # pragma: no cover
                raise NotImplementedError('Parameters in memory not impl')

    def make_call(self, frame, vcall):
        live_regs = frame.live_regs_over(vcall)

        # Caller save registers:
        for register in live_regs:
            if register in self.caller_save:
                yield push(register)

        yield call(vcall.function_name)

        # Restore caller save registers:
        for register in reversed(live_regs):
            if register in self.caller_save:
                yield Pop(register)

    @staticmethod
    def round_upwards(v):
        """ Round value upwards to multiple of 2 """
        return v + (v % 2)

    def gen_prologue(self, frame):
        """ Returns prologue instruction sequence """
        # Label indication function:
        yield Label(frame.name)

        # Callee save registers:
        for reg in self.callee_save:
            if frame.is_used(reg):
                yield push(reg)

        # Adjust stack:
        if frame.stacksize:
            yield Sub(
                ConstSrc(self.round_upwards(frame.stacksize)), RegDst(r1))

        # Setup the frame pointer:
        yield mov(r1, r4)

    def gen_epilogue(self, frame):
        """ Return epilogue sequence for a frame. Adjust frame pointer
            and add constant pool
        """

        # Adjust stack:
        if frame.stacksize:
            yield Add(
                ConstSrc(self.round_upwards(frame.stacksize)), RegDst(r1))

        # Pop save registers back:
        for reg in reversed(self.callee_save):
            if frame.is_used(reg):
                yield Pop(reg)

        # Return from function:
        yield Ret()

        # Add final literal pool:
        for instruction in self.litpool(frame):
            yield instruction

    def litpool(self, frame):
        """ Generate instruction for the current literals """
        # Align at 2 bytes
        if frame.constants:
            yield Alignment(2)

        # Add constant literals:
        while frame.constants:
            label, value = frame.constants.pop(0)
            yield Label(label)
            if isinstance(value, str):
                yield Dw2(value)
            elif isinstance(value, bytes):
                for byte in value:
                    yield Db(byte)
                yield Alignment(2)   # Align at 4 bytes
            else:  # pragma: no cover
                raise NotImplementedError('Constant of type {}'.format(value))

    def determine_arg_locations(self, arg_types):
        """
            Given a set of argument types, determine location for argument
            ABI:
            param1 = r12
            param2 = r13
            param3 = r14
            param4 = r15
            retval = r12
        """
        l = []
        live_in = set()
        regs = [r12, r13, r14, r15]
        for a in arg_types:
            reg = regs.pop(0)
            l.append(reg)
            live_in.add(reg)
        return l, tuple(live_in)

    def determine_rv_location(self, ret_type):
        live_out = set()
        rv = r12
        live_out.add(rv)
        return rv, tuple(live_out)

    def get_runtime(self):
        """ Compiles the runtime support for msp430. It takes some c3 code and
            some assembly helpers.
        """
        # Circular import, but this is possible!
        from ...api import asm, c3c, link
        march = 'msp430'
        # TODO: without the below layout, things go wrong, but why?
        # Layout should not be required here!
        layout = io.StringIO("""
            MEMORY flash LOCATION=0xf000 SIZE=0xfe0 { SECTION(code) }
            MEMORY vector16 LOCATION=0xffe0 SIZE=0x20 { SECTION(reset_vector) }
            MEMORY ram LOCATION=0x200 SIZE=0x800 { SECTION(data) }
        """)
        # report_generator = HtmlReportGenerator(open('msp430.html', 'w'))
        report_generator = DummyReportGenerator()
        with complete_report(report_generator) as reporter:
            obj1 = asm(io.StringIO(RT_ASM_SRC), march)
            obj2 = c3c([io.StringIO(RT_C3_SRC)], [], march, reporter=reporter)
            obj = link([obj1, obj2], layout, partial_link=True)
        return obj


RT_ASM_SRC = """
                     ; Shift left helper:
    __shl_a:
      add.w r12, r12 ; shift 1 bit left
      sub.w #1, r13  ; decrement counter
    __shl:           ; Shift r12 left by r13 bits
      cmp.w #0, r13
      jne __shl_a
      ret

                     ; Shift right helper:
    __shr_a:
      clrc           ; clear carry
      rrc r12        ; shift 1 bit right through carry
      sub.w #1, r13  ; decrement counter
    __shr:           ; Shift r12 right by r13 bits
      cmp.w #0, r13
      jne __shr_a
      ret
"""

# TODO: move the code below to shared location? It is not msp430 specific!
RT_C3_SRC = """
    module msp430_runtime;
    function int __div(int num, int den)
    {
      var int res = 0;
      var int current = 1;

      while (den < num)
      {
        den = den << 1;
        current = current << 1;
      }

      while (current != 0)
      {
        if (num >= den)
        {
          num -= den;
          res = res | current;
        }
        den = den >> 1;
        current = current >> 1;
      }
      return res;
    }

    function int __mul(int a, int b)
    {
      var int res = 0;
      while (b > 0)
      {
        if ((b & 1) == 1)
        {
          res += a;
        }
        a = a << 1;
        b = b >> 1;
      }
      return res;
    }
"""
