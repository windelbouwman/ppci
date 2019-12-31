
; DCD 0x20000678  ; Setup stack pointer
; DCD 0x06daa0e3 ; mov sp, #0x60 << 8
mov sp, 0x30000
global main_main
BL main_main          ; Branch to main (this is actually in the interrupt vector)
local_loop:
B local_loop
