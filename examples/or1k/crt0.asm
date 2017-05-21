
section reset_vector

dd 0 ; 0
dd 0 ; 1
dd 0 ; 2
dd 0 ; 3
dd 0 ; 4
dd 0 ; 5
dd 0 ; 6
dd 0 ; 7
dd 0 ; 8
dd 0 ; 9
dd 0 ; 10
dd 0 ; 11
dd 0 ; 12
dd 0 ; 13
dd 0 ; 14
dcd =reset_handler ; 15 = reset

section code
reset_handler:
  l.jal main_main        ; Enter main
  l.jal bsp_exit         ; Call exit cleaning
end_inf_loop:
  l.j end_inf_loop
