from test_asm import AsmTestCaseBase
import unittest


class Stm8AssemblerTestCase(AsmTestCaseBase):
    """ STM8 instruction assembly test case """
    march = 'stm8'

    def test_nop(self):
        self.feed('nop')
        self.check('9D')


if __name__ == '__main__':
    unittest.main()