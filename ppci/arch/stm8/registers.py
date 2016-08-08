from ..encoding import Register


class Stm8AccumulatorRegister(Register):
    bitsize = 8

class Stm8IndexRegister(Register):
    bitsize = 16

class Stm8StackPointerRegister(Register):
    bitsize = 16

class Stm8ProgramCounterRegister(Register):
    bitsize = 24

class Stm8StatusRegister(Register):
    bitsize = 8


A = Stm8AccumulatorRegister('A')

X = Stm8IndexRegister('X')
Y = Stm8IndexRegister('Y')

SP = Stm8StackPointerRegister('SP')

PC = Stm8ProgramCounterRegister('PC')

CC = Stm8StatusRegister('CC')