from ..encoding import Register, Syntax


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
