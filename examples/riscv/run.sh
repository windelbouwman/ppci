#!/bin/bash

# qemu-system-riscv32 -M sifive_u -nographic -kernel kernel.elf

# Insane tracing:
qemu-system-riscv32 -M sifive_u -D trace.txt -d in_asm,exec,int,op_opt,cpu -singlestep
