#!/usr/bin/python

import unittest
import io
from ppci.target.target_list import avr_target
from ppci.binutils.layout import load_layout
from test_asm import AsmTestCaseBase


class AvrAssemblerTestCase(AsmTestCaseBase):
    target = avr_target

    def test_nop(self):
        self.feed("nop")
        self.check('0000')

    def test_mov(self):
        self.feed("mov r18, r20")
        self.check('242f')

    def test_add(self):
        self.feed("add r11, r7")
        self.check('b70c')

    def test_sub(self):
        self.feed("sub r1, r1")
        self.check('1118')

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

    @unittest.skip('todo')
    def test_breq(self):
        self.feed("breq a")
        self.feed("breq a")
        self.feed("a: breq a")
        self.feed("breq a")
        self.check('09f4 01f4 f9f7 f1f7')

    @unittest.skip('todo')
    def test_jmp(self):
        self.feed("jmp a")
        self.feed("jmp a")
        self.feed("a: jmp a")
        self.feed("jmp a")
        self.check('01c0 00c0 ffcf fecf')


if __name__ == '__main__':
    unittest.main()
