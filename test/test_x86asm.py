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

    def testJumpingAround(self):
        """ Check all kind of assembler cases """
        self.feed('jmp a')
        self.feed('a: jmp a')
        self.feed('jmp a')
        self.check('e9 00 00 00 00   e9 fb ff ff ff   e9 f6 ff ff ff')

    def testCall(self):
        self.feed('call r10')
        self.feed('call rcx')
        self.feed('call b')
        self.feed('b: call b')
        self.feed('call b')
        self.check('41 ff d2 40 ff d1  e8 0000 0000 e8 fbff ffff e8 f6ff ffff')

    def test_ret(self):
        self.feed('ret')
        self.check('c3')

    def test_int(self):
        """ Test interrupt """
        self.feed('int 0x2')
        self.feed('int 0x11')
        self.check('cd02 cd11')

    def testXor(self):
        self.feed('xor rax, rax')
        self.feed('xor r9, r8')
        self.feed('xor rbx, r11')
        self.check('48 31 c0 4d 31 c1 4c 31 db')

    def testInc(self):
        self.feed('inc r11')
        self.feed('inc rcx')
        self.check('49 ff c3 48 ff c1')

    def testPush(self):
        self.feed('push rbp')
        self.feed('push rbx')
        self.feed('push r12')
        self.check('55 53 41 54')

    def test_pop(self):
        self.feed('pop rbx')
        self.feed('pop rbp')
        self.feed('pop r12')
        self.check('5b 5d 41 5c')

    def testAsmLoads(self):
        self.feed('mov rbx, r14')
        self.feed('mov r12, r8')
        self.feed('mov rdi, rsp')
        self.check('4c 89 f3 4d 89 c4 48 89 e7')

    @unittest.skip('not implemented')
    def testAsmMemLoads(self):
        self.feed('mov rax, [r8 + r15 * 1 + 0x11]')
        self.check('4b 8b 44 38 11')
        #assert(assembler.mov('r13', ['rbp','rcx',0x23]) == [0x4c,0x8b,0x6c,0xd,0x23])

        #assert(assembler.mov('r9', ['rbp',-0x33]) == [0x4c,0x8b,0x4d,0xcd])
        #assert(assembler.movreg64('rbx', ['rax']) == [0x48, 0x8b,0x18])

        #assert(assembler.mov('rax', [0xb000]) == [0x48,0x8b,0x4,0x25,0x0,0xb0,0x0,0x0])
        #assert(assembler.mov('r11', [0xa0]) == [0x4c,0x8b,0x1c,0x25,0xa0,0x0,0x0,0x0])

        # assert(assembler.mov('r11', ['RIP', 0xf]) == [0x4c,0x8b,0x1d,0x0f,0x0,0x0,0x0])

    @unittest.skip('todo')
    def testAsmMemStores(self):
      assert(assembler.mov(['rbp', 0x13],'rbx') == [0x48,0x89,0x5d,0x13])
      assert(assembler.mov(['r12', 0x12],'r9') == [0x4d,0x89,0x4c,0x24,0x12])
      assert(assembler.mov(['rcx', 0x11],'r14') == [0x4c,0x89,0x71,0x11])


      assert(assembler.mov([0xab], 'rbx') == [0x48,0x89,0x1c,0x25,0xab,0x0,0x0,0x0])
      assert(assembler.mov([0xcd], 'r13') == [0x4c,0x89,0x2c,0x25,0xcd,0x0,0x0,0x0])

      assert(assembler.mov(['RIP', 0xf], 'r9') == [0x4c,0x89,0x0d,0x0f,0x0,0x0,0x0])

    @unittest.skip('todo')
    def testAsmMOV8(self):
      assert(assembler.mov(['rbp', -8], 'al') == [0x88, 0x45, 0xf8])
      assert(assembler.mov(['r11', 9], 'cl') == [0x41, 0x88, 0x4b, 0x09])

      assert(assembler.mov(['rbx'], 'al') == [0x88, 0x03])
      assert(assembler.mov(['r11'], 'dl') == [0x41, 0x88, 0x13])

    @unittest.skip('todo')
    def testAsmLea(self):
      assert(assembler.leareg64('r11', ['RIP', 0xf]) == [0x4c,0x8d,0x1d,0x0f,0x0,0x0,0x0])
      assert(assembler.leareg64('rsi', ['RIP', 0x7]) == [0x48,0x8d,0x35,0x07,0x0,0x0,0x0])

      assert(assembler.leareg64('rcx', ['rbp', -8]) == [0x48,0x8d,0x4d,0xf8])

    def testAssemblerCmp(self):
        self.feed('cmp rdi, r13')
        self.feed('cmp rbx, r14')
        self.feed('cmp r12, r9')
        self.check('4c 39 ef 4c 39 f3 4d 39 cc')

        # assert(assembler.cmpreg64('rdi', 1)  == [0x48, 0x83, 0xff, 0x01])
        # assert(assembler.cmpreg64('r11', 2)  == [0x49, 0x83, 0xfb, 0x02])

    def testAssemblerAddRegs(self):
        self.feed('add rbx, r13')
        self.feed('add rax, rbx')
        self.feed('add r12, r13')
        self.check('4c 01 eb 48 01 d8 4d 01 ec')

    def testAssemblerAddRegInt(self):
        self.feed('add rbx, 0x13')
        self.feed('add r11, 0x1234567')
        self.feed('add rsp, 0x33')
        self.check('48 81 c3 13 00 00 00   49 81 c3 67 45 23 01   48 81 c4 33 00 00 00')

    def testAssemblerSubRegs(self):
        self.feed('sub rdx, r14')
        self.feed('sub r15, rbx')
        self.feed('sub r8, r9')
        self.check('4c 29 f2 49 29 df 4d 29 c8')

    def testAssemblerSubRegInt(self):
        self.feed('sub rsp, 0x123456')
        self.feed('sub rsp, 0x12')
        self.check('48 81 ec 56 34 12 00  48 81 ec 12 00 00 00')

    @unittest.skip('todo')
    def testAssemblerIDIV(self):
      assert(assembler.idivreg64('r11') == [0x49, 0xf7, 0xfb])
      assert(assembler.idivreg64('rcx') == [0x48, 0xf7, 0xf9])
      assert(assembler.idivreg64('rsp') == [0x48, 0xf7, 0xfc])

    def testAssemblerIMUL(self):
        #assert(assembler.imulreg64_rax('rdi') == [0x48, 0xf7, 0xef])
        #assert(assembler.imulreg64_rax('r10') == [0x49, 0xf7, 0xea])
        #assert(assembler.imulreg64_rax('rdx') == [0x48, 0xf7, 0xea])

        self.feed('imul r11, rdi')
        self.feed('imul r12, rbx')
        self.check('4c 0f af df  4c 0f af e3')
        # nasm generates this machine code: 0x4d, 0x6b, 0xff, 0xee
        # This also works: 4D0FAFFE (another variant?? )
        #assert(assembler.imulreg64('r15', 'r14') == [0x4d, 0x0f, 0xaf, 0xfe])


if __name__ == '__main__':
    unittest.main()
