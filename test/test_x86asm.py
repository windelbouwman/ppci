#!/usr/bin/python

import unittest
from test_asm import AsmTestCaseBase


class AssemblerTestCase(AsmTestCaseBase):
    """
     Checks several assembly constructs agains their bytecodes
    """
    march = 'x86_64'

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
        self.feed('mov rax, [r8, r15, 0x11]')
        self.feed('mov r13, [rbp, rcx, 0x23]')
        self.feed('mov r9, [rbp, -0x33]')
        self.feed('mov rbx, [rax]')
        self.feed('mov r11, [rip, 0xf]')
        self.feed('mov rax, [0xb000]')
        self.feed('mov r11, [0xa0]')
        self.feed('mov r14, [r9, 0xabcdef]')
        self.check(('4b8b443811 4c8b6c0d23'
                    '4c8b4dcd 488b18 4c8b1d0f000000 488b042500b00000'
                    '4c8b1c25a0000000 4d8bb1efcdab00'))

    def test_mov_imm(self):
        self.feed('mov r8, 91')
        self.feed('mov r9, 100')
        self.check('49b8 5B00000000000000 49b9 6400000000000000')

    def test_mov_imm8(self):
        self.feed('mov cl, 91')
        self.feed('mov dl, 100')
        self.check('48b15B 48b264')

    def test_mov_label_address(self):
        self.feed('label_x: mov r8, label_x')
        self.check('49b8 00000000 00000000')

    def test_mem_stores(self):
        """ Test store to memory """
        self.feed('mov [rbp, 0x13], rbx')
        self.feed('mov [rcx, 0x11], r14')
        self.feed('mov [0x20000000], rdi')
        self.check('48895d13 4c897111 48893C2500000020')

    def test_mem_store2(self):
        """ Test rbp without offset results correctly """
        self.feed('mov [rbp], rcx')
        self.feed('mov [r12], rax')
        self.check('48894d00 49890424')

    def test_weird_r12_encoding(self):
        self.feed('mov [r12, 0x12], r9')
        self.feed('mov [0xab], rbx')
        self.feed('mov [0xcd], r13')
        self.feed('mov [rip, 0xf], r9')
        self.check(
            '4d894c2412 48891c25ab000000 4c892c25cd000000 4c890d0f000000')

    def test_asm_mov8(self):
        self.feed('mov [rbp, -8], al')
        self.feed('mov [r11, 9], cl')
        self.feed('mov [rbx], al')
        self.feed('mov [r11], dl')
        self.check('488845f8 49884b09 488803 498813')

    def test_movsx(self):
        """ Test sign extend """
        self.feed('movsx rdx, bl')
        self.check('480fbed3')

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

    def test_add_lo_regs(self):
        self.feed('add al, dl')
        self.check('4800d0')   # rex.w add al, dl

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

    def test_idiv(self):
        """ Test integer divide """
        self.feed('idiv r11')
        self.feed('idiv rcx')
        self.feed('idiv rsp')
        self.check('49f7fb 48f7f9 48f7fc')

    def test_imul(self):
        # assert(assembler.imulreg64_rax('rdi') == [0x48, 0xf7, 0xef])
        # assert(assembler.imulreg64_rax('r10') == [0x49, 0xf7, 0xea])
        # assert(assembler.imulreg64_rax('rdx') == [0x48, 0xf7, 0xea])

        self.feed('imul r11, rdi')
        self.feed('imul r12, rbx')
        self.check('4c0fafdf 4c0fafe3')
        # nasm generates this machine code: 0x4d, 0x6b, 0xff, 0xee
        # This also works: 4D0FAFFE (another variant?? )
        # assert(assembler.imulreg64('r15', 'r14') == [0x4d, 0x0f, 0xaf, 0xfe])


class X87TestCase(AsmTestCaseBase):
    """ Checks floating point x87 instructions """
    march = 'x86_64:x87'

    def test_fld32(self):
        """ Test load 32 bit floating point """
        self.feed('flds [rcx]')
        self.check('40d901')

    def test_fld64(self):
        """ Test load 64 bit floating point """
        self.feed('fldl [rdx]')
        self.check('40dd02')

    @unittest.skip('todo')
    def test_fld80(self):
        """ Test load 80 bit floating point """
        self.feed('fldt [rax]')
        self.feed('fldt [r10]')
        self.feed('fldt [r10, 0x4c6]')
        self.check('db28 41db2a 41dbaac6040000')

    def test_fst32(self):
        """ Test store 32 bit floating point """
        self.feed('fsts [rax]')
        self.check('40d910')

    def test_fsqrt(self):
        """ Test square root instruction """
        self.feed('fsqrt')
        self.check('d9fa')


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
