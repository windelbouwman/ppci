
global burn2_main
global burn2_systick

dd 0x20000678  ; Setup stack pointer
dd 0x08000009  ; Reset vector, jump to address 8
B burn2_main          ; Branch to main (this is actually in the interrupt vector)
align 4
dd 0x0  ; undefined 0xc
dd 0x0  ; undefined 0x10
dd 0x0  ; undefined 0x14
dd 0x0  ; undefined 0x18
dd 0x0  ; undefined 0x1c
dd 0x0  ; undefined 0x20
dd 0x0  ; undefined 0x24
dd 0x0  ; undefined 0x28
dd 0x0  ; undefined 0x2c
dd 0x0  ; undefined 0x30
dd 0x0  ; undefined 0x34
dd 0x0  ; undefined 0x38
dd 0x08000041  ; undefined 0x3c --> systick, hackz for now to branch to next address
B burn2_systick  ; undefined 0x40 jump instruction to systick handler
align 4

; Rest of handlers:
dd 0x0  ; undefined
dd 0x0  ; undefined
dd 0x0  ; undefined
dd 0x0  ; undefined
dd 0x0  ; undefined
dd 0x0  ; undefined
dd 0x0  ; undefined
dd 0x0  ; undefined
dd 0x0  ; undefined
dd 0x0  ; undefined
dd 0x0  ; undefined
dd 0x0  ; undefined

