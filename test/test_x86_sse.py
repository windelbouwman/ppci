
import unittest
from test_asm import AsmTestCaseBase


class Sse1TestCase(AsmTestCaseBase):
    """ Checks sse1 instructions """
    march = 'x86_64'

    def test_movss(self):
        """ Test move scalar single-fp values """
        self.feed('movss xmm4, xmm6')
        self.feed('movss xmm3, [rax, 10]')
        self.feed('movss [rax, 10], xmm9')
        self.check('f30f10e6 f30f10580a f3440f11480a')

    def test_addss(self):
        """ Test add scalar single-fp values """
        self.feed('addss xmm13, xmm9')
        self.feed('addss xmm6, [r11, 1000]')
        self.check('f3450f58e9 f3410f58b3e8030000')

    def test_subss(self):
        """ Test substract scalar single-fp values """
        self.feed('subss xmm11, xmm5')
        self.feed('subss xmm1, [rax, 332]')
        self.check('f3440f5cdd f30f5c884c010000')

    def test_mulss(self):
        """ Test multiply scalar single-fp values """
        self.feed('mulss xmm14, xmm2')
        self.feed('mulss xmm8, [rsi, 3]')
        self.check('f3440f59f2 f3440f594603')

    def test_divss(self):
        """ Test divide scalar single-fp values """
        self.feed('divss xmm7, xmm13')
        self.feed('divss xmm6, [rax, 55]')
        self.check('f3410f5efd f30f5e7037')

    def test_cvtsi2ss(self):
        """ Test cvtsi2ss """
        self.feed('cvtsi2ss xmm7, rdx')
        self.feed('cvtsi2ss xmm3, [rbp, 13]')
        self.check('f3480f2afa f3480f2a5d0d')

    def test_comiss(self):
        """ Test compare single scalar """
        self.feed('comiss xmm2, [rcx]')
        self.check('0f2f11')

    def test_ucomiss(self):
        """ Test unordered compare single scalar """
        self.feed('ucomiss xmm0, xmm1')
        self.check('0f2ec1')


class Sse2TestCase(AsmTestCaseBase):
    """ Checks sse2 instructions """
    march = 'x86_64'

    def test_movsd(self):
        """ Test move float64 values """
        self.feed('movsd xmm4, xmm6')
        self.feed('movsd xmm3, [rax, 10]')
        self.feed('movsd [rax, 18], xmm9')
        self.check('f20f10e6 f20f10580a f2440f114812')

    def test_addsd(self):
        """ Test add scalar float64 """
        self.feed('addsd xmm14, xmm14')
        self.feed('addsd xmm14, [100]')
        self.check('f2450f58f6 f2440f58342564000000')

    def test_subsd(self):
        """ Test substract scalar float64 """
        self.feed('subsd xmm9, xmm2')
        self.feed('subsd xmm4, [r14]')
        self.check('f2440f5cca f2410f5c26')

    def test_mulsd(self):
        """ Test multiply scalar float64 """
        self.feed('mulsd xmm6, xmm12')
        self.feed('mulsd xmm5, [rcx, 99]')
        self.check('f2410f59f4 f20f596963')

    def test_divsd(self):
        """ Test divide scalar float64 """
        self.feed('divsd xmm3, xmm1')
        self.feed('divsd xmm2, [r9]')
        self.check('f20f5ed9 f2410f5e11')

    def test_cvtsd2si(self):
        """ Test convert scalar float64 to integer"""
        self.feed('cvtsd2si rbx, xmm1')
        self.feed('cvtsd2si r11, [rax, 111]')
        self.check('f2480f2dd9 f24c0f2d586f')

    def test_cvtsi2sd(self):
        """ Test convert integer to scalar float64 """
        self.feed('cvtsi2sd xmm3, r12')
        self.feed('cvtsi2sd xmm9, [rsi, 29]')
        self.check('f2490f2adc f24c0f2a4e1d')

    def test_cvtsd2ss(self):
        """ Test convert scalar float64 to float32 """
        self.feed('cvtsd2ss xmm6, [rbx]')
        self.feed('cvtsd2ss xmm2, [rcx]')
        self.check('f20f5a33 f20f5a11')

    def test_cvtss2sd(self):
        """ Test convert scalar float32 to float64 """
        self.feed('cvtss2sd xmm6, [rbx]')
        self.feed('cvtss2sd xmm2, [rcx]')
        self.check('f30f5a33 f30f5a11')


if __name__ == '__main__':
    unittest.main()
