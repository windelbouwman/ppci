#!/bin/bash

# You can choose to load an elf file, or an image file:
# qemu-system-xtensa -M lx60 -m 96M -drive if=pflash,format=raw,file=lx60.flash -serial stdio
qemu-system-xtensa -M lx60 -m 96M -serial stdio -kernel hello.elf
