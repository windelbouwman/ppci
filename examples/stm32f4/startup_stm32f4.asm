

DCD 0x20000678  ; Setup stack pointer
DCD 0x08000009  ; Reset vector, jump to address 8
bw snake_main          ; Branch to main (this is actually in the interrupt vector)
DCD 0x0  ; undefined 0xc
DCD 0x0  ; undefined 0x10
DCD 0x0  ; undefined 0x14
DCD 0x0  ; undefined 0x18
DCD 0x0  ; undefined 0x1c
DCD 0x0  ; undefined 0x20
DCD 0x0  ; undefined 0x24
DCD 0x0  ; undefined 0x28
DCD 0x0  ; undefined 0x2c
DCD 0x0  ; undefined 0x30
DCD 0x0  ; undefined 0x34
DCD 0x0  ; undefined 0x38
DCD 0x08000041  ; undefined 0x3c --> systick, hackz for now to branch to next address
bw snake_systick  ; undefined 0x40 jump instruction to systick handler

; Rest of handlers:
DCD 0x0  ; undefined
DCD 0x0  ; undefined
DCD 0x0  ; undefined
DCD 0x0  ; undefined
DCD 0x0  ; undefined
DCD 0x0  ; undefined
DCD 0x0  ; undefined
DCD 0x0  ; undefined
DCD 0x0  ; undefined
DCD 0x0  ; undefined
DCD 0x0  ; undefined
DCD 0x0  ; undefined

