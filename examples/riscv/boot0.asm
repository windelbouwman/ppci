
global _start
_start:
 lui sp, 0x80030        ; setup stack pointer

global main_main
 jal ra, main_main   ; Branch to sample start LR

main_main:
 lui t0, 0x10010

 andi t1, t1 , 0
 addi t1, t1, 72  ; 'H'
 sw t1, 0(t0)

 andi t1, t1 , 0
 addi t1, t1, 101  ; 'e'
 sw t1, 0(t0)

 andi t1, t1 , 0
 addi t1, t1, 108  ; 'l'
 sw t1, 0(t0)
 sw t1, 0(t0)

 andi t1, t1 , 0
 addi t1, t1, 111  ; 'o'
 sw t1, 0(t0)


limbo:
 j limbo

ebreak
