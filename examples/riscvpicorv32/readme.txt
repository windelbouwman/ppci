1. Icarus verilog (iverilog) needs to be installed (https://github.com/steveicarus/iverilog) for this examples.
2. Generate firmware.hex py running: python3 mkfirm.py
3. Compile the sources with iverilog: ./buildsim.sh
4. Run the simulation: ./runsim.sh
5. Connect the commandline-debugger: python3 dbg_gdb_cli.py
6. Try some debugger commands:
   setbrk main.c3,12  // breakpoint at line 12 of main.c3
   run              // continue
   read 0, 4      // read 4 bytes from address 0
   write 0, ab    // write 0xab to address 0
   read 0,4       // read again
   regs           // read registers
   step           // single instruction stepping
   run            // leave debug monitor
   stop          // restart debug monitor


