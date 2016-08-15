from test_asm import AsmTestCaseBase
import unittest


class Stm8AssemblerTestCase(AsmTestCaseBase):
    """ STM8 instruction assembly test case """
    march = 'stm8'


    def test_adc_a_byte(self):
        self.feed('ADC A,#$12')
        self.check('A912')

#    def test_adc_a_shortmem(self):
#        self.feed('ADC A,$12')
#        self.check('B912')

    def test_adc_a_longmem(self):
        self.feed('ADC A,$1234')
        self.check('C91234')

    def test_adc_a_x(self):
        self.feed('ADC A,(X)')
        self.check('F9')

    def test_adc_a_longoff_x(self):
        self.feed('ADC A,($1234,X)')
        self.check('D91234')

    def test_adc_a_y(self):
        self.feed('ADC A,(Y)')
        self.check('90F9')

    def test_adc_a_longoff_y(self):
        self.feed('ADC A,($1234,Y)')
        self.check('90D91234')

    def test_adc_a_shortoff_sp(self):
        self.feed('ADC A,($12,SP)')
        self.check('1912')

    def test_adc_a_longptr(self):
        self.feed('ADC A,[$1234]')
        self.check('72C91234')

    def test_adc_a_longptr_x(self):
        self.feed('ADC A,([$1234],X)')
        self.check('72D91234')

    def test_adc_a_shortptr_y(self):
        self.feed('ADC A,([$12],Y)')
        self.check('91D912')


    def test_nop(self):
        self.feed('NOP')
        self.check('9D')


if __name__ == '__main__':
    unittest.main()
