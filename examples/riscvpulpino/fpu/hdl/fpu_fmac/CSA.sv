// Copyright 2017 ETH Zurich and University of Bologna.
// Copyright and related rights are licensed under the Solderpad Hardware
// License, Version 0.51 (the “License”); you may not use this file except in
// compliance with the License.  You may obtain a copy of the License at
// http://solderpad.org/licenses/SHL-0.51. Unless required by applicable law
// or agreed to in writing, software, hardware and materials distributed under
// this License is distributed on an “AS IS” BASIS, WITHOUT WARRANTIES OR
// CONDITIONS OF ANY KIND, either express or implied. See the License for the
// specific language governing permissions and limitations under the License.

////////////////////////////////////////////////////////////////////////////////
// Company:        IIS @ ETHZ - Federal Institute of Technology               //
//                                                                            //
// Engineers:      Lei Li  //lile@iis.ee.ethz.ch                              //
//		                                                              //
// Additional contributions by:                                               //
//                                                                            //
//                                                                            //
//                                                                            //
// Create Date:    01/12/2016                                                 //
// Design Name:    fmac                                                       //
// Module Name:    CSA.sv                                                     //
// Project Name:   Private FPU                                                //
// Language:       SystemVerilog                                              //
//                                                                            //
// Description:    Carry Save Adder                                           //
//                                                                            //
// Revision:       22/06/2017                                                 //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

import fpu_defs_fmac::*;

module CSA
#( parameter n=49 )
 (
   input logic [n-1:0]           A_DI,
   input logic [n-1:0]           B_DI,
   input logic [n-1:0]           C_DI,
   output logic [n-1:0]          Sum_DO,
   output logic [n-1:0]          Carry_DO
 );

    generate
      genvar i;
        for (i=0; i<=n-1;i++) 
          begin
            always@(*)
              begin
                Sum_DO[i]= A_DI[i] ^ B_DI[i] ^ C_DI[i];
                Carry_DO[i]=(A_DI[i]&B_DI[i]) | (A_DI[i]&C_DI[i]) | (B_DI[i]&C_DI[i]);
              end
          end
     endgenerate

endmodule


