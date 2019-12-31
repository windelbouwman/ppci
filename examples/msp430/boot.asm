
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

section code

global main_main
global bsp_exit

reset_handler:
  mov.w #0x980, sp       ; setup stack pointer
  call #main_main        ; Enter main
  call #bsp_exit         ; Call exit cleaning
end_inf_loop:
  jmp end_inf_loop

global bsp_putc
bsp_putc:
  mov.b r12, 0x67(r2)  ; write to uart0 tx buf
  ret
