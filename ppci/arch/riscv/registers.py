
from ..registers import Register

# pylint: disable=invalid-name


class RiscvRegister(Register):
    bitsize = 32

    def __repr__(self):
        if self.is_colored:
            return get_register(self.color).name
            return '{}={}'.format(self.name, self.color)
        else:
            return self.name


class RiscvProgramCounterRegister(Register):
    bitsize = 32


def get_register(n):
    """ Based on a number, get the corresponding register """
    return num2regmap[n]


def register_range(a, b):
    """ Return set of registers from a to b """
    assert a.num < b.num
    return {get_register(n) for n in range(a.num, b.num + 1)}


R0 = RiscvRegister('R0', num=0, aka=('zero', 'x0'))
LR = RiscvRegister('LR', num=1, aka=('x1', 'ra'))
SP = RiscvRegister('SP', num=2, aka=('x2',))
R3 = RiscvRegister('R3', num=3, aka=('x3', 'gp'))
R4 = RiscvRegister('R4', num=4, aka=('x4', 'tp'))
R5 = RiscvRegister('R5', num=5, aka=('x5', 't0'))
R6 = RiscvRegister('R6', num=6, aka=('x6', 't1'))
R7 = RiscvRegister('R7', num=7, aka=('x7', 't2'))
FP = RiscvRegister('FP', num=8, aka=('x8',))
R9 = RiscvRegister('R9', num=9, aka=('x9', 's1'))
R10 = RiscvRegister('R10', num=10, aka=('x10', 'a0'))
R11 = RiscvRegister('R11', num=11, aka=('x11', 'a1'))
R12 = RiscvRegister('R12', num=12, aka=('x12', 'a2'))
R13 = RiscvRegister('R13', num=13, aka=('x13', 'a3'))
R14 = RiscvRegister('R14', num=14, aka=('x14', 'a4'))
R15 = RiscvRegister('R15', num=15, aka=('x15', 'a5'))
R16 = RiscvRegister('R16', num=16, aka=('x16', 'a6'))
R17 = RiscvRegister('R17', num=17, aka=('x17', 'a7'))
R18 = RiscvRegister('R18', num=18, aka=('x18', 's2'))
R19 = RiscvRegister('R19', num=19, aka=('x19', 's3'))
R20 = RiscvRegister('R20', num=20, aka=('x20', 's4'))
R21 = RiscvRegister('R21', num=21, aka=('x21', 's5'))
R22 = RiscvRegister('R22', num=22, aka=('x22', 's6'))
R23 = RiscvRegister('R23', num=23, aka=('x23', 's7'))
R24 = RiscvRegister('R24', num=24, aka=('x24', 's8'))
R25 = RiscvRegister('R25', num=25, aka=('x25', 's9'))
R26 = RiscvRegister('R26', num=26, aka=('x26', 's10'))
R27 = RiscvRegister('R27', num=27, aka=('x27', 's11'))
R28 = RiscvRegister('R28', num=28, aka=('x28', 't3'))
R29 = RiscvRegister('R29', num=29, aka=('x29', 't4'))
R30 = RiscvRegister('R30', num=30, aka=('x30', 't5'))
R31 = RiscvRegister('R31', num=31, aka=('x31', 't6'))

PC = RiscvProgramCounterRegister('PC', num=32)

registers_low = [R0, LR, SP, R3, R4, R5, R6, R7]
registers_high = [
    FP, R9, R10, R11, R12, R13, R14, R15, R16,
    R17, R18, R19, R20, R21, R22, R23, R24,
    R25, R26, R27, R28, R29, R30, R31]
all_registers = registers_low + registers_high
RiscvRegister.registers = all_registers
num2regmap = {r.num: r for r in all_registers}

gdb_registers = all_registers + [PC]
