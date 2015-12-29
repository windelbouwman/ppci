"""
    This is an example target with some instructions. It is used in test-cases
    and serves as a minimal example.
"""

from .isa import Instruction, Syntax
from .target import Target
from .isa import register_argument, Register


class SimpleTarget(Target):
    def __init__(self):
        super().__init__('SimpleTarget')


R0 = Register('r0', 0)
R1 = Register('r1', 1)
R2 = Register('r2', 2)
R3 = Register('r3', 3)
R4 = Register('r4', 4)
R5 = Register('r5', 5)
R6 = Register('r6', 6)


class TestInstruction(Instruction):
    """ Base class for all example instructions """
    tokens = []


class Def(TestInstruction):
    rd = register_argument('rd', Register, write=True)
    syntax = Syntax(['def', rd])


class Use(TestInstruction):
    rn = register_argument('rn', Register, read=True)
    syntax = Syntax(['use', rn])


class DefUse(TestInstruction):
    rd = register_argument('rd', Register, write=True)
    rn = register_argument('rn', Register, read=True)
    syntax = Syntax(['cpy', rd, rn])


class Add(TestInstruction):
    rd = register_argument('rd', Register, write=True)
    rm = register_argument('rm', Register, read=True)
    rn = register_argument('rn', Register, read=True)
    syntax = Syntax(['add', rd, rm, rn])


class Cmp(TestInstruction):
    rm = register_argument('rm', Register, read=True)
    rn = register_argument('rn', Register, read=True)
    syntax = Syntax(['cmp', rm, rn])


class Use3(TestInstruction):
    rm = register_argument('rm', Register, read=True)
    rn = register_argument('rn', Register, read=True)
    ro = register_argument('ro', Register, read=True)
    syntax = Syntax(['use3', rm, rn, ro])


class Mov(TestInstruction):
    rd = register_argument('rd', Register, write=True)
    rm = register_argument('rm', Register, read=True)
    syntax = Syntax(['mov', rd, rm])
