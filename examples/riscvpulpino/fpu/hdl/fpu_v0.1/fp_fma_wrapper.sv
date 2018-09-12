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
// Copyright (C) 2017 ETH Zurich, University of Bologna                       //
// All rights reserved.                                                       //
//                                                                            //
//                                                                            //
// Engineer:       Michael Gautschi - gautschi@iis.ee.ethz.ch                 //
// Create Date:    20/06/2017                                                 //
// Design Name:    fp_mac_wrapper                                             //
// Module Name:    fpu_fma_wrapper.sv                                         //
// Project Name:   Shared APU                                                 //
// Language:       SystemVerilog                                              //
//                                                                            //
// Description:    Wraps the fp-mac unit                                      //
//                                                                            //
//                                                                            //
// Revision:                                                                  //
////////////////////////////////////////////////////////////////////////////////

`ifndef SYNTHESIS
//`define FP_SIM_MODELS;
`endif

module fp_fma_wrapper
#(
  parameter C_MAC_PIPE_REGS = 2,
  parameter RND_WIDTH       = 2,
  parameter STAT_WIDTH      = 5
)
 (
  // Clock and Reset
  input  logic                  clk_i,
  input  logic                  rst_ni,

  input  logic                  En_i,

  input logic [31:0]            OpA_i,
  input logic [31:0]            OpB_i,
  input logic [31:0]            OpC_i,
  input logic [1:0]             Op_i,

  input logic [RND_WIDTH-1:0]   Rnd_i,
  output logic [STAT_WIDTH-1:0] Status_o,

  output logic [31:0]           Res_o,
  output logic                  Valid_o,
  output logic                  Ready_o,
  input  logic                  Ack_i
);

   // DISTRIBUTE PIPE REGS
   parameter C_PRE_PIPE_REGS   = C_MAC_PIPE_REGS - 1;
   parameter C_POST_PIPE_REGS  = 1;

   // PRE PIPE REG SIGNALS
   logic [31:0]          OpA_DP     [C_PRE_PIPE_REGS+1];
   logic [31:0]          OpB_DP     [C_PRE_PIPE_REGS+1];
   logic [31:0]          OpC_DP     [C_PRE_PIPE_REGS+1];
   logic                 En_SP      [C_PRE_PIPE_REGS+1];
   logic [RND_WIDTH-1:0] Rnd_DP     [C_PRE_PIPE_REGS+1];

   // POST PIPE REG SIGNALS
   logic                  EnPost_SP      [C_POST_PIPE_REGS+1];
   logic [31:0]           Res_DP         [C_POST_PIPE_REGS+1];
   logic [STAT_WIDTH-1:0] Status_DP      [C_POST_PIPE_REGS+1];
   // Fflags of DW        {PA/DV, HugeInt, NX, Huge, Tiny, IV, Inf, Zero}
   logic [7:0]            status;

   // assign input. note: index [0] is not a register here!
   assign OpA_DP[0]    = En_i ? OpA_i :'0;
   assign OpB_DP[0]    = En_i ? {OpB_i[31] ^ Op_i[1],OpB_i[30:0]} :'0;
   assign OpC_DP[0]    = En_i ? {OpC_i[31] ^ Op_i[0],OpC_i[30:0]} :'0;
   assign En_SP[0]     = En_i;
   assign Rnd_DP[0]    = Rnd_i;

   // propagate states
   assign EnPost_SP[0]      = En_SP[C_PRE_PIPE_REGS];

   // assign output
   assign Res_o             = Res_DP[C_POST_PIPE_REGS];
   assign Valid_o           = EnPost_SP[C_POST_PIPE_REGS];
   assign Status_o          = Status_DP[C_POST_PIPE_REGS];
   assign Ready_o           = 1'b1;

`ifndef VERILATOR
`ifdef FP_SIM_MODELS
   shortreal              a, b, c, res;

   assign a = $bitstoshortreal(OpA_DP[C_PRE_PIPE_REGS]);
   assign b = $bitstoshortreal(OpB_DP[C_PRE_PIPE_REGS]);
   assign c = $bitstoshortreal(OpC_DP[C_PRE_PIPE_REGS]);

   // rounding mode is ignored here
   assign res = (a*b) + c;

   // convert to logic again
   assign Res_DP[0] = $shortrealtobits(res);

   // not used in simulation model
   assign Status_DP[0] = '0;
`else
   //Fflags of RISC-V    {NV,        DZ,   OF,        UF,        NX       }
   assign Status_DP[0] = {status[2], 1'b0, status[4], status[3], status[5]};

fmac
fp_fma_i
  //fmac assumes a + b*c, the fpu core assumes a*b + c
  (
   .Operand_a_DI         ( OpC_DP[C_PRE_PIPE_REGS]       ),
   .Operand_b_DI         ( OpB_DP[C_PRE_PIPE_REGS]       ),
   .Operand_c_DI         ( OpA_DP[C_PRE_PIPE_REGS]       ),
   .RM_SI                ( Rnd_DP[C_PRE_PIPE_REGS]       ),
   .Result_DO            ( Res_DP[0]                     ),
   .Exp_OF_SO            ( status[4]                     ),
   .Exp_UF_SO            ( status[3]                     ),
   .Flag_NX_SO           ( status[5]                     ),
   .Flag_IV_SO           ( status[2]                     )
   );

`endif
`endif
   // PRE_PIPE_REGS
   generate
    genvar i;
      for (i=1; i <= C_PRE_PIPE_REGS; i++)  begin: g_pre_regs

         always_ff @(posedge clk_i or negedge rst_ni) begin : p_pre_regs
            if(~rst_ni) begin
               En_SP[i]         <= '0;
               OpA_DP[i]        <= '0;
               OpB_DP[i]        <= '0;
               OpC_DP[i]        <= '0;
               Rnd_DP[i]        <= '0;
            end
            else begin
               // this one has to be always enabled...
               En_SP[i]       <= En_SP[i-1];
               // enabled regs
               if(En_SP[i-1]) begin
                  OpA_DP[i]       <= OpA_DP[i-1];
                  OpB_DP[i]       <= OpB_DP[i-1];
                  OpC_DP[i]       <= OpC_DP[i-1];
                  Rnd_DP[i]       <= Rnd_DP[i-1];
               end
            end
         end
      end
   endgenerate


   // POST_PIPE_REGS
   generate
    genvar j;
      for (j=1; j <= C_POST_PIPE_REGS; j++)  begin: g_post_regs

         always_ff @(posedge clk_i or negedge rst_ni) begin : p_post_regs
            if(~rst_ni) begin
               EnPost_SP[j]     <= '0;
               Res_DP[j]        <= '0;
               Status_DP[j]     <= '0;
            end
            else begin
               // this one has to be always enabled...
               EnPost_SP[j]       <= EnPost_SP[j-1];

               // enabled regs
               if(EnPost_SP[j-1]) begin
                  Res_DP[j]       <= Res_DP[j-1];
                  Status_DP[j]    <= Status_DP[j-1];
               end
            end
         end
      end
   endgenerate

endmodule
