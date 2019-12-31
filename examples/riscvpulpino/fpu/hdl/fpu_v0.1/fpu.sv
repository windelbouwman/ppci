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
//                 Torbjørn Viem Ness -- torbjovn@stud.ntnu.no                //
//                                                                            //
//                                                                            //
// Create Date:    26/10/2014                                                 //
// Design Name:    FPU                                                        //
// Module Name:    fpu.sv                                                     //
// Project Name:   Private FPU                                                //
// Language:       SystemVerilog                                              //
//                                                                            //
// Description:    Floating point unit with input and ouput registers         //
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

module fpu
#(
   parameter C_CMD = fpu_defs::C_CMD,
   parameter C_RM  = fpu_defs::C_RM,
   parameter C_OP  = fpu_defs::C_OP
)
  (
   //Clock and reset
   input logic 	           Clk_CI,
   input logic 	           Rst_RBI,

   //Input Operands
   input logic [C_OP-1:0]  Operand_a_DI,
   input logic [C_OP-1:0]  Operand_b_DI,
   input logic [C_RM-1:0]  RM_SI,    //Rounding Mode
   input logic [C_CMD-1:0] OP_SI,
   input logic             Enable_SI,

   input logic             Stall_SI,

   output logic [C_OP-1:0] Result_DO,
   //Output-Flags
   output logic            OF_SO,    //Overflow
   output logic            UF_SO,    //Underflow
   output logic            Zero_SO,  //Result zero
   output logic            IX_SO,    //Result inexact
   output logic            IV_SO,    //Result invalid
   output logic            Inf_SO    //Infinity
   );

   //Internal Operands
   logic [C_OP-1:0]        Operand_a_D;
   logic [C_OP-1:0]        Operand_b_D;

   logic [C_RM-1:0]        RM_S;
   logic [C_CMD-1:0]       OP_S;



   //Input register

   always_ff @(posedge Clk_CI, negedge Rst_RBI)
     begin
        if (~Rst_RBI)
          begin
             Operand_a_D <= '0;
             Operand_b_D <= '0;
             RM_S        <= '0;
             OP_S        <= '0;
          end
        else
          begin
             if(~Stall_SI)
               begin
                  Operand_a_D <= Operand_a_DI;
                  Operand_b_D <= Operand_b_DI;
                  RM_S        <= RM_SI;
                  OP_S        <= OP_SI;
               end
          end
     end


   /////////////////////////////////////////////////////////////////////////////
   // FPU_core
   /////////////////////////////////////////////////////////////////////////////
   logic              UF_S;
   logic              OF_S;
   logic              Zero_S;
   logic              IX_S;
   logic              IV_S;
   logic              Inf_S;

   logic [C_OP-1:0]   Result_D;


  fpu_core fpcore
     (
      .Clk_CI        ( Clk_CI       ),
      .Rst_RBI       ( Rst_RBI      ),
      .Enable_SI     ( Enable_SI    ),

      .Operand_a_DI  ( Operand_a_D  ),
      .Operand_b_DI  ( Operand_b_D  ),
      .RM_SI         ( RM_S         ),
      .OP_SI         ( OP_S         ),

      .Result_DO     ( Result_D     ),

      .OF_SO         ( OF_S         ),
      .UF_SO         ( UF_S         ),
      .Zero_SO       ( Zero_S       ),
      .IX_SO         ( IX_S         ),
      .IV_SO         ( IV_S         ),
      .Inf_SO        ( Inf_S        )
      );

   /////////////////////////////////////////////////////////////////////////////
   // Output assignments
   /////////////////////////////////////////////////////////////////////////////

   assign Result_DO = Result_D;

   assign OF_SO     = OF_S;
   assign UF_SO     = UF_S;
   assign Zero_SO   = Zero_S;
   assign IX_SO     = IX_S;
   assign IV_SO     = IV_S;
   assign Inf_SO    = Inf_S;




endmodule // fpu
