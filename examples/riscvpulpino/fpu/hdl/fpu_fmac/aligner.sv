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
// Module Name:    aligner.sv                                                 //
// Project Name:   Private FPU                                                //
// Language:       SystemVerilog                                              //
//                                                                            //
// Description:    To align Mant_a_DI                                         //
//                                                                            //
//                                                                            //
// Revision:       03/04/2018                                                 //
//                 Fixed Torbjørn Viem Ness bugs  and Sticky bit              //
// Revision:       19/04/2018                                                 //
//                 Sticky bit for substraction                                //
// Revision:                                                                  //
//                15/05/2018                                                  //
//                Pass package parameters as default args instead of using    //
//                them directly, improves compatibility with tools like       //  
//                Synopsys Spyglass and DC (GitHub #7) - Torbjørn Viem Ness   //
////////////////////////////////////////////////////////////////////////////////

import fpu_defs_fmac::*;

module aligner
#(
   parameter C_EXP  = fpu_defs_fmac::C_EXP,
   parameter C_MANT = fpu_defs_fmac::C_MANT,
   parameter C_BIAS = fpu_defs_fmac::C_BIAS
)
  (//Inputs
   input logic [C_EXP-1:0]                         Exp_a_DI,
   input logic [C_EXP-1:0]                         Exp_b_DI,
   input logic [C_EXP-1:0]                         Exp_c_DI,
   input logic [C_MANT:0]                          Mant_a_DI,
   input logic                                     Sign_a_DI,
   input logic                                     Sign_b_DI,
   input logic                                     Sign_c_DI,
   input logic [2*C_MANT+2:0]                      Pp_sum_DI,
   input logic [2*C_MANT+2:0]                      Pp_carry_DI,
   input logic                                     Sign_change_SI, //from adders
   //Outputs
   output logic                                    Sub_SO,
   output logic [74:0]                             Mant_postalig_a_DO,
   output logic [C_EXP+1:0]                        Exp_postalig_DO,
   output logic                                    Sign_postalig_DO,
   output logic                                    Sign_amt_DO,
   output logic                                    Sft_stop_SO,
   output logic [2*C_MANT+2:0]                     Pp_sum_postcal_DO,
   output logic [2*C_MANT+2:0]                     Pp_carry_postcal_DO,
   output logic [C_EXP+1:0]                        Minus_sft_amt_DO,
   output logic                                    Mant_sticky_sft_out_SO 
   );

 logic [C_EXP+1:0]                                Exp_dif_D;
 logic [C_EXP+1:0]                                Sft_amt_D;


 assign Sub_SO = Sign_a_DI ^ Sign_b_DI ^ Sign_c_DI;
 assign Exp_dif_D = Exp_a_DI - Exp_b_DI - Exp_c_DI + C_BIAS;
 assign Sft_amt_D = Exp_b_DI + Exp_c_DI - Exp_a_DI - C_BIAS + 27; //Two bits are added including sign bit
 assign Minus_sft_amt_DO = Exp_a_DI - Exp_b_DI - Exp_c_DI + C_BIAS -27; // The right shift amount when Sign_amt_DO =1'b1
 assign Sign_amt_DO = Sft_amt_D[C_EXP+1];         //a>>b*c
 logic                                            Sft_stop_S;       // right shift larger 74
 assign Sft_stop_S = (~Sft_amt_D[C_EXP+1])&&(Sft_amt_D[C_EXP:0]>=74);  //For rounding
 assign Sft_stop_SO = Sft_stop_S;
 // The exponent after alignment
 assign Exp_postalig_DO = Sft_amt_D[C_EXP+1] ? Exp_a_DI : {Exp_b_DI + Exp_c_DI - C_BIAS + 27};

 logic [73:0]                                     Mant_postalig_a_D;
 logic [C_MANT :0]                                Bit_sftout_D;
 assign  {Mant_postalig_a_D, Bit_sftout_D} = {Mant_a_DI,74'h0}>>{Sft_stop_S?0 : Sft_amt_D};     //Alignment

 logic [C_MANT:0]                                 Mant_a_com_DI;
 assign Mant_a_com_DI=~Mant_a_DI+1;
 logic [C_MANT :0]                                Bit_sftout_com_D;
 assign Bit_sftout_com_D=~Bit_sftout_D+1;
 assign  Mant_sticky_sft_out_SO =(Sub_SO&&(~Sign_change_SI)) ? {Sft_stop_S ? (| (Mant_a_com_DI)): (| (Bit_sftout_com_D)) } : {Sft_stop_S ? (| Mant_a_DI) : (| Bit_sftout_D)};
// another case for b*c>>a
 assign   Mant_postalig_a_DO =Sft_amt_D[C_EXP+1] ? {1'b0, Mant_a_DI, 50'h0}:                //Sft_amt_D==1'b1
                             { Sft_stop_S? 75'h0 :{ Sub_SO ? {1'b1,~Mant_postalig_a_D}:{1'b0,Mant_postalig_a_D} } };

 assign Sign_postalig_DO = Sft_amt_D[C_EXP+1] ? Sign_a_DI: Sign_b_DI ^ Sign_c_DI;
 assign Pp_sum_postcal_DO = Sft_amt_D[C_EXP+1] ? '0 : Pp_sum_DI;
 assign Pp_carry_postcal_DO =  Sft_amt_D[C_EXP+1] ? '0 : Pp_carry_DI;

endmodule
