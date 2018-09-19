
section reset
; Reset vector:
; 0x0 = reset
bri _start

; 0x08 - break
; 0x10 - IRQ
; 0x18 - IRQ
; 0x20 - HW exceptions


_start:

; Setup stack
addik  r1, r0, __data_start
; mts    rslr, r1
; addik  r1, r0, _sdata + 0x8000
; mts    rshr, r1

;; Output 'A':
imm 0x8400
addik r6, r0, 4
addik r5, r0, 0x41
sw r5, r6, r0

; Output 'E':
addik r5, r0, 0x45
brlid r15, bsp_putc
or r0,r0,r0  ; fill delay slot

; Output 'Z':
brlid r15, emitZ
or r0,r0,r0  ; fill delay slot

; Copy .data from ROM to RAM:
addik r5, r0, __data_start
addik r6, r0, __data_load_start
addik r7, r0, __data_end
brlid r15, bsp_memcpy
rsub r7, r5, r7  ; Note that this instruction is in the delay slot, so it is actually executed before the memcpy branch

;; call main:
brlid r15, main_main
or r0,r0,r0  ;  fill delay slot

; Call bsp exit:
brlid r15, bsp_exit
or r0,r0,r0  ;  fill delay slot

;; Output 'B':
imm 0x8400
addik r6, r0, 4
addik r5, r0, 0x42
sw r5, r6, r0

end_label:
bri end_label  ; Endless loop!

emitZ:
;; Output 'Z':
; prologue:
addik r1, r1, -4
swi r15, r1, 0

imm 0x8400
addik r6, r0, 4
addik r5, r0, 0x5a
sw r5, r6, r0

; epiloque:
lwi r15, r1, 0
addik r1, r1, 4
rtsd r15, 8
or r0,r0,r0

