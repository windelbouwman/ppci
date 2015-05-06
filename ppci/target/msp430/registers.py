
from .. import Register


class Msp430Register(Register):
    def __init__(self, num, name):
        super().__init__(name)
        self._num = num

# 8 bit registers:
PCB = Msp430Register(0, 'r0')
rpc = PCB
r0 = PCB
r1 = Msp430Register(1, 'r1')
SP = r1  # Stack pointer
r2 = Msp430Register(2, 'r2')
SR = r2  # Status register
r3 = Msp430Register(3, 'r3')
CG = r3  # Constant generator
r4 = Msp430Register(4, 'r4')
r5 = Msp430Register(5, 'r5')
r6 = Msp430Register(6, 'r6')
r7 = Msp430Register(7, 'r7')
r8 = Msp430Register(8, 'r8')
r9 = Msp430Register(9, 'r9')
r10 = Msp430Register(10, 'r10')
r11 = Msp430Register(11, 'r11')
r12 = Msp430Register(12, 'r12')
r13 = Msp430Register(13, 'r13')
r14 = Msp430Register(14, 'r14')
r15 = Msp430Register(15, 'r15')
