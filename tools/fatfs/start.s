lui x2, 0x1F
global main
jal x1, main
ebreak
nop
global rdcyc
rdcyc:
rdcycle x10
jalr x0,x1,0
