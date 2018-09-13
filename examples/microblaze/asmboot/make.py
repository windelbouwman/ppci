
import io
from ppci.api import asm, get_arch, objcopy, link
from ppci.binutils.layout import get_layout
from ppci.arch.microblaze import instructions, registers

arch = get_arch('microblaze')

# See also:
# https://github.com/edgarigl/tbm/blob/master/arch-microblaze/head.S

# According to qemu, we have an xilinx xps uart-lite device.
# This device has the following registers:
# BASE_ADDR + 0x0 : Rx fifo
# BASE_ADDR + 0x4 : Tx fifo
# The uart base addr is: 0x8400_0000
src = """
section code
reset_vector:
; bri _bare_start


_bare_start:

; Setup stack:

; Print 'A' to console:
addik r5, r0, 0x41

; imm prefix to load 0x8400 0004 into r6:
imm 0x8400
addik r6, r0, 4

; Write word (mem[r6+r0] = r5
sw r5, r6, r0

bri -4  ; Endless loop!

section data
"""

layout = get_layout('../layout.mmp')
obj = asm(io.StringIO(src), arch)
obj = link([obj], layout=layout)
print(obj)

objcopy(obj, 'flash', 'bin', 'baremetal.bin')

addik = instructions.Addik(registers.R5, registers.R0, 0x41)
print(addik.encode().hex())

add = instructions.Add(registers.R2, registers.R5, registers.R7)
print(add.encode().hex())

ts = add.get_tokens()
print(ts, ts[0].bit_value)
add.set_all_patterns(ts)
print(ts, hex(ts[0].bit_value))


