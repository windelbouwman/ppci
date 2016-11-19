#!/bin/bash

qemu-system-xtensa -M lx60 -m 96M -pflash lx60.flash -serial stdio
