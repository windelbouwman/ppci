
; boot file for xtensa qemu board
section reset

reset:
  j start1

; Should be 
; serial device is mapped at fd050020
  align 4
thr:
  dd 0xfd050020  ; base of 16650

start1:
  movi a5, 65  ; character 'A'
  l32r a4, thr

  s8i a5, a4, 2
  addi a5, a5, 1
  s8i a5, a4, 2

  call0 main_main

limbo:
  j limbo
