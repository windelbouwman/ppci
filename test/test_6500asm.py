#!/usr/bin/python

import unittest
from test_asm import AsmTestCaseBase


class Mcs6500AssemblerTestCase(AsmTestCaseBase):
    """ Test the 6500 assembler """
    march = 'mcs6500'

    def test_adc(self):
        """ Test add with carry """
        self.feed('adc #10')
        self.check('690a')

    def test_brk(self):
        """ Test simulate interrupt brk """
        self.feed("brk")
        self.check('00')

    def test_clc(self):
        """ Test clear carry flag """
        self.feed("clc")
        self.check('18')

    def test_cld(self):
        """ Test clear decimal mode """
        self.feed("cld")
        self.check('d8')

    def test_cli(self):
        """ Test clear interrupt disable bit """
        self.feed("cli")
        self.check('58')

    def test_clv(self):
        """ Test clear overflow flag """
        self.feed("clv")
        self.check('b8')

    def test_dex(self):
        """ Test decrement index X by 1 """
        self.feed("dex")
        self.check('ca')

    def test_dey(self):
        """ Test decrement index Y by 1 """
        self.feed("dey")
        self.check('88')

    def test_inx(self):
        """ Test increment index X by 1 """
        self.feed("inx")
        self.check('e8')

    def test_iny(self):
        """ Test increment index Y by 1 """
        self.feed("iny")
        self.check('c8')

    def test_nop(self):
        """ Test no operation """
        self.feed("nop")
        self.check('ea')

    def test_pha(self):
        """ Test push accumulator on stack """
        self.feed("pha")
        self.check('48')

    def test_php(self):
        """ Test push processor status on stack """
        self.feed("php")
        self.check('08')

    def test_pla(self):
        """ Test pull accumulator from stack """
        self.feed("pla")
        self.check('68')

    def test_plp(self):
        """ Test pull processor status from stack """
        self.feed("plp")
        self.check('28')

    def test_rti(self):
        """ Test return from interrupt """
        self.feed("rti")
        self.check('40')

    def test_rts(self):
        """ Test return from subroutine """
        self.feed("rts")
        self.check('60')

    @unittest.skip('todo')
    def test_sbc(self):
        """ Test substract with borrow """
        self.feed("sbc #32")
        self.check('e920')

    def test_sec(self):
        """ Test set carry flag """
        self.feed("sec")
        self.check('38')

    def test_sed(self):
        """ Test set decimal flag """
        self.feed("sed")
        self.check('f8')

    def test_sei(self):
        """ Test set interrupt disable status """
        self.feed("sei")
        self.check('78')

    def test_tax(self):
        """ Test transfer accumulator to index X """
        self.feed("tax")
        self.check('aa')

    def test_tay(self):
        """ Test transfer accumulator to index Y """
        self.feed("tay")
        self.check('a8')

    def test_tsx(self):
        """ Test transfer stack pointer to index X """
        self.feed("tsx")
        self.check('ba')

    def test_txa(self):
        """ Test transfer index X to accumulator """
        self.feed("txa")
        self.check('8a')

    def test_txs(self):
        """ Test transfer index X to stack register """
        self.feed("txs")
        self.check('9a')

    def test_tya(self):
        """ Test transfer index Y to accumulator """
        self.feed("tya")
        self.check('98')


if __name__ == '__main__':
    unittest.main()
