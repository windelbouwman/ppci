
from ..isa import Register, Syntax

# pylint: disable=invalid-name


class RiscvRegister(Register):
    bitsize = 32
    def __repr__(self):
        if self.is_colored:
            return get_register(self.color).name
            return '{}={}'.format(self.name, self.color)
        else:
            return self.name

    syntaxi = 'reg', [
        Syntax(['r0'], new_func=lambda: R0),
        Syntax(['lr'], new_func=lambda: LR),
        Syntax(['sp'], new_func=lambda: SP),
        Syntax(['r3'], new_func=lambda: R3),
        Syntax(['r4'], new_func=lambda: R4),
        Syntax(['r5'], new_func=lambda: R5),
        Syntax(['r6'], new_func=lambda: R6),
        Syntax(['r7'], new_func=lambda: R7),
        Syntax(['fp'], new_func=lambda: FP),
        Syntax(['r9'], new_func=lambda: R9),
        Syntax(['r10'], new_func=lambda: R10),
        Syntax(['r11'], new_func=lambda: R11),
        Syntax(['r12'], new_func=lambda: R12),
        Syntax(['r13'], new_func=lambda: R13),
        Syntax(['r14'], new_func=lambda: R14),
        Syntax(['r15'], new_func=lambda: R15),
        Syntax(['r16'], new_func=lambda: R16),
        Syntax(['r17'], new_func=lambda: R17),
        Syntax(['r18'], new_func=lambda: R18),
        Syntax(['r19'], new_func=lambda: R19),
        Syntax(['r20'], new_func=lambda: R20),
        Syntax(['r21'], new_func=lambda: R21),
        Syntax(['r22'], new_func=lambda: R22),
        Syntax(['r23'], new_func=lambda: R23),
        Syntax(['r24'], new_func=lambda: R24),
        Syntax(['r25'], new_func=lambda: R25),
        Syntax(['r26'], new_func=lambda: R26),
        Syntax(['r27'], new_func=lambda: R27),
        Syntax(['r28'], new_func=lambda: R28),
        Syntax(['r29'], new_func=lambda: R29),
        Syntax(['r30'], new_func=lambda: R30),
        Syntax(['r31'], new_func=lambda: R31)
        ]



def get_register(n):
    """ Based on a number, get the corresponding register """
    return num2regmap[n]


def register_range(a, b):
    """ Return set of registers from a to b """
    assert a.num < b.num
    return {get_register(n) for n in range(a.num, b.num + 1)}


R0 = RiscvRegister('R0', num=0)
LR = RiscvRegister('LR', num=1)
SP = RiscvRegister('SP', num=2)
R3 = RiscvRegister('R3', num=3)
R4 = RiscvRegister('R4', num=4)
R5 = RiscvRegister('R5', num=5)
R6 = RiscvRegister('R6', num=6)
R7 = RiscvRegister('R7', num=7)
FP = RiscvRegister('FP', num=8)
R9 = RiscvRegister('R9', num=9)
R10 = RiscvRegister('R10', num=10)
R11 = RiscvRegister('R11', num=11)
R12 = RiscvRegister('R12', num=12)
R13 = RiscvRegister('R13', num=13)
R14 = RiscvRegister('R14', num=14)
R15 = RiscvRegister('R15', num=15)
R16 = RiscvRegister('R16', num=16)
R17 = RiscvRegister('R17', num=17)
R18 = RiscvRegister('R18', num=18)
R19 = RiscvRegister('R19', num=19)
R20 = RiscvRegister('R20', num=20)
R21 = RiscvRegister('R21', num=21)
R22 = RiscvRegister('R22', num=22)
R23 = RiscvRegister('R23', num=23)
R24 = RiscvRegister('R24', num=24)
R25 = RiscvRegister('R25', num=25)
R26 = RiscvRegister('R26', num=26)
R27 = RiscvRegister('R27', num=27)
R28 = RiscvRegister('R28', num=28)
R29 = RiscvRegister('R29', num=29)
R30 = RiscvRegister('R30', num=30)
R31 = RiscvRegister('R31', num=31)

registers_low = [R0, LR, SP, R3, R4, R5, R6, R7]
registers_high = [FP,R9, R10, R11, R12, R13, R14 ,R15, R16, R17, R18, R19, R20, R21, R22, R23, R24, R25, R26, R27, R28, R29, R30, R31]
registers = registers_low + registers_high
num2regmap = {r.num: r for r in registers}




