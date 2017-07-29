""" Description of registers """

from ..registers import Register, RegisterClass
from ... import ir


class Or1kRegister(Register):
    """ An open risc register """
    bitsize = 32

    def __repr__(self):
        if self.is_colored:
            return 'R{}'.format(self.color)
        else:
            return self.name


class Or1kPcRegister(Register):
    """ The program counter """
    bitsize = 32


class Or1kOtherRegister(Register):
    bitsize = 32


r0 = Or1kRegister('r0', num=0)
r1 = Or1kRegister('r1', num=1)
r2 = Or1kRegister('r2', num=2)
r3 = Or1kRegister('r3', num=3)
r4 = Or1kRegister('r4', num=4)
r5 = Or1kRegister('r5', num=5)
r6 = Or1kRegister('r6', num=6)
r7 = Or1kRegister('r7', num=7)
r8 = Or1kRegister('r8', num=8)
r9 = Or1kRegister('r9', num=9)
r10 = Or1kRegister('r10', num=10)
r11 = Or1kRegister('r11', num=11)
r12 = Or1kRegister('r12', num=12)
r13 = Or1kRegister('r13', num=13)
r14 = Or1kRegister('r14', num=14)
r15 = Or1kRegister('r15', num=15)

r16 = Or1kRegister('r16', num=16)
r17 = Or1kRegister('r17', num=17)
r18 = Or1kRegister('r18', num=18)
r19 = Or1kRegister('r19', num=19)
r20 = Or1kRegister('r20', num=20)
r21 = Or1kRegister('r21', num=21)
r22 = Or1kRegister('r22', num=22)
r23 = Or1kRegister('r23', num=23)
r24 = Or1kRegister('r24', num=24)
r25 = Or1kRegister('r25', num=25)
r26 = Or1kRegister('r26', num=26)
r27 = Or1kRegister('r27', num=27)
r28 = Or1kRegister('r28', num=28)
r29 = Or1kRegister('r29', num=29)
r30 = Or1kRegister('r30', num=30)
r31 = Or1kRegister('r31', num=31)

PC = Or1kPcRegister('pc', num=32)
MisteryReg1 = Or1kOtherRegister('mistery1', num=33)
MisteryReg2 = Or1kOtherRegister('mistery2', num=34)

usable_regs = (
    r3, r4, r5, r6, r7,
    r8, r10, r11, r12, r13, r14, r15,
    r16, r17, r18, r19, r20, r21, r22, r23,
    r24, r25, r26, r27, r28, r29, r30, r31)

all_regs = (r0, r1, r2, r9) + usable_regs

gdb_registers = (
    r0, r1, r2, r3, r4, r5, r6, r7,
    r8, r9, r10, r11, r12, r13, r14, r15,
    r16, r17, r18, r19, r20, r21, r22, r23,
    r24, r25, r26, r27, r28, r29, r30, r31,
    PC, MisteryReg1)

Or1kRegister.registers = all_regs

register_classes = [
    RegisterClass(
        'reg', [ir.i8, ir.u8, ir.i16, ir.u16, ir.i32, ir.u32, ir.ptr],
        Or1kRegister, usable_regs),
    ]

callee_save = (
    r10, r14,
    r16, r18, r20, r22, r24, r26, r28, r30)
caller_save = (
    r3, r4, r5, r6, r7, r8, r11, r12,  # arguments and return value
    r13, r15,
    r17, r19, r21, r23, r25, r27, r29, r31)
