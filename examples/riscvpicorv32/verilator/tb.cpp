#include "verilated.h"
#include "verilated_vcd_c.h"
#include "Vsystem.h"

#include <sys/types.h>
#include <stdio.h>
#include <stdlib.h>


vluint64_t main_time = 0;	// Current simulation time (64-bit unsigned)
double sc_time_stamp () {	// Called by $time in Verilog
  return main_time;		// Note does conversion to real, to match SystemC
} 


int main(int argc, char **argv, char **env) {
  int i;
  int clk;
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
  top->resetn = 1;
    // run simulation for 100 clock periods
  i = 0;
  while(1) {
    // dump variables into VCD file and toggle clock
    for (clk=0; clk<2; clk++) {
      if(trace) tfp->dump (2*i+clk);
      top->clk = !top->clk;
      top->eval();
    }
    if(i >5) top->resetn = 0;
    if(i > 20) top->resetn=1;
    if (Verilated::gotFinish())  exit(0);
    i++;
  }
  if(trace) tfp->close();
  exit(0);
}

