
from ..registers import Register

# pylint: disable=invalid-name


class ArmRegister(Register):
    bitsize = 32

    def __repr__(self):
        if self.is_colored:
            return get_register(self.color).name
        else:
            return self.name


class LowArmRegister(ArmRegister):
    pass


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


R0 = LowArmRegister('R0', num=0)
R1 = LowArmRegister('R1', num=1)
R2 = LowArmRegister('R2', num=2)
R3 = LowArmRegister('R3', num=3)
R4 = LowArmRegister('R4', num=4)
R5 = LowArmRegister('R5', num=5)
R6 = LowArmRegister('R6', num=6)
R7 = LowArmRegister('R7', num=7)
R8 = ArmRegister('R8', num=8)
R9 = ArmRegister('R9', num=9)
R10 = ArmRegister('R10', num=10)
R11 = ArmRegister('R11', num=11)
R12 = ArmRegister('R12', num=12)
SP = ArmRegister('SP', num=13)
LR = ArmRegister('LR', num=14)
PC = ArmRegister('PC', num=15)

registers_low = (R0, R1, R2, R3, R4, R5, R6, R7)
registers_high = (R8, R9, R10, R11, R12, SP, LR, PC)
all_registers = registers_low + registers_high
num2regmap = {r.num: r for r in all_registers}


LowArmRegister.registers = registers_low
ArmRegister.registers = all_registers


class Coreg(Register):
    pass


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

Coreg.registers = [
    c0, c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11, c12, c13, c14, c15]


class Coproc(Register):
    pass


p8 = Coproc('p8', 8)
p9 = Coproc('p9', 9)
p10 = Coproc('p10', 10)
p11 = Coproc('p11', 11)
p12 = Coproc('p12', 12)
p13 = Coproc('p13', 13)
p14 = Coproc('p14', 14)
p15 = Coproc('p15', 15)

Coproc.registers = [p8, p9, p10, p11, p12, p13, p14, p15]
