import unittest
import io
from test_asm import AsmTestCaseBase
from ppci.binutils.layout import Layout


class ArmAssemblerTestCase(AsmTestCaseBase):
    """ ARM-mode (not thumb-mode) instruction assembly test case """
    march = 'arm'

    def test_mov_imm(self):
        self.feed('mov r4, 100')
        self.check('6440a0e3')

    def test_mov_imm2(self):
        self.feed('mov sp, 0x6000')
        self.check('06daa0e3')

    def test_mov_reg(self):
        self.feed('mov r3, sp')
        self.feed('mov pc, lr')
        self.feed('mov pc, r2')
        self.feed('mov sp, r4')
        self.feed('mov r5, r6')
        self.check('0d30a0e1 0ef0a0e1 02f0a0e1 04d0a0e1 0650a0e1')

    def test_add2(self):
        self.feed('add r12, r11, 300')
        self.check('4bcf8be2')

    def test_add2_invalid_value(self):
        """ Test add instruction with invalid value """
        with self.assertRaises(ValueError):
            self.feed('add r12, r11, 30000')

    def test_add1(self):
        self.feed('add r9, r7, r2')
        self.check('029087e0')

    def test_sub1(self):
        """ Test substraction """
        self.feed('sub r5, r6, r2')
        self.feed('subcc r5, r6, r2')
        self.feed('subne r5, r6, r2')
        self.check('025046e0 02504630 02504610')

    def test_sub2(self):
        self.feed('sub r0, r1, 0x80000001')
        self.check('060141e2')

    def test_and1(self):
        self.feed('and r9, r0, r2')
        self.feed('and r4, r8, r6')
        self.check('029000e0 064008e0')

    def test_sdiv(self):
        self.feed('sdiv r2, r5, r4')
        self.feed('sdiv r3, r1, r9')
        self.check('15f412e7 11f913e7')

    def test_orr1(self):
        self.feed('orr r8, r7, r6')
        self.check('068087e1')

    def test_lsl(self):
        self.feed('lsl r11, r5, r3')
        self.feed('lsl r4, r8, r6')
        self.check('15b3a0e1 1846a0e1')

    def test_lsr(self):
        self.feed('lsr r9, r0, r2')
        self.feed('lsr r4, r8, r6')
        self.check('3092a0e1 3846a0e1')

    def test_nranches(self):
        """ Test several branch instructions """
        self.feed("""b sjakie
        ble sjakie
        bgt sjakie
        beq sjakie
        bl sjakie
        sjakie:
        b sjakie
        ble sjakie
        bgt sjakie
        beq sjakie
        bl sjakie""")
        self.check(
            '030000ea 020000da 010000ca 0000000a ffffffeb feffffea'
            'fdffffda fcffffca fbffff0a faffffeb')

    def test_push(self):
        self.feed('push {r11,r5,r4,lr}')
        self.check('30482de9')

    def test_pop(self):
        self.feed('pop {r4,r5,r6}')
        self.check('7000bde8')

    def test_str(self):
        self.feed('str r9, [r2, 33]')
        self.check('219082e5')

    def test_ldr(self):
        self.feed('ldr r5, [r3, 87]')
        self.check('575093e5')

    def test_strb(self):
        self.feed('strb r2, [r8, 11]')
        self.check('0b20c8e5')

    def test_ldrb(self):
        self.feed('ldrb r5, [r3, 87]')
        self.check('5750d3e5')

    def test_ldr_label(self):
        """ Test if loading from a label works """
        self.feed('ldr r5, lab1')
        self.feed('ldr r11, lab1')
        self.feed('ldr r10, lab1')
        self.feed('lab1:')
        self.feed('dd 0x12345566')
        self.check('04509fe5 00b09fe5 04a01fe5 66553412')

    def test_adr(self):
        self.feed('adr r5, cval')
        self.feed('adr r9, cval')
        self.feed('adr r8, cval')
        self.feed('cval:')
        self.feed('adr r11, cval')
        self.feed('adr r12, cval')
        self.feed('adr r1, cval')
        self.check('04508fe2 00908fe2 04804fe2 08b04fe2 0cc04fe2 10104fe2')

    def test_ldr_label_address(self):
        self.feed('ldr r8, =a')
        self.feed('a:')
        self.check('04801fe5 04000000')

    def test_ldr_label_address_at_10000(self):
        """ Link code at 0x10000 and check if symbol was correctly patched """
        self.feed('ldr r8, =a')
        self.feed('a:')
        spec = "MEMORY flash LOCATION=0x10000 SIZE=0x10000 { SECTION(code) }"
        layout = Layout.load(io.StringIO(spec))
        self.check('04801fe5 04000100', layout)

    def test_cmp(self):
        """ Test the compare function """
        self.feed('cmp r4, r11')
        self.feed('cmp r5, 0x50000')
        self.check('0b0054e1 050855e3')

    def test_sequence1(self):
        self.feed('sub r4,r5,23')
        self.feed('blt x')
        self.feed('x:')
        self.feed('mul r4,r5,r2')
        self.check('174045e2 ffffffba 950204e0')

    def test_mcr(self):
        """ Test move coprocessor register from arm register """
        self.feed('mcr p15, 0, r1, c2, c0, 0')
        self.feed('mcr p14, 0, r1, c8, c7, 0')
        self.check('101f02ee 171e08ee')

    def test_mrc(self):
        self.feed('mrc p15, 0, r1, c2, c0, 0')
        self.feed('mrc p14, 0, r1, c8, c7, 0')
        self.check('101f12ee 171e18ee')

    def test_repeat(self):
        """ Check if macro repeat works correctly """
        self.feed('repeat 0x5')
        self.feed('dd 0x11')
        self.feed('endrepeat')
        self.check('11000000 11000000 11000000 11000000 11000000')

    def test_mnemonic_as_label(self):
        """ It should be possible to use mnemonics as labels """
        self.feed('cmp:')
        self.feed('b cmp')
        self.check('feffffea')

    def test_div_routine(self):
        """ Test nifty division routine """
        self.feed('div:')
        self.feed('  mov r4, r2')
        self.feed('  cmp r4, r1, lsr 1')
        self.feed('div_90:')
        self.feed('  movls r4, r4, lsl 1')
        self.feed('  cmp r4, r1, lsr 1')
        self.feed('  bls div_90')
        self.feed('  mov r3, 0')
        self.feed('div_91:')
        self.feed('  cmp r1, r4')
        self.feed('  subcs r1, r1, r4')
        self.feed('  adc r3, r3, r3')
        self.feed('  mov r4, r4, lsr 1')
        self.feed('  cmp r4, r2')
        self.feed('  bhs div_91')
        self.check(
            "0240a0e1 a10054e1 8440a091 a10054e1 fcffff9a 0030a0e3"
            "040051e1 04104120 0330a3e0 a440a0e1 020054e1 f9ffff2a")


if __name__ == '__main__':
    unittest.main()
