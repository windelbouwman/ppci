import unittest
from test_asm import AsmTestCaseBase


class RiscvAssemblerTestCase(AsmTestCaseBase):
    """ Riscv-mode instruction assembly test case """
    march = 'riscv'

    def test_sbreak(self):
        self.feed('sbreak')
        self.check('73 00 10 00')

    def test_mov_alias(self):
        self.feed('mov x4, sp')
        self.feed('mov x4, x2')
        self.check('13 02 01 00 13 02 01 00')

    def test_mov_reg_reg(self):
        self.feed('mov x4, x5')
        self.check('13 82 02 00')

    def test_mov_reg_imm(self):
        self.feed('mov x5, 5')
        self.check('93 02 50 00')

    def test_add_reg_imm(self):
        self.feed('add x5, x4, 5')
        self.check('93 02 52 00')

    def test_sub_reg_imm(self):
        self.feed('sub x6, x4, 5')
        self.check('13 03 B2 FF')

    def test_add_imm_pc(self):
        self.feed('auipc x3, 5')
        self.check('97 51 00 00')

    def test_loadupper_imm(self):
        self.feed('lui x6, 0x5000')
        self.check('37 53 00 00')

    def test_jump_link_reg_imm(self):
        self.feed('jalr x7, x5, 5')
        self.check('E7 83 52 00')

    def test_jump_link_label(self):
        self.feed('l1:')
        self.feed('add x5, x4, 5')
        self.feed('jal x4, l1')
        self.check('93 02 52 00 6F F2 DF FF')

    def test_branch_equal(self):
        self.feed('beq x4, x5, l1')
        self.feed('l1:')
        self.feed('add x5, x4, 5')
        self.check('63 02 52 00 93 02 52 00')

    def test_branch_notequal(self):
        self.feed('bne x4, x5, l1')
        self.feed('l1:')
        self.check('63 12 52 00')

    def test_branch_greaterequal(self):
        self.feed('bge x4, x5, l1')
        self.feed('l1:')
        self.check('63 52 52 00')

    def test_branch_greaterequalunsigned(self):
        self.feed('bgeu x4, x5, l1')
        self.feed('l1:')
        self.check('63 72 52 00')

    def test_branch_less(self):
        self.feed('blt x4, x5, l1')
        self.feed('l1:')
        self.check('63 42 52 00')

    def test_branch_lessunsigned(self):
        self.feed('bltu x4, x5, l1')
        self.feed('l1:')
        self.check('63 62 52 00')

    def test_loadbyte(self):
        self.feed('lb x6, 2(x7)')
        self.check('03 83 23 00')

    def test_loadhalfword(self):
        self.feed('lh x6, 2(x7)')
        self.check('03 93 23 00')

    def test_loadword(self):
        self.feed('lw x6, 2(x7)')
        self.check('03 A3 23 00')

    def test_loadbyteunsigned(self):
        self.feed('lbu x6, 2(x7)')
        self.check('03 c3 23 00')

    def test_loadhalfwordunsigned(self):
        self.feed('lhu x6, 2(x7)')
        self.check('03 d3 23 00')

    def test_storebyte(self):
        self.feed('sb x7, 2(x6)')
        self.check('23 01 73 00')

    def test_storehalfword(self):
        self.feed('sh x7, 2(x6)')
        self.check('23 11 73 00')

    def test_storeword(self):
        self.feed('sw x7, 2(x6)')
        self.check('23 21 73 00')

    def test_add_imm(self):
        self.feed('addi x6, x7, 5')
        self.check('13 83 53 00')

    def test_setless_imm(self):
        self.feed('slti x6, x7, -5')
        self.check('13 A3 B3 FF')

    def test_setless_immunsigned(self):
        self.feed('sltiu x6, x7, 5')
        self.check('13 B3 53 00')

    def test_xori(self):
        self.feed('xori x6, x7, 5')
        self.check('13 C3 53 00')

    def test_ori(self):
        self.feed('ori x6, x7, 5')
        self.check('13 E3 53 00')

    def test_andi(self):
        self.feed('andi x6, x7, 5')
        self.check('13 F3 53 00')

    def test_shiftleftlog_imm(self):
        self.feed('slli x6, x7, 5')
        self.check('13 93 53 00')

    def test_shiftrightlog_imm(self):
        self.feed('srli x6, x7, 5')
        self.check('13 D3 53 00')

    def test_shiftrightarith_imm(self):
        self.feed('srai x6, x7, 5')
        self.check('13 D3 53 40')

    def test_add(self):
        self.feed('add x4, x7, x5')
        self.check('33 82 53 00')

    def test_sub(self):
        self.feed('sub x4, x7, x5')
        self.check('33 82 53 40')

    def test_shiftleftlog(self):
        self.feed('sll x4, x7, x5')
        self.check('33 92 53 00')

    def test_setless(self):
        self.feed('slt x4, x7, x5')
        self.check('33 A2 53 00')

    def test_setlessunsigned(self):
        self.feed('sltu x4, x7, x5')
        self.check('33 B2 53 00')

    def test_xor(self):
        self.feed('xor x4, x7, x5')
        self.check('33 C2 53 00')

    def test_shiftrightlog(self):
        self.feed('srl x4, x7, x5')
        self.check('33 D2 53 00')

    def test_shiftrightarith(self):
        self.feed('sra x4, x7, x5')
        self.check('33 D2 53 40')

    def test_or(self):
        self.feed('or x4, x7, x5')
        self.check('33 E2 53 00')

    def test_and(self):
        self.feed('and x4, x7, x5')
        self.check('33 F2 53 00')

    def test_readcycle(self):
        self.feed('rdcycle x4')
        self.check('73 22 00 c0')

    def test_readcycle_high(self):
        self.feed('rdcycleh x4')
        self.check('73 22 00 c8')

    def test_readtime(self):
        self.feed('rdtime x4')
        self.check('73 22 10 c0')

    def test_readtime_high(self):
        self.feed('rdtimeh x4')
        self.check('73 22 10 c8')

    def test_read_instr(self):
        self.feed('rdinstret x4')
        self.check('73 22 20 c0')

    def test_read_instrhigh(self):
        self.feed('rdinstreth x4')
        self.check('73 22 20 c8')

    def test_nop(self):
        self.feed('nop')
        self.check('13 00 00 00')


if __name__ == '__main__':
    unittest.main()
