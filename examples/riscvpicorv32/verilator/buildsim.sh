verilator  -cc  --trace --exe uart.c tb.cpp ../picorv32.v ../system.v simuart.v --Wno-lint --Wno-unoptflat --Wno-combdly --Wno-redefmacro --top-module system
make -C obj_dir -f Vsystem.mk
cd obj_dir
cp Vsystem.* ..
cd ..
