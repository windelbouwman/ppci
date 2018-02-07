#!/bin/bash

# -s = shortcut for -gdb tcp::1234
qemu-system-arm -M lm3s6965evb -kernel hello.bin -serial stdio -s -S

