#!/usr/bin/env bash

echo "Trying to run versatilePB board"

qemu-system-arm -M realview-pb-a8 -m 128M -kernel hello.bin -serial stdio


