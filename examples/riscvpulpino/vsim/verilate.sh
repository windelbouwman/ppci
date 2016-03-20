verilator --cc -f vlist.txt --trace --exe tb.cpp --Wno-lint --Wno-unoptflat --Wno-combdly --Wno-redefmacro --top-module pulpino_top

make -C obj_dir -f vpulpino_top.mk