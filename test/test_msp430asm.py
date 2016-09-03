#!/usr/bin/python

import unittest
import io
from ppci.binutils.layout import Layout
from test_asm import AsmTestCaseBase
from ppci.arch.msp430 import instructions, registers


class Msp430AssemblerTestCase(AsmTestCaseBase):
    """ Test the msp430 assembler """
    march = 'msp430'

    def test_mov(self):
        """ Test move """
        self.feed("mov.w r14, r15")
        self.check('0F4E')

    def test_mov_b(self):
        """ Test move """
        self.feed("mov.b r14, r15")
        self.check('4F4E')

    def test_mov_1337(self):
        """ Test the move of an absolute value """
        self.feed("mov.w #0x1337, r12")
        self.check('3C40 3713')

    def test_mov_indirect(self):
        """ Test the move of memory values """
        self.feed("mov.w #0x1337, 0x123(r12)")
        self.check('bC40 3713 2301')

    def test_mov_global(self):
        """ Store at global location (absolute address) """
        self.feed('a:')
        self.feed('dw 0')
        self.feed('b:')
        self.feed('dw 0')
        self.feed('mov.w &a, r0')
        self.feed('mov.w r0, &b')
        self.feed('mov.w &a, &b')
        spec = "MEMORY flash LOCATION=0xf800 SIZE=0x100 {SECTION(code)}"
        layout = Layout.load(io.StringIO(spec))
        self.check('0000 0000 1042 00f8 8240 02f8 9242 00f8 02f8', layout)

    def test_add(self):
        """ Test add instruction """
        self.feed("add.w r15, r13")
        self.check('0D5F')

    def test_sub(self):
        """ Test sub instruction """
        self.feed("sub.w r4, r5")
        self.check('0584')

    def test_cmp(self):
        """ Test sub instruction """
        self.feed("cmp.w r6, r7")
        self.check('0796')

    def test_bit(self):
        """ Test bit instruction """
        self.feed("bit.w r8, r9")
        self.check('09b8')

    def test_clrc(self):
        """ Test clear carry """
        self.feed("clrc")
        self.check('12c3')

    def test_clrn(self):
        """ Test clear negative flag """
        self.feed("clrn")
        self.check('22c2')

    def test_clrz(self):
        """ Test clear zero flag """
        self.feed("clrz")
        self.check('22c3')

    def test_rrc(self):
        """ Test rrc """
        self.feed("rrc r7")
        self.check('0710')

    def test_rra(self):
        """ Test rra """
        self.feed("rra 0x1234(r6)")
        self.check('1611 3412')

    def test_sxt(self):
        """ Test sxt """
        self.feed("sxt @r4")
        self.check('a411')

    def test_push(self):
        """ Test push """
        self.feed("push @r13+")
        self.check('3d12')

    def test_pop(self):
        """ Test pop (emulated as mov @sp+, dst ) """
        self.feed("pop r6")
        self.check('3641')

    def test_nop(self):
        """ Test nop ( mov #0, r3 ) """
        self.feed("nop")
        self.check('0343')

    def test_ret(self):
        """ Test ret ( mov @sp+, pc ) """
        self.feed("ret")
        self.check('3041')

    def test_call(self):
        """ Test call """
        self.feed("call #a")
        self.feed("call #a")
        self.feed("a: call #a")
        self.check('b0120800 b0120800 b0120800')

    def test_reti(self):
        """ Test return from interrupt """
        self.feed("reti")
        self.check('0013')

    def test_jne(self):
        """ Test jumping around """
        self.feed('jne a')
        self.feed('jne a')
        self.feed('a:')
        self.feed('jne a')
        self.feed('jne a')
        self.check('0120 0020 ff23 fe23')


class Msp430Syntax(unittest.TestCase):
    def test_add(self):
        add = instructions.Add(
            instructions.RegSrc(registers.r2),
            instructions.RegDst(registers.r3))
        self.assertEqual('add.w R2, R3', str(add))


class Msp430InstructionUseDef(unittest.TestCase):
    """ Test instruction use def info """
    def test_cmp(self):
        cp = instructions.Cmp(
            instructions.RegSrc(registers.r4),
            instructions.RegDst(registers.r5))
        self.assertEqual([registers.r4, registers.r5], cp.used_registers)
        self.assertEqual([], cp.defined_registers)

    def test_mov_reg_mem(self):
        mv = instructions.Mov(
            instructions.RegSrc(registers.r4),
            instructions.MemDst(10, registers.r5))
        self.assertEqual([registers.r4, registers.r5], mv.used_registers)
        self.assertEqual([], mv.defined_registers)

    def test_mov_regs(self):
        mv = instructions.Mov(
            instructions.RegSrc(registers.r4),
            instructions.RegDst(registers.r5))
        self.assertEqual([registers.r4], mv.used_registers)
        self.assertEqual([registers.r5], mv.defined_registers)

    def test_mov_mem_mem(self):
        mv = instructions.Mov(
            instructions.MemSrcOffset(20, registers.r4),
            instructions.MemDst(10, registers.r5))
        self.assertEqual([registers.r4, registers.r5], mv.used_registers)
        self.assertEqual([], mv.defined_registers)

    def test_add_regs(self):
        mv = instructions.Add(
            instructions.RegSrc(registers.r4),
            instructions.RegDst(registers.r5))
        self.assertEqual([registers.r4, registers.r5], mv.used_registers)
        self.assertEqual([registers.r5], mv.defined_registers)


class Msp430ConstructorTestCase(unittest.TestCase):
    """ Test instruction use def info """
    def test_cmp(self):
        reg_src = instructions.RegSrc(registers.r4)
        reg_dst = instructions.RegDst(registers.r5)
        cp = instructions.Cmp(reg_src, reg_dst)
        self.assertSequenceEqual([cp, reg_src, reg_dst], list(cp.non_leaves))


if __name__ == '__main__':
    unittest.main()
