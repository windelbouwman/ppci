"""
    This is an example target with some instructions. It is used in test-cases
    and serves as a minimal example.
"""

from .isa import Instruction, Syntax
from .arch import Architecture, Frame
from .isa import register_argument, Register
from ..import ir


class ExampleArch(Architecture):
    name = 'example'
    FrameClass = Frame

    def __init__(self, options=None):
        super().__init__(options=options)
        self.value_classes[ir.i32] = ExampleRegister
        self.value_classes[ir.ptr] = ExampleRegister
        self.byte_sizes['int'] = 4
        self.byte_sizes['ptr'] = 4

    def determine_arg_locations(self, arg_types, ret_type):
        """ Given a set of argument types, determine locations
        """
        arg_locs = []
        live_in = set()
        regs = [R0, R1, R2, R3]
        for a in arg_types:
            r = regs.pop(0)
            arg_locs.append(r)
            live_in.add(r)
        live_out = set()
        rv = R0
        live_out.add(rv)
        return arg_locs, tuple(live_in), rv, tuple(live_out)

    def get_register(self, n):
        regs = [R0, R1, R2, R3, R4, R5, R6]
        mp = {r.num: r for r in regs}
        return mp[n]


class ExampleRegister(Register):
    bitsize = 32

R0 = ExampleRegister('r0', 0)
R1 = ExampleRegister('r1', 1)
R2 = ExampleRegister('r2', 2)
R3 = ExampleRegister('r3', 3)
R4 = ExampleRegister('r4', 4)
R5 = ExampleRegister('r5', 5)
R6 = ExampleRegister('r6', 6)


class TestInstruction(Instruction):
    """ Base class for all example instructions """
    tokens = []


class Def(TestInstruction):
    rd = register_argument('rd', ExampleRegister, write=True)
    syntax = Syntax(['def', rd])


class Use(TestInstruction):
    rn = register_argument('rn', ExampleRegister, read=True)
    syntax = Syntax(['use', rn])


class DefUse(TestInstruction):
    rd = register_argument('rd', ExampleRegister, write=True)
    rn = register_argument('rn', ExampleRegister, read=True)
    syntax = Syntax(['cpy', rd, rn])


class Add(TestInstruction):
    rd = register_argument('rd', ExampleRegister, write=True)
    rm = register_argument('rm', ExampleRegister, read=True)
    rn = register_argument('rn', ExampleRegister, read=True)
    syntax = Syntax(['add', rd, rm, rn])


class Cmp(TestInstruction):
    rm = register_argument('rm', ExampleRegister, read=True)
    rn = register_argument('rn', ExampleRegister, read=True)
    syntax = Syntax(['cmp', rm, rn])


class Use3(TestInstruction):
    rm = register_argument('rm', ExampleRegister, read=True)
    rn = register_argument('rn', ExampleRegister, read=True)
    ro = register_argument('ro', ExampleRegister, read=True)
    syntax = Syntax(['use3', rm, rn, ro])


class Mov(TestInstruction):
    rd = register_argument('rd', ExampleRegister, write=True)
    rm = register_argument('rm', ExampleRegister, read=True)
    syntax = Syntax(['mov', rd, rm])
