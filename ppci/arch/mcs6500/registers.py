from ..registers import Register


class Accumulator(Register):
    bitsize = 8


A = Accumulator('A', num=0)
