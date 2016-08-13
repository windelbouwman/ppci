from test_asm import AsmTestCaseBase
import unittest


class Stm8AssemblerTestCase(AsmTestCaseBase):
    """ STM8 instruction assembly test case """
    march = 'stm8'


    def test_AdcAByte(self):
        self.feed('adc A, #$12')
        self.check('A912')

#    def test_AdcAShortmem(self):
#        self.feed('adc A, $12')
#        self.check('B912')

    def test_AdcALongmem(self):
        self.feed('adc A, $1234')
        self.check('C91234')

    def test_AdcAX(self):
        self.feed('adc A, (X)')
        self.check('F9')

    def test_AdcALongoffX(self):
        self.feed('adc A, ($1234,X)')
        self.check('D91234')

    def test_AdcAY(self):
        self.feed('adc A, (Y)')
        self.check('90F9')

    def test_AdcALongoffY(self):
        self.feed('adc A, ($1234,Y)')
        self.check('90D91234')

    def test_AdcAShortoffSP(self):
        self.feed('adc A, ($12,SP)')
        self.check('1912')

    def test_AdcALongptr(self):
        self.feed('adc A, [$1234]')
        self.check('72C91234')

    def test_AdcALongptrX(self):
        self.feed('adc A, ([$1234], X)')
        self.check('72D91234')

    def test_AdcAShortptrY(self):
        self.feed('adc A, ([$12], Y)')
        self.check('91D912')


    def test_Nop(self):
        self.feed('nop')
        self.check('9D')


if __name__ == '__main__':
    unittest.main()
