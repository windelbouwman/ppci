
from ..isa import Register, Syntax

# pylint: disable=invalid-name


class ArmRegister(Register):
    bitsize = 32
    def __repr__(self):
        if self.is_colored:
            return get_register(self.color).name
        else:
            return self.name

    syntaxi = 'reg', [
        Syntax(['r0'], new_func=lambda: R0),
        Syntax(['r1'], new_func=lambda: R1),
        Syntax(['r2'], new_func=lambda: R2),
        Syntax(['r3'], new_func=lambda: R3),
        Syntax(['r4'], new_func=lambda: R4),
        Syntax(['r5'], new_func=lambda: R5),
        Syntax(['r6'], new_func=lambda: R6),
        Syntax(['r7'], new_func=lambda: R7),
        Syntax(['r8'], new_func=lambda: R8),
        Syntax(['r9'], new_func=lambda: R9),
        Syntax(['r10'], new_func=lambda: R10),
        Syntax(['r11'], new_func=lambda: R11),
        Syntax(['r12'], new_func=lambda: R12),
        Syntax(['sp'], new_func=lambda: SP),
        Syntax(['lr'], new_func=lambda: LR),
        Syntax(['pc'], new_func=lambda: PC)
        ]


class Reg8Op(ArmRegister):
    syntaxi = '$loreg$', [
        Syntax(['r0'], new_func=lambda: R0),
        Syntax(['r1'], new_func=lambda: R1),
        Syntax(['r2'], new_func=lambda: R2),
        Syntax(['r3'], new_func=lambda: R3),
        Syntax(['r4'], new_func=lambda: R4),
        Syntax(['r5'], new_func=lambda: R5),
        Syntax(['r6'], new_func=lambda: R6),
        Syntax(['r7'], new_func=lambda: R7)
        ]


def get_register(n):
    """ Based on a number, get the corresponding register """
    return num2regmap[n]


def register_range(a, b):
    """ Return set of registers from a to b """
    assert a.num < b.num
    return {get_register(n) for n in range(a.num, b.num + 1)}


class RegisterSet(set):
    def __repr__(self):
        reg_names = sorted(str(r) for r in self)
        return ', '.join(reg_names)


R0 = Reg8Op('R0', num=0)
R1 = Reg8Op('R1', num=1)
R2 = Reg8Op('R2', num=2)
R3 = Reg8Op('R3', num=3)
R4 = Reg8Op('R4', num=4)
R5 = Reg8Op('R5', num=5)
R6 = Reg8Op('R6', num=6)
R7 = Reg8Op('R7', num=7)
R8 = ArmRegister('R8', num=8)
R9 = ArmRegister('R9', num=9)
R10 = ArmRegister('R10', num=10)
R11 = ArmRegister('R11', num=11)
R12 = ArmRegister('R12', num=12)
SP = ArmRegister('SP', num=13)
LR = ArmRegister('LR', num=14)
PC = ArmRegister('PC', num=15)

registers_low = [R0, R1, R2, R3, R4, R5, R6, R7]
registers_high = [R8, R9, R10, R11, R12, SP, LR, PC]
all_registers = registers_low + registers_high
num2regmap = {r.num: r for r in all_registers}


class Coreg(Register):

    syntaxi = 'coreg', [
        Syntax(['c0'], new_func=lambda: c0),
        Syntax(['c1'], new_func=lambda: c1),
        Syntax(['c2'], new_func=lambda: c2),
        Syntax(['c3'], new_func=lambda: c3),
        Syntax(['c4'], new_func=lambda: c4),
        Syntax(['c5'], new_func=lambda: c5),
        Syntax(['c6'], new_func=lambda: c6),
        Syntax(['c7'], new_func=lambda: c7),
        Syntax(['c8'], new_func=lambda: c8),
        Syntax(['c9'], new_func=lambda: c9),
        Syntax(['c10'], new_func=lambda: c10),
        Syntax(['c11'], new_func=lambda: c11),
        Syntax(['c12'], new_func=lambda: c12),
        Syntax(['c13'], new_func=lambda: c13),
        Syntax(['c14'], new_func=lambda: c14),
        Syntax(['c15'], new_func=lambda: c15),
        ]

c0 = Coreg('c0', 0)
c1 = Coreg('c1', 1)
c2 = Coreg('c2', 2)
c3 = Coreg('c3', 3)
c4 = Coreg('c4', 4)
c5 = Coreg('c5', 5)
c6 = Coreg('c6', 6)
c7 = Coreg('c7', 7)
c8 = Coreg('c8', 8)
c9 = Coreg('c9', 9)
c10 = Coreg('c10', 10)
c11 = Coreg('c11', 11)
c12 = Coreg('c12', 12)
c13 = Coreg('c13', 13)
c14 = Coreg('c14', 14)
c15 = Coreg('c15', 15)


class Coproc:
    def __init__(self, name, num):
        self.num = num

    syntaxi = 'coproc', [
        Syntax(['p8'], new_func=lambda: p8),
        Syntax(['p9'], new_func=lambda: p9),
        Syntax(['p10'], new_func=lambda: p10),
        Syntax(['p11'], new_func=lambda: p11),
        Syntax(['p12'], new_func=lambda: p12),
        Syntax(['p13'], new_func=lambda: p13),
        Syntax(['p14'], new_func=lambda: p14),
        Syntax(['p15'], new_func=lambda: p15),
        ]


p8 = Coproc('p8', 8)
p9 = Coproc('p9', 9)
p10 = Coproc('p10', 10)
p11 = Coproc('p11', 11)
p12 = Coproc('p12', 12)
p13 = Coproc('p13', 13)
p14 = Coproc('p14', 14)
p15 = Coproc('p15', 15)
