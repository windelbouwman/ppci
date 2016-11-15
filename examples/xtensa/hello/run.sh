#!/bin/bash

qemu-system-xtensa -M lx60 -m 16M -pflash lx60.flash -serial stdio
