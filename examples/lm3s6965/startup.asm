
section reset
dcd 0x2000f000
dcd 0x00000009
BL bsp_boot  ; Branch to bsp boot
BL bsp_exit  ; do exit stuff
local_loop:
B local_loop
