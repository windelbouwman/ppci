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
//                 Michael Gautschi -- gautschi@iis.ee.ethz.ch                //
//                 Torbjørn Viem Ness -- torbjovn@stud.ntnu.no                //
//                                                                            //
//                                                                            //
// Create Date:    26/10/2014                                                 //
// Design Name:    FPU                                                        //
// Module Name:    fpu_private.sv                                             //
// Project Name:   Private FPU                                                //
// Language:       SystemVerilog                                              //
//                                                                            //
// Description:    Floating point unit with enable                            //
//                                                                            //
//                                                                            //
//                                                                            //
// Revision:                                                                  //
//            01/06/2017 added divsqrt module                                 //
// Revision:                                                                  //
//                15/05/2018                                                  //
//                Pass package parameters as default args instead of using    //
//                them directly, improves compatibility with tools like       //  
//                Synopsys Spyglass and DC (GitHub #7) - Torbjørn Viem Ness   //
////////////////////////////////////////////////////////////////////////////////

import fpu_defs::*;

module fpu_private
#(
   parameter C_OP             = fpu_defs::C_OP,
   parameter C_RM             = fpu_defs::C_RM,
   parameter C_CMD            = fpu_defs::C_CMD,
   parameter C_PC             = fpu_defs::C_PC,
   parameter C_FFLAG          = fpu_defs::C_FFLAG,

   parameter C_FPU_ADD_CMD    = fpu_defs::C_FPU_ADD_CMD,
   parameter C_FPU_SUB_CMD    = fpu_defs::C_FPU_SUB_CMD,
   parameter C_FPU_MUL_CMD    = fpu_defs::C_FPU_MUL_CMD,
   parameter C_FPU_DIV_CMD    = fpu_defs::C_FPU_DIV_CMD,
   parameter C_FPU_SQRT_CMD   = fpu_defs::C_FPU_SQRT_CMD,
   parameter C_FPU_I2F_CMD    = fpu_defs::C_FPU_I2F_CMD,
   parameter C_FPU_F2I_CMD    = fpu_defs::C_FPU_F2I_CMD,
   parameter C_FPU_FMADD_CMD  = fpu_defs::C_FPU_FMADD_CMD,
   parameter C_FPU_FMSUB_CMD  = fpu_defs::C_FPU_FMSUB_CMD,
   parameter C_FPU_FNMADD_CMD = fpu_defs::C_FPU_FNMADD_CMD,
   parameter C_FPU_FNMSUB_CMD = fpu_defs::C_FPU_FNMSUB_CMD
)
  (
   //Clock and reset
   input logic 	              clk_i,
   input logic 	              rst_ni,
   // enable
   input logic                fpu_en_i,
   // inputs
   input logic [C_OP-1:0]     operand_a_i,
   input logic [C_OP-1:0]     operand_b_i,
   input logic [C_OP-1:0]     operand_c_i,
   input logic [C_RM-1:0]     rm_i,
   input logic [C_CMD-1:0]    fpu_op_i,
   input logic [C_PC-1:0]     prec_i,

   // outputs
   output logic [C_OP-1:0]    result_o,
   output logic               valid_o,
   output logic [C_FFLAG-1:0] flags_o,
   output logic               divsqrt_busy_o
   );

   logic                     divsqrt_enable;
   logic                     fpu_enable;
   logic                     fma_enable;

   assign divsqrt_enable = fpu_en_i & ((fpu_op_i==C_FPU_DIV_CMD) | (fpu_op_i==C_FPU_SQRT_CMD));
   assign fpu_enable     = fpu_en_i & ((fpu_op_i==C_FPU_ADD_CMD) | (fpu_op_i==C_FPU_SUB_CMD) | (fpu_op_i==C_FPU_MUL_CMD) | (fpu_op_i==C_FPU_I2F_CMD) | (fpu_op_i==C_FPU_F2I_CMD));
   assign fma_enable     = fpu_en_i & ((fpu_op_i==C_FPU_FMADD_CMD) | (fpu_op_i==C_FPU_FMSUB_CMD) | (fpu_op_i==C_FPU_FNMADD_CMD)| (fpu_op_i==C_FPU_FNMSUB_CMD));


   ///////////////////////////////////////////////
   // FPU_core for Add/Sub/Mul/Casts            //
   ///////////////////////////////////////////////

   logic [31:0]                 fpu_operand_a;
   logic [31:0]                 fpu_operand_b;
   logic [31:0]                 fpu_result;
   logic [C_FFLAG-1:0]          fpu_flags;
   logic                        fpu_of, fpu_uf, fpu_zero, fpu_ix, fpu_iv, fpu_inf;

   assign fpu_operand_a = (fpu_enable) ? operand_a_i : '0;
   assign fpu_operand_b = (fpu_enable) ? operand_b_i : '0;

   fpu_core fpu_core
     (
      .Clk_CI        ( clk_i             ),
      .Rst_RBI       ( rst_ni            ),
      // enable
      .Enable_SI     ( fpu_enable        ),
      // inputs
      .Operand_a_DI  ( fpu_operand_a     ),
      .Operand_b_DI  ( fpu_operand_b     ),
      .RM_SI         ( rm_i              ),
      .OP_SI         ( fpu_op_i          ),

      // outputs
      .Result_DO     ( fpu_result        ),
      .Valid_SO      ( fpu_valid         ),

      .OF_SO         ( fpu_of            ),
      .UF_SO         ( fpu_uf            ),
      .Zero_SO       ( fpu_zero          ),
      .IX_SO         ( fpu_ix            ),
      .IV_SO         ( fpu_iv            ),
      .Inf_SO        ( fpu_inf           )
      );

   assign fpu_flags = {fpu_iv, 1'b0, fpu_of, fpu_uf, fpu_ix};


   ///////////////////////////////////////////////
   // Iterative DIV-Sqrt Unit                   //
   ///////////////////////////////////////////////

   // generate inputs for div/sqrt unit
   logic                       div_start, sqrt_start;
   logic [31:0]                divsqrt_operand_a;
   logic [31:0]                divsqrt_operand_b;
   logic [31:0]                divsqrt_result;
   logic [C_FFLAG-1:0]         divsqrt_flags;
   logic                       divsqrt_nv;
   logic                       divsqrt_ix;

   assign sqrt_start = divsqrt_enable & (fpu_op_i == C_FPU_SQRT_CMD);
   assign div_start  = divsqrt_enable & (fpu_op_i == C_FPU_DIV_CMD);

   assign divsqrt_operand_a = (div_start | sqrt_start) ? operand_a_i : '0;
   assign divsqrt_operand_b = (div_start)              ? operand_b_i : '0;


   div_sqrt_top_tp fpu_divsqrt_tp
     (
      .Clk_CI           ( clk_i             ),
      .Rst_RBI          ( rst_ni            ),
      .Div_start_SI     ( div_start         ),
      .Sqrt_start_SI    ( sqrt_start        ),
      .Operand_a_DI     ( divsqrt_operand_a ),
      .Operand_b_DI     ( divsqrt_operand_b ),
      .RM_SI            ( rm_i[1:0]         ),
      .Precision_ctl_SI ( prec_i            ),
      .Result_DO        ( divsqrt_result    ),
      .Exp_OF_SO        ( divsqrt_of        ),
      .Exp_UF_SO        ( divsqrt_uf        ),
      .Div_zero_SO      ( divsqrt_zero      ),
      .Ready_SO         ( divsqrt_busy_o    ),
      .Done_SO          ( divsqrt_valid     )
      );

   assign divsqrt_nv = 1'b0;
   assign divsqrt_ix = 1'b0;
   assign divsqrt_flags = {divsqrt_nv, divsqrt_zero, divsqrt_of, divsqrt_uf, divsqrt_ix};

   ///////////////////////////////////////////////
   // temporary place holder for FMA            //
   ///////////////////////////////////////////////

   logic [31:0]                 fma_operand_a;
   logic [31:0]                 fma_operand_b;
   logic [31:0]                 fma_operand_c;

   logic [31:0]                 fma_result;

   logic [1:0]                  fma_op;
   logic                        fma_valid;
   logic [C_FFLAG-1:0]          fma_flags;

   always_comb begin
      fma_op = 2'b00;

      unique case (fpu_op_i)
        C_FPU_FMADD_CMD:
          fma_op = 2'b00;
        C_FPU_FMSUB_CMD:
          fma_op = 2'b01;
        C_FPU_FNMADD_CMD:
          fma_op = 2'b11;
        C_FPU_FNMSUB_CMD:
          fma_op = 2'b10;
        default:
          fma_op = 2'b0;
      endcase
      end


//`ifndef PULP_FPGA_EMUL
`ifdef VERILATOR

   fp_fma_wrapper
     #(
       .C_MAC_PIPE_REGS(2),
       .RND_WIDTH(2),
       .STAT_WIDTH(5)
       )
   fp_fma_wrap_i
     (
      .clk_i            ( clk_i         ),
      .rst_ni           ( rst_ni        ),
      .En_i             ( fma_enable    ),
      .OpA_i            ( operand_a_i   ),
      .OpB_i            ( operand_b_i   ),
      .OpC_i            ( operand_c_i   ),
      .Op_i             ( fma_op        ),
      .Rnd_i            ( rm_i[1:0]     ),
      .Status_o         ( fma_flags     ),
      .Res_o            ( fma_result    ),
      .Valid_o          ( fma_valid     ),
      .Ready_o          (               ),
      .Ack_i            ( 1'b1          )
      );
`else
   logic [2:0] tuser;

   assign fma_operand_a = (fma_enable) ? operand_a_i                                      : '0;
   assign fma_operand_b = (fma_enable) ? {operand_b_i[31] ^ fma_op[1], operand_b_i[30:0]} : '0;
   assign fma_operand_c = (fma_enable) ? {operand_c_i[31] ^ fma_op[0], operand_c_i[30:0]} : '0;

   xilinx_fp_fma
   fp_fma_wrap
   (
    .aclk                    ( clk_i         ),
    .aresetn                 ( rst_ni        ),
    .s_axis_a_tvalid         ( fma_enable    ),
    .s_axis_a_tdata          ( fma_operand_a ),
    .s_axis_b_tvalid         ( fma_enable    ),
    .s_axis_b_tdata          ( fma_operand_b ),
    .s_axis_c_tvalid         ( fma_enable    ),
    .s_axis_c_tdata          ( fma_operand_c ),
    .s_axis_operation_tvalid ( fma_enable    ),
    .s_axis_operation_tdata  ( '0            ),
    .m_axis_result_tvalid    ( fma_valid     ),
    .m_axis_result_tdata     ( fma_result    ),
    .m_axis_result_tuser     ( tuser         )
    );

   assign fma_flags = {tuser[2], 1'b0, tuser[1], tuser[0], 1'b0};
`endif

   // output assignment

   assign valid_o  = divsqrt_valid | fpu_valid | fma_valid;
   assign result_o = divsqrt_valid ? divsqrt_result : fpu_valid ? fpu_result : fma_valid ? fma_result : '0;
   assign flags_o  = divsqrt_valid ? divsqrt_flags  : fpu_valid ? fpu_flags  : fma_valid ? fma_flags  : '0;

endmodule
