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
// Engineers:      Thomas Gautschi -- gauthoma@student.ethz.ch                //
//                                                                            //
// Additional contributions by:                                               //
//                 Torbjørn Viem Ness -- torbjovn@stud.ntnu.no                //
//                                                                            //
//                                                                            //
// Create Date:    06/10/2014                                                 //
// Design Name:    FPU                                                        //
// Module Name:    fpu_mult.sv                                                //
// Project Name:   Private FPU                                                //
// Language:       SystemVerilog                                              //
//                                                                            //
// Description:    Floating point multiplier                                  //
//                 Calculates exponent and mantissa for                       //
//                 Normalizer/Rounding stage                                  //
//                                                                            //
// Revision:                                                                  //
//                15/05/2018                                                  //
//                Pass package parameters as default args instead of using    //
//                them directly, improves compatibility with tools like       //  
//                Synopsys Spyglass and DC (GitHub #7) - Torbjørn Viem Ness   //
////////////////////////////////////////////////////////////////////////////////

import fpu_defs::*;

module fpu_mult
#(
   parameter C_MANT_PRENORM = fpu_defs::C_MANT_PRENORM,
   parameter C_EXP_PRENORM  = fpu_defs::C_EXP_PRENORM,
   parameter C_EXP          = fpu_defs::C_EXP,
   parameter C_MANT         = fpu_defs::C_MANT,
   parameter C_BIAS         = fpu_defs::C_BIAS
)
  (//Input
   input logic                              Sign_a_DI,
   input logic                              Sign_b_DI,
   input logic [C_EXP-1:0]                  Exp_a_DI,
   input logic [C_EXP-1:0]                  Exp_b_DI,
   input logic [C_MANT:0]                   Mant_a_DI ,
   input logic [C_MANT:0]                   Mant_b_DI,

   //Output
   output logic                             Sign_prenorm_DO,
   output logic signed [C_EXP_PRENORM-1 :0] Exp_prenorm_DO,
   output logic        [C_MANT_PRENORM-1:0] Mant_prenorm_DO
   );

   //Operand components
   logic                                    Sign_a_D;
   logic                                    Sign_b_D;
   logic                                    Sign_prenorm_D;
   logic [C_EXP-1:0]                        Exp_a_D;
   logic [C_EXP-1:0]                        Exp_b_D;
   logic [C_MANT:0]                         Mant_a_D;
   logic [C_MANT:0]                         Mant_b_D;

   //Exponent calculations
   logic signed [C_EXP_PRENORM-1:0]         Exp_prenorm_D;       //signed exponent for normalizer

   //Multiplication
   logic [C_MANT_PRENORM-1:0]               Mant_prenorm_D;

   /////////////////////////////////////////////////////////////////////////////
   // Assign Inputs                                                           //
   /////////////////////////////////////////////////////////////////////////////
   assign Sign_a_D = Sign_a_DI;
   assign Sign_b_D = Sign_b_DI;
   assign Exp_a_D  = Exp_a_DI;
   assign Exp_b_D  = Exp_b_DI;
   assign Mant_a_D = Mant_a_DI;
   assign Mant_b_D = Mant_b_DI;

   /////////////////////////////////////////////////////////////////////////////
   // Output calculations                                                     //
   /////////////////////////////////////////////////////////////////////////////
   assign Sign_prenorm_D = Sign_a_D ^ Sign_b_D;
   assign Exp_prenorm_D  = signed'({2'b0,Exp_a_D}) + signed'({2'b0,Exp_b_D}) - signed'(C_BIAS);
   assign Mant_prenorm_D = Mant_a_D * Mant_b_D;

   /////////////////////////////////////////////////////////////////////////////
   // Output assignments
   /////////////////////////////////////////////////////////////////////////////
   assign Sign_prenorm_DO = Sign_prenorm_D;
   assign Exp_prenorm_DO  = Exp_prenorm_D;
   assign Mant_prenorm_DO = Mant_prenorm_D;

endmodule //fpu_mult

