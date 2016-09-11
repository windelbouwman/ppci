#!/usr/bin/python

import unittest
import io
from ppci.binutils.layout import Layout
from ppci.api import get_arch
from ppci.arch.arch import Frame, VCall
from ppci.arch.avr.instructions import Push, Pop
from ppci.arch.avr.registers import r17, r19r18, r18, r19, r20, r25, r26
from test_asm import AsmTestCaseBase


class AvrArchitectureTestCase(unittest.TestCase):
    def test_gen_call(self):
        arch = get_arch('avr')
        frame = Frame('foo', [], [], None, [])
        pushed = []
        popped = []
        vcall = VCall('bar')
        vcall.live_in = {r17, r19r18}
        vcall.live_out = {r17, r19r18}
        frame.live_regs_over = lambda ins: [r17, r19r18, r20, r25, r26]
        for instruction in arch.make_call(frame, vcall):
            if isinstance(instruction, Push):
                pushed.append(instruction.rd)
            if isinstance(instruction, Pop):
                popped.append(instruction.rd)
        self.assertTrue(pushed)
        self.assertTrue(popped)
        popped.reverse()
        self.assertSequenceEqual(pushed, popped)
        self.assertSequenceEqual([r18, r19, r20, r25, r26], pushed)


class AvrAssemblerTestCase(AsmTestCaseBase):
    march = 'avr'

    def test_nop(self):
        self.feed("nop")
        self.check('0000')

    def test_mov(self):
        self.feed("mov r18, r20")
        self.check('242f')

    def test_movw(self):
        self.feed("movw r19:r18, r21:r20")
        self.feed("movw Z, Y")
        self.check('9a01 fe01')

    def test_add(self):
        self.feed("add r11, r7")
        self.check('b70c')

    def test_adc(self):
        self.feed("adc r21, r22")
        self.check('561f')

    def test_adiw(self):
        self.feed("adiw Y, 20")
        self.check('6496')

    def test_sub(self):
        self.feed("sub r1, r1")
        self.check('1118')

    def test_sbiw(self):
        self.feed("sbiw Y, 20")
        self.check('6497')

    def test_sbc(self):
        self.feed("sbc r2, r3")
        self.check('2308')

    def test_and(self):
        self.feed("and r18, r6")
        self.check('2621')

    def test_or(self):
        self.feed("or r12, r26")
        self.check('ca2a')

    def test_eor(self):
        self.feed("eor r13, r21")
        self.check('d526')

    def test_cp(self):
        self.feed("cp r12, r20")
        self.check('c416')

    def test_cpc(self):
        self.feed("cpc r11, r19")
        self.check('b306')

    def test_cpi(self):
        self.feed("cpi r19, 23")
        self.check('3731')

    def test_ret(self):
        self.feed("ret")
        self.check('0895')

    def test_reti(self):
        self.feed("reti")
        self.check('1895')

    def test_ldi(self):
        self.feed("ldi r26, 0xcb")
        self.feed("ldi r17, 50")
        self.check('abec 12e3')

    def test_in(self):
        self.feed("in r13, 5")
        self.feed("in r25, 57")
        self.check('d5b0 99b7')

    def test_out(self):
        self.feed("out 12, r15")
        self.feed("out 55, r24")
        self.check('fcb8 87bf')

    def test_push(self):
        self.feed("push r30")
        self.feed("push r3")
        self.check('ef93 3f92')

    def test_pop(self):
        self.feed("pop r29")
        self.feed("pop r9")
        self.check('df91 9f90')

    def test_ld(self):
        """ Test ld using X register """
        self.feed("ld r23, X")
        self.feed("ld r2, X")
        self.feed("ld r3, x+")
        self.feed("ld r4, -x")
        self.check('7c91 2c90 3d90 4e90')

    def test_ldd_y(self):
        """ Test ldd using Y register """
        self.feed("ldd r19, Y+60")
        self.feed("ldd r13, Y+13")
        self.check('3cad dd84')

    def test_ldd_z(self):
        self.feed("ldd r11, Z+60")
        self.feed("ldd r14, Z+13")
        self.check('b4ac e584')

    def test_st(self):
        self.feed("st X, r22")
        self.feed("st X, r5")
        self.check('6c93 5c92')

    def test_std_y(self):
        self.feed("std Y+33, r9")
        self.feed("std Y+1, r11")
        self.check('99a2 b982')

    def test_std_z(self):
        self.feed("std Z+2, r24")
        self.feed("std Z+33, r7")
        self.check('8283 71a2')

    def test_lds(self):
        self.feed("lds r26, 0xabcd")
        self.feed("lds r8, 0x1234")
        self.check('a091cdab 80903412')

    def test_sts(self):
        self.feed("sts 0x9a54, r25")
        self.feed("sts 0x5678, r7")
        self.check('9093549a 70927856')

    def test_inc(self):
        self.feed("inc r28")
        self.feed("inc r2")
        self.check('c395 2394')

    def test_dec(self):
        self.feed("dec r27")
        self.feed("dec r1")
        self.check('ba95 1a94')

    def test_rjmp(self):
        self.feed("rjmp a")
        self.feed("rjmp a")
        self.feed("a: rjmp a")
        self.feed("rjmp a")
        self.check('01c0 00c0 ffcf fecf')

    def test_further_rjmp(self):
        spec = "MEMORY flash LOCATION=0x1234 SIZE=0x100 { SECTION(code) }"
        layout = Layout.load(io.StringIO(spec))
        self.feed("rjmp a")
        self.feed("rjmp a")
        self.feed("a: rjmp a")
        self.feed("rjmp a")
        self.check('01c0 00c0 ffcf fecf', layout=layout)

    def test_call(self):
        self.feed("call a")
        self.feed("call a")
        self.feed("a: call a")
        self.feed("call a")
        self.check('01d0 00d0 ffdf fedf')

    def test_brne(self):
        self.feed("brne a")
        self.feed("brne a")
        self.feed("a: brne a")
        self.feed("brne a")
        self.check('09f4 01f4 f9f7 f1f7')

    def test_breq(self):
        self.feed("breq a")
        self.feed("breq a")
        self.feed("a: breq a")
        self.feed("breq a")
        self.check('09f0 01f0 f9f3 f1f3')

    def test_brlt(self):
        self.feed("brlt a")
        self.feed("brlt a")
        self.feed("a: brlt a")
        self.feed("brlt a")
        self.check('0cf0 04f0 fcf3 f4f3')

    def test_ldi_address(self):
        """ Test if lo and hi loads from a relocatable constant work """
        self.feed("a: ldi r16, low(a)")
        self.feed("ldi r16, high(a)")
        spec = "MEMORY flash LOCATION=0x1234 SIZE=0x100 { SECTION(code) }"
        layout = Layout.load(io.StringIO(spec))
        self.check('04e3 02e1', layout=layout)


if __name__ == '__main__':
    unittest.main()
