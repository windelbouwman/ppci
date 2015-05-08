#!/usr/bin/env bash

set -e

echo "Trying to run test on stellaris qemu machine"

qemu-system-arm -M lm3s811evb -m 128M -kernel bare.bin -serial stdio

