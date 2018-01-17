""" Description of mips registers """

from ..registers import Register, RegisterClass
from ... import ir


class MipsRegister(Register):
    bitsize = 32

    def __repr__(self):
        if self.is_colored:
            return 'R{}'.format(self.color)
        else:
            return self.name


r0 = MipsRegister('r0', num=0)
r1 = MipsRegister('r1', num=1)
r2 = MipsRegister('v0', num=2, aka=('r2',))
v0 = r2
r3 = MipsRegister('v1', num=3, aka=('r3',))
v1 = r3
r4 = MipsRegister('a0', num=4, aka=('r4',))
a0 = r4
r5 = MipsRegister('a1', num=5, aka=('r5',))
a1 = r5
r6 = MipsRegister('r6', num=6)
a2 = r6
r7 = MipsRegister('r7', num=7)
a3 = r7
r8 = MipsRegister('r8', num=8)
r9 = MipsRegister('r9', num=9)


r29 = MipsRegister('sp', num=29, aka=('r29',))
sp = r29  # Stack pointer
r30 = MipsRegister('fp', num=30, aka=('r30',))
fp = r30  # Frame pointer
r31 = MipsRegister('ra', num=31, aka=('r31',))
lr = r31  # Link register / return address
ra = r31

MipsRegister.registers = [r1, r2, r3, r4, r5, r6, r7, r8, r9, r29, r30, r31]

all_registers = [r1, r2, r3, r4, r5, r6, r7, r8, r9, r31]

register_classes = [
    RegisterClass(
        'reg', [ir.i16, ir.i8, ir.u16, ir.u8, ir.i32, ir.u32, ir.ptr],
        MipsRegister, all_registers)
    ]

caller_save = []
callee_save = []
