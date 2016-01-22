#!/usr/bin/python

import unittest
from ppci.arch.target_list import x86target
from test_asm import AsmTestCaseBase


class AssemblerTestCase(AsmTestCaseBase):
    """
    test methods start with 'test*'
     Checks several assembly constructs agains their bytecodes
    """
    target = x86target

    def test_x86(self):
        self.feed('mov rax, rbx')
        self.feed('xor rcx, rbx')
        self.feed('inc rcx')
        self.check('4889d8 4831d9 48ffc1')

    def test_jumping_around(self):
        """ Check all kind of assembler cases """
        self.feed('jmpshort a')
        self.feed('jmp a')
        self.feed('a: jmp a')
        self.feed('jmp a')
        self.feed('jmpshort a')
        self.check('eb05 e900000000 e9fbffffff e9f6ffffff ebf4')

    def test_conditional_jumping_around(self):
        """ Check all kind of assembler cases """
        self.feed('jz a')
        self.feed('jne a')
        self.feed('a: jge a')
        self.feed('jg a')
        self.check('0f84 06000000 0f85 00000000 0f8d faffffff 0f8f f4ffffff')

    def test_call(self):
        """ Test call instruction """
        self.feed('call *r10')
        self.feed('call *rcx')
        self.feed('call b')
        self.feed('b: call b')
        self.feed('call b')
        self.check('41ffd2 40ffd1  e800000000 e8fbffffff e8f6ffffff')

    def test_ret(self):
        self.feed('ret')
        self.check('c3')

    def test_int(self):
        """ Test interrupt """
        self.feed('int 0x2')
        self.feed('int 0x11')
        self.check('cd02 cd11')

    def test_xor(self):
        self.feed('xor rax, rax')
        self.feed('xor r9, r8')
        self.feed('xor rbx, r11')
        self.check('4831c0 4d31c1 4c31db')

    def test_inc(self):
        self.feed('inc r11')
        self.feed('inc rcx')
        self.check('49ffc3 48ffc1')

    def test_push(self):
        self.feed('push rbp')
        self.feed('push rbx')
        self.feed('push r12')
        self.check('55 53 4154')

    def test_pop(self):
        self.feed('pop rbx')
        self.feed('pop rbp')
        self.feed('pop r12')
        self.check('5b 5d 415c')

    def test_asm_loads(self):
        self.feed('mov rbx, r14')
        self.feed('mov r12, r8')
        self.feed('mov rdi, rsp')
        self.check('4c89f3 4d89c4 4889e7')

    def test_asm_mem_loads(self):
        #self.feed('mov rax, [r8 + r15 + 0x11]')
        #self.check('4b 8b 44 38 11')
        #assert(assembler.mov('r13', ['rbp','rcx',0x23]) == [0x4c,0x8b,0x6c,0xd,0x23])

        #assert(assembler.mov('r9', ['rbp',-0x33]) == [0x4c,0x8b,0x4d,0xcd])
        self.feed('mov rbx, [rax]')
        self.check('488b18')

        # assert(assembler.mov('rax', [0xb000]) == [0x48,0x8b,0x4,0x25,0x0,0xb0,0x0,0x0])
        # assert(assembler.mov('r11', [0xa0]) == [0x4c,0x8b,0x1c,0x25,0xa0,0x0,0x0,0x0])

        # assert(assembler.mov('r11', ['RIP', 0xf]) == [0x4c,0x8b,0x1d,0x0f,0x0,0x0,0x0])

    def test_mov_imm(self):
        self.feed('mov r8, 91')
        self.feed('mov r9, 100')
        self.check('49b8 5B00000000000000 49b9 6400000000000000')

    def test_mov_label_address(self):
        self.feed('label_x: mov r8, label_x')
        self.check('49b8 00000000 00000000')

    def test_mem_stores(self):
        """ Test store to memory """
        self.feed('mov [rbp, 0x13], rbx')
        self.feed('mov [rcx, 0x11], r14')
        self.feed('mov [0x20000000], rdi')
        self.check('48895d13 4c897111 48893C2500000020')

    def test_weird_r12_encoding(self):
        self.feed('mov [r12, 0x12], r9')
        self.check('4d894c2412')

        # assert(assembler.mov([0xab], 'rbx') == [0x48,0x89,0x1c,0x25,0xab,0x0,0x0,0x0])
        # assert(assembler.mov([0xcd], 'r13') == [0x4c,0x89,0x2c,0x25,0xcd,0x0,0x0,0x0])

        # assert(assembler.mov(['RIP', 0xf], 'r9') == [0x4c,0x89,0x0d,0x0f,0x0,0x0,0x0])

    @unittest.skip('todo')
    def testAsmMOV8(self):
        self.feed('mov [rbp, -8], al')
        self.check('8845f8')
        # assert(assembler.mov(['r11', 9], 'cl') == [0x41, 0x88, 0x4b, 0x09])

        # assert(assembler.mov(['rbx'], 'al') == [0x88, 0x03])
        # assert(assembler.mov(['r11'], 'dl') == [0x41, 0x88, 0x13])

    def test_lea(self):
        self.feed('lea r11, [RIP, 0xf]')
        self.feed('lea rsi, [RIP, 0x7]')
        self.feed('lea rcx, [rbp, -8]')
        self.check('4c8d1d0f000000  488d3507000000 488d4df8')

    @unittest.skip('todo')
    def test_lea_label(self):
        self.feed('lea r11, [a]')
        self.feed('a: lea rsi, [a]')
        self.feed('lea rcx, [a]')
        self.check('4c8d1d0f000000  488d3507000000 488d4df8')

    def test_cmp(self):
        self.feed('cmp rdi, r13')
        self.feed('cmp rbx, r14')
        self.feed('cmp r12, r9')
        self.check('4c39ef 4c39f3 4d39cc')

        # assert(assembler.cmpreg64('rdi', 1)  == [0x48, 0x83, 0xff, 0x01])
        # assert(assembler.cmpreg64('r11', 2)  == [0x49, 0x83, 0xfb, 0x02])

    def test_add_regs(self):
        self.feed('add rbx, r13')
        self.feed('add rax, rbx')
        self.feed('add r12, r13')
        self.check('4c01eb 4801d8 4d01ec')

    def test_add_int(self):
        self.feed('add rbx, 0x13')
        self.feed('add r11, 0x1234567')
        self.feed('add rsp, 0x33')
        self.check('4881c313000000 4981c367452301 4881c433000000')

    def test_sub_regs(self):
        self.feed('sub rdx, r14')
        self.feed('sub r15, rbx')
        self.feed('sub r8, r9')
        self.check('4c 29 f2 49 29 df 4d 29 c8')

    def test_sub_int(self):
        self.feed('sub rsp, 0x123456')
        self.feed('sub rsp, 0x12')
        self.check('4881ec56341200 4881ec12000000')

    @unittest.skip('todo')
    def test_idiv(self):
        assert(assembler.idivreg64('r11') == [0x49, 0xf7, 0xfb])
        assert(assembler.idivreg64('rcx') == [0x48, 0xf7, 0xf9])
        assert(assembler.idivreg64('rsp') == [0x48, 0xf7, 0xfc])

    def test_imul(self):
        #assert(assembler.imulreg64_rax('rdi') == [0x48, 0xf7, 0xef])
        #assert(assembler.imulreg64_rax('r10') == [0x49, 0xf7, 0xea])
        #assert(assembler.imulreg64_rax('rdx') == [0x48, 0xf7, 0xea])

        self.feed('imul r11, rdi')
        self.feed('imul r12, rbx')
        self.check('4c 0f af df  4c 0f af e3')
        # nasm generates this machine code: 0x4d, 0x6b, 0xff, 0xee
        # This also works: 4D0FAFFE (another variant?? )
        # assert(assembler.imulreg64('r15', 'r14') == [0x4d, 0x0f, 0xaf, 0xfe])


if __name__ == '__main__':
    unittest.main()
