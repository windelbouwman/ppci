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
out 0x4, r16

; sei  ; enable interrupts
global main_main
rjmp main_main


; Assembly functions:

; pb5 on
global main_on
main_on:
ldi r16, 32
out 0x5, r16
ret

; pb5 off
global main_off
main_off:
ldi r16, 0
out 0x5, r16
ret

; delay x times 10 ms:
global main_delay
main_delay:
    push r20
    push r19
    mov r20, r1
L1: ldi r19, 16
L2: ldi r18, 100
L3: ldi r17, 50  ; 50 x 2 instructions
L4: dec r17
    brne L4
    dec r18
    brne L3
    dec r19
    brne L2
    dec r20
    brne L1
    pop r19
    pop r20
ret

