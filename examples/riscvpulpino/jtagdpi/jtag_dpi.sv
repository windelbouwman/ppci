//////////////////////////////////////////////////////////////////////
////                                                              ////
////  jtag_dpi.sv, former dbg_comm_vpi.v                          ////
////                                                              ////
////                                                              ////
////  This file is part of the SoC/OpenRISC Development Interface ////
////  http://www.opencores.org/cores/DebugInterface/              ////
////                                                              ////
////                                                              ////
////  Author(s):                                                  ////
////       Igor Mohor (igorm@opencores.org)                       ////
////       Gyorgy Jeney (nog@sdf.lonestar.net)                    ////
////       Nathan Yawn (nathan.yawn@opencores.org)                ////
////       Andreas Traber (atraber@iis.ee.ethz.ch)                ////
////                                                              ////
////                                                              ////
//////////////////////////////////////////////////////////////////////
////                                                              ////
//// Copyright (C) 2000-2015 Authors                              ////
////                                                              ////
//// This source file may be used and distributed without         ////
//// restriction provided that this copyright statement is not    ////
//// removed from the file and that any derivative work contains  ////
//// the original copyright notice and the associated disclaimer. ////
////                                                              ////
//// This source file is free software; you can redistribute it   ////
//// and/or modify it under the terms of the GNU Lesser General   ////
//// Public License as published by the Free Software Foundation; ////
//// either version 2.1 of the License, or (at your option) any   ////
//// later version.                                               ////
////                                                              ////
//// This source is distributed in the hope that it will be       ////
//// useful, but WITHOUT ANY WARRANTY; without even the implied   ////
//// warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR      ////
//// PURPOSE.  See the GNU Lesser General Public License for more ////
//// details.                                                     ////
////                                                              ////
//// You should have received a copy of the GNU Lesser General    ////
//// Public License along with this source; if not, download it   ////
//// from http://www.opencores.org/lgpl.shtml                     ////
////                                                              ////
//////////////////////////////////////////////////////////////////////

module jtag_dpi
#(
  parameter TCP_PORT      = 4567,
  parameter TIMEOUT_COUNT = 6'h08 // 1/2 of a TCK clock will be this many clk_i ticks.  Must be less than 6 bits.
)
(
  input     clk_i,
  input     enable_i,

  output    tms_o,
  output    tck_o,
  output    trst_o,
  output    tdi_o,
  input     tdo_i
  );

  import "DPI-C"         function void jtag_init(input int port);
  import "DPI-C" context function int  jtag_recv(output byte out);
  import "DPI-C"         function void jtag_timeout();

  export "DPI-C" function rtl_get_tdo;


  logic [5:0] clk_count = TIMEOUT_COUNT + 1;


  logic [7:0]  out;
  logic [7:0] 	tmpreg;   
   



  function logic rtl_get_tdo();
    return tdo_i;
  endfunction

  // Handle commands from the upper level
  initial
  begin
    jtag_init(TCP_PORT);
  end

   always @(posedge clk_i)
   begin
      if(jtag_recv(out)!=0)
	begin
	   clk_count = 'h0;  // Reset the timeout clock in case jp wants to wait for a timeout / half TCK period
	   tmpreg <= out;	   
	end
   end
 
  // Send timeouts / wait periods to the upper layer
  always @(posedge clk_i)
  begin
    if(clk_count < TIMEOUT_COUNT)
      clk_count = clk_count + 1;
    else if(clk_count == TIMEOUT_COUNT)
    begin
      jtag_timeout();
      clk_count = clk_count + 1;
    end
    // else it's already timed out, don't do anything
  end

  assign tck_o  = tmpreg[0];
  assign trst_o = tmpreg[1];
  assign tdi_o  = tmpreg[2];
  assign tms_o  = tmpreg[3];

endmodule
