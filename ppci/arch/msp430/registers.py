""" Description of msp430 registers """

from ..registers import Register, RegisterClass
from ... import ir


class Msp430Register(Register):
    bitsize = 16

    def __repr__(self):
        if self.is_colored:
            return 'R{}'.format(self.color)
        else:
            return self.name


# 8 bit registers:
PCB = Msp430Register('r0', num=0, aka=('pc',))
rpc = PCB
r0 = PCB
PC = r0
r1 = Msp430Register('r1', num=1, aka=('sp',))
SP = r1  # Stack pointer
r2 = Msp430Register('r2', num=2, aka=('sr',))
SR = r2  # Status register
r3 = Msp430Register('r3', num=3, aka=('cg',))
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

Msp430Register.registers = [
    r0, r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12, r13, r14, r15]

all_registers = [r4, r5, r6, r7, r8, r9, r10, r11, r12, r13, r14, r15]

num2reg = {r.num: r for r in all_registers}

register_classes = [
    RegisterClass(
        'reg', [ir.i16, ir.i8, ir.u16, ir.u8, ir.ptr],
        Msp430Register, all_registers)
    ]
