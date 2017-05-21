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
        self.check('9c 22 00 c8')

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

    def test_or(self):
        self.feed("l.or r1, r2, r3")
        self.check('e0 22 18 04')

    def test_ori(self):
        self.feed("l.ori r1, r2, 200")
        self.check('a8 22 00 c8')

    def test_sub(self):
        self.feed("l.sub r1, r2, r3")
        self.check('e0 22 18 02')

    def test_xor(self):
        self.feed("l.xor r1, r2, r3")
        self.check('e0 22 18 05')

    def test_xori(self):
        self.feed("l.xori r1, r2, 200")
        self.check('ac 22 00 c8')


if __name__ == '__main__':
    unittest.main()
