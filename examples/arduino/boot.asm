; interrupt vector

rjmp reset
rjmp unhandled
rjmp unhandled
rjmp unhandled
rjmp unhandled
rjmp unhandled
rjmp unhandled
rjmp unhandled
rjmp unhandled
rjmp unhandled
rjmp unhandled
rjmp unhandled
rjmp unhandled

unhandled:
reti

reset:
ldi r16, 0x8
out 0x3e, r16  ; Setup stack pointer (SPH)
ldi r16, 0xff
out 0x3d, r16   ; SPL

; Setup pb5 as output:
ldi r16, 32
ldi r17, 0
out 0x4, r16

; Toggle pb5 as fast as possible:
label1:
out 0x5, r16
out 0x5, r17
rjmp label1

; sei  ; enable interrupts
rjmp main_main


; Assembly functions:
main_on:
ldi r16, 32
out 0x5, r16
ret

main_off:
ldi r16, 0
out 0x5, r16
ret

main_delay:
ret


