
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

_data_load_start:
  dcd =__data_load_start
_data_start:
  dcd =__data_start
_data_end:
  dcd =__data_end

start1:
  l32r a4, thr

  movi a5, 65  ; character 'A'
  ; s8i a5, a4, 2

  l32r a1, stackpointer ; Load stack pointer

  ; addi a5, a5, 1 ; character A+1
  ; s8i a5, a4, 2

  ; call0 do_c
  ; push a8
  ; call0 do_c
  ; pop a8
  ; call0 do_c

  ; ====================
  ; Load initial data!
  l32r a6, _data_load_start ; src pointer
  l32r a7, _data_start ; dst pointer
  l32r a8, _data_end ; dst end
  beq a7, a8, _load_done  ; No data to load

_load_loop:
  l32i a9, a6, 0 ; load 32 bit
  addi a6, a6, 4 ; update src pointer
  s32i a9, a7, 0 ; store 32 bit
  addi a7, a7, 4 ; update dst pointer
  bltu a7, a8, _load_loop

_load_done:
  ; ====================

  call0 main_main
  call0 bsp_exit

limbo:
  j limbo


align 4
do_c:
  addi a5, a5, 1 ; character A+1
  s8i a5, a4, 2
  ret
