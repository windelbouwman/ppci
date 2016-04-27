"""
MSP430 architecture description.
"""

import io
from ..arch import Architecture, VCall
from .registers import r10, r11, r12, r13, r14, r15, Msp430Register
from .registers import get_register
from ...ir import i8, i16, ptr
from .instructions import isa, mov, nop, ret, pop, clrc, clrn, clrz
from ..data_instructions import data_isa
from .frame import Msp430Frame
from ...binutils.assembler import BaseAssembler
from ...utils.reporting import HtmlReportGenerator, complete_report
from ...utils.reporting import DummyReportGenerator


class Msp430Assembler(BaseAssembler):
    def __init__(self):
        super().__init__()
        self.add_keyword('nop')
        self.add_rule(
            'instruction', ['nop'],
            lambda rhs: nop())
        self.add_keyword('ret')
        self.add_rule(
            'instruction', ['ret'],
            lambda rhs: ret())
        self.add_keyword('pop')
        self.add_rule(
            'instruction', ['pop', 'reg'],
            lambda rhs: pop(rhs[1]))
        self.add_keyword('clrc')
        self.add_rule(
            'instruction', ['clrc'],
            lambda rhs: clrc())
        self.add_keyword('clrn')
        self.add_rule(
            'instruction', ['clrn'],
            lambda rhs: clrn())
        self.add_keyword('clrz')
        self.add_rule(
            'instruction', ['clrz'],
            lambda rhs: clrz())


def get_runtime():
    """ Compiles the runtime support for msp430. It takes some c3 code and
        some assembly helpers.
    """
    # Circular import, but this is possible!
    from ...api import asm, c3c, link
    asm_src = """
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
    c3_src = """
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
    march = 'msp430'
    layout = io.StringIO("""
        MEMORY flash LOCATION=0xf000 SIZE=0xfe0 { SECTION(code) }
        MEMORY vector16 LOCATION=0xffe0 SIZE=0x20 { SECTION(reset_vector) }
        MEMORY ram LOCATION=0x200 SIZE=0x800 { SECTION(data) }
    """)
    # report_generator = HtmlReportGenerator(open('msp430.html', 'w'))
    report_generator = DummyReportGenerator()
    with complete_report(report_generator) as reporter:
        obj1 = asm(io.StringIO(asm_src), march)
        obj2 = c3c([io.StringIO(c3_src)], [], march, reporter=reporter)
        obj = link([obj1, obj2], layout, march, partial_link=True)
    return obj


class Msp430Arch(Architecture):
    """ Texas Instruments msp430 target architecture """
    name = 'msp430'

    def __init__(self, options=None):
        super().__init__(options=options)
        self.byte_sizes['int'] = 2
        self.byte_sizes['ptr'] = 2
        self.value_classes[i16] = Msp430Register
        self.value_classes[ptr] = Msp430Register
        self.value_classes[i8] = Msp430Register
        self.isa = isa + data_isa
        self.assembler = Msp430Assembler()
        self.assembler.gen_asm_parser(self.isa)
        # import ipdb; ipdb.set_trace()

        self.FrameClass = Msp430Frame

        self.registers.append(r10)
        self.registers.append(r11)
        self.registers.append(r12)
        self.registers.append(r13)
        self.registers.append(r14)
        self.registers.append(r15)

    def move(self, dst, src):
        """ Generate a move from src to dst """
        return mov(src, dst)

    def gen_call(self, label, arg_types, ret_type, args, res_var):
        arg_locs, live_in, rv, live_out = \
            self.determine_arg_locations(arg_types, ret_type)

        # Setup parameters:
        for arg_loc, arg in zip(arg_locs, args):
            if isinstance(arg_loc, Msp430Register):
                yield self.move(arg_loc, arg)
            else:  # pragma: no cover
                raise NotImplementedError('Parameters in memory not impl')

        yield VCall(label, extra_uses=live_in, extra_defs=live_out)
        yield self.move(res_var, rv)

    def get_register(self, color):
        return get_register(color)

    def determine_arg_locations(self, arg_types, ret_type):
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

        live_out = set()
        rv = r12
        live_out.add(rv)
        return l, tuple(live_in), rv, tuple(live_out)

    def get_runtime(self):
        return get_runtime()
