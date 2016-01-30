#!/usr/bin/python

import unittest
from test_asm import AsmTestCaseBase


class Mos6500AssemblerTestCase(AsmTestCaseBase):
    """ Test the 6500 assembler """
    march = '6500'

    def test_brk(self):
        """ Test simulate interrupt brk """
        self.feed("brk")
        self.check('00')


if __name__ == '__main__':
    unittest.main()
