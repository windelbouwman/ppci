"""
    This is an example target with some instructions. It is used in test-cases
    and serves as a minimal example.
"""

from .isa import Instruction, Syntax
from .arch import Architecture, Frame
from .isa import register_argument, Register, RegisterClass
from ..import ir


class ExampleArch(Architecture):
    """ Simple example architecture. This is intended as starting point
    when creating a new backend """
    name = 'example'
    FrameClass = Frame

    def __init__(self, options=None):
        super().__init__(options=options)
        self.byte_sizes['int'] = 4
        self.byte_sizes['ptr'] = 4
        self.register_classes = [
            RegisterClass(
                'reg', [ir.i32, ir.ptr], ExampleRegister, [R0, R1, R2, R3])
            ]
        self.gdb_registers = gdb_registers

    def determine_arg_locations(self, arg_types):
        """ Given a set of argument types, determine locations
        """
        arg_locs = []
        live_in = set()
        regs = [R0, R1, R2, R3]
        for a in arg_types:
            r = regs.pop(0)
            arg_locs.append(r)
            live_in.add(r)
        return arg_locs, tuple(live_in)

    def determine_rv_location(self, ret_type):
        live_out = set()
        rv = R0
        live_out.add(rv)
        return rv, tuple(live_out)


class ExampleRegister(Register):
    """ Example register class """
    bitsize = 32


R0 = ExampleRegister('r0', 0)
R1 = ExampleRegister('r1', 1)
R2 = ExampleRegister('r2', 2)
R3 = ExampleRegister('r3', 3)
R4 = ExampleRegister('r4', 4)
R5 = ExampleRegister('r5', 5)
R6 = ExampleRegister('r6', 6)

gdb_registers = (R0, R1, R2)

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
