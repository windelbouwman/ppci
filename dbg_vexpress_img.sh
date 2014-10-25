#!/bin/bash

# This script start qemu with a given image and attaches gdb to it:

echo "Using image: $1"

# Start qemu in background:
qemu-system-arm -m 16M -s -S -M realview-pb-a8 -kernel $1 &

# Start gdb:
arm-none-eabi-gdb -ex "target remote localhost:1234"

