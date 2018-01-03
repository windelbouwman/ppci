verilator  -cc  --trace --exe -CFLAGS -fpermissive sd.c spi_sdcard.c tb.cpp ../picorv32.v ../system.v simsd.v --Wno-lint --Wno-unoptflat --Wno-combdly --Wno-redefmacro --top-module system
make -C obj_dir -f Vsystem.mk
cd obj_dir
cp Vsystem.* ..
cd ..
