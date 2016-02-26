"""
    Contains register definitions for x86 target.
"""
from ..isa import Register, Syntax


def get_register(n):
    """ Based on a number, get the corresponding register """
    return num2regmap[n]


class X86Register(Register):
    bitsize = 64

    def __repr__(self):
        if self.is_colored:
            return get_register(self.color).name
        else:
            return self.name

    @property
    def rexbit(self):
        return (self.num >> 3) & 0x1

    @property
    def regbits(self):
        return self.num & 0x7

    syntaxi = 'reg', [
        Syntax(['rax'], new_func=lambda: rax),
        Syntax(['rcx'], new_func=lambda: rcx),
        Syntax(['rdx'], new_func=lambda: rdx),
        Syntax(['rbx'], new_func=lambda: rbx),
        Syntax(['rsp'], new_func=lambda: rsp),
        Syntax(['rbp'], new_func=lambda: rbp),
        Syntax(['rsi'], new_func=lambda: rsi),
        Syntax(['rdi'], new_func=lambda: rdi),

        Syntax(['r8'], new_func=lambda: r8),
        Syntax(['r9'], new_func=lambda: r9),
        Syntax(['r10'], new_func=lambda: r10),
        Syntax(['r11'], new_func=lambda: r11),
        Syntax(['r12'], new_func=lambda: r12),
        Syntax(['r13'], new_func=lambda: r13),
        Syntax(['r14'], new_func=lambda: r14),
        Syntax(['r15'], new_func=lambda: r15),
        ]


class LowRegister(Register):
    bitsize = 64

    @property
    def rexbit(self):
        return (self.num >> 3) & 0x1

    @property
    def regbits(self):
        return self.num & 0x7

    syntaxi = 'reg8', [
        Syntax(['al'], new_func=lambda: al),
        Syntax(['cl'], new_func=lambda: cl),
        Syntax(['dl'], new_func=lambda: dl),
        Syntax(['bl'], new_func=lambda: bl)
        ]

# Calculation of the rexb bit:
# rexbit = {'rax': 0, 'rcx':0, 'rdx':0, 'rbx': 0, 'rsp': 0, 'rbp': 0, 'rsi':0,
# 'rdi':0,'r8':1,'r9':1,'r10':1,'r11':1,'r12':1,'r13':1,'r14':1,'r15':1}

al = LowRegister('al', 0)
cl = LowRegister('cl', 1)
dl = LowRegister('dl', 2)
bl = LowRegister('bl', 3)

# regs64 = {'rax': 0,'rcx':1,'rdx':2,'rbx':3,'rsp':4,'rbp':5,'rsi':6,'rdi':7,
# 'r8':0,'r9':1,'r10':2,'r11':3,'r12':4,'r13':5,'r14':6,'r15':7}
# regs32 = {'eax': 0, 'ecx':1, 'edx':2, 'ebx': 3, 'esp': 4, 'ebp': 5, 'esi':6,
# 'edi':7}
# regs8 = {'al':0,'cl':1,'dl':2,'bl':3,'ah':4,'ch':5,'dh':6,'bh':7}
rax = X86Register('rax', 0)
rcx = X86Register('rcx', 1)
rdx = X86Register('rdx', 2)
rbx = X86Register('rbx', 3)
rsp = X86Register('rsp', 4)
rbp = X86Register('rbp', 5)
rsi = X86Register('rsi', 6)
rdi = X86Register('rdi', 7)

r8 = X86Register('r8', 8)
r9 = X86Register('r9', 9)
r10 = X86Register('r10', 10)
r11 = X86Register('r11', 11)
r12 = X86Register('r12', 12)
r13 = X86Register('r13', 13)
r14 = X86Register('r14', 14)
r15 = X86Register('r15', 15)
rip = X86Register('rip', 999)

low_regs = {rax, rcx, rdx, rbx, rsp, rbp, rsi, rdi}

high_regs = {r8, r9, r10, r11, r12, r13, r14, r15}
full_registers = high_regs | low_regs

all_registers = list(sorted(full_registers, key=lambda r: r.num)) + [rip]

num2regmap = {r.num: r for r in full_registers}
