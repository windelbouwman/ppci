#!/usr/bin/python

import unittest
import io
from ppci.arch.target_list import msp430target
from ppci.binutils.layout import load_layout
from test_asm import AsmTestCaseBase


class Msp430AssemblerTestCase(AsmTestCaseBase):
    """ Test the msp430 assembler """
    target = msp430target

    def test_mov(self):
        """ Test move """
        self.feed("mov.w r14, r15")
        self.check('0F4E')

    def test_mov_b(self):
        """ Test move """
        self.feed("mov.b r14, r15")
        self.check('4F4E')

    def test_mov_1337(self):
        """ Test the move of an absolute value """
        self.feed("mov.w #0x1337, r12")
        self.check('3C40 3713')

    def test_mov_indirect(self):
        """ Test the move of memory values """
        self.feed("mov.w #0x1337, 0x123(r12)")
        self.check('bC40 3713 2301')

    def test_mov_global(self):
        """ Store at global location (absolute address) """
        self.feed('a:')
        self.feed('dw 0')
        self.feed('b:')
        self.feed('dw 0')
        self.feed('mov.w &a, r0')
        self.feed('mov.w r0, &b')
        self.feed('mov.w &a, &b')
        spec = "MEMORY flash LOCATION=0xf800 SIZE=0x100 {SECTION(code)}"
        layout = load_layout(io.StringIO(spec))
        self.check('0000 0000 1042 00f8 8240 02f8 9242 00f8 02f8', layout)

    def test_add(self):
        """ Test add instruction """
        self.feed("add.w r15, r13")
        self.check('0D5F')

    def test_sub(self):
        """ Test sub instruction """
        self.feed("sub.w r4, r5")
        self.check('0584')

    def test_cmp(self):
        """ Test sub instruction """
        self.feed("cmp.w r6, r7")
        self.check('0796')

    def test_bit(self):
        """ Test bit instruction """
        self.feed("bit.w r8, r9")
        self.check('09b8')

    def test_rrc(self):
        """ Test rrc """
        self.feed("rrc r7")
        self.check('0710')

    def test_rra(self):
        """ Test rra """
        self.feed("rra 0x1234(r6)")
        self.check('1611 3412')

    def test_sxt(self):
        """ Test sxt """
        self.feed("sxt @r4")
        self.check('a411')

    def test_push(self):
        """ Test push """
        self.feed("push @r13+")
        self.check('3d12')

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
