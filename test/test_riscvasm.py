import unittest
from test_asm import AsmTestCaseBase


class RiscvAssemblerTestCase(AsmTestCaseBase):
    """ Riscv-mode instruction assembly test case """
    march = 'riscv'

    def test_mov_reg_reg(self):
        self.feed('mov r4, r5')
        self.check('13 82 02 00')
        
    def test_mov_reg_imm(self):
        self.feed('mov r5, 5')
        self.check('93 02 50 00')
    
    def test_add_reg_imm(self):
        self.feed('add r5, r4, 5')
        self.check('93 02 52 00')
        
    def test_sub_reg_imm(self):
        self.feed('sub r6, r4, 5')
        self.check('13 03 B2 FF')
        
    def test_add_imm_pc(self):
        self.feed('auipc r3, 5')
        self.check('97 51 00 00')
    
    def test_loadupper_imm(self):
        self.feed('lui r6, 0x5000')
        self.check('37 53 00 00')
        
    def test_jump_link_reg_imm(self):
        self.feed('jalr r7, r5, 5')
        self.check('E7 83 52 00')
        
    def test_jump_link_label(self):
        self.feed('l1:')
        self.feed('add r5, r4, 5')
        self.feed('jal r4, l1')
        self.check('93 02 52 00 6F F2 DF FF')
    
    def test_branch_equal(self):
        self.feed('beq r4, r5, l1')
        self.feed('l1:')
        self.feed('add r5, r4, 5')
        self.check('63 02 52 00 93 02 52 00')
        
    def test_branch_notequal(self):
        self.feed('bne r4, r5, l1')
        self.feed('l1:')
        self.check('63 12 52 00')
        
    def test_branch_greaterequal(self):
        self.feed('bge r4, r5, l1')
        self.feed('l1:')
        self.check('63 52 52 00')
        
    def test_branch_greaterequalunsigned(self):
        self.feed('bgeu r4, r5, l1')
        self.feed('l1:')
        self.check('63 72 52 00')

    def test_branch_less(self):
        self.feed('blt r4, r5, l1')
        self.feed('l1:')
        self.check('63 42 52 00')
        
    def test_branch_lessunsigned(self):
        self.feed('bltu r4, r5, l1')
        self.feed('l1:')
        self.check('63 62 52 00')
        
    def test_loadbyte(self):
        self.feed('lb r6, r7, 2')
        self.check('03 83 23 00')
    
    def test_loadhalfword(self):
        self.feed('lh r6, r7, 2')
        self.check('03 93 23 00')
        
    def test_loadword(self):
        self.feed('lw r6, r7, 2')
        self.check('03 A3 23 00')
        
    def test_loadbyteunsigned(self):
        self.feed('lbu r6, r7, 2')
        self.check('03 c3 23 00')
    
    def test_loadhalfwordunsigned(self):
        self.feed('lhu r6, r7, 2')
        self.check('03 d3 23 00')
        
    def test_storebyte(self):
        self.feed('sb r6, r7, 2')
        self.check('23 01 73 00')
        
    def test_storehalfword(self):
        self.feed('sh r6, r7, 2')
        self.check('23 11 73 00')
        
    def test_storeword(self):
        self.feed('sw r6, r7, 2')
        self.check('23 21 73 00')
    
    def test_add_imm(self):
        self.feed('addi r6, r7, 5')
        self.check('13 83 53 00')

    def test_setless_imm(self):
        self.feed('slti r6, r7, -5')
        self.check('13 A3 B3 FF')

    def test_setless_immunsigned(self):
        self.feed('sltiu r6, r7, 5')
        self.check('13 B3 53 00')

    def test_xori(self):
        self.feed('xori r6, r7, 5')
        self.check('13 C3 53 00')

    def test_ori(self):
        self.feed('ori r6, r7, 5')
        self.check('13 E3 53 00')

    def test_andi(self):
        self.feed('andi r6, r7, 5')
        self.check('13 F3 53 00')

    def test_shiftleftlog_imm(self):
        self.feed('slli r6, r7, 5')
        self.check('13 93 53 00')

    def test_shiftrightlog_imm(self):
        self.feed('srli r6, r7, 5')
        self.check('13 D3 53 00')

    def test_shiftrightarith_imm(self):
        self.feed('srai r6, r7, 5')
        self.check('13 D3 53 40')
    
    def test_add(self):
        self.feed('add r4, r7, r5')
        self.check('33 82 53 00')
        
    def test_sub(self):
        self.feed('sub r4, r7, r5')
        self.check('33 82 53 40')
        
    def test_shiftleftlog(self):
        self.feed('sll r4, r7, r5')
        self.check('33 92 53 00')

    def test_setless(self):
        self.feed('slt r4, r7, r5')
        self.check('33 A2 53 00')

    def test_setless(self):
        self.feed('slt r4, r7, r5')
        self.check('33 A2 53 00')

    def test_setlessunsigned(self):
        self.feed('sltu r4, r7, r5')
        self.check('33 B2 53 00')

    def test_xor(self):
        self.feed('xor r4, r7, r5')
        self.check('33 C2 53 00')

    def test_shiftrightlog(self):
        self.feed('srl r4, r7, r5')
        self.check('33 D2 53 00')

    def test_shiftrightarith(self):
        self.feed('sra r4, r7, r5')
        self.check('33 D2 53 40')    

    def test_or(self):
        self.feed('or r4, r7, r5')
        self.check('33 E2 53 00')

    def test_and(self):
        self.feed('and r4, r7, r5')
        self.check('33 F2 53 00')

    def test_readcycle(self):
        self.feed('rdcycle r4')
        self.check('73 22 00 c0')

    def test_readcycle_high(self):
        self.feed('rdcycleh r4')
        self.check('73 22 00 c8')

    def test_readtime(self):
        self.feed('rdtime r4')
        self.check('73 22 10 c0')

    def test_readtime_high(self):
        self.feed('rdtimeh r4')
        self.check('73 22 10 c8')

    def test_read_instr(self):
        self.feed('rdinstret r4')
        self.check('73 22 20 c0')

    def test_read_instrhigh(self):
        self.feed('rdinstreth r4')
        self.check('73 22 20 c8')


if __name__ == '__main__':
    unittest.main()
