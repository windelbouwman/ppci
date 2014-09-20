#!/usr/bin/python

import unittest
from ppci.target.target_list import msp430target
from test_asm import AsmTestCaseBase


class Msp430AssemblerTestCase(AsmTestCaseBase):
    def setUp(self):
        super().setUp()
        self.target = msp430target
        self.assembler = msp430target.assembler

    def testMov(self):
        self.feed("mov r14, r15")
        self.check('0F4E')

    def testMov1337(self):
        self.feed("mov 0x1337, r12")
        self.check('3C403713')

    def testAdd(self):
        self.feed("add r15, r13")
        self.check('0D5F')

    def testReti(self):
        self.feed("reti")
        self.check('0013')


if __name__ == '__main__':
    unittest.main()
