
from ..basetarget import Register

class Msp430Register(Register):
    def __init__(self, num, name):
        super().__init__(name)
        self.num = num

# 8 bit registers:
PCB = Msp430Register(0, 'r0')
rpc = PCB
r10 = Msp430Register(10, 'r10')
r11 = Msp430Register(11, 'r11')
r12 = Msp430Register(12, 'r12')
r13 = Msp430Register(13, 'r13')
r14 = Msp430Register(14, 'r14')
r15 = Msp430Register(15, 'r15')

