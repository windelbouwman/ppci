#!/bin/bash

qemu-system-or1k -kernel hello.bin -M or1k-sim -serial stdio -S -s &

python ../../dbg_gdb_cli.py hello.oj

