
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


R0 = RiscvRegister('x0', num=0, aka=('zero',))
LR = RiscvRegister('x1', num=1, aka=('ra',))
SP = RiscvRegister('x2', num=2, aka=('sp',))
R3 = RiscvRegister('x3', num=3, aka=('gp',))
R4 = RiscvRegister('x4', num=4, aka=('tp',))
R5 = RiscvRegister('x5', num=5, aka=('t0',))
R6 = RiscvRegister('x6', num=6, aka=('t1',))
R7 = RiscvRegister('x7', num=7, aka=('t2',))
FP = RiscvRegister('x8', num=8, aka=('s0', 'fp'))
R9 = RiscvRegister('x9', num=9, aka=('s1',))
R10 = RiscvRegister('x10', num=10, aka=('a0',))
R11 = RiscvRegister('x11', num=11, aka=('a1',))
R12 = RiscvRegister('x12', num=12, aka=('a2',))
R13 = RiscvRegister('x13', num=13, aka=('a3',))
R14 = RiscvRegister('x14', num=14, aka=('a4',))
R15 = RiscvRegister('x15', num=15, aka=('a5',))
R16 = RiscvRegister('x16', num=16, aka=('a6',))
R17 = RiscvRegister('x17', num=17, aka=('a7',))
R18 = RiscvRegister('x18', num=18, aka=('s2',))
R19 = RiscvRegister('x19', num=19, aka=('s3',))
R20 = RiscvRegister('x20', num=20, aka=('s4',))
R21 = RiscvRegister('x21', num=21, aka=('s5',))
R22 = RiscvRegister('x22', num=22, aka=('s6',))
R23 = RiscvRegister('x23', num=23, aka=('s7',))
R24 = RiscvRegister('x24', num=24, aka=('s8',))
R25 = RiscvRegister('x25', num=25, aka=('s9',))
R26 = RiscvRegister('x26', num=26, aka=('s10',))
R27 = RiscvRegister('x27', num=27, aka=('s11',))
R28 = RiscvRegister('x28', num=28, aka=('t3',))
R29 = RiscvRegister('x29', num=29, aka=('t4',))
R30 = RiscvRegister('x30', num=30, aka=('t5',))
R31 = RiscvRegister('x31', num=31, aka=('t6',))

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
