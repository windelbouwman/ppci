

all: Vsystem Vsystemdbg

obj_dir/Vsystem.mk:
	verilator  -cc  --trace --exe uart.c tb.cpp ../picorv32.v ../system.v simuart.v --Wno-lint --Wno-unoptflat --Wno-combdly --Wno-redefmacro --top-module system --o Vsystem --Mdir obj_dir

obj_dir_dbg/Vsystem.mk:
	verilator  -DDBGUART -cc  --trace --exe uart.c tb.cpp ../picorv32.v ../system.v simuart.v --Wno-lint --Wno-unoptflat --Wno-combdly --Wno-redefmacro --top-module system --o Vsystemdbg --Mdir obj_dir_dbg

Vsystem: obj_dir/Vsystem.mk
	make -C obj_dir -f Vsystem.mk
	cp obj_dir/Vsystem .

Vsystemdbg: obj_dir_dbg/Vsystem.mk
	make -C obj_dir_dbg -f Vsystem.mk
	cp obj_dir_dbg/Vsystemdbg .

clean:
	rm -rf obj_dir
	rm -f Vsystem
	rm -rf obj_dir_dbg
	rm -f Vsystemdbg
