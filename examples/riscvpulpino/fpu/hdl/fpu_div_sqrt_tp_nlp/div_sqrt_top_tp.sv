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
// Engineers:      Lei Li -- lile@iis.ee.ethz.ch                              //
//                                                                            //
// Additional contributions by:                                               //
//                                                                            //
//                                                                            //
//                                                                            //
// Create Date:    01/12/2016                                                 //
// Design Name:    div_sqrt_top                                               //
// Module Name:    div_sqrt_top.sv                                            //
// Project Name:   The shared divisor and square root                         //
// Language:       SystemVerilog                                              //
//                                                                            //
// Description:    The top of div and sqrt                                    //
//                                                                            //
//                                                                            //
// Revision:       07/02/2017                                                 //
////////////////////////////////////////////////////////////////////////////////

import fpu_defs_div_sqrt_tp::*;

module div_sqrt_top_tp
#(
   parameter   Precision_ctl_Enable_S = 0,
   parameter   Accuracy_ctl_Enable_S  = 1
)
  (//Input
   input logic                  Clk_CI,
   input logic                  Rst_RBI,
   input logic                  Div_start_SI,
   input logic                  Sqrt_start_SI,

   //Input Operands
   input logic [C_DIV_OP-1:0]   Operand_a_DI,
   input logic [C_DIV_OP-1:0]   Operand_b_DI,
   input logic [C_DIV_RM-1:0]   RM_SI,    //Rounding Mode
   input logic [C_DIV_PC-1:0]   Precision_ctl_SI, // Precision Control

   output logic [31:0]          Result_DO,

   //Output-Flags
   output logic                 Exp_OF_SO,
   output logic                 Exp_UF_SO,
   output logic                 Div_zero_SO,
   output logic                 Ready_SO,
   output logic                 Done_SO
 );



  logic [C_DIV_MANT-1:0]        Mant_res_DO;
  logic [C_DIV_EXP-1:0]         Exp_res_DO;
  logic                         Sign_res_DO;

   assign Result_DO =   {Sign_res_DO,Exp_res_DO, Mant_res_DO};

   //Operand components
   logic                       Sign_a_D;
   logic                       Sign_b_D;
   logic [C_DIV_EXP:0]         Exp_a_D;
   logic [C_DIV_EXP:0]         Exp_b_D;
   logic [C_DIV_MANT:0]        Mant_a_D;
   logic [C_DIV_MANT:0]        Mant_b_D;

   logic [C_DIV_EXP+1:0]       Exp_z_D;
   logic [C_DIV_MANT:0]        Mant_z_D;
   logic                       Sign_z_D;
   logic                       Start_S;
   logic [C_DIV_RM-1:0]        RM_dly_S;
   logic                       Mant_zero_S_a, Mant_zero_S_b;
   logic                       Div_enable_S;
   logic                       Sqrt_enable_S;
   logic                       Inf_a_S;
   logic                       Inf_b_S;
   logic                       Zero_a_S;
   logic                       Zero_b_S;
   logic                       NaN_a_S;
   logic                       NaN_b_S;

   logic [3:0]                 Round_bit_D;

 preprocess  precess_U0
 (
   .Clk_CI                (Clk_CI             ),
   .Rst_RBI               (Rst_RBI            ),
   .Div_start_SI          (Div_start_SI       ),
   .Sqrt_start_SI         (Sqrt_start_SI      ),
   .Operand_a_DI          (Operand_a_DI       ),
   .Operand_b_DI          (Operand_b_DI       ),
   .RM_SI                 (RM_SI              ),
   .Start_SO              (Start_S            ),
   .Exp_a_DO_norm         (Exp_a_D            ),
   .Exp_b_DO_norm         (Exp_b_D            ),
   .Mant_a_DO_norm        (Mant_a_D           ),
   .Mant_b_DO_norm        (Mant_b_D           ),
   .RM_dly_SO             (RM_dly_S           ),
   .Sign_z_DO             (Sign_z_D           ),
   .Inf_a_SO              (Inf_a_S            ),
   .Inf_b_SO              (Inf_b_S            ),
   .Zero_a_SO             (Zero_a_S           ),
   .Zero_b_SO             (Zero_b_S           ),
   .NaN_a_SO              (NaN_a_S            ),
   .NaN_b_SO              (NaN_b_S            )

   );

 nrbd_nrsc_tp #(Precision_ctl_Enable_S, Accuracy_ctl_Enable_S)  nrbd_nrsc_U0
  (
   .Clk_CI                (Clk_CI             ),
   .Rst_RBI               (Rst_RBI            ),
   .Div_start_SI          (Div_start_SI       ) ,
   .Sqrt_start_SI         (Sqrt_start_SI      ),
   .Start_SI              (Start_S            ),
   .Div_enable_SO         (Div_enable_S       ),
   .Sqrt_enable_SO        (Sqrt_enable_S      ),
   .Precision_ctl_SI      (Precision_ctl_SI   ),
   .Exp_a_DI              (Exp_a_D            ),
   .Exp_b_DI              (Exp_b_D            ),
   .Mant_a_DI             (Mant_a_D           ),
   .Mant_b_DI             (Mant_b_D           ),
   .Ready_SO              (Ready_SO           ),
   .Done_SO               (Done_SO            ),
   .Exp_z_DO              (Exp_z_D            ),
   .Mant_z_DO             (Mant_z_D           ),
   .Round_bit_DO          (Round_bit_D        )
    );


 fpu_norm_div_sqrt  fpu_norm_U0
  (
   .Mant_in_DI            (Mant_z_D           ),
   .Round_bit_DI          (Round_bit_D        ),
   .Exp_in_DI             (Exp_z_D            ),
   .Sign_in_DI            (Sign_z_D           ),
   .Div_enable_SI         (Div_enable_S       ),
   .Sqrt_enable_SI        (Sqrt_enable_S      ),
   .Inf_a_SI              (Inf_a_S            ),
   .Inf_b_SI              (Inf_b_S            ),
   .Zero_a_SI             (Zero_a_S           ),
   .Zero_b_SI             (Zero_b_S           ),
   .NaN_a_SI              (NaN_a_S            ),
   .NaN_b_SI              (NaN_b_S            ),
   .RM_SI                 (RM_dly_S           ),
   .Mant_res_DO           (Mant_res_DO        ),
   .Exp_res_DO            (Exp_res_DO         ),
   .Sign_res_DO           (Sign_res_DO        ),
   .Exp_OF_SO             (Exp_OF_SO          ),
   .Exp_UF_SO             (Exp_UF_SO          ),
   .Div_zero_SO           (Div_zero_SO         )
   );

endmodule
