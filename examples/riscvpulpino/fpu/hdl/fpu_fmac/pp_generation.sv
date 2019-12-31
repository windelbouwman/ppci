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
// Module Name:    pp_generation.sv                                           //
// Project Name:   Private FPU                                                //
// Language:       SystemVerilog                                              //
//                                                                            //
// Description:    pp_generation                                              //
//                                                                            //
//                                                                            //
//                                                                            //
// Revision:        21/06/2017                                                //
// Revision:                                                                  //
//                15/05/2018                                                  //
//                Pass package parameters as default args instead of using    //
//                them directly, improves compatibility with tools like       //  
//                Synopsys Spyglass and DC (GitHub #7) - Torbjørn Viem Ness   //
////////////////////////////////////////////////////////////////////////////////

import fpu_defs_fmac::*;

module pp_generation
#(
   parameter C_MANT = fpu_defs_fmac::C_MANT
)
  (//Inputs
   input logic [C_MANT:0]                            Mant_a_DI,
   input logic [C_MANT:0]                            Mant_b_DI,
   //Outputs
   output logic [12:0] [2*C_MANT+2:0]                Pp_index_DO
   );
   
  logic                                              Sel_xnor_S;
////////////////////////////////////////////////////////////////////////////////
//                        Booth Encoding (13)                                 //
////////////////////////////////////////////////////////////////////////////////

  logic [C_MANT+5:0]                                 Mant_b_D;
  assign Mant_b_D={2'b00,Mant_b_DI,2'b00};//left shift 2 bit.

  logic  [12:0]                                      Sel_1x_S;
  logic  [12:0]                                      Sel_2x_S;
  logic  [12:0]                                      Sel_sign_S;
  generate 
    genvar i;
      for (i=1; i <=13 ; i++)
        begin 
          booth_encoder  booth_encoding (  .Booth_b_DI(Mant_b_D[2*i+1:2*i-1]), .Sel_1x_SO(Sel_1x_S[i-1]), .Sel_2x_SO(Sel_2x_S[i-1]), .Sel_sign_SO(Sel_sign_S[i-1]));
        end
  endgenerate

////////////////////////////////////////////////////////////////////////////////
//                        Booth Selectors (13)                                //
////////////////////////////////////////////////////////////////////////////////

  logic [C_MANT+2:0]                                Mant_a_D;
  assign Mant_a_D = {Mant_a_DI,1'b0};
  logic [12:0] [C_MANT+1:0]                         Booth_pp_D;

  generate 
    genvar l,j;
      for (l=1; l <=13 ; l++)
        begin 
          for (j=1;j<=C_MANT+2;j++)
            begin
              booth_selector  booth_selection (  .Booth_a_DI(Mant_a_D[j:j-1]), .Sel_1x_SI(Sel_1x_S[l-1]), .Sel_2x_SI(Sel_2x_S[l-1]), .Sel_sign_SI(Sel_sign_S[l-1]),.Booth_pp_DO(Booth_pp_D[l-1][j-1]));
            end
        end
  endgenerate


////////////////////////////////////////////////////////////////////////////////
//                        Sign Extension  and adding hot ones                 //
////////////////////////////////////////////////////////////////////////////////

  assign Pp_index_DO[0]={21'h00000,~Sel_sign_S[0],Sel_sign_S[0],Sel_sign_S[0],Booth_pp_D[0]};   //49-bit
  assign Pp_index_DO[1]={20'h00000,1'b1,~Sel_sign_S[1],Booth_pp_D[1],1'b0,Sel_sign_S[0]};       //49-bit
  assign Pp_index_DO[2]={18'h00000,1'b1,~Sel_sign_S[2],Booth_pp_D[2],1'b0,Sel_sign_S[1],2'h0};  //49-bit 
  assign Pp_index_DO[3]={16'h0000,1'b1,~Sel_sign_S[3],Booth_pp_D[3],1'b0,Sel_sign_S[2],4'h0};   //49-bit 
  assign Pp_index_DO[4]={14'h0000,1'b1,~Sel_sign_S[4],Booth_pp_D[4],1'b0,Sel_sign_S[3],6'h00};  //49-bit
  assign Pp_index_DO[5]={12'h000,1'b1,~Sel_sign_S[5],Booth_pp_D[5],1'b0,Sel_sign_S[4],8'h00};   //49-bit
  assign Pp_index_DO[6]={10'h000,1'b1,~Sel_sign_S[6],Booth_pp_D[6],1'b0,Sel_sign_S[5],10'h000}; //49-bit
  assign Pp_index_DO[7]={8'h00,1'b1,~Sel_sign_S[7],Booth_pp_D[7],1'b0,Sel_sign_S[6],12'h000};   //49-bit
  assign Pp_index_DO[8]={6'h00,1'b1,~Sel_sign_S[8],Booth_pp_D[8],1'b0,Sel_sign_S[7],14'h0000};  //49-bit
  assign Pp_index_DO[9]={4'h0,1'b1,~Sel_sign_S[9],Booth_pp_D[9],1'b0,Sel_sign_S[8],16'h0000};   //49-bit
  assign Pp_index_DO[10]={2'h0,1'b1,~Sel_sign_S[10],Booth_pp_D[10],1'b0,Sel_sign_S[9],18'h00000};//49-bit
  assign Pp_index_DO[11]={1'b1,~Sel_sign_S[11],Booth_pp_D[11],1'b0,Sel_sign_S[10],20'h00000};    //49-bit
  assign Pp_index_DO[12]={Booth_pp_D[12],1'b0,Sel_sign_S[11],22'h00000};                         //49-bit

endmodule


