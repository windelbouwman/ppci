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
// Create Date:    31/10/2014                                                 //
// Design Name:    FPU                                                        //
// Module Name:    fpu_itof.sv                                                //
// Project Name:   Private FPU                                                //
// Language:       SystemVerilog                                              //
//                                                                            //
// Description:    Integer to floating point converter                        //
//                                                                            //
//                                                                            //
//                                                                            //
// Revision:                                                                  //
//                15/05/2018                                                  //
//                Pass package parameters as default args instead of using    //
//                them directly, improves compatibility with tools like       //  
//                Synopsys Spyglass and DC (GitHub #7) - Torbjørn Viem Ness   //
////////////////////////////////////////////////////////////////////////////////

import fpu_defs::*;

module fpu_itof
#(
   parameter C_EXP_PRENORM  = fpu_defs::C_EXP_PRENORM,
   parameter C_MANT_PRENORM = fpu_defs::C_MANT_PRENORM,
   parameter C_MANT_INT     = fpu_defs::C_MANT_INT,
   parameter C_PADMANT      = fpu_defs::C_PADMANT,
   parameter C_UNKNOWN      = fpu_defs::C_UNKNOWN,
   parameter C_OP           = fpu_defs::C_OP
)
  (//Input
   input logic [C_OP-1:0]                   Operand_a_DI,

   //Output
   output logic                             Sign_prenorm_DO,
   output logic signed [C_EXP_PRENORM-1 :0] Exp_prenorm_DO,
   output logic        [C_MANT_PRENORM-1:0] Mant_prenorm_DO
   );

   //Internal Operands
   logic [C_OP-1:0]                         Operand_a_D;
   logic                                    Sign_int_D;
   logic                                    Sign_prenorm_D;
   logic [C_MANT_INT-1:0]                   Mant_int_D;                 //Integer number w/o sign-bit
   logic [C_OP-1:0]                         Temp_twos_to_unsigned_D;
   logic [C_MANT_PRENORM-1:0]               Mant_prenorm_D;


   //Hidden Bits
   logic                                    Hb_a_D;

   //Exponent calculations
   logic signed [C_EXP_PRENORM-1:0]         Exp_prenorm_D;       //signed exponent for normalizer

   /////////////////////////////////////////////////////////////////////////////
   // Assign Inputs/Disassemble Operands                                      //
   /////////////////////////////////////////////////////////////////////////////

   assign Operand_a_D = Operand_a_DI;

   //Disassemble Operands
   assign Sign_int_D  = Operand_a_D[C_OP-1];
   assign Mant_int_D  = Operand_a_D[C_MANT_INT-1:0];
   logic  Twos_to_unsigned_zero;
   assign Temp_twos_to_unsigned_D = ~Operand_a_D + 1'b1;
   assign Twos_to_unsigned_zero_D = ~(|Temp_twos_to_unsigned_D[C_MANT_INT-1:0]);

   /////////////////////////////////////////////////////////////////////////////
   // Output calculations                                                     //
   /////////////////////////////////////////////////////////////////////////////

   assign Sign_prenorm_D = Sign_int_D;
   assign Exp_prenorm_D  = signed'({2'd0,C_UNKNOWN});
   assign Mant_prenorm_D = Sign_int_D ? {Twos_to_unsigned_zero_D,Temp_twos_to_unsigned_D[C_MANT_INT-1:0], C_PADMANT} : {1'b0,Mant_int_D, C_PADMANT};

   /////////////////////////////////////////////////////////////////////////////
   // Output assignments                                                      //
   /////////////////////////////////////////////////////////////////////////////

   assign Sign_prenorm_DO = Sign_prenorm_D;
   assign Exp_prenorm_DO  = Exp_prenorm_D;
   assign Mant_prenorm_DO = Mant_prenorm_D;

endmodule //fpu_itof
