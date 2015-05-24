
from ..isa import Register, Syntax


class Msp430Register(Register):
    def __init__(self, num, name):
        super().__init__(name)
        self._num = num
    syntaxi = 'reg', [
        Syntax(['r0'], new_func=lambda: r0),
        Syntax(['r1'], new_func=lambda: r1),
        Syntax(['sp'], new_func=lambda: SP),
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
        ]

# 8 bit registers:
PCB = Msp430Register(0, 'r0')
rpc = PCB
r0 = PCB
r1 = Msp430Register(1, 'r1')
SP = r1  # Stack pointer
r2 = Msp430Register(2, 'r2')
SR = r2  # Status register
r3 = Msp430Register(3, 'r3')
CG = r3  # Constant generator
r4 = Msp430Register(4, 'r4')
r5 = Msp430Register(5, 'r5')
r6 = Msp430Register(6, 'r6')
r7 = Msp430Register(7, 'r7')
r8 = Msp430Register(8, 'r8')
r9 = Msp430Register(9, 'r9')
r10 = Msp430Register(10, 'r10')
r11 = Msp430Register(11, 'r11')
r12 = Msp430Register(12, 'r12')
r13 = Msp430Register(13, 'r13')
r14 = Msp430Register(14, 'r14')
r15 = Msp430Register(15, 'r15')
