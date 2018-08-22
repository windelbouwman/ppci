""" Contains register definitions for x86 target. """

from ..registers import Register, RegisterClass
from ... import ir


def get_register(n):
    """ Based on a number, get the corresponding register """
    return num2regmap[n]


class Register64(Register):
    """ 64-bit register like 'rax' """
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


class Register32(Register):
    """ 32-bit register like 'eax' """
    bitsize = 32

    def __repr__(self):
        if self.is_colored:
            return get32reg(self.color).name
        else:
            return self.name

    @property
    def rexbit(self):
        return (self.num >> 3) & 0x1

    @property
    def regbits(self):
        return self.num & 0x7


class Register16(Register):
    """ 16-bit register like 'ax' """
    bitsize = 16

    def __repr__(self):
        if self.is_colored:
            return get16reg(self.color).name
        else:
            return self.name


class Register8(Register):
    """ 8-bit register like 'al' """
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

    def __repr__(self):
        if self.is_colored:
            return get_xmm_reg(self.color).name
        else:
            return self.name


class XmmRegisterSingle(Register):
    bitsize = 32

    def __repr__(self):
        if self.is_colored:
            return get_xmm_reg(self.color).name
        else:
            return self.name


# Calculation of the rexb bit:
# rexbit = {'rax': 0, 'rcx':0, 'rdx':0, 'rbx': 0, 'rsp': 0, 'rbp': 0, 'rsi':0,
# 'rdi':0,'r8':1,'r9':1,'r10':1,'r11':1,'r12':1,'r13':1,'r14':1,'r15':1}

al = Register8('al', 0)
cl = Register8('cl', 1)
dl = Register8('dl', 2)
bl = Register8('bl', 3)
ah = Register8('ah', 4)
ch = Register8('ch', 5)
dh = Register8('dh', 6)
bh = Register8('bh', 7)

Register8.registers = [al, bl, cl, dl, ah, ch, dh, bh]

ax = Register16('ax', 0, aliases=(al, ah))
cx = Register16('cx', 1, aliases=(cl, ch))
dx = Register16('dx', 2, aliases=(dl, dh))
bx = Register16('bx', 3, aliases=(bl, bh))
si = Register16('si', 6)
di = Register16('di', 7)
Register16.registers = (ax, bx, cx, dx, si, di)

eax = Register32('eax', 0, aliases=(ax,))
ecx = Register32('ecx', 1, aliases=(cx,))
edx = Register32('edx', 2, aliases=(dx,))
ebx = Register32('ebx', 3, aliases=(bx,))
esi = Register32('esi', 6, aliases=(si,))
edi = Register32('edi', 7, aliases=(di,))
r8d = Register32('r8d', 8)
r9d = Register32('r9d', 9)
r10d = Register32('r10d', 10)
r11d = Register32('r11d', 11)
r12d = Register32('r12d', 12)
r13d = Register32('r13d', 13)
r14d = Register32('r14d', 14)
r15d = Register32('r15d', 15)
Register32.registers = [
    eax, ecx, edx, ebx, esi, edi,
    r8d, r9d, r10d, r11d, r12d, r13d, r14d, r15d]

# regs64 = {'rax': 0,'rcx':1,'rdx':2,'rbx':3,'rsp':4,'rbp':5,'rsi':6,'rdi':7,
# 'r8':0,'r9':1,'r10':2,'r11':3,'r12':4,'r13':5,'r14':6,'r15':7}
# regs32 = {'eax': 0, 'ecx':1, 'edx':2, 'ebx': 3, 'esp': 4, 'ebp': 5, 'esi':6,
# 'edi':7}
# regs8 = {'al':0,'cl':1,'dl':2,'bl':3,'ah':4,'ch':5,'dh':6,'bh':7}
rax = Register64('rax', 0, aliases=(eax,))
rcx = Register64('rcx', 1, aliases=(ecx,))
rdx = Register64('rdx', 2, aliases=(edx,))
rbx = Register64('rbx', 3, aliases=(ebx,))
rsp = Register64('rsp', 4)
rbp = Register64('rbp', 5)
rsi = Register64('rsi', 6, aliases=(esi,))
rdi = Register64('rdi', 7, aliases=(edi,))

r8 = Register64('r8', 8, aliases=(r8d,))
r9 = Register64('r9', 9, aliases=(r9d,))
r10 = Register64('r10', 10, aliases=(r10d,))
r11 = Register64('r11', 11, aliases=(r11d,))
r12 = Register64('r12', 12, aliases=(r12d,))
r13 = Register64('r13', 13, aliases=(r13d,))
r14 = Register64('r14', 14, aliases=(r14d,))
r15 = Register64('r15', 15, aliases=(r15d,))
rip = Register64('rip', 999)

low_regs = {rax, rcx, rdx, rbx, rsp, rbp, rsi, rdi}

high_regs = {r8, r9, r10, r11, r12, r13, r14, r15}
full_registers = high_regs | low_regs

registers64 = [
    rax, rbx, rdx, rcx, rdi, rsi, rsp, rbp,
    r8, r9, r10, r11, r12, r13, r14, r15]
Register64.registers = registers64

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
    xmm0,
    xmm1,
    xmm2,
    xmm3,
    xmm4,
    xmm5,
    xmm6,
    xmm7,
    xmm8,
    xmm9,
    xmm10,
    xmm11,
    xmm12,
    xmm13,
    xmm14,
    xmm15
]

XmmRegisterDouble = XmmRegister

# Single precision scalar registers:
xmm0_single = XmmRegisterSingle('xmm0', 0, aliases=(xmm0,))
xmm1_single = XmmRegisterSingle('xmm1', 1, aliases=(xmm1,))
xmm2_single = XmmRegisterSingle('xmm2', 2, aliases=(xmm2,))
xmm3_single = XmmRegisterSingle('xmm3', 3, aliases=(xmm3,))
xmm4_single = XmmRegisterSingle('xmm4', 4, aliases=(xmm4,))
xmm5_single = XmmRegisterSingle('xmm5', 5, aliases=(xmm5,))
xmm6_single = XmmRegisterSingle('xmm6', 6, aliases=(xmm6,))
xmm7_single = XmmRegisterSingle('xmm7', 7, aliases=(xmm7,))

xmm8_single = XmmRegisterSingle('xmm8', 8, aliases=(xmm8,))
xmm9_single = XmmRegisterSingle('xmm9', 9, aliases=(xmm9,))
xmm10_single = XmmRegisterSingle('xmm10', 10, aliases=(xmm10,))
xmm11_single = XmmRegisterSingle('xmm11', 11, aliases=(xmm11,))
xmm12_single = XmmRegisterSingle('xmm12', 12, aliases=(xmm12,))
xmm13_single = XmmRegisterSingle('xmm13', 13, aliases=(xmm13,))
xmm14_single = XmmRegisterSingle('xmm14', 14, aliases=(xmm14,))
xmm15_single = XmmRegisterSingle('xmm15', 15, aliases=(xmm15,))

XmmRegisterSingle.registers = [
    xmm0_single,
    xmm1_single,
    xmm2_single,
    xmm3_single,
    xmm4_single,
    xmm5_single,
    xmm6_single,
    xmm7_single,
    xmm8_single,
    xmm9_single,
    xmm10_single,
    xmm11_single,
    xmm12_single,
    xmm13_single,
    xmm14_single,
    xmm15_single,
]


xmm_mp = {r.num: r for r in XmmRegister.registers}
def get_xmm_reg(num):
    return xmm_mp[num]


reg8_mp = {r.num: r for r in [al, bl, cl, dl]}
def get8reg(num):
    return reg8_mp[num]


reg16_mp = {r.num: r for r in Register16.registers}
def get16reg(num):
    return reg16_mp[num]


reg32_mp = {r.num: r for r in Register32.registers}
def get32reg(num):
    return reg32_mp[num]


callee_save = (
    rbx, r12, r13, r14, r15,
    xmm6, xmm7,
    xmm8, xmm9, xmm10, xmm11, xmm12, xmm13, xmm14, xmm15)
caller_save = (
    rax, rcx, rdx, rdi, rsi, r8, r9, r10, r11,
    xmm0, xmm1, xmm2, xmm3, xmm4, xmm5)


# Register classes:
# TODO: should 16 and 32 bit values have its own class?
register_classes = [
    RegisterClass(
        'reg64',
        [ir.i64, ir.u64, ir.ptr],
        Register64,
        [rax, rbx, rdx, rcx, rdi, rsi, r8, r9, r10, r11, r14, r15]),
    RegisterClass(
        'reg32', [ir.i32, ir.u32], Register32,
        [eax, ebx, ecx, edx, esi, edi, r8d, r9d, r10d, r11d, r14d, r15d]),
    RegisterClass(
        'reg16', [ir.i16, ir.u16], Register16, [ax, bx, cx, dx, si, di]),
    RegisterClass(
        'reg8', [ir.i8, ir.u8], Register8, [al, bl, cl, dl]),
    RegisterClass(
        'regfp32', [ir.f32], XmmRegisterSingle,
        XmmRegisterSingle.registers),
    RegisterClass(
        'regfp64', [ir.f64], XmmRegisterDouble,
        XmmRegisterDouble.registers),
    ]
