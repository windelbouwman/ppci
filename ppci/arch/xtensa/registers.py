
from ..registers import Register, RegisterClass


class AddressRegister(Register):
    bitsize = 32


a0 = AddressRegister('a0', num=0)
a1 = AddressRegister('a1', num=1)
a2 = AddressRegister('a2', num=2)
a3 = AddressRegister('a3', num=3)
a4 = AddressRegister('a4', num=4)
a5 = AddressRegister('a5', num=5)
a6 = AddressRegister('a6', num=6)
a7 = AddressRegister('a7', num=7)

a8 = AddressRegister('a8', num=8)
a9 = AddressRegister('a9', num=9)
a10 = AddressRegister('a10', num=10)
a11 = AddressRegister('a11', num=11)
a12 = AddressRegister('a12', num=12)
a13 = AddressRegister('a13', num=13)
a14 = AddressRegister('a14', num=14)
a15 = AddressRegister('a15', num=15)
