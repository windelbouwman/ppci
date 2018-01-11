from test_asm import AsmTestCaseBase
import unittest


class MipsAssemblyTestCase(AsmTestCaseBase):
    """ Mips assembly test case """
    march = 'mips'

    def test_add(self):
        self.feed('add v0, v1, a0')
        self.check('20106400')

    def test_addi(self):
        self.feed('addi v0, v1, -1')
        self.check('ffff6220')

    def test_sub(self):
        self.feed('sub v0, v1, a0')
        self.check('22106400')

    def test_lw(self):
        self.feed('lw r1, -8(r30)')
        self.check('f8ffc18f')

    def test_sw(self):
        self.feed('sw ra, 4(sp)')
        self.check('0400bfaf')

    def test_jal(self):
        self.feed('jal woot')
        self.feed('woot:')
        self.check('0100000c')


if __name__ == '__main__':
    unittest.main()
