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
// Create Date:    29/10/2014                                                 //
// Design Name:    FPU                                                        //
// Module Name:    fpu_ftoi.sv                                                //
// Project Name:   Private FPU                                                //
// Language:       SystemVerilog                                              //
//                                                                            //
// Description:    Floating point to unsigned integer converter               //
//                 sets flags if necessary                                    //
//                                                                            //
//                                                                            //
// Revision:                                                                  //
//                15/05/2018                                                  //
//                Pass package parameters as default args instead of using    //
//                them directly, improves compatibility with tools like       //  
//                Synopsys Spyglass and DC (GitHub #7) - Torbjørn Viem Ness   //
////////////////////////////////////////////////////////////////////////////////

import fpu_defs::*;

module fpu_ftoi
#(
   parameter C_EXP_SHIFT  = fpu_defs::C_EXP_SHIFT,
   parameter C_SHIFT_BIAS = fpu_defs::C_SHIFT_BIAS,
   parameter C_OP         = fpu_defs::C_OP,
   parameter C_EXP        = fpu_defs::C_EXP,
   parameter C_MANT       = fpu_defs::C_MANT,
   parameter C_INF        = fpu_defs::C_INF,
   parameter C_MINF       = fpu_defs::C_MINF
)
  (//Input
   input logic             Sign_a_DI,
   input logic [C_EXP-1:0] Exp_a_DI,
   input logic [C_MANT:0]  Mant_a_DI,

   //Output
   output logic [C_OP-1:0] Result_DO,

   output logic            OF_SO,       //Overflow
   output logic            UF_SO,       //Underflow
   output logic            Zero_SO,     //Result zero
   output logic            IX_SO,       //Result inexact
   output logic            IV_SO,       //Result invalid
   output logic            Inf_SO       //Infinity
   );

   //Internal Operands
   logic              Sign_a_D;
   logic [C_EXP-1:0] 	Exp_a_D;
   logic [C_MANT:0]   Mant_a_D;

   //Output result
   logic [C_OP-1:0]   Result_D;

   //Disassemble Operand
   assign Sign_a_D = Sign_a_DI;
   assign Exp_a_D  = Exp_a_DI;
   assign Mant_a_D = Mant_a_DI;

   /////////////////////////////////////////////////////////////////////////////
   // Conversion
   /////////////////////////////////////////////////////////////////////////////
   logic signed [C_EXP_SHIFT-1:0]   Shift_amount_D; //8
   logic [C_MANT+C_OP-2:0]          Temp_shift_D;          // 23 bit fraction + 31 bit integer (w/o sign-bit)
   logic [C_OP-1:0]                 Temp_twos_D;
   logic                            Shift_amount_neg_S;
   logic                            Result_zero_S;
   logic                            Input_zero_S;

   assign Shift_amount_D     = signed'({1'b0,Exp_a_D}) - signed'(C_SHIFT_BIAS);
   assign Shift_amount_neg_S = Shift_amount_D[C_EXP_SHIFT-1]; //8

   assign Temp_shift_D = Shift_amount_neg_S ? '0 : (Mant_a_D << Shift_amount_D);
   assign Temp_twos_D  = ~{1'b0,Temp_shift_D[C_MANT+C_OP-2:C_MANT]} + 1'b1;

   /////////////////////////////////////////////////////////////////////////////
   // Output assignments
   /////////////////////////////////////////////////////////////////////////////

   //assign result
   assign Result_D  = OF_SO ? (Sign_a_D ? C_MINF : C_INF) : (Sign_a_D ? Temp_twos_D : {Sign_a_D, Temp_shift_D[C_MANT+C_OP-2:C_MANT]});
   assign Result_DO = Result_D;

   //assign flags
   assign Result_zero_S = (~|Result_D);
   assign Input_zero_S  = (~|{Exp_a_D,Mant_a_D});

   assign UF_SO   = 1'b0;
   assign OF_SO   = Shift_amount_D > (C_OP-2);
   assign Zero_SO = Result_zero_S & ~OF_SO;
   assign IX_SO   = (|Temp_shift_D[C_MANT-1:0] | Shift_amount_neg_S | OF_SO) & ~Input_zero_S;
   assign IV_SO   = (&Exp_a_D) && (|Mant_a_D);
   assign Inf_SO  = 1'b0;


endmodule //fpu_ftoi
