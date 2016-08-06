#!/bin/bash

verilator -Wall --cc --trace -f vlist.txt --exe sim_main.cpp --top-module tb_openMSP430

make -C obj_dir -f Vourexe.mk Vour
