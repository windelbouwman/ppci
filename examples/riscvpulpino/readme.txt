1. generate l2_stim.slm and tcdm_bank0.slm by running mkfirmpulpino.py
For the simulation verilator(www.veripool.org) needs to be installed. To
compile the pulpino-sources with verilator:
2. cd vsim
3. ./verilate.sh
4. cp ob_dir/Vpulpino_top ..
5. cd ..
6. compile adv_jtag_bridge(source at https://github.com/pulp-platform/riscv_jtag_server):
   cd jtagserver
   ./autogen.sh
   ./configure
   make
   cd..
7. Start Simulation: ./Vpulpino_top
8. Start adv_jtag_bridge: cd jtagserver
   ./run.sh
9. run dbg.py
10. Use the following debug commands:
    restart               // restart pulpino
    // Hello world from Pulpino,
     //..compiler with ppci-riscv.
    setbrk main.c3,6       // set breakpoint
    restart           // restart
    // Hello world from Pulpino,
    // further commands:
    regs    //show registers
    read 0,8 //read 8 bytes memory from adr 0
    write 0,4,12345678 // write 4 bytes to adr 0
