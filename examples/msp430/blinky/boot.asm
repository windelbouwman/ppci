
; The msp M430G2553 contains 16 kb flash and 256 bytes ram
; interrupt vector

section reset

dw 0 ; 31 = reset
dw 0
dw 0
dw 0
dw 0
dw 0
dw 0
dw 0 ; 24

dw 0 ; 23
dw 0
dw 0
dw 0
dw 0
dw 0
dw 0
dw 0 ; 16

dw 0 ; 15
dw 0
dw 0
dw 0
dw 0
dw 0
dw 0
dw 0 ; 8

dw 0 ; 7
dw 0
dw 0
dw 0
dw 0
dw 0
dw 0
dw 0 ; 0

; TODO: dd =reset

; P1IN  0x20
; P1OUT 0x21
; P1DIR 0x22

; P1.0 (red led)
; P1.6 green led
; P1.3 switch

; main code:

section code

reset:

  mov.w #0x280, sp       ; setup stack pointer
  bis.b #0x41, 0x22(r2)  ; config P1.0 and P1.6 as output

main:
  bit.b #0x4, 0x20(r2)
  jc off

on:
  bic.b #0x1, 0x21(r2)
  bis.b #0x40, 0x21(r2)
  jmp wait

off:
  bic.b #0x1, 0x21(r2)
  bis.b #0x40, 0x21(r2)

wait:
  jmp main

