from ..encoding import Register
from ..registers import RegisterClass
from ... import ir


class Stm8Register(Register):
    pass


class Stm88BitRegister(Stm8Register):
    bitsize = 8


class Stm816BitRegister(Stm8Register):
    bitsize = 16


class Stm824BitRegister(Stm8Register):
    bitsize = 24


class Stm8AccumulatorRegister(Stm88BitRegister):
    pass


class Stm8IndexLowRegister(Stm88BitRegister):
    pass


class Stm8IndexHighRegister(Stm88BitRegister):
    pass


class Stm8IndexRegister(Stm816BitRegister):
    pass


class Stm8StackPointerRegister(Stm816BitRegister):
    pass


class Stm8ProgramCounterRegister(Stm824BitRegister):
    pass


class Stm8ConditionCodeRegister(Stm88BitRegister):
    pass


class Stm8RegisterA(Stm8AccumulatorRegister):
    pass


class Stm8RegisterXL(Stm8IndexLowRegister):
    pass


class Stm8RegisterXH(Stm8IndexHighRegister):
    pass


class Stm8RegisterX(Stm8IndexRegister):
    pass


class Stm8RegisterYL(Stm8IndexLowRegister):
    pass


class Stm8RegisterYH(Stm8IndexHighRegister):
    pass


class Stm8RegisterY(Stm8IndexRegister):
    pass


class Stm8RegisterSP(Stm8StackPointerRegister):
    pass


class Stm8RegisterPC(Stm8ProgramCounterRegister):
    pass


class Stm8RegisterCC(Stm8ConditionCodeRegister):
    pass


A = Stm8RegisterA('A')

XL = Stm8RegisterXL('XL')
XH = Stm8RegisterXH('XH')
X = Stm8RegisterX('X', aliases=(XL, XH))

YL = Stm8RegisterYL('YL')
YH = Stm8RegisterYH('YH')
Y = Stm8RegisterY('Y', aliases=(YL, YH))

SP = Stm8RegisterSP('SP')

PC = Stm8RegisterPC('PC')

CC = Stm8RegisterCC('CC')

Stm8Register.registers = [A, XL, XH, X, YL, YH, Y, SP, PC, CC]
Stm88BitRegister.registers = [A, XL, XH, YL, YH, CC]
Stm816BitRegister.registers = [X, Y, SP]
Stm824BitRegister.registers = [PC]
Stm8AccumulatorRegister.registers = [A]
Stm8IndexLowRegister.registers = [XL, YL]
Stm8IndexHighRegister.registers = [XH, YH]
Stm8IndexRegister.registers = [X, Y]
Stm8StackPointerRegister.registers = [SP]
Stm8ProgramCounterRegister.registers = [PC]
Stm8ConditionCodeRegister.registers = [CC]
Stm8RegisterA.registers = [A]
Stm8RegisterXL.registers = [XL]
Stm8RegisterXH.registers = [XH]
Stm8RegisterX.registers = [X]
Stm8RegisterYL.registers = [YL]
Stm8RegisterYH.registers = [YH]
Stm8RegisterY.registers = [Y]
Stm8RegisterSP.registers = [SP]
Stm8RegisterPC.registers = [PC]
Stm8RegisterCC.registers = [CC]


# Emulate 'registers' in memory bytes at address 0..16

class Stm8Virt8Register(Register):
    """ Virtual stm8 register of 8 bit """
    bitsize = 8


class Stm8Virt16Register(Register):
    """ Virtual stm8 register of 16 bit """
    bitsize = 16


vrb0 = Stm8Virt8Register('vrb0', num=0)
vrb1 = Stm8Virt8Register('vrb1', num=1)
vrb2 = Stm8Virt8Register('vrb2', num=2)
vrb3 = Stm8Virt8Register('vrb3', num=3)
vrb4 = Stm8Virt8Register('vrb4', num=4)
vrb5 = Stm8Virt8Register('vrb5', num=5)
vrb6 = Stm8Virt8Register('vrb6', num=6)
vrb7 = Stm8Virt8Register('vrb7', num=7)
vrb8 = Stm8Virt8Register('vrb8', num=8)
vrb9 = Stm8Virt8Register('vrb9', num=9)
vrb10 = Stm8Virt8Register('vrb10', num=10)
vrb11 = Stm8Virt8Register('vrb11', num=11)
Stm8Virt8Register.registers = [
    vrb0, vrb1, vrb2, vrb3, vrb4, vrb5, vrb6, vrb7,
    vrb8, vrb9, vrb10, vrb11]

vrw0 = Stm8Virt16Register('vrw0', num=0, aliases=(vrb0, vrb1))
vrw1 = Stm8Virt16Register('vrw1', num=2, aliases=(vrb2, vrb3))
vrw2 = Stm8Virt16Register('vrw2', num=4, aliases=(vrb4, vrb5))
vrw3 = Stm8Virt16Register('vrw3', num=6, aliases=(vrb6, vrb7))
vrw4 = Stm8Virt16Register('vrw4', num=8, aliases=(vrb8, vrb9))
Stm8Virt16Register.registers = [
    vrw0, vrw1, vrw2, vrw3, vrw4]


register_classes = [
    RegisterClass(
        'vreg8', [ir.i8, ir.u8], Stm8Virt8Register,
        Stm8Virt8Register.registers),
    RegisterClass(
        'vreg16', [ir.ptr, ir.i16, ir.u16], Stm8Virt16Register,
        Stm8Virt16Register.registers),
    ]
