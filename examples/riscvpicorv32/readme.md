1. For runnig this examples either Icarus verilog (iverilog) (https://github.com/steveicarus/iverilog)
   or verilator((www.veripool.org)) needs to be installed. As iverilog is much slower,
   it is recommended to use verilator for debugging.

2. For iverilog: cd iverilog
   for verilator: cd verilator

3. Build the simulation:
      ./buildsim.sh
   cd ..

4. Generate firmware.hex py running:
   for c3 with debugger:
       python3 mkfwc3.py --debug hello  // for /c3src/hello/main.c3
   for c3 without debugger:
       python3 mkfwc3.py hello  // for /c3src/hello/main.c3
   for c with debugger:
       python3 mkfwdbgc.py max   // for /csrc/max/main.c
   for c without debugger:
       python3 mkfwc.py max  // for /csrc/max/main.c

5. Start the simulation:
         ./runsimv.sh(without debugger) or ./runsimvdbg.sh for verilator
         ./runsimi.sh(without debugger) or ./runsimidbg.sh for iverilog

6. Connect the commandline-debugger: python3 dbg_gdb_cli.py

7. Try some debugger commands:
   setbrk ./c3src/hello/main.c3,12  // breakpoint at line 12 of main.c3
   restart        // reset
   read 0, 4      // read 4 bytes from address 0
   write 0, ab    // write 0xab to address 0
   read 0,4       // read again
   readregs       // read registers
   clrbrk ./c3src/hello/main.c3,12  // remove breakpoint at line 12 of main.c3
   run            // leave debug monitor
   stop          // send break signal


