verilator  -cc  --trace --exe uart.c tb.cpp ../picorv32.v ../system.v simuart.v --Wno-lint --Wno-unoptflat --Wno-combdly --Wno-redefmacro --top-module system --o Vsystem
make -C obj_dir -f Vsystem.mk
cd obj_dir
cp Vsystem ..
cd ..
verilator  -DDBGUART -cc  --trace --exe uart.c tb.cpp ../picorv32.v ../system.v simuart.v --Wno-lint --Wno-unoptflat --Wno-combdly --Wno-redefmacro --top-module system --o Vsystemdbg
make -C obj_dir -f Vsystem.mk
cd obj_dir
cp Vsystemdbg ..
cd ..