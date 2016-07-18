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

call bsp_init

; sei  ; enable interrupts
call main_main

endless:
rjmp endless

