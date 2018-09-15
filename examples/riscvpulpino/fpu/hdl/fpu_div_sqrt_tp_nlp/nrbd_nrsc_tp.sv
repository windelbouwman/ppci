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
// Engineers:      Lei Li      lile@iis.ee.ethz.ch                            //
//                                                                            //
// Additional contributions by:                                               //
//                                                                            //
//                                                                            //
//                                                                            //
// Create Date:    01/12/2016                                                 //
// Design Name:    div_sqrt                                                   //
// Module Name:    nrbd.sv                                                    //
// Project Name:   Private FPU                                                //
// Language:       SystemVerilog                                              //
//                                                                            //
// Description:   non restroring binary  divisior/ square root                //
//                                                   t                        //
//                                                                            //
// Revision:       19/01/2017                                                 //
////////////////////////////////////////////////////////////////////////////////

import fpu_defs_div_sqrt_tp::*;

module nrbd_nrsc_tp
#(
   parameter   Precision_ctl_Enable_S = 0,
   parameter   Accuracy_ctl_Enable_S  = 1
)
  (//Input
   input logic                                 Clk_CI,
   input logic                                 Rst_RBI,
   input logic                                 Div_start_SI,
   input logic                                 Sqrt_start_SI,
   input logic                                 Start_SI,
   input logic [C_DIV_PC-1:0]                  Precision_ctl_SI,
   input logic [C_DIV_MANT:0]                  Mant_a_DI,
   input logic [C_DIV_MANT:0]                  Mant_b_DI,
   input logic [C_DIV_EXP:0]                   Exp_a_DI,
   input logic [C_DIV_EXP:0]                   Exp_b_DI,
  //output
   output logic                                Div_enable_SO,
   output logic                                Sqrt_enable_SO,
   output logic                                Ready_SO,
   output logic                                Done_SO,
   output logic  [C_DIV_MANT:0]                Mant_z_DO,
   output logic [C_DIV_EXP+1:0]                Exp_z_DO,
   output logic [3:0]                          Round_bit_DO
    );

    logic [C_DIV_MANT+1+1:0]                  First_iteration_cell_sum_D;
    logic [C_DIV_MANT+1+2:0]                  Sec_iteration_cell_sum_D;
    logic [C_DIV_MANT+1+3:0]                  Thi_iteration_cell_sum_D;
    logic [C_DIV_MANT+1+4:0]                  Fou_iteration_cell_sum_D;
    logic                                     First_iteration_cell_carry_D,Sec_iteration_cell_carry_D,Thi_iteration_cell_carry_D,Fou_iteration_cell_carry_D;
    logic [1:0]                               Sqrt_Da0,Sqrt_Da1,Sqrt_Da2,Sqrt_Da3;
    logic [1:0]                               Sqrt_D0,Sqrt_D1,Sqrt_D2,Sqrt_D3;
    logic [C_DIV_MANT+1+1:0]                  First_iteration_cell_a_D,First_iteration_cell_b_D;
    logic [C_DIV_MANT+1+2:0]                  Sec_iteration_cell_a_D,Sec_iteration_cell_b_D;
    logic [C_DIV_MANT+1+3:0]                  Thi_iteration_cell_a_D,Thi_iteration_cell_b_D;
    logic [C_DIV_MANT+1+4:0]                  Fou_iteration_cell_a_D,Fou_iteration_cell_b_D;
    logic                                     Div_start_dly_S,Sqrt_start_dly_S;


control_tp #(Precision_ctl_Enable_S,Accuracy_ctl_Enable_S)         control_U0
(  .Clk_CI                                   (Clk_CI                          ),
   .Rst_RBI                                  (Rst_RBI                         ),
   .Div_start_SI                             (Div_start_SI                    ),
   .Sqrt_start_SI                            (Sqrt_start_SI                   ),
   .Start_SI                                 (Start_SI                        ),
   .Precision_ctl_SI                         (Precision_ctl_SI                ),
   .Numerator_DI                             (Mant_a_DI                       ),
   .Exp_num_DI                               (Exp_a_DI                        ),
   .Denominator_DI                           (Mant_b_DI                       ),
   .Exp_den_DI                               (Exp_b_DI                        ),
   .First_iteration_cell_sum_DI              (First_iteration_cell_sum_D      ),
   .First_iteration_cell_carry_DI            (First_iteration_cell_carry_D    ),
   .Sqrt_Da0                                 (Sqrt_Da0                        ),
   .Sec_iteration_cell_sum_DI                (Sec_iteration_cell_sum_D        ),
   .Sec_iteration_cell_carry_DI              (Sec_iteration_cell_carry_D      ),
   .Sqrt_Da1                                 (Sqrt_Da1                        ),
   .Thi_iteration_cell_sum_DI                (Thi_iteration_cell_sum_D        ),
   .Thi_iteration_cell_carry_DI              (Thi_iteration_cell_carry_D      ),
   .Sqrt_Da2                                 (Sqrt_Da2                        ),
   .Fou_iteration_cell_sum_DI                (Fou_iteration_cell_sum_D        ),
   .Fou_iteration_cell_carry_DI              (Fou_iteration_cell_carry_D      ),
   .Sqrt_Da3                                 (Sqrt_Da3                        ),
   .Div_start_dly_SO                         (Div_start_dly_S                 ),
   .Sqrt_start_dly_SO                        (Sqrt_start_dly_S                ),
   .Div_enable_SO                            (Div_enable_SO                   ),
   .Sqrt_enable_SO                           (Sqrt_enable_SO                  ),
   .Sqrt_D0                                  (Sqrt_D0                         ),
   .Sqrt_D1                                  (Sqrt_D1                         ),
   .Sqrt_D2                                  (Sqrt_D2                         ),
   .Sqrt_D3                                  (Sqrt_D3                         ),
   .First_iteration_cell_a_DO                (First_iteration_cell_a_D        ),
   .First_iteration_cell_b_DO                (First_iteration_cell_b_D        ),
   .Sec_iteration_cell_a_DO                  (Sec_iteration_cell_a_D          ),
   .Sec_iteration_cell_b_DO                  (Sec_iteration_cell_b_D          ),
   .Thi_iteration_cell_a_DO                  (Thi_iteration_cell_a_D          ),
   .Thi_iteration_cell_b_DO                  (Thi_iteration_cell_b_D          ),
   .Fou_iteration_cell_a_DO                  (Fou_iteration_cell_a_D          ),
   .Fou_iteration_cell_b_DO                  (Fou_iteration_cell_b_D          ),
   .Ready_SO                                 (Ready_SO                        ),
   .Done_SO                                  (Done_SO                         ),
   .Mant_result_prenorm_DO                   (Mant_z_DO                       ),
   .Round_bit_DO                             (Round_bit_DO                    ),
   .Exp_result_prenorm_DO                    (Exp_z_DO                        )
);

iteration_div_sqrt_first #(26) iteration_unit_U0
(
   .A_DI                                    (First_iteration_cell_a_D        ),
   .B_DI                                    (First_iteration_cell_b_D        ),
   .Div_enable_SI                           (Div_enable_SO                   ),
   .Div_start_dly_SI                        (Div_start_dly_S                 ),
   .Sqrt_enable_SI                          (Sqrt_enable_SO                  ),
   .D_DI                                    (Sqrt_D0                         ),
   .D_DO                                    (Sqrt_Da0                        ),
   .Sum_DO                                  (First_iteration_cell_sum_D      ),
   .Carry_out_DO                            (First_iteration_cell_carry_D    )
);

iteration_div_sqrt #(27) iteration_unit_U1
(
   .A_DI                                    (Sec_iteration_cell_a_D          ),
   .B_DI                                    (Sec_iteration_cell_b_D          ),
   .Div_enable_SI                           (Div_enable_SO                   ),
   .Sqrt_enable_SI                          (Sqrt_enable_SO                  ),
   .D_DI                                    (Sqrt_D1                         ),
   .D_DO                                    (Sqrt_Da1                        ),
   .Sum_DO                                  (Sec_iteration_cell_sum_D        ),
   .Carry_out_DO                            (Sec_iteration_cell_carry_D      )
);

iteration_div_sqrt #(28) iteration_unit_U2
(
   .A_DI                                    (Thi_iteration_cell_a_D         ),
   .B_DI                                    (Thi_iteration_cell_b_D         ),
   .Div_enable_SI                           (Div_enable_SO                  ),
   .Sqrt_enable_SI                          (Sqrt_enable_SO                 ),
   .D_DI                                    (Sqrt_D2                        ),
   .D_DO                                    (Sqrt_Da2                       ),
   .Sum_DO                                  (Thi_iteration_cell_sum_D       ),
   .Carry_out_DO                            (Thi_iteration_cell_carry_D     )
);

iteration_div_sqrt #(29) iteration_unit_U3
(
   .A_DI                                    (Fou_iteration_cell_a_D        ),
   .B_DI                                    (Fou_iteration_cell_b_D        ),
   .Div_enable_SI                           (Div_enable_SO                 ),
   .Sqrt_enable_SI                          (Sqrt_enable_SO                ),
   .D_DI                                    (Sqrt_D3                       ),
   .D_DO                                    (Sqrt_Da3                      ),
   .Sum_DO                                  (Fou_iteration_cell_sum_D      ),
   .Carry_out_DO                            (Fou_iteration_cell_carry_D    )
);

endmodule
