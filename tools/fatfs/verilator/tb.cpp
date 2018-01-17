#include "verilated.h"
#include "verilated_vcd_c.h"
#include "Vsystem.h"

#include <sys/types.h>
#include <stdio.h>
#include <stdlib.h>

#define TCLK 20

vluint64_t main_time = 0;	// Current simulation time (64-bit unsigned)
double sc_time_stamp () {	// Called by $time in Verilog
  return main_time;		// Note does conversion to real, to match SystemC
} 


int main(int argc, char **argv, char **env) {
  int trace = 0;
  Verilated::commandArgs(argc, argv);
  Vsystem* top = new Vsystem;
  // init top verilog instance
   if(argc==2 && strcmp(argv[1],"vcd")==0) trace = 1;
  // init trace dump
  Verilated::traceEverOn(true);
  VerilatedVcdC* tfp = new VerilatedVcdC;
  top->trace (tfp, 99);
  if(trace) tfp->open ("picorv32.vcd");
  // initialize simulation inputs
  top->clk = 0;
  top->resetn = 0;
   // run endless simulation
  while(1) {
    if(main_time > 5*TCLK) top->resetn=1;
    top->clk = !top->clk;
    // dump variables into VCD file and toggle clock
    if(trace) tfp->dump (main_time);
    top->eval();
    if (Verilated::gotFinish())  exit(0);
    main_time += TCLK/2;
  }
  if(trace) tfp->close();
  exit(0);
}

