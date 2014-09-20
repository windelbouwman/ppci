#!/usr/bin/python

import unittest
from ppci.target.target_list import x86target
from test_asm import AsmTestCaseBase


class AssemblerTestCase(AsmTestCaseBase):
    """
    test methods start with 'test*'
     Checks several assembly constructs agains their bytecodes
    """
    def setUp(self):
        super().setUp()
        self.target = x86target
        self.assembler = self.target.assembler
        self.assembler.prepare()

    def testX86(self):
        self.feed('mov rax, rbx')
        self.feed('xor rcx, rbx')
        self.feed('inc rcx')
        self.check('48 89 d8 48 31 d9 48 ff c1')

    @unittest.skip('not implemented')
    def testJumpingAround(self):
        """ Check all kind of assembler cases """
        assert(assembler.shortjump(5) == [0xeb, 0x5])
        assert(assembler.shortjump(-2) == [0xeb, 0xfc])
        assert(assembler.shortjump(10,'GE') == [0x7d, 0xa])
        assert(assembler.nearjump(5) == [0xe9, 0x5,0x0,0x0,0x0])
        assert(assembler.nearjump(-2) == [0xe9, 0xf9, 0xff,0xff,0xff])
        assert(assembler.nearjump(10,'LE') == [0x0f, 0x8e, 0xa,0x0,0x0,0x0])

    @unittest.skip('not implemented')
    def testCall(self):
        self.feed('call r10')
        self.check('')
        self.feed('call rcx')
        # assert(assembler.call('r10') == [0x41, 0xff, 0xd2])
        # assert(assembler.call('rcx') == [0xff, 0xd1])

    def testXOR(self):
        self.feed('xor rax, rax')
        self.feed('xor r9, r8')
        self.feed('xor rbx, r11')
        self.check('48 31 c0 4d 31 c1 4c 31 db')

    def testINC(self):
        self.feed('inc r11')
        self.feed('inc rcx')
        self.check('49 ff c3 48 ff c1')

    def testPush(self):
        self.feed('push rbp')
        self.feed('push rbx')
        self.feed('push r12')
        self.check('55 53 41 54')

    def testPop(self):
        self.feed('pop rbx')
        self.feed('pop rbp')
        self.feed('pop r12')
        self.check('5b 5d 41 5c')

    @unittest.skip('not implemented')
    def testAsmLoads(self):
        self.feed('mov rbx, r14')
        self.feed('mov r12, r8')
        self.feed('mov rdi, rsp')
        self.check('4c 89 f3 4d 89 c4 48 89 e7')

    @unittest.skip('not implemented')
    def testAsmMemLoads(self):
      assert(assembler.mov('rax', ['r8','r15',0x11]) == [0x4b,0x8b,0x44,0x38,0x11])
      assert(assembler.mov('r13', ['rbp','rcx',0x23]) == [0x4c,0x8b,0x6c,0xd,0x23])

      assert(assembler.mov('r9', ['rbp',-0x33]) == [0x4c,0x8b,0x4d,0xcd])
      #assert(assembler.movreg64('rbx', ['rax']) == [0x48, 0x8b,0x18])

      assert(assembler.mov('rax', [0xb000]) == [0x48,0x8b,0x4,0x25,0x0,0xb0,0x0,0x0])
      assert(assembler.mov('r11', [0xa0]) == [0x4c,0x8b,0x1c,0x25,0xa0,0x0,0x0,0x0])

      assert(assembler.mov('r11', ['RIP', 0xf]) == [0x4c,0x8b,0x1d,0x0f,0x0,0x0,0x0])

    @unittest.skip
    def testAsmMemStores(self):
      assert(assembler.mov(['rbp', 0x13],'rbx') == [0x48,0x89,0x5d,0x13])
      assert(assembler.mov(['r12', 0x12],'r9') == [0x4d,0x89,0x4c,0x24,0x12])
      assert(assembler.mov(['rcx', 0x11],'r14') == [0x4c,0x89,0x71,0x11])


      assert(assembler.mov([0xab], 'rbx') == [0x48,0x89,0x1c,0x25,0xab,0x0,0x0,0x0])
      assert(assembler.mov([0xcd], 'r13') == [0x4c,0x89,0x2c,0x25,0xcd,0x0,0x0,0x0])

      assert(assembler.mov(['RIP', 0xf], 'r9') == [0x4c,0x89,0x0d,0x0f,0x0,0x0,0x0])

    @unittest.skip
    def testAsmMOV8(self):
      assert(assembler.mov(['rbp', -8], 'al') == [0x88, 0x45, 0xf8])
      assert(assembler.mov(['r11', 9], 'cl') == [0x41, 0x88, 0x4b, 0x09])

      assert(assembler.mov(['rbx'], 'al') == [0x88, 0x03])
      assert(assembler.mov(['r11'], 'dl') == [0x41, 0x88, 0x13])

    @unittest.skip
    def testAsmLea(self):
      assert(assembler.leareg64('r11', ['RIP', 0xf]) == [0x4c,0x8d,0x1d,0x0f,0x0,0x0,0x0])
      assert(assembler.leareg64('rsi', ['RIP', 0x7]) == [0x48,0x8d,0x35,0x07,0x0,0x0,0x0])

      assert(assembler.leareg64('rcx', ['rbp', -8]) == [0x48,0x8d,0x4d,0xf8])

    @unittest.skip
    def testAssemblerCMP(self):
      assert(assembler.cmpreg64('rdi', 'r13') == [0x4c, 0x39, 0xef])
      assert(assembler.cmpreg64('rbx', 'r14') == [0x4c, 0x39, 0xf3])
      assert(assembler.cmpreg64('r12', 'r9')  == [0x4d, 0x39, 0xcc])

      assert(assembler.cmpreg64('rdi', 1)  == [0x48, 0x83, 0xff, 0x01])
      assert(assembler.cmpreg64('r11', 2)  == [0x49, 0x83, 0xfb, 0x02])

    @unittest.skip
    def testAssemblerADD(self):
      assert(assembler.addreg64('rbx', 'r13') == [0x4c, 0x01, 0xeb])
      assert(assembler.addreg64('rax', 'rbx') == [0x48, 0x01, 0xd8])
      assert(assembler.addreg64('r12', 'r13') == [0x4d, 0x01, 0xec])

      assert(assembler.addreg64('rbx', 0x13) == [0x48, 0x83, 0xc3, 0x13])
      assert(assembler.addreg64('r11', 0x1234567) == [0x49, 0x81, 0xc3, 0x67, 0x45,0x23,0x1])
      assert(assembler.addreg64('rsp', 0x33) == [0x48, 0x83, 0xc4, 0x33])

    @unittest.skip
    def testAssemblerSUB(self):
      assert(assembler.subreg64('rdx', 'r14') == [0x4c, 0x29, 0xf2])
      assert(assembler.subreg64('r15', 'rbx') == [0x49, 0x29, 0xdf])
      assert(assembler.subreg64('r8', 'r9') == [0x4d, 0x29, 0xc8])

      assert(assembler.subreg64('rsp', 0x123456) == [0x48, 0x81, 0xec, 0x56,0x34,0x12,0x0])
      assert(assembler.subreg64('rsp', 0x12) == [0x48, 0x83, 0xec, 0x12])

    @unittest.skip
    def testAssemblerIDIV(self):
      assert(assembler.idivreg64('r11') == [0x49, 0xf7, 0xfb])
      assert(assembler.idivreg64('rcx') == [0x48, 0xf7, 0xf9])
      assert(assembler.idivreg64('rsp') == [0x48, 0xf7, 0xfc])

    @unittest.skip
    def testAssemblerIMUL(self):
      assert(assembler.imulreg64_rax('rdi') == [0x48, 0xf7, 0xef])
      assert(assembler.imulreg64_rax('r10') == [0x49, 0xf7, 0xea])
      assert(assembler.imulreg64_rax('rdx') == [0x48, 0xf7, 0xea])

      assert(assembler.imulreg64('r11', 'rdi') == [0x4c, 0xf, 0xaf, 0xdf])
      assert(assembler.imulreg64('r12', 'rbx') == [0x4c, 0xf, 0xaf, 0xe3])
      # nasm generates this machine code: 0x4d, 0x6b, 0xff, 0xee
      # This also works: 4D0FAFFE (another variant?? )
      assert(assembler.imulreg64('r15', 'r14') == [0x4d, 0x0f, 0xaf, 0xfe])


if __name__ == '__main__':
    unittest.main()
