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
// Module Name:    adders.sv                                                  //
// Project Name:   Private FPU                                                //
// Language:       SystemVerilog                                              //
//                                                                            //
// Description:    To produce the final postive results and offer the inputs  //
//                 LZA, including EACA and the incrementer                    //
//                                                                            //
// Revision:       03/04/2018                                                 //
//                 Fixed Torbjørn Viem Ness bugs  and Sticky bit              //
//                                                                            //
// Revision:                                                                  //
//                15/05/2018                                                  //
//                Pass package parameters as default args instead of using    //
//                them directly, improves compatibility with tools like       //  
//                Synopsys Spyglass and DC (GitHub #7) - Torbjørn Viem Ness   //
////////////////////////////////////////////////////////////////////////////////

import fpu_defs_fmac::*;

module adders
#(
   parameter C_MANT = fpu_defs_fmac::C_MANT,
   parameter C_EXP  = fpu_defs_fmac::C_EXP
)
  (

   input  logic [2*C_MANT+1:0]             AL_DI,  // The sum of the former unit  
   input  logic [2*C_MANT+1:0]             BL_DI,  // The carry-out of the former unit
   input  logic                            Sub_SI,
   input  logic [2:0]                      Sign_cor_SI,
   input  logic                            Sign_amt_DI,
   input  logic                            Sft_stop_SI,
   input  logic [C_MANT+3:0]               BH_DI,
   input  logic                            Sign_postalig_DI,
   input  logic [C_EXP+1:0]                Minus_sft_amt_DI, 
   input  logic                            Inf_b_SI,
   input  logic                            Inf_c_SI,
   input  logic                            Zero_b_SI,
   input  logic                            Zero_c_SI, 
   input  logic                            NaN_b_SI,
   input  logic                            NaN_c_SI,
   output logic [3*C_MANT+4:0]             Sum_pos_DO,
   output logic                            Sign_out_DO,
   output logic [3*C_MANT+4:0]             A_LZA_DO,
   output logic [3*C_MANT+4:0]             B_LZA_DO,
   output logic                            Minus_sticky_bit_SO,
   output logic                            Sign_change_SO

   );

////////////////////////////////////////////////////////////////////////////////////  
//                  LSBs                                                          //
////////////////////////////////////////////////////////////////////////////////////

   logic                                  Carry_postcor_D;
   assign Carry_postcor_D = (Sign_amt_DI )? 1'b0 : {(~(| Sign_cor_SI) ^ BL_DI[2*C_MANT+1]) };

   logic  Carry_uninv_LS;
   logic [2*C_MANT+1:0] Sum_uninv_LD;
   assign {Carry_uninv_LS, Sum_uninv_LD} = {1'b0,AL_DI}+{Carry_postcor_D,BL_DI[2*C_MANT:0],Sub_SI};

   logic  Carry_inv_LS;
   logic [2*C_MANT+2:0] Sum_inv_LD;
  
   assign {Carry_inv_LS, Sum_inv_LD} = {1'b1,~AL_DI,1'b1}+{~Carry_postcor_D,~BL_DI[2*C_MANT:0],~Sub_SI,1'b1}+2;  //adding 2                  Sub_SI=0, donot choose this one 

////////////////////////////////////////////////////////////////////////////////////
//                  MSBs                                                          //
////////////////////////////////////////////////////////////////////////////////////
// incrementer
   logic [C_MANT+3:0]               BH_inv_D;
   logic [C_MANT+3:0]               Sum_uninv_HD,  Sum_inv_HD;
   assign  BH_inv_D = ~  BH_DI;
   assign  {Carryout_uninv_HS, Sum_uninv_HD}= Carry_uninv_LS ? {BH_DI+1} : BH_DI;
   assign  {Carryout_inv_HS,Sum_inv_HD}=Carry_inv_LS? BH_inv_D : {BH_inv_D-1};

   logic                            Minus_or_Mant_bc_S;
   assign  Minus_or_Mant_bc_S = ~( Inf_b_SI | Inf_c_SI | Zero_b_SI | Zero_c_SI | NaN_b_SI | NaN_c_SI); //b*c!=0

   logic [3*C_MANT+4:0]             Sub_Minus_D;
   assign  Sub_Minus_D = {{BH_DI[C_MANT+2:0],1'b0} - Minus_or_Mant_bc_S, {47'b0}} ;
   assign Sum_pos_DO =Sft_stop_SI ? {{26'h0} , Sum_uninv_LD[2*C_MANT+1:0]} : 
                     {Sign_amt_DI?  { Sub_SI ? Sub_Minus_D : {BH_DI[C_MANT+2:0], {48'b0}} }: 
                     {Sum_uninv_HD[C_MANT+3] ?  {Sum_inv_HD[C_MANT+2:0] , Sum_inv_LD[2*C_MANT+2:1]} : {Sum_uninv_HD[C_MANT+2:0] , Sum_uninv_LD} } };  
   assign Sign_out_DO = Sign_amt_DI? Sign_postalig_DI : (Sum_uninv_HD[C_MANT+3] ^ Sign_postalig_DI);
   assign Sign_change_SO = Sum_uninv_HD[C_MANT+3];
////////////////////////////////////////////////////////////////////////////////////
//                  Sticky_bit                                                    //
////////////////////////////////////////////////////////////////////////////////////
// for Sign_amt_DI=1'b1, if is difficult to compute combined with other cases.  When addition,   | (b*c) ; when substruction, | (b*c) for rounding excption trunction. 

   assign Minus_sticky_bit_SO = Sign_amt_DI && (Minus_or_Mant_bc_S);

/////////////////////////////////////////////////////////////////////////////////////
//                  to LZA                                                         //
/////////////////////////////////////////////////////////////////////////////////////

   assign A_LZA_DO = Sum_pos_DO ;
   assign B_LZA_DO = {74'h0} ;

endmodule
