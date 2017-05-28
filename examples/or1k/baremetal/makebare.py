""" Bare metal example for open risc.

Run the result with qemu-system-or1k:

$ qemu-system-or1k -kernel baremetal.bin -M or1k-sim -serial stdio

"""

import io
from ppci import api
from ppci.utils.reporting import HtmlReportGenerator


boot_src = """
section reset
l.j start
l.nop 0

section code
start:

; Load address:
l.movhi r29, 0x9000
l.ori r29, r29, 0

; Load 'A' (0x41)
l.movhi r27, 0
l.ori r27, r27, 0x41

; Store char
l.sb 0(r29), r27

; Use 'function' to output character 'B':
l.jal outputb
l.nop 0
l.jal outputb
l.nop 0

; setup stack:
l.movhi r1, 0x1

; Enter c3 code:
l.jal main_main
l.nop 0

endless:
l.j endless
l.nop 0

outputb:
; Load 'B':
l.movhi r27, 0
l.ori r27, r27, 0x42

; Store char
l.sb 0(r29), r27

l.jr r9
l.nop 0
"""

src = """
module main;

function void putc(byte c)
{
  var byte* uart_dr = 0x90000000;
  *uart_dr = c;
}

public function void main()
{
  var byte* uart_dr = 0x90000000;
  *uart_dr = 0x46;
  putc(0x43);
  putc(0x44);
  putc(0x45);
}
"""

layout = """

MEMORY flash LOCATION=0x100 SIZE=0x800 {
 SECTION(reset)
 SECTION(code)
}

MEMORY ram LOCATION=0x001000 SIZE=0x800 {
 SECTION(data)
}
"""

obj1 = api.asm(io.StringIO(boot_src), 'or1k')
with open('report.html', 'w') as f:
    obj2 = api.c3c(
        [io.StringIO(src)], [], march='or1k', opt_level=2,
        reporter=HtmlReportGenerator(f))

print(obj1)
print(obj2)
obj = api.link([obj1, obj2], layout=io.StringIO(layout))
print(obj)
api.objcopy(obj, 'flash', 'bin', 'baremetal.bin')

