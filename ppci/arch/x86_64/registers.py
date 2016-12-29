""" Contains register definitions for x86 target. """

from ..registers import Register, RegisterClass
from ... import ir


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


class LowRegister(Register):
    bitsize = 8

    def __repr__(self):
        if self.is_colored:
            return get8reg(self.color).name
        else:
            return self.name

    @property
    def rexbit(self):
        return (self.num >> 3) & 0x1

    @property
    def regbits(self):
        return self.num & 0x7


class X87StackRegister(Register):
    bitsize = 64


class XmmRegister(Register):
    bitsize = 128
    # TODO: actually the register is 128 bit wide, but float is now 32 bit
    # bitsize = 32


# Calculation of the rexb bit:
# rexbit = {'rax': 0, 'rcx':0, 'rdx':0, 'rbx': 0, 'rsp': 0, 'rbp': 0, 'rsi':0,
# 'rdi':0,'r8':1,'r9':1,'r10':1,'r11':1,'r12':1,'r13':1,'r14':1,'r15':1}

al = LowRegister('al', 0)
cl = LowRegister('cl', 1)
dl = LowRegister('dl', 2)
bl = LowRegister('bl', 3)

LowRegister.registers = [al, bl, cl, dl]

# regs64 = {'rax': 0,'rcx':1,'rdx':2,'rbx':3,'rsp':4,'rbp':5,'rsi':6,'rdi':7,
# 'r8':0,'r9':1,'r10':2,'r11':3,'r12':4,'r13':5,'r14':6,'r15':7}
# regs32 = {'eax': 0, 'ecx':1, 'edx':2, 'ebx': 3, 'esp': 4, 'ebp': 5, 'esi':6,
# 'edi':7}
# regs8 = {'al':0,'cl':1,'dl':2,'bl':3,'ah':4,'ch':5,'dh':6,'bh':7}
rax = X86Register('rax', 0, aliases=(al,))
rcx = X86Register('rcx', 1, aliases=(cl,))
rdx = X86Register('rdx', 2, aliases=(dl,))
rbx = X86Register('rbx', 3, aliases=(bl,))
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

registers64 = [
    rax, rbx, rdx, rcx, rdi, rsi, rsp, rbp,
    r8, r9, r10, r11, r12, r13, r14, r15]
X86Register.registers = registers64

all_registers = list(sorted(full_registers, key=lambda r: r.num)) + [rip]

num2regmap = {r.num: r for r in full_registers}


st0 = X87StackRegister('st0', 0)
st1 = X87StackRegister('st1', 1)
st2 = X87StackRegister('st2', 2)
st3 = X87StackRegister('st3', 3)
st4 = X87StackRegister('st4', 4)
st5 = X87StackRegister('st5', 5)
st6 = X87StackRegister('st6', 6)
st7 = X87StackRegister('st7', 7)


xmm0 = XmmRegister('xmm0', 0)
xmm1 = XmmRegister('xmm1', 1)
xmm2 = XmmRegister('xmm2', 2)
xmm3 = XmmRegister('xmm3', 3)
xmm4 = XmmRegister('xmm4', 4)
xmm5 = XmmRegister('xmm5', 5)
xmm6 = XmmRegister('xmm6', 6)
xmm7 = XmmRegister('xmm7', 7)

xmm8 = XmmRegister('xmm8', 8)
xmm9 = XmmRegister('xmm9', 9)
xmm10 = XmmRegister('xmm10', 10)
xmm11 = XmmRegister('xmm11', 11)
xmm12 = XmmRegister('xmm12', 12)
xmm13 = XmmRegister('xmm13', 13)
xmm14 = XmmRegister('xmm14', 14)
xmm15 = XmmRegister('xmm15', 15)

XmmRegister.registers = [
    xmm0, xmm1, xmm2, xmm3, xmm4, xmm5, xmm6, xmm7,
    xmm8, xmm9, xmm10, xmm11, xmm12, xmm13, xmm14, xmm15]


def get8reg(num):
    mp = {r.num: r for r in [al, bl, cl, dl]}
    return mp[num]


# Register classes:
register_classes = [
    RegisterClass(
        'reg64', [ir.i64, ir.u64, ir.ptr], X86Register,
        [rax, rbx, rdx, rcx, rdi, rsi, r8, r9, r10, r11, r14, r15]),
    RegisterClass('reg8', [ir.i8, ir.u8], LowRegister, [al, bl, cl, dl]),
    RegisterClass(
        'regfp', [ir.f32, ir.f64], XmmRegister,
        XmmRegister.registers),
    ]
