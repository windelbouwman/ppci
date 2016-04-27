#include "svdpi.h"
#include "verilated.h"
#include "verilated_vcd_c.h"
#include "Vtopsim.h"
#include "Vtopsim__Dpi.h"



#include <sys/types.h>
#include <stdio.h>
#include <stdlib.h>


vluint64_t main_time = 0;	// Current simulation time (64-bit unsigned)
double sc_time_stamp () {	// Called by $time in Verilog
  return main_time;		// Note does conversion to real, to match SystemC
} 

Vtopsim* top = new Vtopsim;


int main(int argc, char **argv, char **env) {
  int i;
  int clk;
  Verilated::commandArgs(argc, argv);
  // init top verilog instance
  
  // init trace dump
  Verilated::traceEverOn(true);
  VerilatedVcdC* tfp = new VerilatedVcdC;
  top->trace (tfp, 99);
  tfp->open ("pulpino.vcd");
  // initialize simulation inputs
  top->clk = 0;
  top->rst_n = 1;
  top->clk_sel_i = 0;
  top->testmode_i = 0;
  top->fetch_enable_i = 0;
  top->spi_clk_i = 0;
  top->spi_cs_i = 1;
    // run simulation for 100 clock periods
  i = 0;
  while(1) {
    // dump variables into VCD file and toggle clock
    for (clk=0; clk<2; clk++) {
      //tfp->dump (2*i+clk);
      top->clk = !top->clk;
      top->eval();
    }
    if(i >5) top->rst_n = 0;
    if(i > 20) top->rst_n=1;
    if(i > 100) top->fetch_enable_i=1;	
    if (Verilated::gotFinish())  exit(0);
    i++;
  }
  tfp->close();
  exit(0);
}

