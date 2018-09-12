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
//                 Thomas Gautschi -- gauthoma@sutdent.ethz.ch                //
//                                                                            //
// Additional contributions by:                                               //
//                 Torbjørn Viem Ness -- torbjovn@stud.ntnu.no                //
//                                                                            //
//                                                                            //
//                                                                            //
// Create Date:    26/10/2014                                                 //
// Design Name:    FPU                                                        //
// Module Name:    fpu_shared.sv                                              //
// Project Name:   FPU                                                        //
// Language:       SystemVerilog                                              //
//                                                                            //
// Description:    Wrapper for connecting the FPU to the shared interconnect  //
//                                                                            //
// Revision:                                                                  //
//                15/05/2018                                                  //
//                Pass package parameters as default args instead of using    //
//                them directly, improves compatibility with tools like       //  
//                Synopsys Spyglass and DC (GitHub #7) - Torbjørn Viem Ness   //
////////////////////////////////////////////////////////////////////////////////

import fpu_defs::*;

module fpu_shared
  #(
    parameter ADD_REGISTER = 1,

    parameter C_OP         = fpu_defs::C_OP,
    parameter C_CMD        = fpu_defs::C_CMD,
    parameter C_RM         = fpu_defs::C_RM,
    parameter C_TAG        = fpu_defs::C_TAG,
    parameter C_FLAG       = fpu_defs::C_FLAG
    )
  (
   input logic     Clk_CI,
   input logic     Rst_RBI,
   marx_apu_if.apu Interface
   );

   logic [C_OP-1:0]  Operand_a_D;
   logic [C_OP-1:0]  Operand_b_D;
   logic [C_CMD-1:0] Op_S;
   logic [C_RM-1:0]  RM_S;

   logic             Valid_S;
   logic [C_TAG-1:0] Tag_D;

   /////////////////////////////////////////////////////////////////////////////
   // Optional Input Register
   /////////////////////////////////////////////////////////////////////////////

   generate
      if (ADD_REGISTER == 1)
        begin
           logic [C_OP-1:0]  Operand_a_DN;
           logic [C_OP-1:0]  Operand_b_DN;
           logic [C_RM-1:0]  RM_SN;
           logic [C_CMD-1:0] Op_SN;

           logic             Valid_SN;
           logic [C_TAG-1:0] Tag_DN;

           assign  Operand_a_DN = Interface.arga_ds_d;
           assign  Operand_b_DN = Interface.argb_ds_d;
           assign  RM_SN        = Interface.flags_ds_d;
           assign  Op_SN        = Interface.op_ds_d;

           assign  Valid_SN     = Interface.valid_ds_s;
           assign  Tag_DN       = Interface.tag_ds_d;

           always_ff @(posedge Clk_CI, negedge Rst_RBI) begin
              if (~Rst_RBI) begin
                 Operand_a_D <= '0;
                 Operand_b_D <= '0;
                 Op_S        <= '0;
                 RM_S        <= '0;

                 Valid_S     <= '0;
                 Tag_D       <= '0;
              end
              else begin
                 Operand_a_D <= Operand_a_DN;
                 Operand_b_D <= Operand_b_DN;
                 RM_S        <= RM_SN;
                 Op_S        <= Op_SN;

                 Valid_S     <= Valid_SN;
                 Tag_D       <= Tag_DN;
              end
           end
        end
      else
        begin
           assign Operand_a_D  = Interface.arga_ds_d;
           assign Operand_b_D  = Interface.argb_ds_d;
           assign RM_S         = Interface.flags_ds_d;
           assign Op_S         = Interface.op_ds_d;

           assign Valid_S      = Interface.valid_ds_s;
           assign Tag_D        = Interface.tag_ds_d;
        end
   endgenerate

   /////////////////////////////////////////////////////////////////////////////
   // FPU core instance
   /////////////////////////////////////////////////////////////////////////////

   logic [C_OP-1:0]   Result_D;

   logic [C_FLAG-1:0] Flags_S;
   logic              UF_S;
   logic              OF_S;
   logic              Zero_S;
   logic              IX_S;
   logic              IV_S;
   logic              Inf_S;

   fpu_core core
     (
      .Clk_CI       ( Clk_CI        ),
      .Rst_RBI      ( Rst_RBI       ),
      .Enable_SI    ( Valid_S       ),

      .Operand_a_DI ( Operand_a_D   ),
      .Operand_b_DI ( Operand_b_D   ),
      .RM_SI        ( RM_S          ),
      .OP_SI        ( Op_S          ),

      .Result_DO    ( Result_D      ),

      .OF_SO        ( OF_S          ),
      .UF_SO        ( UF_S          ),
      .Zero_SO      ( Zero_S        ),
      .IX_SO        ( IX_S          ),
      .IV_SO        ( IV_S          ),
      .Inf_SO       ( Inf_S         )
      );


   /////////////////////////////////////////////////////////////////////////////
   // Shim register for tag and valid
   /////////////////////////////////////////////////////////////////////////////

   logic              ValidDelayed_SP;
   logic              ValidDelayed_SN;
   logic [C_TAG-1:0]  TagDelayed_DP;
   logic [C_TAG-1:0]  TagDelayed_DN;

   assign ValidDelayed_SN = Valid_S;
   assign TagDelayed_DN   = Tag_D;

   always_ff @(posedge Clk_CI, negedge Rst_RBI)
     begin
        if (~Rst_RBI)
          begin
             ValidDelayed_SP <= '0;
             TagDelayed_DP   <= '0;
          end
        else
          begin
             ValidDelayed_SP <= ValidDelayed_SN;
             TagDelayed_DP   <= TagDelayed_DN;
          end
     end // always_ff @ (posedge Clk_CI, negedge Rst_RBI)

   /////////////////////////////////////////////////////////////////////////////
   // Output assignments
   /////////////////////////////////////////////////////////////////////////////

   assign Interface.result_us_d = Result_D;
   assign Interface.flags_us_d  = {1'b0, Inf_S, IV_S, IX_S, Zero_S, 2'b0, UF_S, OF_S};
   assign Interface.tag_us_d    = TagDelayed_DP;
   assign Interface.req_us_s    = ValidDelayed_SP;
   assign Interface.ready_ds_s  = 1'b1;

endmodule
