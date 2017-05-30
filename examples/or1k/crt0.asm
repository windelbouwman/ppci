
section reset
l.j start
l.nop 0

section code
start:
  ; Initialize ram!
  l.movhi r3, hi(__data_load_start)
  l.ori r3, r3, lo(__data_load_start)
  l.movhi r4, hi(__data_start)
  l.ori r4, r4, lo(__data_start)
  l.movhi r5, hi(__data_end)
  l.ori r5, r5, lo(__data_end)

  l.sflts r4, r5
  l.bnf _load_done
  l.nop 0
_load_loop:
  l.lbz r9, 0(r3)
  l.addi r3, r3, 1
  l.sb 0(r4), r9
  l.addi r4, r4, 1
  l.sflts r4, r5
  l.bf _load_loop
  l.nop 0

_load_done:

  ; Setup stack and enter main!
  l.movhi r1, 0x3        ; Setup stack pointer to 0x30000
  l.jal main_main        ; Enter main
  l.nop 0                ; fill delay slot
  l.jal bsp_exit         ; Call exit cleaning
  l.nop 0                ; fill delay slot

end_inf_loop:
  l.j end_inf_loop
  l.nop 0                ; fill delay slot
