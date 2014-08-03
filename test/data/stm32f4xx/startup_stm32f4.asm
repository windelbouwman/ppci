

DCD 0x20000678  ; Setup stack pointer
DCD 0x08000009  ; Reset vector, jump to address 8
B burn2_main          ; Branch to main (this is actually in the interrupt vector)

