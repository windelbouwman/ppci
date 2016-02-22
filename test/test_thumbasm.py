#!/usr/bin/env python

import unittest
from test_asm import AsmTestCaseBase


class ThumbAssemblerTestCase(AsmTestCaseBase):
    march = 'arm:thumb'

    def setUp(self):
        super().setUp()
        self.as_args = ['-mthumb']

    def test_mov_imm8(self):
        self.feed('mov r4, 100')
        self.check('6424')

    def test_mov_regs(self):
        self.feed('mov r0, r1')
        # self.check(None)

    @unittest.skip('todo')
    def test_mov_ext(self):
        self.feed('mov r3, sp')
        self.check('')

    def test_yield(self):
        self.feed('yield')
        self.check('10bf')

    def test_push(self):
        self.feed('push {r2,r3,lr}')
        self.check('0cb5')

    def test_pop(self):
        """ test pop instruction """
        self.feed('pop {r4-r6, pc}')
        self.check('70bd')

    def test_str5(self):
        self.feed('str r4, [r1, 0]')
        self.check('0c60')

    def test_ldr5(self):
        self.feed('ldr r4, [r0, 0]')
        self.check('0468')

    def test_ldr_sp_rel(self):
        self.feed('ldr r0, [sp, 4]')
        self.check('0198')

    def test_str_sp_rel(self):
        self.feed('str r0, [sp, 4]')
        self.check('0190')

    def test_ldr_pc_rel(self):
        self.feed('ldr r7, henkie')
        self.feed('ldr r6, henkie')
        self.feed('ldr r1, henkie')
        self.feed('align 4')
        self.feed('dd 1')
        self.feed('henkie: dd 2')
        self.check('024F024E 01490000 01000000 02000000')

    def test_adr(self):
        self.feed('adr r2, x')
        self.feed('adr r2, x')
        self.feed('x: dd 1')
        self.check('00a200a2 01000000')

    def test_branch(self):
        """ Test conditional branches """
        self.feed('start: b henkie')
        self.feed('beq henkie')
        self.feed('bne henkie')
        self.feed('henkie: b start')
        self.feed('eof: b eof')
        self.check('01e000d0 ffd1fbe7 fee7')

    def test_long_conditional_branch(self):
        """ Check if long branches work """
        self.feed('bnew x')
        self.feed('beqw x')
        self.feed('x: bnew x')
        self.feed('beqw x')
        self.check('40f00280 00f00080 7ff4feaf 3ff4fcaf')

    def test_long_branch(self):
        """ Check if long and short branch works """
        self.feed('b x')
        self.feed('bw x')
        self.feed('bw x')
        self.feed('x: bw x')
        self.feed('bw x')
        self.feed('b x')
        self.check('03e0 00f002b8 00f000b8 fff7febf fff7fcbf fae7')

    def test_conditions(self):
        """ Check conditional jumping around """
        self.feed('blt x')
        self.feed('bgt x')
        self.feed('x:')
        self.feed('ble x')
        self.feed('bge x')
        self.check('00dbffdc feddfdda')

    def test_b_off(self):
        """ Test offset of branch instruction """
        self.feed('b henkie')
        self.feed('b henkie')
        self.feed('b henkie')
        self.feed('b henkie')
        self.feed('b henkie')
        self.feed('b henkie')
        self.feed('b henkie')
        self.feed('henkie:')
        self.feed('b henkie')
        self.feed('b henkie')
        self.feed('b henkie')
        self.feed('b henkie')
        self.check('05e004e0 03e002e0 01e000e0 ffe7fee7 fde7fce7 fbe7')

    def test_bl(self):
        self.feed('bl henkie')
        self.feed('bl henkie')
        self.feed('henkie:')
        self.feed('bl henkie')
        self.feed('bl henkie')
        self.check('00f0 02f8 00f0 00f8 fff7 feff fff7 fcff')

    def test_cmp_reg_reg(self):
        self.feed('cmp r0, r1')
        self.check('8842')

    def test_add_imm3(self):
        self.feed('add r3, r5, 2')
        self.feed('add r4, r1, 6')
        self.check('ab1c8c1d')

    def test_sub_imm3(self):
        self.feed('sub r3, r5, 2')
        self.feed('sub r4, r1, 6')
        self.check('ab1e8c1f')

    def test_and(self):
        self.feed('and r7, r1')
        self.check('0f40')

    def test_or(self):
        self.feed('orr r7, r1')
        self.check('0f43')

    def test_nop(self):
        self.feed('nop')
        self.check('')

    def test_left_shift(self):
        self.feed('lsl r3, r5')
        self.check('ab40')

    def test_right_shift(self):
        self.feed('lsr r2, r6')
        self.check('f240')

    def test_add_sp(self):
        self.feed('add sp,sp,8')
        self.feed('add sp,sp,16')
        self.check('02b004b0')

    def test_sub_sp(self):
        self.feed('sub sp,sp,32')
        self.feed('sub sp,sp,4')
        self.check('88b081b0')

    def test_sequence1(self):
        self.feed('mov r5, 3')
        self.feed('add r4, r5, 0')
        self.feed('loop: add r6, r4, 7')
        self.feed('cmp r6, 5')
        self.check('0325 2c1c e61d 052e')

    def test_sequence2(self):
        self.feed('henkie:')
        self.feed('push {r1,r4,r5}')
        self.feed('add r5, r2, r4')
        self.feed('cmp r4, r2')
        self.feed('ldr r0, [sp, 4]')
        self.feed('str r3, [sp, 16]')
        self.feed('pop {r1, r4, r5}')
        self.feed('lsl r3, r4')
        self.feed('cmp r3, r5')
        self.feed('beq henkie')
        self.feed('bne henkie')
        self.feed('b henkie')
        self.check('32b41519 94420198 049332bc a340ab42 f6d0f5d1 f4e7')


if __name__ == '__main__':
    unittest.main()
