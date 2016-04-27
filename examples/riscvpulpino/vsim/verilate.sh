verilator --cc -f vlist.txt  --trace --exe  ../jtagdpi/jtag_dpi.c tb.cpp --Wno-lint --Wno-unoptflat --Wno-combdly --Wno-redefmacro --top-module topsim

make -C obj_dir -f Vtopsim.mk
