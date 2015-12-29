
dd 0x20000678  ; Setup stack pointer
dd 0x00000009  ; Reset vector, jump to address 8
B hello_main          ; Branch to main (this is actually in the interrupt vector)

