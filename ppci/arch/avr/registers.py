from ..isa import Register, Syntax


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


class AvrPseudo16Register(Register):
    """
        To be able to use 16 bit values, use this imaginary register type
        containing a pair of real registers.
    """
    bitsize = 16

    def __init__(self, name, hi=None, lo=None):
        super().__init__(name)
        if not hi:
            hi = AvrRegister(name + '_hi')
        if not lo:
            lo = AvrRegister(name + '_lo')
        self._hi = hi
        self._lo = lo

    @property
    def hi(self):
        return self._hi

    @property
    def lo(self):
        return self._lo


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

r16 = AvrRegister('r16', num=16)
r17 = AvrRegister('r17', num=17)
r18 = AvrRegister('r18', num=18)
r19 = AvrRegister('r19', num=19)
r20 = AvrRegister('r20', num=20)
r21 = AvrRegister('r21', num=21)
r22 = AvrRegister('r22', num=22)
r23 = AvrRegister('r23', num=23)

r24 = AvrRegister('r24', num=24)
r25 = AvrRegister('r25', num=25)
r26 = AvrRegister('r26', num=26)
r27 = AvrRegister('r27', num=27)
r28 = AvrRegister('r28', num=28)
r29 = AvrRegister('r29', num=29)
r30 = AvrRegister('r30', num=30)
r31 = AvrRegister('r31', num=31)

X = AvrPseudo16Register('X', hi=r27, lo=r26)
Y = AvrPseudo16Register('Y', hi=r29, lo=r28)
Z = AvrPseudo16Register('Z', hi=r31, lo=r30)

all_regs = [r0, r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12, r13, r14,
            r15, r16, r17, r18, r19, r20, r21, r22, r23, r24, r25, r26, r27,
            r28, r29, r30, r31]

num_reg_map = {r.num: r for r in all_regs}


def get_register(n):
    return num_reg_map[n]
