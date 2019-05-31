.align 4
lui sp, 0x1E
dd 0x0600000b  ; naskirq x0,x0
j start
ebreak
irq_vec:
dd 0x0200810b ; setq q2, x1
dd 0x0201018b ; setq q3, x2
la x1, irq_regs
sw x0, 0(x1)
dd 0x0000010b ; getq x2, q0    ; pc
sw x2, 128(x1)
dd 0x0001010b ; getq x2, q2    ; x1
sw x2, 4(x1)
dd 0x0001810b ; getq x2, q3    ; x2
sw x2, 8(x1)
sw x3, 12(x1)
sw x4, 16(x1)
sw x5, 20(x1)
sw x6, 24(x1)
sw x7, 28(x1)
sw x8, 32(x1)
sw x9, 36(x1)
sw x10, 40(x1)
sw x11, 44(x1)
sw x12, 48(x1)
sw x13, 52(x1)
sw x14, 56(x1)
sw x15, 60(x1)
sw x16, 64(x1)
sw x17, 68(x1)
sw x18, 72(x1)
sw x19, 76(x1)
sw x20, 80(x1)
sw x21, 84(x1)
sw x22, 88(x1)
sw x23, 92(x1)
sw x24, 96(x1)
sw x25, 100(x1)
sw x26, 104(x1)
sw x27, 108(x1)
sw x28, 112(x1)
sw x29, 116(x1)
sw x30, 120(x1)
sw x31, 124(x1)
mv x12, x1
dd 0x0000868b ; getq x13, q1
lui sp, 0x1F
jal ra, irq_irq
beq x10, x0, nostepping
dd 0x0c05000b ; delint
nostepping:
la x1, irq_regs
lw x2, 128(x1)
dd 0x0201000b ; set q0, x2   ; pc
lw x2, 8(x1)
lw x3, 12(x1)
lw x4, 16(x1)
lw x5, 20(x1)
lw x6, 24(x1)
lw x7, 28(x1)
lw x8, 32(x1)
lw x9, 36(x1)
lw x10, 40(x1)
lw x11, 44(x1)
lw x12, 48(x1)
lw x13, 52(x1)
lw x14, 56(x1)
lw x15, 60(x1)
lw x16, 64(x1)
lw x17, 68(x1)
lw x18, 72(x1)
lw x19, 76(x1)
lw x20, 80(x1)
lw x21, 84(x1)
lw x22, 88(x1)
lw x23, 92(x1)
lw x24, 96(x1)
lw x25, 100(x1)
lw x26, 104(x1)
lw x27, 108(x1)
lw x28, 112(x1)
lw x29, 116(x1)
lw x30, 120(x1)
lw x31, 124(x1)
lw x1, 4(x1)
dd 0x0400000b ; retirq
irq_regs:
repeat 33
nop
endrepeat
start:
mv x1, x0
;not SP
mv x3, x0
mv x4, x0
mv x5, x0
mv x6, x0
mv x7, x0
mv x8, x0
mv x9, x0
mv x10, x0
mv x11, x0
mv x12, x0
mv x13, x0
mv x14, x0
mv x15, x0
mv x16, x0
mv x17, x0
mv x18, x0
mv x19, x0
mv x20, x0
mv x21, x0
mv x21, x0
mv x22, x0
mv x23, x0
mv x24, x0
mv x25, x0
mv x26, x0
mv x27, x0
mv x28, x0
mv x29, x0
mv x30, x0
mv x31, x0
global main_main
jal ra, main_main
ebreak