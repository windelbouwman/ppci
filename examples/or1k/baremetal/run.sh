#!/bin/bash

# TRACE="-D trace.txt -d in_asm,exec,int,cpu,op_opt"
qemu-system-or1k -kernel baremetal.bin -M or1k-sim -serial stdio -m 16M

# Debugging tip:
# qemu-system-or1k -kernel baremetal.bin -M or1k-sim -serial stdio -m 16M -D trace.txt -d in_asm,exec,int,op_opt,cpu
