
; The msp M430G2553 contains 16 kb flash and 256 bytes ram
; interrupt vector of 16 pieces

section reset_vector

dw 0 ; 0
dw 0 ; 1
dw 0 ; 2
dw 0 ; 3
dw 0 ; 4
dw 0 ; 5
dw 0 ; 6
dw 0 ; 7
dw 0 ; 8
dw 0 ; 9
dw 0 ; 10
dw 0 ; 11
dw 0 ; 12
dw 0 ; 13
dw 0 ; 14
dw reset_handler ; 15 = reset


; P1IN  0x20
; P1OUT 0x21
; P1DIR 0x22

; P1.0 (red led)
; P1.6 green led
; P1.3 switch

; main code:

section code

reset_handler:

  mov.w #0x280, sp       ; setup stack pointer
  bis.b #0x41, 0x22(r2)  ; config P1.0 and P1.6 as output

  ; Send char a to output:
  mov.b #0x41, 0x67(r2)
  mov.b #0x42, 0x67(r2)
  mov.b #0x43, 0x67(r2)

main:
  xor.b #0x41, 0x21(r2)

wait:
  mov.b #0x4, 0x67(r2)  ; end of transmission
  jmp main


main_on:
  ret

main_off:
  ret

main_delay:
  ret
