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


if __name__ == '__main__':
    unittest.main()
