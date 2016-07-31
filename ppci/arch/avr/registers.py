from ..isa import Register, Syntax, RegisterClass
from ...ir import i16, i8, ptr


class AvrRegister(Register):
    bitsize = 8

    def __repr__(self):
        if self.is_colored:
            return get_register(self.color).name
        else:
            return self.name

    syntaxi = 'reg', [
        Syntax(['r0'], new_func=lambda: r0),
        Syntax(['r1'], new_func=lambda: r1),
        Syntax(['r2'], new_func=lambda: r2),
        Syntax(['r3'], new_func=lambda: r3),
        Syntax(['r4'], new_func=lambda: r4),
        Syntax(['r5'], new_func=lambda: r5),
        Syntax(['r6'], new_func=lambda: r6),
        Syntax(['r7'], new_func=lambda: r7),
        Syntax(['r8'], new_func=lambda: r8),
        Syntax(['r9'], new_func=lambda: r9),
        Syntax(['r10'], new_func=lambda: r10),
        Syntax(['r11'], new_func=lambda: r11),
        Syntax(['r12'], new_func=lambda: r12),
        Syntax(['r13'], new_func=lambda: r13),
        Syntax(['r14'], new_func=lambda: r14),
        Syntax(['r15'], new_func=lambda: r15),
        Syntax(['r16'], new_func=lambda: r16),
        Syntax(['r17'], new_func=lambda: r17),
        Syntax(['r18'], new_func=lambda: r18),
        Syntax(['r19'], new_func=lambda: r19),
        Syntax(['r20'], new_func=lambda: r20),
        Syntax(['r21'], new_func=lambda: r21),
        Syntax(['r22'], new_func=lambda: r22),
        Syntax(['r23'], new_func=lambda: r23),
        Syntax(['r24'], new_func=lambda: r24),
        Syntax(['r25'], new_func=lambda: r25),
        Syntax(['r26'], new_func=lambda: r26),
        Syntax(['r27'], new_func=lambda: r27),
        Syntax(['r28'], new_func=lambda: r28),
        Syntax(['r29'], new_func=lambda: r29),
        Syntax(['r30'], new_func=lambda: r30),
        Syntax(['r31'], new_func=lambda: r31),
        ]


class HighAvrRegister(AvrRegister):
    syntaxi = 'hireg', [
        Syntax(['r16'], new_func=lambda: r16),
        Syntax(['r17'], new_func=lambda: r17),
        Syntax(['r18'], new_func=lambda: r18),
        Syntax(['r19'], new_func=lambda: r19),
        Syntax(['r20'], new_func=lambda: r20),
        Syntax(['r21'], new_func=lambda: r21),
        Syntax(['r22'], new_func=lambda: r22),
        Syntax(['r23'], new_func=lambda: r23),
        Syntax(['r24'], new_func=lambda: r24),
        Syntax(['r25'], new_func=lambda: r25),
        Syntax(['r26'], new_func=lambda: r26),
        Syntax(['r27'], new_func=lambda: r27),
        Syntax(['r28'], new_func=lambda: r28),
        Syntax(['r29'], new_func=lambda: r29),
        Syntax(['r30'], new_func=lambda: r30),
        Syntax(['r31'], new_func=lambda: r31),
        ]


class AvrRegCombo:
    """
        To be able to use 16 bit values, use this imaginary register type
        containing a pair of real registers.
    """
    def __init__(self, hi, lo):
        self._hi = hi
        self._lo = lo

    @property
    def hi(self):
        return self._hi

    @property
    def lo(self):
        return self._lo


class AvrPseudo16Register(AvrRegCombo):
    pass


class AvrWordRegister(Register):
    """ Register covering two 8 bit registers """
    bitsize = 16
    syntaxi = 'reg16', [
        Syntax(['r17', ':', 'r16'], new_func=lambda: r17r16),
        Syntax(['r19', ':', 'r18'], new_func=lambda: r19r18),
        Syntax(['r21', ':', 'r20'], new_func=lambda: r21r20),
        ]

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


class AvrPointerRegister(HighAvrWordRegister):
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
r25r24 = HighAvrWordRegister('r25:r24', num=24, aliases=(r25, r24))
X = AvrPointerRegister('X', num=26, aliases=(r27, r26))
Y = AvrPointerRegister('Y', num=28, aliases=(r29, r28))
Z = AvrPointerRegister('Z', num=30, aliases=(r31, r30))


lo_regs = (r0, r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12, r13, r14,
           r15)
hi_regs = (r16, r17, r18, r19, r20, r21, r22, r23, r24, r25, r26, r27,
           r28, r29, r30, r31)
all_regs = lo_regs + hi_regs

gdb_registers = all_regs + (SREG, SP, PC)

lo_w_regs = (
    r1r0, r3r2, r5r4, r7r6, r9r8, r11r10, r13r12, r15r14)
hi_w_regs = (
    r17r16, r19r18, r21r20, r23r22, r25r24, X, Y, Z)
all_w_regs = lo_w_regs + hi_w_regs

num_reg_map = {r.num: r for r in all_regs}


def get_register(n):
    return num_reg_map[n]


get8reg = get_register


def get16reg(n):
    mp = {r.num: r for r in all_w_regs}
    return mp[n]


register_classes = [
    RegisterClass('reg', [i8], AvrRegister, all_regs),
    RegisterClass('hireg', [], HighAvrRegister, hi_regs),
    RegisterClass('ptrreg', [], AvrPointerRegister, (X, Y, Z)),
    RegisterClass('reg16', [i16, ptr], AvrWordRegister, all_w_regs),
    RegisterClass('hireg16', [], HighAvrWordRegister, hi_w_regs),
    ]
