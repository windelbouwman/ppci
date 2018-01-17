#!/bin/bash

qemu-system-xtensa -M lx60 -m 96M -drive if=pflash,format=raw,file=lx60.flash -serial stdio
