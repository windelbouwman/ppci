// Copyright 2017, 2018 ETH Zurich and University of Bologna.
// Copyright and related rights are licensed under the Solderpad Hardware
// License, Version 0.51 (the "License"); you may not use this file except in
// compliance with the License.  You may obtain a copy of the License at
// http://solderpad.org/licenses/SHL-0.51. Unless required by applicable law
// or agreed to in writing, software, hardware and materials distributed under
// this License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
// CONDITIONS OF ANY KIND, either express or implied. See the License for the
// specific language governing permissions and limitations under the License.
////////////////////////////////////////////////////////////////////////////////
// Company:        IIS @ ETHZ - Federal Institute of Technology               //
//                                                                            //
// Engineers:      Lukas Mueller -- lukasmue@student.ethz.ch                  //
//                 Thomas Gautschi -- gauthoma@student.ethz.ch                //
//                                                                            //
// Additional contributions by:                                               //
//                  Lei Li       --lile@iis.ee.ethz.ch                        //
//                 Torbjørn Viem Ness -- torbjovn@stud.ntnu.no                //
//                                                                            //
//                                                                            //
// Create Date:    06/10/2014                                                 //
// Design Name:    FPU                                                        //
// Module Name:    fpexc.sv                                                   //
// Project Name:   Private FPU                                                //
// Language:       SystemVerilog                                              //
//                                                                            //
// Description:    Handles all exceptions and sets output and flags           //
//                 accordingly.                                               //
//                                                                            //
//                                                                            //
// Revision:                                                                  //
//                12/09/2012                                                  //
//                Fixed some wrong flags by Lei Li                            //
// Revision:                                                                  //
//                15/05/2018                                                  //
//                Pass package parameters as default args instead of using    //
//                them directly, improves compatibility with tools like       //  
//                Synopsys Spyglass and DC (GitHub #7) - Torbjørn Viem Ness   //
////////////////////////////////////////////////////////////////////////////////

import fpu_defs::*;

module fpexc
#(
   parameter C_MANT_ZERO   = fpu_defs::C_MANT_ZERO,
   parameter C_EXP_ZERO    = fpu_defs::C_EXP_ZERO,
   parameter C_EXP_INF     = fpu_defs::C_EXP_INF,

   parameter C_EXP         = fpu_defs::C_EXP,
   parameter C_MANT        = fpu_defs::C_MANT,

   parameter C_CMD         = fpu_defs::C_CMD,

   parameter C_FPU_ADD_CMD = fpu_defs::C_FPU_ADD_CMD,
   parameter C_FPU_SUB_CMD = fpu_defs::C_FPU_SUB_CMD,
   parameter C_FPU_MUL_CMD = fpu_defs::C_FPU_MUL_CMD,
   parameter C_FPU_I2F_CMD = fpu_defs::C_FPU_I2F_CMD,
   parameter C_FPU_F2I_CMD = fpu_defs::C_FPU_F2I_CMD
)
  (//Input
   input logic [C_MANT:0]   Mant_a_DI,
   input logic [C_MANT:0]   Mant_b_DI,
   input logic [C_EXP-1:0]  Exp_a_DI,
   input logic [C_EXP-1:0]  Exp_b_DI,
   input logic              Sign_a_DI,
   input logic              Sign_b_DI,

   input logic [C_MANT:0]   Mant_norm_DI,
   input logic [C_EXP-1:0]  Exp_res_DI,

   input logic [C_CMD-1:0]  Op_SI,

   input logic Mant_rounded_SI,
   input logic Exp_OF_SI,
   input logic Exp_UF_SI,

   input logic OF_SI,
   input logic UF_SI,
   input logic Zero_SI,
   input logic IX_SI,
   input logic IV_SI,
   input logic Inf_SI,

   //Output
   output logic Exp_toZero_SO,
   output logic Exp_toInf_SO,
   output logic Mant_toZero_SO,

   output logic OF_SO,
   output logic UF_SO,
   output logic Zero_SO,
   output logic IX_SO,
   output logic IV_SO,
   output logic Inf_SO
   ) ;


   /////////////////////////////////////////////////////////////////////////////
   // preliminary checks for infinite/zero operands                           //
   /////////////////////////////////////////////////////////////////////////////

   logic        Inf_a_S;
   logic        Inf_b_S;
   logic        Zero_a_S;
   logic        Zero_b_S;
   logic        NaN_a_S;
   logic        NaN_b_S;

   logic        Mant_zero_S;

   assign Inf_a_S = (Exp_a_DI == C_EXP_INF) & (Mant_a_DI[C_MANT-1:0] == C_MANT_NoHB_ZERO);
   assign Inf_b_S = (Exp_b_DI == C_EXP_INF) & (Mant_b_DI[C_MANT-1:0] == C_MANT_NoHB_ZERO);

   assign Zero_a_S = (Exp_a_DI == C_EXP_ZERO) & (Mant_a_DI == C_MANT_ZERO);
   assign Zero_b_S = (Exp_b_DI == C_EXP_ZERO) & (Mant_b_DI == C_MANT_ZERO);

   assign NaN_a_S = (Exp_a_DI == C_EXP_INF) & (Mant_a_DI[C_MANT-1:0] != C_MANT_NoHB_ZERO);
   assign NaN_b_S = (Exp_b_DI == C_EXP_INF) & (Mant_b_DI[C_MANT-1:0] != C_MANT_NoHB_ZERO);

   assign Mant_zero_S = Mant_norm_DI == C_MANT_ZERO;


   /////////////////////////////////////////////////////////////////////////////
   // flag assignments                                                        //
   /////////////////////////////////////////////////////////////////////////////

   assign OF_SO   = (Op_SI == C_FPU_F2I_CMD) ? OF_SI : (Exp_OF_SI & ~Mant_zero_S) | (~IV_SO & (Inf_a_S ^ Inf_b_S) & (Op_SI != C_FPU_I2F_CMD));
   assign UF_SO   = (Op_SI == C_FPU_F2I_CMD) ? UF_SI : Exp_UF_SI & Mant_rounded_SI;
   assign Zero_SO = (Op_SI == C_FPU_F2I_CMD) ? Zero_SI : (Mant_zero_S & ~IV_SO);
   assign IX_SO   = (Op_SI == C_FPU_F2I_CMD) ? IX_SI : Mant_rounded_SI | OF_SO;

   always_comb //check operation validity
     begin
        IV_SO = 1'b0;
        case (Op_SI)
          C_FPU_ADD_CMD, C_FPU_SUB_CMD : //input logic already adjusts operands
            begin
               if (((Inf_a_S & Inf_b_S) & (Sign_a_DI ^ Sign_b_DI)) | NaN_a_S | NaN_b_S)
                 IV_SO = 1'b1;
            end
          C_FPU_MUL_CMD :
            begin
            if (((Inf_a_S & Zero_b_S) | (Inf_b_S & Zero_a_S)) | NaN_a_S | NaN_b_S)
              IV_SO = 1'b1;
            end
          C_FPU_F2I_CMD :
            IV_SO = IV_SI;
        endcase
     end

   logic Inf_temp_S;
   always_comb //check infinite outputs
     begin
        Inf_temp_S = 1'b0;
        case(Op_SI)
          C_FPU_ADD_CMD, C_FPU_SUB_CMD : //input logic already adjusts operands
            if ((Inf_a_S ^ Inf_b_S) | ((Inf_a_S & Inf_b_S) & ~(Sign_a_DI ^ Sign_b_DI)))
              Inf_temp_S = 1'b1;
          C_FPU_MUL_CMD :
            if ((Inf_a_S & ~Zero_b_S) | (Inf_b_S & ~Zero_a_S))
              Inf_temp_S = 1'b1;
        endcase // case (Op_SI)
     end // always_comb begin

   assign Inf_SO = (Op_SI == C_FPU_F2I_CMD) ? Inf_SI : Inf_temp_S | (Exp_OF_SI & ~Mant_zero_S);

   /////////////////////////////////////////////////////////////////////////////
   // flags/signals for result manipulation                                   //
   /////////////////////////////////////////////////////////////////////////////
   assign Exp_toZero_SO =(Op_SI == C_FPU_I2F_CMD) ? (Zero_a_S & ~Sign_a_DI) : Exp_UF_SI | (Mant_zero_S & ~Exp_toInf_SO);
   assign Exp_toInf_SO = (OF_SO | IV_SO);
   assign Mant_toZero_SO = Inf_SO;

endmodule // fpexc
