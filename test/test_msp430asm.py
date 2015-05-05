#!/usr/bin/python

import unittest
from ppci.target.target_list import msp430target
from test_asm import AsmTestCaseBase


class Msp430AssemblerTestCase(AsmTestCaseBase):
    """ Test the msp430 assembler """
    target = msp430target

    def testMov(self):
        self.feed("mov r14, r15")
        self.check('0F4E')

    def testMov1337(self):
        self.feed("mov 0x1337, r12")
        self.check('3C40 3713')

    def test_add(self):
        """ Test add instruction """
        self.feed("add r15, r13")
        self.check('0D5F')

    def test_sub(self):
        """ Test sub instruction """
        self.feed("sub r4, r5")
        self.check('0584')

    def test_cmp(self):
        """ Test sub instruction """
        self.feed("cmp r6, r7")
        self.check('0796')

    def test_reti(self):
        """ Test return from interrupt """
        self.feed("reti")
        self.check('0013')

    def test_jne(self):
        """ Test jumping around """
        self.feed('jne a')
        self.feed('jne a')
        self.feed('a:')
        self.feed('jne a')
        self.feed('jne a')
        self.check('0120 0020 ff23 fe23')


if __name__ == '__main__':
    unittest.main()
