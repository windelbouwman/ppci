import unittest
from test_asm import AsmTestCaseBase


class Or1kOrbisTestCase(AsmTestCaseBase):
    """ Check the open risc basic instruction set (orbis) """
    march = 'or1k'

    def test_add(self):
        self.feed("l.add r1, r2, r3")
        self.check('e0 22 18 00')

    def test_addc(self):
        self.feed("l.addc r1, r2, r3")
        self.check('e0 22 18 01')

    def test_addi(self):
        self.feed("l.addi r1, r2, 200")
        self.feed("l.addi r1, r1, -28")
        self.check('9c 22 00 c8 9c 21 ff e4')

    def test_addic(self):
        self.feed("l.addic r1, r2, 200")
        self.check('a0 22 00 c8')

    def test_and(self):
        self.feed("l.and r1, r2, r3")
        self.check('e0 22 18 03')

    def test_andi(self):
        self.feed("l.andi r1, r2, 200")
        self.check('a4 22 00 c8')

    def test_bf(self):
        self.feed("l.bf x")
        self.feed("x: l.bf x")
        self.feed("l.bf x")
        self.check('10 00 00 01  10 00 00 00  13 ff ff ff')

    def test_bnf(self):
        self.feed("l.bnf x")
        self.feed("x: l.bnf x")
        self.feed("l.bnf x")
        self.check('0c 00 00 01  0c 00 00 00  0f ff ff ff')

    def test_cmov(self):
        self.feed("l.cmov r1, r2, r3")
        self.check('e0 22 18 0e')

    def test_csync(self):
        self.feed("l.csync")
        self.check('23 00 00 00')

    def test_div(self):
        self.feed("l.div r1, r2, r3")
        self.check('e0 22 1b 09')

    def test_divu(self):
        self.feed("l.divu r1, r2, r3")
        self.check('e0 22 1b 0a')

    def test_extbs(self):
        self.feed("l.extbs r1, r2")
        self.check('e0 22 00 4c')

    def test_extbz(self):
        self.feed("l.extbz r1, r2")
        self.check('e0 22 00 cc')

    def test_exths(self):
        self.feed("l.exths r1, r2")
        self.check('e0 22 00 0c')

    def test_exthz(self):
        self.feed("l.exthz r1, r2")
        self.check('e0 22 00 8c')

    def test_j(self):
        """ Test unconditional jump """
        self.feed("l.j x")
        self.feed("x:l.j x")
        self.feed("l.j x")
        self.check('00 00 00 01  00 00 00 00  03 ff ff ff')

    def test_jal(self):
        """ Check jump and link """
        self.feed("l.jal x")
        self.feed("x:l.jal x")
        self.feed("l.jal x")
        self.check('04 00 00 01  04 00 00 00  07 ff ff ff')

    def test_jalr(self):
        self.feed("l.jalr r2")
        self.check('48 00 10 00')

    def test_jr(self):
        self.feed("l.jr r2")
        self.check('44 00 10 00')

    def test_lbs(self):
        self.feed("l.lbs r1, 30000(r2)")
        self.check('90 22 75 30')

    def test_lbz(self):
        self.feed("l.lbz r1, 30000(r2)")
        self.check('8c 22 75 30')

    def test_lhs(self):
        self.feed("l.lhs r1, 30000(r2)")
        self.check('98 22 75 30')

    def test_lhz(self):
        self.feed("l.lhz r1, 30000(r2)")
        self.check('94 22 75 30')

    def test_lwa(self):
        self.feed("l.lwa r1, 30000(r2)")
        self.check('6c 22 75 30')

    def test_lws(self):
        self.feed("l.lws r1, 30000(r2)")
        self.check('88 22 75 30')

    def test_lwz(self):
        self.feed("l.lwz r1, 30000(r2)")
        self.check('84 22 75 30')

    def test_nop(self):
        self.feed("l.nop 0x1234")
        self.check('15 00 12 34')

    def test_movhi(self):
        self.feed("l.movhi r3, 0xcafe")
        self.check('18 60 ca fe')

    def test_movhi_label(self):
        self.feed("l.movhi r3, hi(foo)")
        self.feed("l.movhi r3, lo(foo)")
        self.feed("foo: db 1")
        self.check('18 60 00 00 18 60 00 08 01')

    def test_mul(self):
        self.feed("l.mul r1, r2, r3")
        self.check('e0 22 1b 06')

    def test_mulu(self):
        """ Check unsigned multiplication """
        self.feed("l.mulu r1, r2, r3")
        self.check('e0 22 1b 0b')

    def test_or(self):
        """ Check or """
        self.feed("l.or r1, r2, r3")
        self.check('e0 22 18 04')

    def test_ori(self):
        """ Test or with immediate """
        self.feed("l.ori r1, r2, 200")
        self.check('a8 22 00 c8')

    def test_sfeq(self):
        self.feed("l.sfeq r1, r2")
        self.check('e4 01 10 00')

    def test_sfne(self):
        self.feed("l.sfne r1, r2")
        self.check('e4 21 10 00')

    def test_sfgtu(self):
        self.feed("l.sfgtu r1, r2")
        self.check('e4 41 10 00')

    def test_sfgeu(self):
        self.feed("l.sfgeu r1, r2")
        self.check('e4 61 10 00')

    def test_sfltu(self):
        self.feed("l.sfltu r1, r2")
        self.check('e4 81 10 00')

    def test_sfleu(self):
        self.feed("l.sfleu r1, r2")
        self.check('e4 a1 10 00')

    def test_sfgts(self):
        self.feed("l.sfgts r1, r2")
        self.check('e5 41 10 00')

    def test_sfges(self):
        self.feed("l.sfges r1, r2")
        self.check('e5 61 10 00')

    def test_sflts(self):
        self.feed("l.sflts r1, r2")
        self.check('e5 81 10 00')

    def test_sfles(self):
        self.feed("l.sfles r1, r2")
        self.check('e5 a1 10 00')

    def test_sb(self):
        """ Test store byte """
        self.feed("l.sb 30000(r1), r2")
        self.check('d9 c1 15 30')

    def test_sh(self):
        """ Test store half word """
        self.feed("l.sh 30000(r1), r2")
        self.check('dd c1 15 30')

    def test_sll(self):
        """ Test shift left logical """
        self.feed("l.sll r1, r2, r3")
        self.check('e0 22 18 08')

    def test_slli(self):
        """ Test shift left logical """
        self.feed("l.slli r1, r2, 33")
        self.check('b8 22 00 21')

    def test_srl(self):
        """ Test shift right logical """
        self.feed("l.srl r1, r2, r3")
        self.check('e0 22 18 48')

    def test_srli(self):
        """ Test shift right logical with immediate """
        self.feed("l.srli r1, r2, 33")
        self.check('b8 22 00 61')

    def test_sra(self):
        """ Test shift right arithmatic """
        self.feed("l.sra r1, r2, r3")
        self.check('e0 22 18 88')

    def test_srai(self):
        """ Test shift right arithmatic """
        self.feed("l.srai r1, r2, 33")
        self.check('b8 22 00 a1')

    def test_sub(self):
        self.feed("l.sub r1, r2, r3")
        self.check('e0 22 18 02')

    def test_sw(self):
        """ Test store word """
        self.feed("l.sw 30000(r1), r2")
        self.check('d5 c1 15 30')

    def test_swa(self):
        """ Test store word atomic """
        self.feed("l.swa 30000(r1), r2")
        self.check('cd c1 15 30')

    def test_xor(self):
        self.feed("l.xor r1, r2, r3")
        self.check('e0 22 18 05')

    def test_xori(self):
        self.feed("l.xori r1, r2, 200")
        self.check('ac 22 00 c8')


if __name__ == '__main__':
    unittest.main()
