
section reset
l.j start
l.nop 0

section code
start:
  l.movhi r1, 0x3        ; Setup stack pointer to 0x30000
  l.jal main_main        ; Enter main
  l.nop 0                ; fill delay slot
  l.jal bsp_exit         ; Call exit cleaning
  l.nop 0                ; fill delay slot

end_inf_loop:
  l.j end_inf_loop
  l.nop 0                ; fill delay slot
