
from ..basetarget import Register

class ArmRegister(Register):
    def __init__(self, num, name):
        super().__init__(name)
        self.num = num

    def __repr__(self):
        return self.name


class Reg8Op(ArmRegister):
    pass


def get_register(n):
    """ Based on a number, get the corresponding register """
    return num2regmap[n]


def register_range(a, b):
    """ Return set of registers from a to b """
    assert a.num < b.num
    return {get_register(n) for n in range(a.num, b.num + 1)}


R0 = Reg8Op(0, 'r0')
R1 = Reg8Op(1, 'r1')
R2 = Reg8Op(2, 'r2')
R3 = Reg8Op(3, 'r3')
R4 = Reg8Op(4, 'r4')
R5 = Reg8Op(5, 'r5')
R6 = Reg8Op(6, 'r6')
R7 = Reg8Op(7, 'r7')
R8 = ArmRegister(8, 'r8')
R9 = ArmRegister(9, 'r9')
R10 = ArmRegister(10, 'r10')
R11 = ArmRegister(11, 'r11')
R12 = ArmRegister(12, 'r12')

# Other registers:
# TODO
SP = ArmRegister(13, 'sp')
LR = ArmRegister(14, 'lr')
PC = ArmRegister(15, 'pc')

registers = [R0, R1, R2, R3, R4, R5, R6, R7, SP, LR, PC]
num2regmap = {r.num: r for r in registers}

