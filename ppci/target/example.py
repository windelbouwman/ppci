"""
    This is an example target with some instructions. It is used in test-cases
    and serves as a minimal example.
"""

from . import Instruction, Target
from . import register_argument, Register


class SimpleTarget(Target):
    def __init__(self):
        super().__init__('SimpleTarget')


class TestInstruction(Instruction):
    """ Base class for all example instructions """
    pass


class Def(TestInstruction):
    rd = register_argument('rd', Register, write=True)
    syntax = ['def', rd]


class Use(TestInstruction):
    rn = register_argument('rn', Register, read=True)
    syntax = ['use', rn]


class DefUse(TestInstruction):
    rd = register_argument('rd', Register, write=True)
    rn = register_argument('rn', Register, read=True)
    syntax = ['cpy', rd, rn]


class Add(TestInstruction):
    rd = register_argument('rd', Register, write=True)
    rm = register_argument('rm', Register, read=True)
    rn = register_argument('rn', Register, read=True)
    syntax = ['add', rd, rm, rn]


class Cmp(TestInstruction):
    rm = register_argument('rm', Register, read=True)
    rn = register_argument('rn', Register, read=True)
    syntax = ['cmp', rm, rn]


class Use3(TestInstruction):
    rm = register_argument('rm', Register, read=True)
    rn = register_argument('rn', Register, read=True)
    ro = register_argument('ro', Register, read=True)
    syntax = ['use3', rm, rn, ro]


class Mov(TestInstruction):
    rd = register_argument('rd', Register, write=True)
    rm = register_argument('rm', Register, read=True)
    syntax = ['mov', rd, rm]
