
; boot file for xtensa qemu board
section reset

reset:
  j start1

; Should be 
; serial device is mapped at fd050020
  align 4
thr:
  dd 0xfd050020  ; base of 16650
stackpointer:
  dd 0xd8020000  ; initial value for stack pointer

start1:
  l32r a4, thr

  ; movi a5, 65  ; character 'A'
  ; s8i a5, a4, 2

  l32r a1, stackpointer ; Load stack pointer

  ; addi a5, a5, 1 ; character A+1
  ; s8i a5, a4, 2

  ; call0 do_c
  ; push a8
  ; call0 do_c
  ; pop a8
  ; call0 do_c

  call0 main_main
  call0 bsp_exit

limbo:
  j limbo


align 4
do_c:
  addi a5, a5, 1 ; character A+1
  s8i a5, a4, 2
  ret
