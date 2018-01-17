#!/bin/bash

qemu-system-mips -M help -m 96M -drive if=pflash,format=raw,file=lx60.flash -serial stdio
