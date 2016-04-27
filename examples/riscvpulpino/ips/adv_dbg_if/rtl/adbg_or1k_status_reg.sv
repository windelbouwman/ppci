//////////////////////////////////////////////////////////////////////
////                                                              ////
////  adbg_or1k_status_reg.v                                      ////
////                                                              ////
////                                                              ////
////  This file is part of the SoC Debug Interface.               ////
////                                                              ////
////  Author(s):                                                  ////
////       Igor Mohor (igorm@opencores.org)                       ////
////       Nathan Yawn (nyawn@opencores.org)                      ////
////                                                              ////
////                                                              ////
////                                                              ////
//////////////////////////////////////////////////////////////////////
////                                                              ////
//// Copyright (C) 2000 - 2011 Authors                            ////
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
//
// CVS Revision History
//
// $Log: adbg_or1k_status_reg.v,v $
// Revision 1.3  2011-10-24 02:25:11  natey
// Removed extraneous '#1' delays, which were a holdover from the original
// versions in the previous dbg_if core.
//
// Revision 1.2  2010-01-10 22:54:10  Nathan
// Update copyright dates
//
// Revision 1.1  2008/07/22 20:28:31  Nathan
// Changed names of all files and modules (prefixed an a, for advanced).  Cleanup, indenting.  No functional changes.
//
// Revision 1.3  2008/07/06 20:02:54  Nathan
// Fixes for synthesis with Xilinx ISE (also synthesizable with 
// Quartus II 7.0).  Ran through dos2unix.
//
// Revision 1.2  2008/06/26 20:52:32  Nathan
// OR1K module tested and working.  Added copyright / license info 
// to _define files.  Other cleanup.
//
//
//
//

`include "adbg_or1k_defines.v"

module adbg_or1k_status_reg  #( 
        parameter NB_CORES = 4
    ) (
    input                       tck_i,
    input                       trstn_i,
    input                       we_i,
    input                       cpu_clk_i,
    input                       cpu_rstn_i,
    input  logic         [15:0] data_i,
    input  logic [NB_CORES-1:0] bp_i,
    output logic [NB_CORES-1:0] ctrl_reg_o,
    output logic [NB_CORES-1:0] cpu_stall_o
);

   reg   [NB_CORES-1:0] stall_bp, stall_bp_csff, stall_bp_tck;
   reg   [NB_CORES-1:0] stall_reg, stall_reg_csff, stall_reg_cpu;

   // Breakpoint is latched and synchronized. Stall is set and latched.
   // This is done in the CPU clock domain, because the JTAG clock (TCK) is
   // irregular.  By only allowing bp_i to set (but not reset) the stall_bp
   // signal, we insure that the CPU will remain in the stalled state until
   // the debug host can read the state.
    always @ (posedge cpu_clk_i or negedge cpu_rstn_i)
    begin
        if(~cpu_rstn_i)
            stall_bp <= '0;
        else
        begin
            for (int i=0;i<NB_CORES;i++)
            begin
                if(bp_i[i])
                    stall_bp[i] <= 1'b1;
                else if(stall_reg_cpu[i])
                    stall_bp[i] <= 1'b0;
            end
        end
    end


   // Synchronizing
   always @ (posedge tck_i or negedge trstn_i)
     begin
    if (~trstn_i)
      begin
         stall_bp_csff <= '0;
         stall_bp_tck  <= '0;
      end
    else
      begin
         stall_bp_csff <= stall_bp;
         stall_bp_tck  <= stall_bp_csff;
      end
     end


   always @ (posedge cpu_clk_i or negedge cpu_rstn_i)
     begin
    if (~cpu_rstn_i)
      begin
         stall_reg_csff <= '0;
         stall_reg_cpu  <= '0;
      end
    else
      begin
         stall_reg_csff <= stall_reg;
         stall_reg_cpu  <= stall_reg_csff;
      end
     end

   // bp_i forces a stall immediately on a breakpoint
   // stall_bp holds the stall until the debug host acts
   // stall_reg_cpu allows the debug host to control a stall.
   assign cpu_stall_o = bp_i | stall_bp | stall_reg_cpu;


   // Writing data to the control registers (stall)
   // This can be set either by the debug host, or by
   // a CPU breakpoint.  It can only be cleared by the host.
    always @ (posedge tck_i or negedge trstn_i)
    begin
        if (~trstn_i)
            stall_reg <= '0;
        else
        begin
            for (int i=0;i<NB_CORES;i++)
            begin
                if (stall_bp_tck[i])
                    stall_reg[i] <= 1'b1;
                else if (we_i)
                    stall_reg[i] <= data_i[i];
            end
        end
    end

   // Value for read back
   assign ctrl_reg_o = {stall_reg};


endmodule

