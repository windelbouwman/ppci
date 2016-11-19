from test_asm import AsmTestCaseBase
import unittest


class XtensaAssemblyTestCase(AsmTestCaseBase):
    """ Xtensa instruction assembly test case """
    march = 'xtensa'

    def test_abs(self):
        self.feed('abs a4, a5')
        self.check('504160')

    def test_add(self):
        self.feed('add a7, a5, a9')
        self.check('907580')

    def test_addi(self):
        self.feed('addi a7, a5, 99')
        self.feed('addi a7, a5, -77')
        self.feed('addi a7, a5, 4')
        self.feed('addi a7, a5, -4')
        self.check('72c563 72c5b3 72c504 72c5fc')

    def test_bany(self):
        self.feed('bany a7, a5, label1')
        self.feed('bany a7, a5, label1')
        self.feed('label1: bany a7, a5, label1')
        self.check('578702 5787ff 5787fc')

    def test_bbc(self):
        self.feed('bbc a9, a3, label1')
        self.feed('bbc a9, a3, label1')
        self.feed('label1: bbc a9, a3, label1')
        self.check('375902 3759ff 3759fc')

    def test_beq(self):
        self.feed('beq a14, a15, label1')
        self.feed('beq a14, a15, label1')
        self.feed('label1: beq a14, a15, label1')
        self.check('f71e02 f71eff f71efc')

    def test_beqz(self):
        self.feed('beqz a13, label1')
        self.feed('beqz a13, label1')
        self.feed('label1: beqz a13, label1')
        self.check('162d00 16fdff 16cdff')

    def test_bge(self):
        self.feed('bge a4, a8, label1')
        self.feed('bge a4, a8, label1')
        self.feed('label1: bge a4, a8, label1')
        self.check('87a402 87a4ff 87a4fc')

    def test_bgeu(self):
        self.feed('bgeu a4, a8, label1')
        self.feed('bgeu a4, a8, label1')
        self.feed('label1: bgeu a4, a8, label1')
        self.check('87b402 87b4ff 87b4fc')

    def test_blt(self):
        self.feed('blt a11, a3, label1')
        self.feed('blt a11, a3, label1')
        self.feed('label1: blt a11, a3, label1')
        self.check('372b02 372bff 372bfc')

    def test_bltu(self):
        self.feed('bltu a11, a3, label1')
        self.feed('bltu a11, a3, label1')
        self.feed('label1: bltu a11, a3, label1')
        self.check('373b02 373bff 373bfc')

    def test_bne(self):
        self.feed('bne a12, a0, label1')
        self.feed('bne a12, a0, label1')
        self.feed('label1: bne a12, a0, label1')
        self.check('079c02 079cff 079cfc')

    def test_bnez(self):
        self.feed('bnez a13, label1')
        self.feed('bnez a13, label1')
        self.feed('label1: bnez a13, label1')
        self.check('562d00 56fdff 56cdff')

    def test_call0(self):
        """ Test non windowed call """
        self.feed('call0 label1')
        self.feed('call0 label1')
        self.feed('call0 label1')
        self.feed('call0 label1')
        self.feed('label1: call0 label1')
        self.feed('call0 label1')
        self.feed('call0 label1')
        self.check('850000 850000 450000 050000 c5ffff c5ffff 85ffff')

    def test_j(self):
        """ Test unconditional jump """
        self.feed('j label1')
        self.feed('j label1')
        self.feed('label1: j label1')
        self.check('860000 c6ffff 06ffff')

    def test_l8ui(self):
        self.feed('l8ui a3, a2, 4')
        self.check('320204')

    def test_l16si(self):
        self.feed('l16si a10, a11, 70')
        self.check('a29b23')

    def test_l16ui(self):
        self.feed('l16ui a12, a13, 80')
        self.check('c21d28')

    def test_l32i(self):
        self.feed('l32i a6, a7, 136')
        self.check('622722')

    def test_l32in(self):
        self.feed('l32i.n a1, a5, 28')
        self.check('1875')

    def test_l32r(self):
        """ Test load 32 bit value pc relative """
        self.feed('label1: ret')
        self.feed('l32r a9, label1')
        self.feed('l32r a9, label1')
        self.feed('l32r a9, label1')
        self.feed('l32r a9, label1')
        self.feed('l32r a9, label1')
        self.check('800000 91ffff 91feff 91fdff 91fdff 91fcff')

    def test_movi(self):
        """ Test move immediate """
        self.feed('movi a1, 0x345')
        self.check('12a345')

    def test_neg(self):
        """ Test negate """
        self.feed('neg a1, a2')
        self.check('201060')

    def test_nop(self):
        """ Test nop """
        self.feed('nop')
        self.check('f02000')

    def test_or(self):
        """ Test bitwise logical or """
        self.feed('or a1, a5, a9')
        self.check('901520')

    def test_ret(self):
        """ Test return """
        self.feed('ret')
        self.check('800000')

    def test_s8i(self):
        self.feed('s8i a6, a1, 7')
        self.check('624107')

    def test_s16i(self):
        self.feed('s16i a6, a1, 28')
        self.check('62510e')

    def test_s32i(self):
        self.feed('s32i a6, a1, 28')
        self.check('626107')

    def test_sll(self):
        self.feed('sll a6, a3')
        self.check('0063a1')

    def test_sra(self):
        self.feed('sra a6, a1')
        self.check('1060b1')

    def test_srl(self):
        self.feed('srl a6, a1')
        self.check('106091')

    def test_srli(self):
        self.feed('srli a6, a1, 7')
        self.check('106741')

    def test_ssl(self):
        self.feed('ssl a6')
        self.check('001640')

    def test_ssr(self):
        self.feed('ssr a6')
        self.check('000640')

    def test_sub(self):
        """ Test substract """
        self.feed('sub a7, a5, a9')
        self.check('9075c0')

    def test_subx2(self):
        self.feed('subx2 a7, a5, a9')
        self.check('9075d0')

    def test_subx4(self):
        self.feed('subx4 a7, a5, a9')
        self.check('9075e0')

    def test_subx8(self):
        self.feed('subx8 a7, a5, a9')
        self.check('9075f0')

    def test_xor(self):
        """ Test bitwise exclusive or """
        self.feed('xor a7, a5, a9')
        self.check('907530')

if __name__ == '__main__':
    unittest.main()
