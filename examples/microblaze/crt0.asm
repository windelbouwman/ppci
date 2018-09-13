
section reset
bri _start


_start:

; Setup stack
; addik  r1, r0, _sdata
; mts    rslr, r1
; addik  r1, r0, _sdata + 0x8000
; mts    rshr, r1

; Copy .data from ROM to RAM:
; addik r5, r0, _sdata
; addik r6, r0, _etext
; addik r7, r0, _edata
brlid r15, bsp_memcpy
rsub r7, r5, r7  ; Note that this instruction is in the delay slot, so it is actually executed before the memcpy branch

