""" Description of registers """

from ..registers import Register, RegisterClass
from ... import ir


class M68kRegister(Register):
    """ An 68000 register """

    bitsize = 32


class DataRegister(M68kRegister):
    """ Data register """

    @classmethod
    def from_num(cls, num):
        return num_data_reg_map[num]


class AddressRegister(M68kRegister):
    """ Address register """

    @classmethod
    def from_num(cls, num):
        return num_address_reg_map[num]


D0 = DataRegister("D0", num=0)
D1 = DataRegister("D1", num=1)
D2 = DataRegister("D2", num=2)
D3 = DataRegister("D3", num=3)
D4 = DataRegister("D4", num=4)
D5 = DataRegister("D5", num=5)
D6 = DataRegister("D6", num=6)
D7 = DataRegister("D7", num=7)

data_registers = [D0, D1, D2, D3, D4, D5, D6, D7]
num_data_reg_map = {r.num: r for r in data_registers}
DataRegister.registers = data_registers

A0 = AddressRegister("A0", num=0)
A1 = AddressRegister("A1", num=1)
A2 = AddressRegister("A2", num=2)
A3 = AddressRegister("A3", num=3)
A4 = AddressRegister("A4", num=4)
A5 = AddressRegister("A5", num=5)
A6 = AddressRegister("A6", num=6)

address_registers = [A0, A1, A2, A3, A4, A5, A6]
num_address_reg_map = {r.num: r for r in address_registers}
AddressRegister.registers = address_registers

register_classes = [
    RegisterClass(
        "regd",
        [ir.i8, ir.u8, ir.i16, ir.u16, ir.i32, ir.u32, ir.ptr],
        DataRegister,
        data_registers,
    ),
    RegisterClass("rega", [], AddressRegister, address_registers),
]
