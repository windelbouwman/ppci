from ..registers import Register, RegisterClass
from ... import ir


class Accumulator(Register):
    bitsize = 8


# TODO: hack, this is no register but a stack position!
class Temporary(Register):
    """ On stack temporary """
    bitsize = 8


A = Accumulator('A', num=0)

r0 = Temporary('r0', 0)
r1 = Temporary('r1', 1)
r2 = Temporary('r2', 2)
r3 = Temporary('r3', 3)
r4 = Temporary('r4', 4)


Temporary.registers = [r0, r1, r2, r3, r4]


register_classes = [
    RegisterClass(
        'reg', [ir.i8, ir.u8, ir.ptr], Temporary,
        Temporary.registers),
    ]
