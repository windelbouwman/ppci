import unittest
import io
from test_asm import AsmTestCaseBase
from ppci.target.target_list import arm_target
from ppci.binutils.layout import load_layout


class ArmAssemblerTestCase(AsmTestCaseBase):
    """ ARM-mode (not thumb-mode) instruction assembly test case """
    def setUp(self):
        super().setUp()
        self.target = arm_target
        self.assembler = arm_target.assembler
        self.assembler.prepare()

    def testMovImm(self):
        self.feed('mov r4, 100')
        self.check('6440a0e3')

    def testMovImm2(self):
        self.feed('mov sp, 0x6000')
        self.check('06daa0e3')

    def testMovReg(self):
        self.feed('mov r3, sp')
        self.feed('mov pc, lr')
        self.feed('mov pc, r2')
        self.feed('mov sp, r4')
        self.feed('mov r5, r6')
        self.check('0d30a0e1 0ef0a0e1 02f0a0e1 04d0a0e1 0650a0e1')

    def testAdd2(self):
        self.feed('add r12, r11, 300')
        self.check('4bcf8be2')

    def testAdd2InvalidValue(self):
        """ Test add instruction with invalid value """
        with self.assertRaises(ValueError):
            self.feed('add r12, r11, 30000')

    def testAdd1(self):
        self.feed('add r9, r7, r2')
        self.check('029087e0')

    def testSub1(self):
        self.feed('sub r5, r6, r2')
        self.check('025046e0')

    def testSub2(self):
        self.feed('sub r0, r1, 0x80000001')
        self.check('060141e2')

    def testAnd1(self):
        self.feed('and r9, r0, r2')
        self.feed('and r4, r8, r6')
        self.check('029000e0 064008e0')

    def testOrr1(self):
        self.feed('orr r8, r7, r6')
        self.check('068087e1')

    def testLsl(self):
        self.feed('lsl r11, r5, r3')
        self.feed('lsl r4, r8, r6')
        self.check('15b3a0e1 1846a0e1')

    def testLsr(self):
        self.feed('lsr r9, r0, r2')
        self.feed('lsr r4, r8, r6')
        self.check('3092a0e1 3846a0e1')

    def testBranches(self):
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
        self.check('030000ea 020000da 010000ca 0000000a ffffffeb feffffea \
                    fdffffda fcffffca fbffff0a faffffeb')

    def testPush(self):
        self.feed('push {r11,r5,r4,lr}')
        self.check('30482de9')

    def testPop(self):
        self.feed('pop {r4,r5,r6}')
        self.check('7000bde8')

    def testStr(self):
        self.feed('str r9, [r2, 33]')
        self.check('219082e5')

    def testLdr(self):
        self.feed('ldr r5, [r3, 87]')
        self.check('575093e5')

    def testStrb(self):
        self.feed('strb r2, [r8, 11]')
        self.check('0b20c8e5')

    def testLdrb(self):
        self.feed('ldrb r5, [r3, 87]')
        self.check('5750d3e5')

    def testLdrLabel(self):
        self.feed('ldr r5, lab1')
        self.feed('ldr r11, lab1')
        self.feed('ldr r10, lab1')
        self.feed('lab1:')
        self.feed('dcd 0x12345566')
        self.check('04509fe5 00b09fe5 04a01fe5 66553412')

    def testAdr(self):
        self.feed('adr r5, cval')
        self.feed('adr r9, cval')
        self.feed('adr r8, cval')
        self.feed('cval:')
        self.feed('adr r11, cval')
        self.feed('adr r12, cval')
        self.feed('adr r1, cval')
        self.check('04508fe2 00908fe2 04804fe2 08b04fe2 0cc04fe2 10104fe2')

    def testLdrLabelAddress(self):
        self.feed('ldr r8, =a')
        self.feed('a:')
        self.check('04801fe5 04000000')

    def testLdrLabelAddressAt10000(self):
        """ Link code at 0x10000 and check if symbol was correctly patched """
        self.feed('ldr r8, =a')
        self.feed('a:')
        spec = """
            MEMORY flash LOCATION=0x10000 SIZE=0x10000 {
                SECTION(code)
            }
        """
        layout = load_layout(io.StringIO(spec))
        self.check('04801fe5 04000100', layout)

    def testCmp(self):
        self.feed('cmp r4, r11')
        self.feed('cmp r5, 0x50000')
        self.check('0b0054e1 050855e3')

    def testSequence1(self):
        self.feed('sub r4,r5,23')
        self.feed('blt x')
        self.feed('x:')
        self.feed('mul r4,r5,r2')
        self.check('174045e2 ffffffba 950204e0')

    def testMcr(self):
        """ Test move coprocessor register from arm register """
        self.feed('mcr p15, 0, r1, c2, c0, 0')
        self.feed('mcr p14, 0, r1, c8, c7, 0')
        self.check('101f02ee 171e08ee')

    def testMrc(self):
        self.feed('mrc p15, 0, r1, c2, c0, 0')
        self.feed('mrc p14, 0, r1, c8, c7, 0')
        self.check('101f12ee 171e18ee')

    def testRepeat(self):
        self.feed('repeat 0x5')
        self.feed('dcd 0x11')
        self.feed('endrepeat')
        self.check('11000000 11000000 11000000 11000000 11000000')


if __name__ == '__main__':
    unittest.main()
