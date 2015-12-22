from ..isa import Register, Syntax


class AvrRegister(Register):
    bitsize = 8
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
        ]


#for i in range(32):
#    reg_name = 'r{}'.format(i)
#    globals()['r{}'.format(i)] = AvrRegister(reg_name, num=i)

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
