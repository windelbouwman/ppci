"""
    Contains register definitions for x86 target.
"""
from ..basetarget import Register


class X86Register(Register):
    def __init__(self, num, name):
        super().__init__(name)
        self.num = num

    def __repr__(self):
        return 'x86reg {}'.format(self.name)

    @property
    def rexbit(self):
        return (self.num >> 3) & 0x1

    @property
    def regbits(self):
        return self.num & 0x7

# Calculation of the rexb bit:
# rexbit = {'rax': 0, 'rcx':0, 'rdx':0, 'rbx': 0, 'rsp': 0, 'rbp': 0, 'rsi':0,
# 'rdi':0,'r8':1,'r9':1,'r10':1,'r11':1,'r12':1,'r13':1,'r14':1,'r15':1}

# regs64 = {'rax': 0,'rcx':1,'rdx':2,'rbx':3,'rsp':4,'rbp':5,'rsi':6,'rdi':7,
# 'r8':0,'r9':1,'r10':2,'r11':3,'r12':4,'r13':5,'r14':6,'r15':7}
# regs32 = {'eax': 0, 'ecx':1, 'edx':2, 'ebx': 3, 'esp': 4, 'ebp': 5, 'esi':6,
# 'edi':7}
# regs8 = {'al':0,'cl':1,'dl':2,'bl':3,'ah':4,'ch':5,'dh':6,'bh':7}
rax = X86Register(0, 'rax')
rcx = X86Register(1, 'rcx')
rdx = X86Register(2, 'rdx')
rbx = X86Register(3, 'rbx')
rsp = X86Register(4, 'rsp')
rbp = X86Register(5, 'rbp')
rsi = X86Register(6, 'rsi')
rdi = X86Register(7, 'rdi')

r8 = X86Register(8, 'r8')
r9 = X86Register(9, 'r9')
r10 = X86Register(10, 'r10')
r11 = X86Register(11, 'r11')
r12 = X86Register(12, 'r12')
r13 = X86Register(13, 'r13')
r14 = X86Register(14, 'r14')
r15 = X86Register(15, 'r15')

low_regs = {rax, rcx, rdx, rbx, rsp, rbp, rsi, rdi}

regs64 = {r8, r9, r10, r11, r12, r13, r14, r15} | low_regs
