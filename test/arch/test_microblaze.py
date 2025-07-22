#!/usr/bin/python

import unittest
from ..test_asm import AsmTestCaseBase


class MicroBlazeAssemblerTestCase(AsmTestCaseBase):
    march = 'microblaze'

    def test_add(self):
        """ Add two registers into a third """
        self.feed("add r2, r5, r7")
        # From microblaze reference manual:
        # bit labels are msbit=0, lsbit=31
        # msb=0                              lsb=31
        # 0         6     11    16               31
        # 000 K C 0 rD    rA    rB    000 0000 0000
        # 000 0 0 0 00010 00101 00111 000 0000 0000
        # 0000 0000 0100 0101 0011 1000 0000 0000
        self.check('00 45 38 00')
        # Bit reverse per byte:
        # 0000 0000 1010 0010 0001 1100 0000 0000
        # self.check('00 a2 1c 00')
        # Bit-reversed big endian:
        # 0000 0000 00011100 10100 01000 0 0 0 0000
        # 0000 0000 0001 1100 1010 0010 0000 0000
        # Big endian, bit reversed format:
        # self.check('00 1c a2 00')

    def test_addik(self):
        """ Test add immediate """
        self.feed("addik r5, r0, 65")
        self.check('30 a0 00 41')


if __name__ == '__main__':
    unittest.main()
