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

    def test_and(self):
        """ Test and """
        self.feed('and #0x10')
        self.feed('and $4400,X')
        self.feed('and ($44,X)')
        self.check('2910 3d0044 2144')

    def test_asl(self):
        """ Test arithmatic shift left """
        self.feed('asl')
        self.feed('asl $4400')
        self.feed('asl $4400,X')
        self.check('0a 0e0044 1e0044')

    def test_bcs(self):
        """ Test branch if carry set """
        self.feed('bcs $44')
        self.check('b044')

    def test_beq(self):
        """ Test branch if equal """
        self.feed('beq $44')
        self.check('f044')

    def test_beq_label(self):
        """ Test branch if equal """
        self.feed('beq a')
        self.feed('beq a')
        self.feed('a: beq a')
        self.feed('beq a')
        self.check('f002 f000 f0fe f0fc')

    def test_bit(self):
        """ Test bit test """
        self.feed('bit $4400')
        self.check('2c0044')

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

    def test_cmp(self):
        """ Test compare accumulator """
        self.feed('cmp #$44')
        self.feed('cmp $4400')
        self.feed('cmp $4400,X')
        self.feed('cmp $4400,y')
        self.feed('cmp ($44,x)')
        self.feed('cmp ($44),y')
        self.check('c944 cd0044 dd0044 d90044 c144 d144')

    def test_cpx(self):
        """ Test compare X register """
        self.feed('cpx #$44')
        self.feed('cpx $4400')
        self.check('e044 ec0044')

    def test_cpy(self):
        """ Test compare Y register """
        self.feed('cpy #$44')
        self.feed('cpy $4400')
        self.check('c044 cc0044')

    def test_dec(self):
        """ Test decrement """
        self.feed("dec $4400")
        self.feed("dec $4400,x")
        self.check('ce0044 de0044')

    def test_dex(self):
        """ Test decrement index X by 1 """
        self.feed("dex")
        self.check('ca')

    def test_dey(self):
        """ Test decrement index Y by 1 """
        self.feed("dey")
        self.check('88')

    def test_eor(self):
        """ Test bitwise exclusive or """
        self.feed("eor #$44")
        self.feed("eor $4400")
        self.feed("eor $4400,x")
        self.feed("eor $4400,y")
        self.feed("eor ($44,x)")
        self.feed("eor ($44),y")
        self.check('4944 4D0044 5D0044 590044 4144 5144')

    def test_inc(self):
        """ Test increment """
        self.feed("inc $4400")
        self.feed("inc $4400,x")
        self.check('ee0044 fe0044')

    def test_inx(self):
        """ Test increment index X by 1 """
        self.feed("inx")
        self.check('e8')

    def test_iny(self):
        """ Test increment index Y by 1 """
        self.feed("iny")
        self.check('c8')

    def test_jmp(self):
        """ Test jump """
        self.feed("jmp $5597")
        self.check('4c 9755')

    def test_jsr(self):
        """ Test jump to subroutine """
        self.feed("jsr $5597")
        self.check('20 9755')

    def test_jsr_label(self):
        """ Test jump to subroutine """
        self.feed("jsr a")
        self.feed("a: jsr a")
        self.feed("jsr a")
        self.check('200300 200300 200300')

    def test_lda(self):
        """ Test load accumulator """
        self.feed("lda #$44")
        self.feed("lda $4400")
        self.feed("lda ($44),y")
        self.check('a944 ad0044 b144')

    def test_ldx(self):
        """ Test load X register """
        self.feed("ldx #$44")
        self.feed("ldx $4400")
        self.feed("ldx $4400,y")
        self.check('a244 ae0044 be0044')

    def test_ldy(self):
        """ Test load Y register """
        self.feed("ldy #$44")
        self.feed("ldy $4400")
        self.feed("ldy $4400,x")
        self.check('a044 ac0044 bc0044')

    def test_lsr(self):
        """ Test logical shift right """
        self.feed("lsr")
        self.feed("lsr $4400")
        self.feed("lsr $4400,x")
        self.check('4a 4e0044 5e0044')

    def test_ora(self):
        """ Test bitwise or with accumulator """
        self.feed("ora #$44")
        self.feed("ora $4400")
        self.feed("ora $4400,x")
        self.feed("ora $4400,y")
        self.feed("ora ($44,x)")
        self.feed("ora ($44),y")
        self.check('0944 0D0044 1D0044 190044 0144 1144')

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

    def test_rol(self):
        """ Test rotate left """
        self.feed("rol")
        self.feed("rol $4400")
        self.feed("rol $4400,x")
        self.check('2a 2e0044 3e0044')

    def test_ror(self):
        """ Test rotate right """
        self.feed("ror")
        self.feed("ror $4400")
        self.feed("ror $4400,x")
        self.check('6a 6e0044 7e0044')

    def test_rti(self):
        """ Test return from interrupt """
        self.feed("rti")
        self.check('40')

    def test_rts(self):
        """ Test return from subroutine """
        self.feed("rts")
        self.check('60')

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

    def test_sta(self):
        """ Test store accumulator """
        self.feed("sta $4400")
        self.feed("sta $4400,x")
        self.feed("sta $4400,y")
        self.feed("sta ($44,x)")
        self.feed("sta ($44),y")
        self.check('8d0044 9d0044 990044 8144 9144')

    def test_stx(self):
        """ Test store X register """
        self.feed("stx $4400")
        self.check('8e0044')

    def test_sty(self):
        """ Test store Y register """
        self.feed("sty $4400")
        self.check('8c0044')

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
