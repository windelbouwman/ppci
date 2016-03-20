#include "svdpi.h"
#include "verilated.h"
#include "verilated_vcd_c.h"
#include "Vpulpino_top.h"
#include "Vpulpino_top__Dpi.h"



#include <sys/types.h>
#include <stdio.h>
#include <stdlib.h>


vluint64_t main_time = 0;	// Current simulation time (64-bit unsigned)
double sc_time_stamp () {	// Called by $time in Verilog
  return main_time;		// Note does conversion to real, to match SystemC
} 

Vpulpino_top* top = new Vpulpino_top;


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
  top->tck_i = 0;
  top->trstn_i = 0;
  top->tms_i = 0;
  top->tdi_i = 0;
    // run simulation for 100 clock periods
  for (i=0; i<10000; i++) {
    // dump variables into VCD file and toggle clock
    for (clk=0; clk<2; clk++) {
      tfp->dump (2*i+clk);
      top->clk = !top->clk;
      top->eval();
    }
    if(i >5) top->rst_n = 0;
    if(i > 20) top->rst_n=1;
    if(i > 100) top->fetch_enable_i=1;	
    if (Verilated::gotFinish())  exit(0);
  }
  tfp->close();
  exit(0);
}

