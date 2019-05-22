lui sp, 0x1E        ; setup stack pointer
global main_main
jal ra, main_main   ; Branch to sample start LR
ebreak
