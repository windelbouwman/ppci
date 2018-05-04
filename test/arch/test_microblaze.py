#!/usr/bin/python

import unittest
from test_asm import AsmTestCaseBase


@unittest.skip('TODO')
class MicroBlazeAssemblerTestCase(AsmTestCaseBase):
    march = 'microblaze'

    def test_add(self):
        self.feed("add r2, r5, r7")
        self.check('0000 0000')


if __name__ == '__main__':
    unittest.main()
