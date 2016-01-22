
from ..isa import Register, Syntax


def get_register(color):
    return num2reg[color]


class Msp430Register(Register):
    bitsize = 16
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

    def __repr__(self):
        if self.is_colored:
            return 'R{}'.format(self.color)
        else:
            return self.name


# 8 bit registers:
PCB = Msp430Register('r0', num=0)
rpc = PCB
r0 = PCB
PC = r0
r1 = Msp430Register('r1', num=1)
SP = r1  # Stack pointer
r2 = Msp430Register('r2', num=2)
SR = r2  # Status register
r3 = Msp430Register('r3', num=3)
CG = r3  # Constant generator
r4 = Msp430Register('r4', num=4)
r5 = Msp430Register('r5', num=5)
r6 = Msp430Register('r6', num=6)
r7 = Msp430Register('r7', num=7)
r8 = Msp430Register('r8', num=8)
r9 = Msp430Register('r9', num=9)
r10 = Msp430Register('r10', num=10)
r11 = Msp430Register('r11', num=11)
r12 = Msp430Register('r12', num=12)
r13 = Msp430Register('r13', num=13)
r14 = Msp430Register('r14', num=14)
r15 = Msp430Register('r15', num=15)

all_registers = [r4, r5, r6, r7, r8, r9, r10, r11, r12, r13, r14, r15]

num2reg = {r.num: r for r in all_registers}
