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
//                                                                            //
// Additional contributions by:                                               //
//                 Torbjørn Viem Ness -- torbjovn@stud.ntnu.no                //
//                                                                            //
//                                                                            //
// Create Date:    06/10/2014                                                 //
// Design Name:    FPU                                                        //
// Module Name:    fpu_add.sv                                                 //
// Project Name:   Private FPU                                                //
// Language:       SystemVerilog                                              //
//                                                                            //
// Description:    Floating point addition/subtraction                        //
//                 Adjusts exponents, adds/subtracts mantissas                //
//                 for Normalizer/Rounding stage                              //
//                                                                            //
// Revision:                                                                  //
//                15/05/2018                                                  //
//                Pass package parameters as default args instead of using    //
//                them directly, improves compatibility with tools like       //  
//                Synopsys Spyglass and DC (GitHub #7) - Torbjørn Viem Ness   //
////////////////////////////////////////////////////////////////////////////////

import fpu_defs::*;

module fpu_add
#(
   parameter C_EXP_PRENORM  = fpu_defs::C_EXP_PRENORM,
   parameter C_MANT_PRENORM = fpu_defs::C_MANT_PRENORM,
   parameter C_MANT_SHIFTED = fpu_defs::C_MANT_SHIFTED,
   parameter C_MANT_SHIFTIN = fpu_defs::C_MANT_SHIFTIN,
   parameter C_MANT_ADDOUT  = fpu_defs::C_MANT_ADDOUT,
   parameter C_MANT_ADDIN   = fpu_defs::C_MANT_ADDIN,
   parameter C_EXP          = fpu_defs::C_EXP,
   parameter C_MANT         = fpu_defs::C_MANT
)
  (//Input
   input logic               Sign_a_DI,
   input logic               Sign_b_DI,
   input logic [C_EXP-1:0]   Exp_a_DI,
   input logic [C_EXP-1:0]   Exp_b_DI,
   input logic [C_MANT:0]    Mant_a_DI ,
   input logic [C_MANT:0]    Mant_b_DI,

   //Output
   output logic                              Sign_prenorm_DO,
   output logic signed [C_EXP_PRENORM-1 :0]  Exp_prenorm_DO,
   output logic        [C_MANT_PRENORM-1:0]  Mant_prenorm_DO
   );

   //Operand components
   logic              Sign_a_D;
   logic              Sign_b_D;
   logic [C_EXP-1:0]  Exp_a_D;
   logic [C_EXP-1:0]  Exp_b_D;
   logic [C_MANT:0]   Mant_a_D;
   logic [C_MANT:0]   Mant_b_D;

   //Post-Normalizer result
   logic              Sign_norm_D;

   /////////////////////////////////////////////////////////////////////////////
   // Assign Inputs
   /////////////////////////////////////////////////////////////////////////////
   assign Sign_a_D = Sign_a_DI;
   assign Sign_b_D = Sign_b_DI;
   assign Exp_a_D  = Exp_a_DI;
   assign Exp_b_D  = Exp_b_DI;
   assign Mant_a_D = Mant_a_DI;
   assign Mant_b_D = Mant_b_DI;

   /////////////////////////////////////////////////////////////////////////////
   // Exponent operations
   /////////////////////////////////////////////////////////////////////////////

   logic             Exp_agtb_S;
   logic             Exp_equal_S;
   logic [C_EXP-1:0] Exp_diff_D;
   logic [C_EXP-1:0] Exp_prenorm_D;

   assign Exp_agtb_S  = Exp_a_D > Exp_b_D;
   assign Exp_equal_S = Exp_diff_D == 0;

   always_comb
     begin
        if (Exp_agtb_S)
          begin
             Exp_diff_D    = Exp_a_D - Exp_b_D;
             Exp_prenorm_D = Exp_a_D;
          end
        else
          begin
             Exp_diff_D    = Exp_b_D - Exp_a_D;
             Exp_prenorm_D = Exp_b_D;
          end
     end // always_comb

   /////////////////////////////////////////////////////////////////////////////
   // Mantissa operations
   /////////////////////////////////////////////////////////////////////////////

   logic                       Mant_agtb_S;
   logic [C_MANT_SHIFTIN-1:0]  Mant_shiftIn_D;
   logic [C_MANT_SHIFTED-1:0]  Mant_shifted_D;
   logic                       Mant_sticky_D;
   logic [C_MANT_SHIFTED-1:0]  Mant_unshifted_D;

   //Main Adder
   logic [C_MANT_ADDIN-1:0]   Mant_addInA_D;
   logic [C_MANT_ADDIN-1:0]   Mant_addInB_D;
   logic [C_MANT_ADDOUT-1:0]  Mant_addOut_D;

   logic [C_MANT_PRENORM-1:0] Mant_prenorm_D;

   //Inversion and carry for Subtraction
   logic        Mant_addCarryIn_D;
   logic        Mant_invA_S;
   logic        Mant_invB_S;

   logic        Subtract_S;

   //Shift the number with the smaller exponent to the right
   assign Mant_agtb_S      = Mant_a_D > Mant_b_D;
   assign Mant_unshifted_D = {(Exp_agtb_S ? Mant_a_D : Mant_b_D), 3'b0};
   assign Mant_shiftIn_D   = {(Exp_agtb_S ? Mant_b_D : Mant_a_D), 2'b0};


   always_comb //sticky bit
     begin
        Mant_sticky_D = 1'b0;
        if (Exp_diff_D >= (C_MANT+3)) // 23 + guard, round, sticky
          Mant_sticky_D = | Mant_shiftIn_D;
        else
          Mant_sticky_D = | (Mant_shiftIn_D << ((C_MANT+3) - Exp_diff_D));
     end
   assign Mant_shifted_D = {(Mant_shiftIn_D >> Exp_diff_D), Mant_sticky_D};

   always_comb
     begin
        Mant_invA_S = '0;
        Mant_invB_S = '0;
        if (Subtract_S)
          begin
             if (Exp_agtb_S)
               Mant_invA_S = 1'b1;
             else if (Exp_equal_S)
               begin
                 if (Mant_agtb_S)
                   Mant_invB_S = 1'b1;
                 else
                   Mant_invA_S = 1'b1;
               end
             else
               Mant_invA_S = 1'b1;
          end // if (Subtract_S)
     end // always_comb begin

   assign Mant_addCarryIn_D = Subtract_S;
   assign Mant_addInA_D     = (Mant_invA_S) ? ~Mant_shifted_D   : Mant_shifted_D;
   assign Mant_addInB_D     = (Mant_invB_S) ? ~Mant_unshifted_D : Mant_unshifted_D;

   assign Mant_addOut_D     = Mant_addInA_D + Mant_addInB_D + Mant_addCarryIn_D;

   assign Mant_prenorm_D    = {(Mant_addOut_D[C_MANT_ADDOUT-1] & ~Subtract_S), Mant_addOut_D[C_MANT_ADDOUT-2:0], 20'b0};

   /////////////////////////////////////////////////////////////////////////////
   // Sign operations
   /////////////////////////////////////////////////////////////////////////////

   assign Subtract_S = Sign_a_D ^ Sign_b_D;

   always_comb
     begin
        Sign_norm_D = 1'b0;
        if (Exp_agtb_S)
          Sign_norm_D = Sign_a_D;
        else if (Exp_equal_S)
          begin
             if (Mant_agtb_S)
               Sign_norm_D = Sign_a_D;
             else
               Sign_norm_D = Sign_b_D;
          end
        else //Exp_a < Exp_b
          Sign_norm_D = Sign_b_D;
     end

   /////////////////////////////////////////////////////////////////////////////
   // Output Assignments
   /////////////////////////////////////////////////////////////////////////////

   assign Sign_prenorm_DO = Sign_norm_D;
   assign Exp_prenorm_DO  = signed'({2'b0,Exp_prenorm_D});
   assign Mant_prenorm_DO = Mant_prenorm_D;

endmodule // fpadd
