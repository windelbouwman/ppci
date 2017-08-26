#!/bin/bash

qemu-system-or1k -kernel hello.bin -M or1k-sim -serial stdio -S -s &

python ../../../tools/dbgui/dbguigdb.py hello.oj

