#!/bin/bash

# Extensive tracing: -D trace.txt -d in_asm,exec,int,op_opt,cpu

qemu-system-microblaze -kernel hello.bin -serial stdio

