""" Microblaze register definitions """

from ... import ir
from ..registers import Register, RegisterClass


class MicroBlazeRegister(Register):
    """ A microblaze register """
    bitsize = 32


R0 = MicroBlazeRegister('R0', num=0)
R1 = MicroBlazeRegister('R1', num=1)
R2 = MicroBlazeRegister('R2', num=2)
R3 = MicroBlazeRegister('R3', num=3)
R4 = MicroBlazeRegister('R4', num=4)
R5 = MicroBlazeRegister('R5', num=5)
R6 = MicroBlazeRegister('R6', num=6)
R7 = MicroBlazeRegister('R7', num=7)
R8 = MicroBlazeRegister('R8', num=8)
R9 = MicroBlazeRegister('R9', num=9)
R10 = MicroBlazeRegister('R10', num=10)
R11 = MicroBlazeRegister('R11', num=11)
R12 = MicroBlazeRegister('R12', num=12)
R13 = MicroBlazeRegister('R13', num=13)
R14 = MicroBlazeRegister('R14', num=14)
R15 = MicroBlazeRegister('R15', num=15)
R16 = MicroBlazeRegister('R16', num=16)
R17 = MicroBlazeRegister('R17', num=17)
R18 = MicroBlazeRegister('R18', num=18)
R19 = MicroBlazeRegister('R19', num=19)
R20 = MicroBlazeRegister('R20', num=20)
R21 = MicroBlazeRegister('R21', num=21)
R22 = MicroBlazeRegister('R22', num=22)
R23 = MicroBlazeRegister('R23', num=23)
R24 = MicroBlazeRegister('R24', num=24)
R25 = MicroBlazeRegister('R25', num=25)
R26 = MicroBlazeRegister('R26', num=26)
R27 = MicroBlazeRegister('R27', num=27)
R28 = MicroBlazeRegister('R28', num=28)
R29 = MicroBlazeRegister('R29', num=29)
R30 = MicroBlazeRegister('R30', num=30)
R31 = MicroBlazeRegister('R31', num=31)
all_registers = [
    R0, R1, R2, R3, R4, R5, R6, R7,
    R8, R9, R10, R11, R12, R13, R14, R15,
    R16, R17, R18, R19, R20, R21, R22, R23,
    R24, R25, R26, R27, R28, R29, R30, R31
]
MicroBlazeRegister.registers = all_registers

caller_saved = [
    R3, R4, R5, R6, R7, R8, R9, R10, R11, R12
]
callee_saved = [
    R19, R20, R21, R22, R23,
    R24, R25, R26, R27, R28, R29, R30, R31
]

general_purpose = caller_saved + callee_saved

register_classes = [
    RegisterClass(
        'reg',
        [ir.i8, ir.i16, ir.i32, ir.ptr, ir.u8, ir.u16, ir.u32],
        MicroBlazeRegister,
        all_registers)
    ]


