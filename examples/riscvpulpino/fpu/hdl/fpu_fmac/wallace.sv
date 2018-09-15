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
// Engineers:      Lei Li  lile@iis.ee.ethz.ch                                //
//                                                                            //
// Additional contributions by:                                               //
//                 Torbjørn Viem Ness -- torbjovn@stud.ntnu.no                //
//                                                                            //
//                                                                            //
// Create Date:    01/12/2016                                                 //
// Design Name:    fmac                                                       //
// Module Name:    wallace.sv                                                 //
// Project Name:   Private FPU                                                //
// Language:       SystemVerilog                                              //
//                                                                            //
// Description:    Wallace Tree                                               //
//                                                                            //
//                                                                            //
//                                                                            //
// Revision:       23/06/2017                                                 //
// Revision:                                                                  //
//                15/05/2018                                                  //
//                Pass package parameters as default args instead of using    //
//                them directly, improves compatibility with tools like       //  
//                Synopsys Spyglass and DC (GitHub #7) - Torbjørn Viem Ness   //
////////////////////////////////////////////////////////////////////////////////

import fpu_defs_fmac::*;

module wallace
#(
   parameter C_MANT = fpu_defs_fmac::C_MANT
)
  (
   input logic [12:0] [2*C_MANT+2:0]                Pp_index_DI,
   output logic [2*C_MANT+2:0]                      Pp_sum_DO,
   output logic [2*C_MANT+2:0]                      Pp_carry_DO,
   output logic                                     MSB_cor_DO
   );

   logic [2*C_MANT+2:0]                             CSA_u0_Sum_DI;
   logic [2*C_MANT+2:0]                             CSA_u0_Carry_DI;
   logic [2*C_MANT+2:0]                             CSA_u1_Sum_DI;
   logic [2*C_MANT+2:0]                             CSA_u1_Carry_DI;
   logic [2*C_MANT+2:0]                             CSA_u2_Sum_DI;
   logic [2*C_MANT+2:0]                             CSA_u2_Carry_DI;
   logic [2*C_MANT+2:0]                             CSA_u3_Sum_DI;
   logic [2*C_MANT+2:0]                             CSA_u3_Carry_DI;
   logic [2*C_MANT+2:0]                             CSA_u4_Sum_DI;
   logic [2*C_MANT+2:0]                             CSA_u4_Carry_DI;
   logic [2*C_MANT+2:0]                             CSA_u5_Sum_DI;
   logic [2*C_MANT+2:0]                             CSA_u5_Carry_DI;
   logic [2*C_MANT+2:0]                             CSA_u6_Sum_DI;
   logic [2*C_MANT+2:0]                             CSA_u6_Carry_DI;
   logic [2*C_MANT+2:0]                             CSA_u7_Sum_DI;
   logic [2*C_MANT+2:0]                             CSA_u7_Carry_DI;
   logic [2*C_MANT+2:0]                             CSA_u8_Sum_DI;
   logic [2*C_MANT+2:0]                             CSA_u8_Carry_DI;
   logic [2*C_MANT+2:0]                             CSA_u9_Sum_DI;
   logic [2*C_MANT+2:0]                             CSA_u9_Carry_DI;
   
   CSA  #(2*C_MANT+3)  CSA_U0  ( .A_DI(Pp_index_DI[0]),.B_DI(Pp_index_DI[1]),.C_DI(Pp_index_DI[2]), .Sum_DO(CSA_u0_Sum_DI), .Carry_DO(CSA_u0_Carry_DI));
   CSA  #(2*C_MANT+3)  CSA_U1  ( .A_DI(Pp_index_DI[3]),.B_DI(Pp_index_DI[4]),.C_DI(Pp_index_DI[5]), .Sum_DO(CSA_u1_Sum_DI), .Carry_DO(CSA_u1_Carry_DI));
   CSA  #(2*C_MANT+3)  CSA_U2  ( .A_DI(Pp_index_DI[6]),.B_DI(Pp_index_DI[7]),.C_DI(Pp_index_DI[8]), .Sum_DO(CSA_u2_Sum_DI), .Carry_DO(CSA_u2_Carry_DI));
   CSA  #(2*C_MANT+3)  CSA_U3  ( .A_DI(Pp_index_DI[9]),.B_DI(Pp_index_DI[10]),.C_DI(Pp_index_DI[11]),.Sum_DO(CSA_u3_Sum_DI), .Carry_DO(CSA_u3_Carry_DI));
   CSA  #(2*C_MANT+3)  CSA_U4  ( .A_DI(CSA_u0_Sum_DI),.B_DI({CSA_u0_Carry_DI[2*C_MANT+1:0],1'b0}),.C_DI(CSA_u1_Sum_DI),.Sum_DO(CSA_u4_Sum_DI), .Carry_DO(CSA_u4_Carry_DI));
   CSA  #(2*C_MANT+3)  CSA_U5  ( .A_DI({CSA_u1_Carry_DI[2*C_MANT+1:0],1'b0}),.B_DI({CSA_u2_Carry_DI[2*C_MANT+1:0],1'b0}),.C_DI(CSA_u2_Sum_DI),.Sum_DO(CSA_u5_Sum_DI), .Carry_DO(CSA_u5_Carry_DI));
   CSA  #(2*C_MANT+3)  CSA_U6  ( .A_DI(CSA_u3_Sum_DI),.B_DI({CSA_u3_Carry_DI[2*C_MANT+1:0],1'b0}),.C_DI(CSA_u4_Sum_DI),.Sum_DO(CSA_u6_Sum_DI), .Carry_DO(CSA_u6_Carry_DI));
   CSA  #(2*C_MANT+3)  CSA_U7  ( .A_DI({CSA_u4_Carry_DI[2*C_MANT+1:0],1'b0}),.B_DI({CSA_u5_Carry_DI[2*C_MANT+1:0],1'b0}),.C_DI(CSA_u5_Sum_DI),.Sum_DO(CSA_u7_Sum_DI), .Carry_DO(CSA_u7_Carry_DI));
   CSA  #(2*C_MANT+3)  CSA_U8  ( .A_DI(CSA_u6_Sum_DI),.B_DI({CSA_u6_Carry_DI[2*C_MANT+1:0],1'b0}),.C_DI(CSA_u7_Sum_DI),.Sum_DO(CSA_u8_Sum_DI), .Carry_DO(CSA_u8_Carry_DI));
   CSA  #(2*C_MANT+3)  CSA_U9  ( .A_DI({CSA_u7_Carry_DI[2*C_MANT+1:0],1'b0}),.B_DI({CSA_u8_Carry_DI[2*C_MANT+1:0],1'b0}),.C_DI(CSA_u8_Sum_DI),.Sum_DO(CSA_u9_Sum_DI), .Carry_DO(CSA_u9_Carry_DI));
   CSA  #(2*C_MANT+3)  CSA_U10 ( .A_DI(CSA_u9_Sum_DI),.B_DI({CSA_u9_Carry_DI[2*C_MANT+1:0],1'b0}),.C_DI(Pp_index_DI[12]),.Sum_DO(Pp_sum_DO), .Carry_DO(Pp_carry_DO));
   assign  MSB_cor_DO = CSA_u9_Carry_DI[2*C_MANT+2] | CSA_u8_Carry_DI[2*C_MANT+2] | CSA_u7_Carry_DI[2*C_MANT+2] | CSA_u6_Carry_DI[2*C_MANT+2] | CSA_u5_Carry_DI[2*C_MANT+2]  | CSA_u4_Carry_DI[2*C_MANT+2] | CSA_u3_Carry_DI[2*C_MANT+2];

endmodule


