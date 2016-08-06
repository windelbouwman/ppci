import unittest
from test_asm import AsmTestCaseBase



class RiscvrvcAssemblerTestCase(AsmTestCaseBase):
    """ Riscv-mode instruction assembly test case """
    march = 'riscv:rvc'
    
    def setUp(self):
        super().setUp()
        self.as_args = ['-mrvc']
    
    def test_csub(self):
        self.feed('c.sub x4, x7')
        self.check('1D 8E')
    
    def test_cxor(self):
        self.feed('c.xor x4, x7')
        self.check('3D 8E')

    def test_cor(self):
        self.feed('c.or x4, x7')
        self.check('5D 8E')
        
    def test_cand(self):
        self.feed('c.and x4, x7')
        self.check('7D 8E')
        
    def test_csrli(self):
        self.feed('c.srli x4, x4, 5')
        self.check('15 82')
        
    def test_csrai(self):
        self.feed('c.srai x4, x4, 5')
        self.check('15 86')
        
    def test_caddi(self):
        self.feed('c.addi x4, x4, 5')
        self.check('15 02')
    
    def test_cnop(self):
        self.feed('c.nop')
        self.check('01 00')
    
    def test_cebreak(self):
        self.feed('c.ebreak')
        self.check('02 90')
    
    def test_cjal(self):
        self.feed('l1:')
        self.feed('add x5, x4, 5')
        self.feed('c.jal l1')
        self.check('93 02 52 00 F5 3F')
    
    def test_cj(self):
        self.feed('l1:')
        self.feed('add x5, x4, 5')
        self.feed('c.j l1')
        self.check('93 02 52 00 F5 BF')
    
    def test_cjump_link_reg(self):
        self.feed('c.jr x7')
        self.check('82 83')
        
    def test_cjump_reg(self):
        self.feed('c.jr x7')
        self.check('82 83')
        
    def test_cjump_link_reg(self):
        self.feed('c.jalr x7')
        self.check('82 93')
        
    def test_cbranch_equal(self):
        self.feed('c.beqz x9, l1')
        self.feed('l1:')
        self.feed('add x5, x4, 5')
        self.check('0B C0 93 02 52 00')
    
    def test_cbranch_equal(self):
        self.feed('c.bneqz x9, l1')
        self.feed('l1:')
        self.feed('add x5, x4, 5')
        self.check('89 E0 93 02 52 00')
        
    def test_cloadword(self):
        self.feed('c.lw x6, 4(x7)')
        self.check('D8 43')
        
    def test_cstoreword(self):
        self.feed('c.sw x6, 4(x7)')
        self.check('D8 C3')
        
    def test_cloadwordsp(self):
        self.feed('c.lwsp x6, 4(x2)')
        self.check('12 43')
    
    def test_cstorewordsp(self):
        self.feed('c.swsp x6, 4(x2)')
        self.check('1A C2')
if __name__ == '__main__':
    unittest.main()
