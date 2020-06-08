from ..registers import Register, RegisterClass
from ... import ir

# pylint: disable=invalid-name


class RiscvRegister(Register):
    bitsize = 32

    def __repr__(self):
        if self.is_colored:
            return get_register(self.color).name
            return "{}={}".format(self.name, self.color)
        else:
            return self.name


class RiscvProgramCounterRegister(Register):
    bitsize = 32


class RiscvFRegister(Register):
    bitsize = 32


class RiscvCsrRegister(Register):
    bitsize = 32


def get_register(n):
    """ Based on a number, get the corresponding register """
    return num2regmap[n]


def register_range(a, b):
    """ Return set of registers from a to b """
    assert a.num < b.num
    return {get_register(n) for n in range(a.num, b.num + 1)}


R0 = RiscvRegister("x0", num=0, aka=("zero",))
LR = RiscvRegister("x1", num=1, aka=("ra",))
SP = RiscvRegister("x2", num=2, aka=("sp",))
R3 = RiscvRegister("x3", num=3, aka=("gp",))
R4 = RiscvRegister("x4", num=4, aka=("tp",))
R5 = RiscvRegister("x5", num=5, aka=("t0",))
R6 = RiscvRegister("x6", num=6, aka=("t1",))
R7 = RiscvRegister("x7", num=7, aka=("t2",))
FP = RiscvRegister("x8", num=8, aka=("s0", "fp"))
R9 = RiscvRegister("x9", num=9, aka=("s1",))
R10 = RiscvRegister("x10", num=10, aka=("a0",))
R11 = RiscvRegister("x11", num=11, aka=("a1",))
R12 = RiscvRegister("x12", num=12, aka=("a2",))
R13 = RiscvRegister("x13", num=13, aka=("a3",))
R14 = RiscvRegister("x14", num=14, aka=("a4",))
R15 = RiscvRegister("x15", num=15, aka=("a5",))
R16 = RiscvRegister("x16", num=16, aka=("a6",))
R17 = RiscvRegister("x17", num=17, aka=("a7",))
R18 = RiscvRegister("x18", num=18, aka=("s2",))
R19 = RiscvRegister("x19", num=19, aka=("s3",))
R20 = RiscvRegister("x20", num=20, aka=("s4",))
R21 = RiscvRegister("x21", num=21, aka=("s5",))
R22 = RiscvRegister("x22", num=22, aka=("s6",))
R23 = RiscvRegister("x23", num=23, aka=("s7",))
R24 = RiscvRegister("x24", num=24, aka=("s8",))
R25 = RiscvRegister("x25", num=25, aka=("s9",))
R26 = RiscvRegister("x26", num=26, aka=("s10",))
R27 = RiscvRegister("x27", num=27, aka=("s11",))
R28 = RiscvRegister("x28", num=28, aka=("t3",))
R29 = RiscvRegister("x29", num=29, aka=("t4",))
R30 = RiscvRegister("x30", num=30, aka=("t5",))
R31 = RiscvRegister("x31", num=31, aka=("t6",))

PC = RiscvProgramCounterRegister("PC", num=32)

F0 = RiscvFRegister("f0", num=0)
F1 = RiscvFRegister("f1", num=1)
F2 = RiscvFRegister("f2", num=2)
F3 = RiscvFRegister("f3", num=3)
F4 = RiscvFRegister("f4", num=4)
F5 = RiscvFRegister("f5", num=5)
F6 = RiscvFRegister("f6", num=6)
F7 = RiscvFRegister("f7", num=7)
F8 = RiscvFRegister("f8", num=8)
F9 = RiscvFRegister("f9", num=9)
F10 = RiscvFRegister("f10", num=10)
F11 = RiscvFRegister("f11", num=11)
F12 = RiscvFRegister("f12", num=12)
F13 = RiscvFRegister("f13", num=13)
F14 = RiscvFRegister("f14", num=14)
F15 = RiscvFRegister("f15", num=15)
F16 = RiscvFRegister("f16", num=16)
F17 = RiscvFRegister("f17", num=17)
F18 = RiscvFRegister("f18", num=18)
F19 = RiscvFRegister("f19", num=19)
F20 = RiscvFRegister("f20", num=20)
F21 = RiscvFRegister("f21", num=21)
F22 = RiscvFRegister("f22", num=22)
F23 = RiscvFRegister("f23", num=23)
F24 = RiscvFRegister("f24", num=24)
F25 = RiscvFRegister("f25", num=25)
F26 = RiscvFRegister("f26", num=26)
F27 = RiscvFRegister("f27", num=27)
F28 = RiscvFRegister("f28", num=28)
F29 = RiscvFRegister("f29", num=29)
F30 = RiscvFRegister("f30", num=30)
F31 = RiscvFRegister("f31", num=31)

MSTATUS = RiscvCsrRegister("mstatus", num=0x300)
MIE = RiscvCsrRegister("mie", num=0x304)
MTVEC = RiscvCsrRegister("mtvec", num=0x305)
MEPC = RiscvCsrRegister("mepc", num=0x341)
MCAUSE = RiscvCsrRegister("mcause", num=0x342)
MHARTID = RiscvCsrRegister("mhartid", num=0xF14)
FRM = RiscvCsrRegister("frm", num=0x2)

registers = [
    R0,
    LR,
    SP,
    R3,
    R4,
    R5,
    R6,
    R7,
    FP,
    R9,
    R10,
    R11,
    R12,
    R13,
    R14,
    R15,
    R16,
    R17,
    R18,
    R19,
    R20,
    R21,
    R22,
    R23,
    R24,
    R25,
    R26,
    R27,
    R28,
    R29,
    R30,
    R31,
]
RiscvRegister.registers = registers

fregisters = [
    F0,
    F1,
    F2,
    F3,
    F4,
    F5,
    F6,
    F7,
    F8,
    F9,
    F10,
    F11,
    F12,
    F13,
    F14,
    F15,
    F16,
    F17,
    F18,
    F19,
    F20,
    F21,
    F22,
    F23,
    F24,
    F25,
    F26,
    F27,
    F28,
    F29,
    F30,
    F31,
]

RiscvFRegister.registers = fregisters
num2regmap = {r.num: r for r in registers}

gdb_registers = registers + [PC]
RiscvCsrRegister.registers = [MSTATUS, MIE, MTVEC, MEPC, MCAUSE, MHARTID, FRM]

register_classes_hwfp = [
    RegisterClass(
        "reg",
        [ir.i8, ir.i16, ir.i32, ir.ptr, ir.u8, ir.u16, ir.u32],
        RiscvRegister,
        [
            R9,
            R10,
            R11,
            R12,
            R13,
            R14,
            R15,
            R16,
            R17,
            R18,
            R19,
            R20,
            R21,
            R22,
            R23,
            R24,
            R25,
            R26,
            R27,
        ],
    ),
    RegisterClass("freg", [ir.f32, ir.f64], RiscvFRegister, fregisters),
]

register_classes_swfp = [
    RegisterClass(
        "reg",
        [ir.i8, ir.i16, ir.i32, ir.ptr, ir.u8, ir.u16, ir.u32, ir.f32, ir.f64],
        RiscvRegister,
        [
            R9,
            R10,
            R11,
            R12,
            R13,
            R14,
            R15,
            R16,
            R17,
            R18,
            R19,
            R20,
            R21,
            R22,
            R23,
            R24,
            R25,
            R26,
            R27,
        ],
    )
]
