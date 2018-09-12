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
// Engineers:      Lei Li -- lile@iis.ee.ethz.ch                              //
//                                                                            //
// Additional contributions by:                                               //
//                 Torbjørn Viem Ness -- torbjovn@stud.ntnu.no                //
//                                                                            //
//                                                                            //
//                                                                            //
// Create Date:    01/06/2017                                                 //
// Design Name:    fmac                                                       //
// Module Name:    fmac.sv                                                    //
// Project Name:   Private FPU                                                //
// Language:       SystemVerilog                                              //
//                                                                            //
// Description:    The top module of fmac                                     //
// function:       Result_DO=Operand_a_DI+Operand_b_DI*Operand_c_DI           //
//                                                                            //
// Revision:       07/07/2017                                                 //
// Revision:       04/09/2017                                                 //
//                 No_one_S was added  by Lei Li                              //
// Revision:       03/04/2018                                                 //
//                 Fixed Torbjørn Viem Ness bugs  and Sticky bit              //
// Revision:                                                                  //
//                15/05/2018                                                  //
//                Pass package parameters as default args instead of using    //
//                them directly, improves compatibility with tools like       //  
//                Synopsys Spyglass and DC (GitHub #7) - Torbjørn Viem Ness   //
////////////////////////////////////////////////////////////////////////////////

import fpu_defs_fmac::*;

module fmac
#(
   parameter C_EXP           = fpu_defs_fmac::C_EXP,
   parameter C_MANT          = fpu_defs_fmac::C_MANT,
   parameter C_OP            = fpu_defs_fmac::C_OP,
   parameter C_RM            = fpu_defs_fmac::C_RM,
   parameter C_LEADONE_WIDTH = fpu_defs_fmac::C_LEADONE_WIDTH
)
(
   //Inputs
   input logic [C_OP-1:0]   Operand_a_DI,
   input logic [C_OP-1:0]   Operand_b_DI,
   input logic [C_OP-1:0]   Operand_c_DI,
   input logic [C_RM-1:0]   RM_SI,    //Rounding Mode
   //Output-result
   output logic [31:0]      Result_DO,
   //Output-Flags
   output logic             Exp_OF_SO,
   output logic             Exp_UF_SO,
   output logic             Flag_NX_SO,
   output logic             Flag_IV_SO
 );

  logic [C_MANT-1:0]        Mant_res_DO;
  logic [C_EXP-1:0]         Exp_res_DO;
  logic                     Sign_res_DO;
  logic                     DeN_a_S, Sub_S, Sign_postalig_D, Sign_amt_D, Sft_stop_S, Sign_out_D;


  assign Result_DO =   {Sign_res_DO,Exp_res_DO, Mant_res_DO};

   logic                   Sign_a_D;
   logic                   Sign_b_D;
   logic                   Sign_c_D;
   logic [C_EXP-1:0]       Exp_a_D;
   logic [C_EXP-1:0]       Exp_b_D;
   logic [C_EXP-1:0]       Exp_c_D;
   logic [C_MANT:0]        Mant_a_D;
   logic [C_MANT:0]        Mant_b_D;
   logic [C_MANT:0]        Mant_c_D;
   logic                   Inf_a_S;
   logic                   Inf_b_S;
   logic                   Inf_c_S;
   logic                   NaN_a_S;
   logic                   NaN_b_S;
   logic                   NaN_c_S;

preprocess_fmac  precess_U0
 (
   .Operand_a_DI          (Operand_a_DI       ),
   .Operand_b_DI          (Operand_b_DI       ),
   .Operand_c_DI          (Operand_c_DI       ),
   .Exp_a_DO              (Exp_a_D            ),
   .Mant_a_DO             (Mant_a_D           ),
   .Sign_a_DO             (Sign_a_D           ),
   .Exp_b_DO              (Exp_b_D            ),
   .Mant_b_DO             (Mant_b_D           ),
   .Sign_b_DO             (Sign_b_D           ),
   .Exp_c_DO              (Exp_c_D            ),
   .Mant_c_DO             (Mant_c_D           ),
   .Sign_c_DO             (Sign_c_D           ),
   .DeN_a_SO              (DeN_a_S            ),
   .Inf_a_SO              (Inf_a_S            ),
   .Inf_b_SO              (Inf_b_S            ),
   .Inf_c_SO              (Inf_c_S            ),
   .Zero_a_SO             (Zero_a_S           ),
   .Zero_b_SO             (Zero_b_S           ),
   .Zero_c_SO             (Zero_c_S           ),
   .NaN_a_SO              (NaN_a_S            ),
   .NaN_b_SO              (NaN_b_S            ),
   .NaN_c_SO              (NaN_c_S            )
   );

 logic [12:0] [2*C_MANT+2:0]                 Pp_index_D;
 pp_generation  pp_gneration_U0
 (
   .Mant_a_DI             (Mant_b_D          ),
   .Mant_b_DI             (Mant_c_D          ),
   .Pp_index_DO           (Pp_index_D        )
 );

   logic [2*C_MANT+2:0]                      Pp_sum_D;
   logic [2*C_MANT+2:0]                      Pp_carry_D;
   logic                                     MSB_cor_D;
 wallace   wallace_U0
 ( 
   .Pp_index_DI           (Pp_index_D        ),
   .Pp_sum_DO             (Pp_sum_D          ),
   .Pp_carry_DO           (Pp_carry_D        ),
   .MSB_cor_DO            (MSB_cor_D         )
 );

 logic [74:0]                               Mant_postalig_a_D;
 logic signed [C_EXP+1:0]                   Exp_postalig_D;
 logic [2*C_MANT+2:0]                       Pp_sum_postcal_D;
 logic [2*C_MANT+2:0]                       Pp_carry_postcal_D;
 logic [C_EXP+1:0]                          Minus_sft_amt_D; 
 logic                                      Mant_sticky_sft_out_S;
 logic                                      Sign_change_S;
 aligner  aligner_U0
 (
   .Exp_a_DI              (Exp_a_D          ),
   .Exp_b_DI              (Exp_b_D          ),
   .Mant_a_DI             (Mant_a_D         ),
   .Exp_c_DI              (Exp_c_D          ),

   .Sign_a_DI             (Sign_a_D         ),
   .Sign_b_DI             (Sign_b_D         ),
   .Sign_c_DI             (Sign_c_D         ),
   .Pp_sum_DI             (Pp_sum_D         ),
   .Pp_carry_DI           (Pp_carry_D       ),
   .Sign_change_SI        (Sign_change_S    ),
   .Sub_SO                (Sub_S            ),
   .Mant_postalig_a_DO    (Mant_postalig_a_D),
   .Exp_postalig_DO       (Exp_postalig_D   ),
   .Sign_postalig_DO      (Sign_postalig_D  ),
   .Sign_amt_DO           (Sign_amt_D       ),
   .Sft_stop_SO           (Sft_stop_S       ),
   .Pp_sum_postcal_DO     (Pp_sum_postcal_D ),
   .Pp_carry_postcal_DO   (Pp_carry_postcal_D),
   .Minus_sft_amt_DO      (Minus_sft_amt_D   ),
   .Mant_sticky_sft_out_SO (Mant_sticky_sft_out_S)
 );

// 48-bit CSA. In fact the bit width is 49 bits including sign bit. After this CSA, EDCA is used to produce the correct sum and the carry out bit.
   logic [2*C_MANT+1:0]                      Csa_sum_D;
   logic [2*C_MANT+1:0]                      Csa_carry_D;
CSA   #(2*C_MANT+2)  CSA_U0
 ( 
   .A_DI                  (Mant_postalig_a_D[2*C_MANT+1:0]), 
   .B_DI                  ({Pp_sum_postcal_D[2*C_MANT+1:0]}       ),
   .C_DI                  ({Pp_carry_postcal_D[2*C_MANT:0],1'b0}  ), 
   .Sum_DO                (Csa_sum_D                      ), 
   .Carry_DO              (Csa_carry_D                    )
 );

// The correction based sign extension is included in adders.  
 logic [73:0]                               Sum_pos_D;
 logic [3*C_MANT+4:0]                       A_LZA_D;
 logic [3*C_MANT+4:0]                       B_LZA_D;
 logic                                      Minus_sticky_bit_S;
adders adders_U0
 (
  .AL_DI                   (Csa_sum_D        ),
  .BL_DI                   (Csa_carry_D      ),
  .Sub_SI                  (Sub_S            ),
  .Sign_cor_SI             ({MSB_cor_D, Pp_carry_postcal_D[2*C_MANT+2],{Pp_sum_postcal_D[2*C_MANT+2] && Pp_carry_postcal_D[2*C_MANT+1]}}),
  .Sign_amt_DI             (Sign_amt_D       ), 
  .Sft_stop_SI             (Sft_stop_S       ),
  .BH_DI                   (Mant_postalig_a_D[3*C_MANT+5:2*C_MANT+2]),
  .Sign_postalig_DI        (Sign_postalig_D  ),
  .Inf_b_SI                (Inf_b_S          ),
  .Inf_c_SI                (Inf_c_S          ),
  .Zero_b_SI               (Zero_b_S         ),
  .Zero_c_SI               (Zero_c_S         ),
  .NaN_b_SI                (NaN_b_S          ),
  .NaN_c_SI                (NaN_c_S          ),
  .Minus_sft_amt_DI        (Minus_sft_amt_D  ),
  .Sum_pos_DO              (Sum_pos_D        ),
  .Sign_out_DO             (Sign_out_D       ),
  .A_LZA_DO                (A_LZA_D          ),
  .B_LZA_DO                (B_LZA_D          ),
  .Minus_sticky_bit_SO     (Minus_sticky_bit_S),
  .Sign_change_SO          (Sign_change_S    )
 );
 

 logic [C_LEADONE_WIDTH-1:0]                Leading_one_D;
 logic                                      No_one_S;

LZA #(3*C_MANT+5) LZA_U0
  (
   .A_DI                   (A_LZA_D       ),
   .B_DI                   (B_LZA_D       ), 
   .Leading_one_DO         (Leading_one_D ),
   .No_one_SO              (No_one_S      ) 
   );


 fpu_norm_fmac  fpu_norm_U0
  (
   .Mant_in_DI            (Sum_pos_D          ),
   .Exp_in_DI             (Exp_postalig_D     ),
   .Sign_in_DI            (Sign_out_D         ),
   .Leading_one_DI        (Leading_one_D      ), 
   .No_one_SI             (No_one_S           ),
   .Sign_amt_DI           (Sign_amt_D         ), 
   .Sub_SI                (Sub_S              ),
   .Exp_a_DI              (Operand_a_DI[C_OP-2:C_MANT]), //exponent
   .Mant_a_DI             (Mant_a_D           ),
   .Sign_a_DI             (Sign_a_D           ),
   .DeN_a_SI              (DeN_a_S            ),
   .RM_SI                 (RM_SI              ),    //Rounding Mode
   .Inf_a_SI              (Inf_a_S            ),
   .Inf_b_SI              (Inf_b_S            ),
   .Inf_c_SI              (Inf_c_S            ),
   .Zero_a_SI             (Zero_a_S           ),
   .Zero_b_SI             (Zero_b_S           ),
   .Zero_c_SI             (Zero_c_S           ),
   .NaN_a_SI              (NaN_a_S            ),
   .NaN_b_SI              (NaN_b_S            ),
   .NaN_c_SI              (NaN_c_S            ),
   .Mant_sticky_sft_out_SI (Mant_sticky_sft_out_S),
   .Minus_sticky_bit_SI   (Minus_sticky_bit_S ),
   .Mant_res_DO           (Mant_res_DO        ),
   .Exp_res_DO            (Exp_res_DO         ),
   .Sign_res_DO           (Sign_res_DO        ),
   .Exp_OF_SO             (Exp_OF_SO          ),
   .Exp_UF_SO             (Exp_UF_SO          ),
   .Flag_Inexact_SO       (Flag_NX_SO         ),
   .Flag_Invalid_SO       (Flag_IV_SO         )
   );

endmodule
