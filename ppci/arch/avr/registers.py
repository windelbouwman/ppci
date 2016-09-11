""" Description of avr registers """

from ..registers import Register, RegisterClass
from ...ir import i16, i8, ptr


class AvrRegister(Register):
    """ An 8-bit avr register """
    bitsize = 8

    def __repr__(self):
        if self.is_colored:
            return get_register(self.color).name
        else:
            return self.name


class HighAvrRegister(AvrRegister):
    pass


class AvrWordRegister(Register):
    """ Register covering two 8 bit registers """
    bitsize = 16

    def __repr__(self):
        if self.is_colored:
            return get16reg(self.color).name
        else:
            return self.name

    @property
    def lo(self):
        return get8reg(self.num)

    @property
    def hi(self):
        return get8reg(self.num + 1)


class HighAvrWordRegister(AvrWordRegister):
    # The higher half of word registers
    pass


class SuperHighAvrWordRegister(AvrWordRegister):
    # The higher quarter of the word registers
    pass


class AvrPointerRegister(SuperHighAvrWordRegister):
    pass


class AvrXRegister(AvrPointerRegister):
    pass


class AvrYRegister(AvrPointerRegister):
    pass


class AvrZRegister(AvrPointerRegister):
    pass


# Special registers:
class AvrSpecialRegister(Register):
    pass


class AvrStatusRegister(AvrSpecialRegister):
    bitsize = 8


class AvrStackPointerRegister(AvrSpecialRegister):
    bitsize = 16


class AvrProgramCounterRegister(AvrSpecialRegister):
    bitsize = 32


SREG = AvrStatusRegister('SREG')
SP = AvrStackPointerRegister('SP')
PC = AvrProgramCounterRegister('PC')


r0 = AvrRegister('r0', num=0)
r1 = AvrRegister('r1', num=1)
r2 = AvrRegister('r2', num=2)
r3 = AvrRegister('r3', num=3)
r4 = AvrRegister('r4', num=4)
r5 = AvrRegister('r5', num=5)
r6 = AvrRegister('r6', num=6)
r7 = AvrRegister('r7', num=7)

r8 = AvrRegister('r8', num=8)
r9 = AvrRegister('r9', num=9)
r10 = AvrRegister('r10', num=10)
r11 = AvrRegister('r11', num=11)
r12 = AvrRegister('r12', num=12)
r13 = AvrRegister('r13', num=13)
r14 = AvrRegister('r14', num=14)
r15 = AvrRegister('r15', num=15)

r16 = HighAvrRegister('r16', num=16)
r17 = HighAvrRegister('r17', num=17)
r18 = HighAvrRegister('r18', num=18)
r19 = HighAvrRegister('r19', num=19)
r20 = HighAvrRegister('r20', num=20)
r21 = HighAvrRegister('r21', num=21)
r22 = HighAvrRegister('r22', num=22)
r23 = HighAvrRegister('r23', num=23)

r24 = HighAvrRegister('r24', num=24)
r25 = HighAvrRegister('r25', num=25)
r26 = HighAvrRegister('r26', num=26)
r27 = HighAvrRegister('r27', num=27)
r28 = HighAvrRegister('r28', num=28)
r29 = HighAvrRegister('r29', num=29)
r30 = HighAvrRegister('r30', num=30)
r31 = HighAvrRegister('r31', num=31)

r1r0 = AvrWordRegister('r1:r0', num=0, aliases=(r1, r0))
r3r2 = AvrWordRegister('r3:r2', num=2, aliases=(r3, r2))
r5r4 = AvrWordRegister('r5:r4', num=4, aliases=(r5, r4))
r7r6 = AvrWordRegister('r7:r6', num=6, aliases=(r7, r6))
r9r8 = AvrWordRegister('r9:r8', num=8, aliases=(r9, r8))
r11r10 = AvrWordRegister('r11:r10', num=10, aliases=(r11, r10))
r13r12 = AvrWordRegister('r13:r12', num=12, aliases=(r13, r12))
r15r14 = AvrWordRegister('r15:r14', num=14, aliases=(r15, r14))
r17r16 = HighAvrWordRegister('r17:r16', num=16, aliases=(r17, r16))
r19r18 = HighAvrWordRegister('r19:r18', num=18, aliases=(r19, r18))
r21r20 = HighAvrWordRegister('r21:r20', num=20, aliases=(r21, r20))
r23r22 = HighAvrWordRegister('r23:r22', num=22, aliases=(r23, r22))
W = SuperHighAvrWordRegister('W', num=24, aliases=(r25, r24), aka=('r25:r24',))
X = AvrXRegister('X', num=26, aliases=(r27, r26), aka=('r27:r26',))
AvrXRegister.registers = [X]
Y = AvrYRegister('Y', num=28, aliases=(r29, r28), aka=('r29:r28',))
AvrYRegister.registers = [Y]
Z = AvrZRegister('Z', num=30, aliases=(r31, r30), aka=('r31:r30',))
AvrZRegister.registers = [Z]
AvrPointerRegister.registers = (X, Y, Z)
SuperHighAvrWordRegister.registers = (W, X, Y, Z)


lo_regs = (r0, r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12, r13, r14,
           r15)
hi_regs = (r16, r17, r18, r19, r20, r21, r22, r23, r24, r25, r26, r27,
           r28, r29, r30, r31)
all_regs = lo_regs + hi_regs
alloc_lo_regs = (r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12, r13, r14, r15)
alloc_regs = alloc_lo_regs + hi_regs

callee_save = (
    r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12, r13, r14, r15, r16, r17)

caller_save = (r18, r19, r20, r21, r22, r23, r24, r25, r26, r27, r30, r31)

gdb_registers = all_regs + (SREG, SP, PC)

lo_w_regs = (
    r1r0, r3r2, r5r4, r7r6, r9r8, r11r10, r13r12, r15r14)
hi_w_regs = (
    r17r16, r19r18, r21r20, r23r22, W, X, Y, Z)
all_w_regs = lo_w_regs + hi_w_regs
alloc_lo_w_regs = (
    r3r2, r5r4, r7r6, r9r8, r11r10, r13r12, r15r14)
alloc_w_regs = alloc_lo_w_regs + hi_w_regs

num_reg_map = {r.num: r for r in all_regs}

AvrRegister.registers = all_regs
HighAvrRegister.registers = hi_regs
AvrWordRegister.registers = all_w_regs
HighAvrWordRegister.registers = hi_w_regs


def get_register(n):
    return num_reg_map[n]


get8reg = get_register


def get16reg(n):
    mp = {r.num: r for r in all_w_regs}
    return mp[n]


register_classes = [
    RegisterClass('reg', [i8], AvrRegister, alloc_regs),
    RegisterClass('hireg', [], HighAvrRegister, hi_regs),
    RegisterClass('suhireg', [], SuperHighAvrWordRegister, (W, X, Y, Z)),
    RegisterClass('ptrreg', [], AvrPointerRegister, (X, Y, Z)),
    RegisterClass('xreg', [], AvrXRegister, (X,)),
    RegisterClass('yreg', [], AvrYRegister, (Y,)),
    RegisterClass('zreg', [], AvrZRegister, (Z,)),
    RegisterClass('reg16', [i16, ptr], AvrWordRegister, alloc_w_regs),
    RegisterClass('hireg16', [], HighAvrWordRegister, hi_w_regs),
    ]
