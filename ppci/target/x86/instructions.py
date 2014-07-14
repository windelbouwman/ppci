"""
    X86 target descriptions and encodings.
"""

from ..basetarget import Register, Instruction
from .registers import regs64, X86Register

from ..token import Token, u32, u8, bit_range


modrm = {'rax': 0, 'rbx': 1}

# Table 3.1 of the intel manual:
# use REX.W on the table below:


# Helper functions:
def imm64(x):
   """ represent 64 bits integer in little endian 8 bytes"""
   if x < 0:
      x = x + (1 << 64)
   x = x & 0xFFFFFFFFFFFFFFFF
   return [ (x >> (p*8)) & 0xFF for p in range(8) ]

def imm32(x):
   """ represent 32 bits integer in little endian 4 bytes"""
   if x < 0:
      x = x + (1 << 32)
   x = x & 0xFFFFFFFF
   return [ (x >> (p*8)) & 0xFF for p in range(4) ]


def imm8(x):
    if x < 0:
        x = x + (1 << 8)
    x = x & 0xFF
    return [ x ]


class ModRmToken(Token):
    """ Construct the modrm byte from its components """
    def __init__(self, mod=0, rm=0, reg=0):
        super().__init__(8)
        assert(mod <= 3)
        assert(rm <= 7)
        assert(reg <= 7)
        self.mod = mod
        self.rm = rm
        self.reg = reg

    mod = bit_range(6, 8)
    rm = bit_range(0, 3)
    reg = bit_range(3, 6)

    def encode(self):
        return u8(self.bit_value)


class RexToken(Token):
    """ Create a REX prefix byte """
    def __init__(self, w=0, r=0, x=0, b=0):
        super().__init__(8)
        assert(w <= 1)
        assert(r <= 1)
        assert(x <= 1)
        assert(b <= 1)
        self.w = w
        self.r = r
        self.x = x
        self.b = b
        self.set_bit(6, 1)

    w = bit_range(3, 4)
    r = bit_range(2, 3)
    x = bit_range(1, 2)
    b = bit_range(0, 1)

    def encode(self):
        return u8(self.bit_value)


def sib(ss=0, index=0, base=0):
   assert(ss <= 3)
   assert(index <= 7)
   assert(base <= 7)
   return (ss << 6) | (index << 3) | base

tttn = {'L':0xc,'G':0xf,'NE':0x5,'GE':0xd,'LE':0xe, 'E':0x4}

# Actual instructions:
def nearjump(distance, condition=None):
   """ jmp imm32 """
   lim = (1<<30)
   if abs(distance) > lim:
      Error('near jump cannot jump over more than {0} bytes'.format(lim))
   if condition:
      if distance < 0:
         distance -= 6 # Skip own instruction
      opcode = 0x80 | tttn[condition] # Jcc imm32
      return [0x0F, opcode] + imm32(distance)
   else:
      if distance < 0:
         distance -= 5 # Skip own instruction
      return [ 0xE9 ] + imm32(distance)

def shortjump(distance, condition=None):
   """ jmp imm8 """
   lim = 118
   if abs(distance) > lim:
      Error('short jump cannot jump over more than {0} bytes'.format(lim))
   if distance < 0:
      distance -= 2 # Skip own instruction
   if condition:
      opcode = 0x70 | tttn[condition] # Jcc rel8
   else:
      opcode = 0xeb # jmp rel8
   return [opcode] + imm8(distance)

# Helper that determines jump type:
def reljump(distance):
   if abs(distance) < 110:
      return shortjump(distance)
   else:
      return nearjump(distance)


class Push(Instruction):
    def __init__(self, reg):
        assert(reg in regs64), str(reg)
        self.reg = reg

    def encode(self):
        code = []
        if self.reg.rexbit == 1:
            code.append(0x41)
        code.append(0x50 + self.reg.regbits)
        return bytes(code)


class Pop(Instruction):
    def __init__(self, reg):
        assert(reg in regs64), str(reg)
        self.reg = reg

    def encode(self):
        code = []
        if self.reg.rexbit == 1:
            code.append(0x41)
        code.append(0x58 + self.reg.regbits)
        return bytes(code)


def pop(reg):
   if reg in regs64:
      if rexbit[reg] == 1:
         rexprefix = rex(b=1)
         opcode = 0x58 + regs64[reg]
         return [rexprefix, opcode]
      else:
         opcode = 0x58 + regs64[reg]
         return [ opcode ]
   else:
      Error('pop for {0} not implemented'.format(reg))

def INT(number):
   opcode = 0xcd
   return [opcode] + imm8(number)

def syscall():
   return [0x0F, 0x05]

def call(distance):
   if type(distance) is int:
      return [0xe8]+imm32(distance)
   elif type(distance) is str and distance in regs64:
      reg = distance
      opcode = 0xFF # 0xFF /2 == call r/m64
      mod_rm = modrm(mod=3, reg=2, rm=regs64[reg])
      if rexbit[reg] == 1:
         rexprefix = rex(b=rexbit[reg])
         return [rexprefix, opcode, mod_rm]
      else:
         return [opcode, mod_rm]
   else:
      Error('Cannot call to {0}'.format(distance))


class Ret(Instruction):
    def __init__(self):
        pass

    def encode(self):
        return [ 0xc3 ]


class Inc(Instruction):
    def __init__(self, reg):
        assert(reg in regs64), str(reg)
        self.rex = RexToken(w=1, b=reg.rexbit)
        self.opcode = 0xff
        self.mod_rm = ModRmToken(mod=3, rm=reg.regbits)

    def encode(self):
        code = bytes([self.opcode])
        return self.rex.encode() + code + self.mod_rm.encode()


def prepost8(r8, rm8):
   assert(r8 in regs8)
   pre = []
   if type(rm8) is list:
      # TODO: merge mem access with prepost for 64 bits
      if len(rm8) == 1:
         base, = rm8
         if type(base) is str and base in regs64:
            assert(not base in ['rbp', 'rsp', 'r12', 'r13'])
            mod_rm = modrm(mod=0, rm=regs64[base], reg=regs8[r8])
            if rexbit[base] == 1:
               pre.append(rex(b=1))
            post = [mod_rm]
         else:
            Error('One arg of type {0} not implemented'.format(base))
      elif len(rm8) == 2:
         base, offset = rm8
         assert(type(offset) is int)
         assert(base in regs64)

         if base == 'rsp' or base == 'r12':
            Error('Cannot use rsp or r12 as base yet')
         if rexbit[base] == 1:
            pre.append( rex(b=1) )
         mod_rm = modrm(mod=1, rm=regs64[base], reg=regs8[r8])
         post = [mod_rm] + imm8(offset)
      else:
         Error('not supporting prepost8 with list len {0}'.format(len(rm8)))
   else:
      Error('Not supporting move with reg8 {0}'.format(r8))
   return pre, post

def prepost(r64, rm64):
   assert(r64 in regs64)
   if type(rm64) is list:
      if len(rm64) == 3:
            base, index, disp = rm64
            assert(base in regs64)
            assert(index in regs64)
            assert(type(disp) is int)
            # Assert that no special cases are used:
            # TODO: swap base and index to avoid special cases
            # TODO: exploit special cases and make better code
            assert(index != 'rsp')

            rexprefix = rex(w=1, r=rexbit[r64], x=rexbit[index], b=rexbit[base])
            # mod=1 and rm=4 indicates a SIB byte: [--][--]+imm8
            mod_rm = modrm(mod=1, rm=4, reg=regs64[r64])
            si_b = sib(ss=0, index=regs64[index], base=regs64[base])
            return [rexprefix], [mod_rm, si_b] + imm8(disp)
      elif len(rm64) == 2:
         base, offset = rm64
         assert(type(offset) is int)
         if base == 'RIP':
            # RIP pointer relative addressing mode!
            rexprefix = rex(w=1, r=rexbit[r64])
            mod_rm = modrm(mod=0, rm=5, reg=regs64[r64])
            return [rexprefix], [mod_rm] + imm32(offset)
         else:
            assert(base in regs64)

            if base == 'rsp' or base == 'r12':
               # extended function that uses SIB byte
               rexprefix = rex(w=1, r=rexbit[r64], b=rexbit[base])
               # rm=4 indicates a SIB byte follows
               mod_rm = modrm(mod=1, rm=4, reg=regs64[r64])
               # index=4 indicates that index is not used
               si_b = sib(ss=0, index=4, base=regs64[base])
               return [rexprefix], [mod_rm, si_b] + imm8(offset)
            else:
               rexprefix = rex(w=1, r=rexbit[r64], b=rexbit[base])
               mod_rm = modrm(mod=1, rm=regs64[base], reg=regs64[r64])
               return [rexprefix], [mod_rm] + imm8(offset)
      elif len(rm64) == 1:
         offset = rm64[0]
         if type(offset) is int:
            rexprefix = rex(w=1, r=rexbit[r64])
            mod_rm = modrm(mod=0, rm=4,reg=regs64[r64])
            si_b = sib(ss=0, index=4,base=5) # 0x25
            return [rexprefix], [mod_rm, si_b] + imm32(offset)
         else:
            Error('Memory reference of type {0} not implemented'.format(offset))
      else:
         Error('Memory reference not implemented')
   elif rm64 in regs64:
      rexprefix = rex(w=1, r=rexbit[r64], b=rexbit[rm64])
      mod_rm = modrm(3, rm=regs64[rm64], reg=regs64[r64])
      return [rexprefix], [mod_rm]


def leareg64(rega, m):
   opcode = 0x8d # lea r64, m
   pre, post = prepost(rega, m)
   return pre + [opcode] + post


class Mov1(Instruction):
    """ Mov r64 to r64 """
    def __init__(self, dst, src):
        assert src in regs64, str(src)
        assert dst in regs64, str(dst)
        self.rex = RexToken(w=1, r=dst.rexbit, b=src.rexbit)
        self.mod_rm = ModRmToken(mod=3, rm=dst.regbits, reg=src.regbits)

    def encode(self):
        opcode = 0x89 # mov r/m64, r64
        code = bytes([opcode])
        return self.rex.encode() + code + self.mod_rm.encode()


def Mov(dst, src):
    if type(src) is int:
        pre = [rex(w=1, b=rexbit[rega])]
        opcode = 0xb8 + regs64[rega]
        post = imm64(regb)
    elif type(src) is X86Register:
        return Mov1(dst, src)
    elif type(src) is str:
      if rega in regs64:
         opcode = 0x8b # mov r64, r/m64
         pre, post = prepost(rega, regb)
      else:
         raise Exception('Unknown register {0}'.format(rega))
    else:
        raise Exception('Move of this kind {0}, {1} not implemented'.format(rega, regb))
    return pre + [opcode] + post


def Xor(rega, regb):
    return Xor1(rega, regb)


class Xor1(Instruction):
    def __init__(self, a, b):
        self.rex = RexToken(w=1, r=b.rexbit, b=a.rexbit)
        self.mod_rm = ModRmToken(mod=3, rm=a.regbits, reg=b.regbits)

    def encode(self):
        opcode = 0x31  # XOR r/m64, r64
        # Alternative is 0x33 XOR r64, r/m64
        code = bytes([opcode])
        return self.rex.encode() + code + self.mod_rm.encode()


# integer arithmatic:
def addreg64(rega, regb):
   if regb in regs64:
      pre, post = prepost(regb, rega)
      opcode = 0x01 # ADD r/m64, r64
      return pre + [opcode] + post
   elif type(regb) is int:
      if regb < 100:
         rexprefix = rex(w=1, b=rexbit[rega])
         opcode = 0x83 # add r/m, imm8
         mod_rm = modrm(3, rm=regs64[rega], reg=0)
         return [rexprefix, opcode, mod_rm]+imm8(regb)
      elif regb < (1<<31):
         rexprefix = rex(w=1, b=rexbit[rega])
         opcode = 0x81 # add r/m64, imm32
         mod_rm = modrm(3, rm=regs64[rega], reg=0)
         return [rexprefix, opcode, mod_rm]+imm32(regb)
      else:
         Error('Constant value too large!')
   else:
      Error('unknown second operand!'.format(regb))

def subreg64(rega, regb):
   if regb in regs64:
      pre, post = prepost(regb, rega)
      opcode = 0x29 # SUB r/m64, r64
      return pre + [opcode] + post
   elif type(regb) is int:
      if regb < 100:
         rexprefix = rex(w=1, b=rexbit[rega])
         opcode = 0x83 # sub r/m, imm8
         mod_rm = modrm(3, rm=regs64[rega], reg=5)
         return [rexprefix, opcode, mod_rm]+imm8(regb)
      elif regb < (1<<31):
         rexprefix = rex(w=1, b=rexbit[rega])
         opcode = 0x81 # sub r/m64, imm32
         mod_rm = modrm(3, rm=regs64[rega], reg=5)
         return [rexprefix, opcode, mod_rm]+imm32(regb)
      else:
         Error('Constant value too large!')

   else:
      Error('unknown second operand!'.format(regb))

def idivreg64(reg):
   rexprefix = rex(w=1, b=rexbit[reg])
   opcode = 0xf7 # IDIV r/m64
   mod_rm = modrm(3, rm=regs64[reg], reg=7)
   return [rexprefix, opcode, mod_rm]

def imulreg64_rax(reg):
   rexprefix = rex(w=1, b=rexbit[reg])
   opcode = 0xf7 # IMUL r/m64
   mod_rm = modrm(3, rm=regs64[reg], reg=5)
   return [rexprefix, opcode, mod_rm]

def imulreg64(rega, regb):
   pre, post = prepost(rega, regb)
   opcode = 0x0f # IMUL r64, r/m64
   opcode2 = 0xaf
   return pre + [opcode, opcode2] + post


def cmpreg64(rega, regb):
   if regb in regs64:
      pre, post = prepost(regb, rega)
      opcode = 0x39 # CMP r/m64, r64
      return pre + [opcode] + post
   elif type(regb) is int:
      rexprefix = rex(w=1, b=rexbit[rega])
      opcode = 0x83 # CMP r/m64, imm8
      mod_rm = modrm(3, rm=regs64[rega], reg=7)
      return [rexprefix, opcode, mod_rm] + imm8(regb)
   else:
      Error('not implemented cmp64')
