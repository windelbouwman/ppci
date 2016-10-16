1. For runnig this examples either Icarus verilog (iverilog) (https://github.com/steveicarus/iverilog)
   or verilator((www.veripool.org)) needs to be installed.
2. Generate firmware.hex py running: python3 mkfirm.py
3. For iverilog: cd iverilog
   for verilator: cd verilator
4. Build the simulation: ./buildsim.sh
5. Start the simulation: ./runsim.sh
6. cd ..
7. Connect the commandline-debugger: python3 dbg_gdb_cli.py
8. Try some debugger commands:
   setbrk main.c3,12  // breakpoint at line 12 of main.c3
   run              // continue
   read 0, 4      // read 4 bytes from address 0
   write 0, ab    // write 0xab to address 0
   read 0,4       // read again
   regs           // read registers
   step           // single instruction stepping
   nstep 0xff     // run 0xff instructions
   run            // leave debug monitor
   stop          // send break signal


