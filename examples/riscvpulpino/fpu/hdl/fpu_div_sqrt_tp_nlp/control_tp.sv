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
// Engineers:      Lei Li                    lile@iis.ee.ethz.ch              //
//                                                                            //
// Additional contributions by:                                               //
//                                                                            //
//                                                                            //
//                                                                            //
// Create Date:    01/12/2016                                                 //
// Design Name:    FPU                                                        //
// Module Name:    control_tp.sv                                              //
// Project Name:   Private FPU                                                //
// Language:       SystemVerilog                                              //
//                                                                            //
// Description:    the control logic  of div and sqrt                         //
//                                                                            //
//                                                                            //
// Revision:       19/01/2017                                                 //
//                                                                            //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

import fpu_defs_div_sqrt_tp::*;

module control_tp
#(
   parameter   Precision_ctl_Enable_S = 0,
   parameter   Accuracy_ctl_Enable_S  = 1
)
  (//Input
   input logic                                       Clk_CI,
   input logic                                       Rst_RBI,
   input logic                                       Div_start_SI ,
   input logic                                       Sqrt_start_SI,
   input logic                                       Start_SI,
   input logic [C_DIV_PC-1:0]                        Precision_ctl_SI,
   input logic [C_DIV_MANT:0]                        Numerator_DI,
   input logic [C_DIV_EXP:0]                         Exp_num_DI,
   input logic [C_DIV_MANT:0]                        Denominator_DI,
   input logic [C_DIV_EXP:0]                         Exp_den_DI,
   input logic [C_DIV_MANT+1+1:0]                    First_iteration_cell_sum_DI,
   input logic                                       First_iteration_cell_carry_DI,
   input logic [1:0]                                 Sqrt_Da0,
   input logic [C_DIV_MANT+1+2:0]                    Sec_iteration_cell_sum_DI,
   input logic                                       Sec_iteration_cell_carry_DI,
   input logic [1:0]                                 Sqrt_Da1,
   input logic [C_DIV_MANT+1+3:0]                    Thi_iteration_cell_sum_DI,
   input logic                                       Thi_iteration_cell_carry_DI,
   input logic [1:0]                                 Sqrt_Da2,
   input logic [C_DIV_MANT+1+4:0]                    Fou_iteration_cell_sum_DI,
   input logic                                       Fou_iteration_cell_carry_DI,
   input logic [1:0]                                 Sqrt_Da3,

   output logic                                      Div_start_dly_SO ,
   output logic                                      Sqrt_start_dly_SO,
   output logic                                      Div_enable_SO,
   output logic                                      Sqrt_enable_SO,

   output logic [1:0]                                Sqrt_D0,
   output logic [1:0]                                Sqrt_D1,
   output logic [1:0]                                Sqrt_D2,
   output logic [1:0]                                Sqrt_D3,

   output logic [C_DIV_MANT+1+1:0]                   First_iteration_cell_a_DO,
   output logic [C_DIV_MANT+1+1:0]                   First_iteration_cell_b_DO,
   output logic [C_DIV_MANT+1+2:0]                   Sec_iteration_cell_a_DO,
   output logic [C_DIV_MANT+1+2:0]                   Sec_iteration_cell_b_DO,
   output logic [C_DIV_MANT+1+3:0]                   Thi_iteration_cell_a_DO,
   output logic [C_DIV_MANT+1+3:0]                   Thi_iteration_cell_b_DO,
   output logic [C_DIV_MANT+1+4:0]                   Fou_iteration_cell_a_DO,
   output logic [C_DIV_MANT+1+4:0]                   Fou_iteration_cell_b_DO,

   //To next stage
   output logic                                      Ready_SO,
   output logic                                      Done_SO,
   output logic [C_DIV_MANT:0]                       Mant_result_prenorm_DO,
   output logic [3:0]                                Round_bit_DO,
   output logic [C_DIV_EXP+1:0]                      Exp_result_prenorm_DO
 );

   logic  [C_DIV_MANT+1+4:0]                         Partial_remainder_DN,Partial_remainder_DP;
   logic  [C_DIV_MANT+4:0]                           Quotient_DP;
   /////////////////////////////////////////////////////////////////////////////
   // Assign Inputs                                                          //
   /////////////////////////////////////////////////////////////////////////////
   logic [C_DIV_MANT+1:0]                            Numerator_se_D;  //sign extension and hidden bit
   logic [C_DIV_MANT+1:0]                            Denominator_se_D; //signa extension and hidden bit
   logic [C_DIV_MANT+1:0]                            Denominator_se_DB;  //1's complement

   assign  Numerator_se_D={1'b0,Numerator_DI};

   assign  Denominator_se_D={1'b0,Denominator_DI};
   assign  Denominator_se_DB=~Denominator_se_D;


   logic [C_DIV_MANT+1:0]                            Mant_D_sqrt_Norm;

   assign Mant_D_sqrt_Norm=Exp_num_DI[0]?{1'b0,Numerator_DI}:{Numerator_DI,1'b0}; //for sqrt

   /////////////////////////////////////////////////////////////////////////////
   // Precision Control                                                       //
   /////////////////////////////////////////////////////////////////////////////

   logic [C_DIV_PC-1:0]                              Precision_ctl_S;

   always_ff @(posedge Clk_CI, negedge Rst_RBI)
     begin
        if(~Rst_RBI)
          begin
            Precision_ctl_S<='b0;
          end
        else if(Start_SI)
          begin
             if(Precision_ctl_Enable_S==1)
               begin
                 Precision_ctl_S<=Precision_ctl_SI;
               end
             else
               begin
                 Precision_ctl_S<=5'b10111;
               end
          end
        else
          begin
            Precision_ctl_S<=Precision_ctl_S;
          end
    end

     logic [2:0]                                     State_ctl_S;

     always_comb
       begin
         if(Precision_ctl_Enable_S==1)
         begin
         case(Precision_ctl_S)
           5'b01000,5'b01001,5'b01010,5'b01011:
             begin
               State_ctl_S<=3'b010;
             end
           5'b01100,5'b01101,5'b01110,5'b01111:
             begin
               State_ctl_S<=3'b011;
             end
           5'b10000,5'b10001,5'b10010,5'b10011:
             begin
               State_ctl_S<=3'b100;
             end
           5'b10100,5'b10101,5'b10110,5'b10111:
             begin
               State_ctl_S<=3'b101;
             end
           default:
             begin
               State_ctl_S<=3'b101;
             end
           endcase
          end
        else if(Accuracy_ctl_Enable_S==1)
             begin
               State_ctl_S<=3'b110;
             end
        else
             begin
               State_ctl_S<=3'b101;
             end
       end

   /////////////////////////////////////////////////////////////////////////////
   // control logic                                                           //
   /////////////////////////////////////////////////////////////////////////////

   logic                                               Div_start_dly_S;

   always_ff @(posedge Clk_CI, negedge Rst_RBI)   //  generate Div_start_dly_S signal
     begin
        if(~Rst_RBI)
          begin
            Div_start_dly_S<=1'b0;
          end
        else if(Div_start_SI)
         begin
           Div_start_dly_S<=1'b1;
         end
        else
          begin
            Div_start_dly_S<=1'b0;
          end
    end

   assign Div_start_dly_SO=Div_start_dly_S;

   always_ff @(posedge Clk_CI, negedge Rst_RBI)   //  generate Div_enable_SO signal
     begin
        if(~Rst_RBI)
          begin
            Div_enable_SO<=1'b0;
          end
        else if(Div_start_SI)
         begin
           Div_enable_SO<=1'b1;
         end
         else if(Done_SO)
          begin
            Div_enable_SO<=1'b0;
          end
       else
          begin
            Div_enable_SO<=Div_enable_SO;
          end
    end


   logic                                                Sqrt_start_dly_S;

   always_ff @(posedge Clk_CI, negedge Rst_RBI)   //  generate Sqrt_start_dly_SI signal
     begin
        if(~Rst_RBI)
          begin
            Sqrt_start_dly_S<=1'b0;
          end
        else if(Sqrt_start_SI)
         begin
           Sqrt_start_dly_S<=1'b1;
         end
        else
          begin
            Sqrt_start_dly_S<=1'b0;
          end
      end
    assign Sqrt_start_dly_SO=Sqrt_start_dly_S;

   always_ff @(posedge Clk_CI, negedge Rst_RBI)   //  generate Sqrt_enable_SO signal
     begin
        if(~Rst_RBI)
          begin
            Sqrt_enable_SO<=1'b0;
          end
        else if(Sqrt_start_SI)
         begin
           Sqrt_enable_SO<=1'b1;
         end
        else if(Done_SO)
          begin
           Sqrt_enable_SO<=1'b0;
          end
       else
          begin
           Sqrt_enable_SO<=Sqrt_enable_SO;
          end
    end

   logic [2:0]                                                  Crtl_cnt_S;
   logic                                                        Start_dly_S;

   assign   Start_dly_S=Div_start_dly_S |Sqrt_start_dly_S;

   logic       Fsm_enable_S;
   assign      Fsm_enable_S=(Start_dly_S | (| Crtl_cnt_S[2:0]));

   logic  Final_state_S;
   assign     Final_state_S= (Crtl_cnt_S==State_ctl_S);
   //4 iteration units per stage
   always_ff @(posedge Clk_CI, negedge Rst_RBI) //control_FSM
     begin
        if (~Rst_RBI)
          begin
             Crtl_cnt_S    <= '0;
          end
          else if (Final_state_S)
            begin
              Crtl_cnt_S    <= '0;
            end
          else if(Fsm_enable_S) // one cycle Start_SI
            begin
              Crtl_cnt_S    <= Crtl_cnt_S+1;
            end
          else
            begin
              Crtl_cnt_S    <= '0;
            end
     end // always_ff



    always_ff @(posedge Clk_CI, negedge Rst_RBI) //Generate  Done_SO,  they can share this Done_SO.
      begin
        if(~Rst_RBI)
          begin
            Done_SO<=1'b0;
          end
        else if(Start_SI)
          begin
            Done_SO<=1'b0;
          end
        else if(Final_state_S)
          begin
            Done_SO<=1'b1;
          end
        else
          begin
            Done_SO<=1'b0;
          end
       end




   always_ff @(posedge Clk_CI, negedge Rst_RBI) //Generate  Ready_SO
     begin
       if(~Rst_RBI)
         begin
           Ready_SO<=1'b1;
         end

       else if(Start_SI)
         begin
           Ready_SO<=1'b0;
         end
       else if(Final_state_S)
         begin
           Ready_SO<=1'b1;
         end
       else
         begin
           Ready_SO<=Ready_SO;
         end
     end

   //logic [C_DIV_MANT+1:0]                                        Sqrt_R4;//partial remainder for each iteration

   logic [3:0]                                                   Qcnt0, Q_cnt_cmp_0;
   logic [6:0]                                                   Qcnt1, Q_cnt_cmp_1;
   logic [10:0]                                                  Qcnt2, Q_cnt_cmp_2;
   logic [14:0]                                                  Qcnt3, Q_cnt_cmp_3;
   logic [18:0]                                                  Qcnt4, Q_cnt_cmp_4;
   logic [22:0]                                                  Qcnt5, Q_cnt_cmp_5;
   logic [26:0]                                                  Qcnt6, Q_cnt_cmp_6;   //To improve the accuracy
   logic [C_DIV_MANT+1+1:0]                                      Sqrt_R0,Sqrt_Q0,Q_sqrt0,Q_sqrt_com_0;
   logic [C_DIV_MANT+1+2:0]                                      Sqrt_R1,Sqrt_Q1,Q_sqrt1,Q_sqrt_com_1;
   logic [C_DIV_MANT+1+3:0]                                      Sqrt_R2,Sqrt_Q2,Q_sqrt2,Q_sqrt_com_2;
   logic [C_DIV_MANT+1+4:0]                                      Sqrt_R3,Sqrt_Q3,Q_sqrt3,Q_sqrt_com_3,Sqrt_R4; //Sqrt_Q4;

   //logic [C_DIV_MANT+1:0]                                        Q_sqrt0,Q_sqrt1,Q_sqrt2,Q_sqrt3,Q_sqrt4;
   //logic [C_DIV_MANT+1:0]                                        Q_sqrt_com_0,Q_sqrt_com_1,Q_sqrt_com_2,Q_sqrt_com_3,Q_sqrt_com_4;

   assign Qcnt0=    {1'b0,            ~First_iteration_cell_sum_DI[24],~Sec_iteration_cell_sum_DI[24],~Thi_iteration_cell_sum_DI[24]};  //qk for each feedback
   assign Qcnt1=    {Quotient_DP[3:0],~First_iteration_cell_sum_DI[24],~Sec_iteration_cell_sum_DI[24],~Thi_iteration_cell_sum_DI[24]};
   assign Qcnt2=    {Quotient_DP[7:0],~First_iteration_cell_sum_DI[24],~Sec_iteration_cell_sum_DI[24],~Thi_iteration_cell_sum_DI[24]};
   assign Qcnt3=    {Quotient_DP[11:0],~First_iteration_cell_sum_DI[24],~Sec_iteration_cell_sum_DI[24],~Thi_iteration_cell_sum_DI[24]};
   assign Qcnt4=    {Quotient_DP[15:0],~First_iteration_cell_sum_DI[24],~Sec_iteration_cell_sum_DI[24],~Thi_iteration_cell_sum_DI[24]};
   assign Qcnt5=    {Quotient_DP[19:0],~First_iteration_cell_sum_DI[24],~Sec_iteration_cell_sum_DI[24],~Thi_iteration_cell_sum_DI[24]};  //just 24 iteration
   assign Qcnt6=    {Quotient_DP[23:0],~First_iteration_cell_sum_DI[25],~Sec_iteration_cell_sum_DI[26],~Thi_iteration_cell_sum_DI[27]};  //To improve the accuracy



   assign Q_cnt_cmp_0=~Qcnt0;
   assign Q_cnt_cmp_1=~Qcnt1;
   assign Q_cnt_cmp_2=~Qcnt2;
   assign Q_cnt_cmp_3=~Qcnt3;
   assign Q_cnt_cmp_4=~Qcnt4;
   assign Q_cnt_cmp_5=~Qcnt5;
   assign Q_cnt_cmp_6=~Qcnt6;   //To improve the accuracy





  always_comb begin  // the intermediate operands for sqrt
  case(Crtl_cnt_S)

    3'b000: begin

       Sqrt_D0=Mant_D_sqrt_Norm[C_DIV_MANT+1:C_DIV_MANT];
       Sqrt_D1=Mant_D_sqrt_Norm[C_DIV_MANT-1:C_DIV_MANT-2];
       Sqrt_D2=Mant_D_sqrt_Norm[C_DIV_MANT-3:C_DIV_MANT-4];
       Sqrt_D3=Mant_D_sqrt_Norm[C_DIV_MANT-5:C_DIV_MANT-6];

       Q_sqrt0={24'h000000,Qcnt0[3]};
       Q_sqrt1={23'h000000,Qcnt0[3:2]};
       Q_sqrt2={22'h000000,Qcnt0[3:1]};
       Q_sqrt3={21'h000000,Qcnt0[3:0]};

       Q_sqrt_com_0={24'hffffff, Q_cnt_cmp_0[3]};
       Q_sqrt_com_1={23'h7fffff,Q_cnt_cmp_0[3:2]};
       Q_sqrt_com_2={22'h3fffff,Q_cnt_cmp_0[3:1]};
       Q_sqrt_com_3={21'h1fffff,Q_cnt_cmp_0[3:0]};

       Sqrt_Q0=Q_sqrt_com_0;
       Sqrt_Q1=First_iteration_cell_sum_DI[24]?Q_sqrt1:Q_sqrt_com_1;
       Sqrt_Q2=Sec_iteration_cell_sum_DI[24]?Q_sqrt2:Q_sqrt_com_2;
       Sqrt_Q3=Thi_iteration_cell_sum_DI[24]?Q_sqrt3:Q_sqrt_com_3;

    end

    3'b001: begin
       Sqrt_D0=Mant_D_sqrt_Norm[C_DIV_MANT-7:C_DIV_MANT-8];
       Sqrt_D1=Mant_D_sqrt_Norm[C_DIV_MANT-9:C_DIV_MANT-10];
       Sqrt_D2=Mant_D_sqrt_Norm[C_DIV_MANT-11:C_DIV_MANT-12];
       Sqrt_D3=Mant_D_sqrt_Norm[C_DIV_MANT-13:C_DIV_MANT-14];

       Q_sqrt0={21'h000000,Qcnt1[6:3]};
       Q_sqrt1={20'h00000,Qcnt1[6:2]};
       Q_sqrt2={19'h00000,Qcnt1[6:1]};
       Q_sqrt3={18'h00000,Qcnt1[6:0]};

       Q_sqrt_com_0={21'h1fffff,Q_cnt_cmp_1[6:3]};
       Q_sqrt_com_1={20'hfffff,Q_cnt_cmp_1[6:2]};
       Q_sqrt_com_2={19'h7ffff,Q_cnt_cmp_1[6:1]};
       Q_sqrt_com_3={18'h3ffff,Q_cnt_cmp_1[6:0]};


       Sqrt_Q0=Quotient_DP[0]?Q_sqrt_com_0:Q_sqrt0;
       Sqrt_Q1=First_iteration_cell_sum_DI[24]?Q_sqrt1:Q_sqrt_com_1;
       Sqrt_Q2=Sec_iteration_cell_sum_DI[24]?Q_sqrt2:Q_sqrt_com_2;
       Sqrt_Q3=Thi_iteration_cell_sum_DI[24]?Q_sqrt3:Q_sqrt_com_3;

    end

    3'b010: begin
       Sqrt_D0=Mant_D_sqrt_Norm[C_DIV_MANT-15:C_DIV_MANT-16];
       Sqrt_D1=Mant_D_sqrt_Norm[C_DIV_MANT-17:C_DIV_MANT-18];
       Sqrt_D2=Mant_D_sqrt_Norm[C_DIV_MANT-19:C_DIV_MANT-20];
       Sqrt_D3=Mant_D_sqrt_Norm[C_DIV_MANT-21:C_DIV_MANT-22];

       Q_sqrt0={17'h00000,Qcnt2[10:3]};
       Q_sqrt1={16'h0000,Qcnt2[10:2]};
       Q_sqrt2={15'h0000,Qcnt2[10:1]};
       Q_sqrt3={14'h0000,Qcnt2[10:0]};

       Q_sqrt_com_0={17'h1ffff,Q_cnt_cmp_2[10:3]};
       Q_sqrt_com_1={16'hffff,Q_cnt_cmp_2[10:2]};
       Q_sqrt_com_2={15'h7fff,Q_cnt_cmp_2[10:1]};
       Q_sqrt_com_3={14'h3fff,Q_cnt_cmp_2[10:0]};

       Sqrt_Q0=Quotient_DP[0]?Q_sqrt_com_0:Q_sqrt0;
       Sqrt_Q1=First_iteration_cell_sum_DI[24]?Q_sqrt1:Q_sqrt_com_1;
       Sqrt_Q2=Sec_iteration_cell_sum_DI[24]?Q_sqrt2:Q_sqrt_com_2;
       Sqrt_Q3=Thi_iteration_cell_sum_DI[24]?Q_sqrt3:Q_sqrt_com_3;

    end

    3'b011: begin
       Sqrt_D0={Mant_D_sqrt_Norm[0],1'b0};;
       Sqrt_D1='0;
       Sqrt_D2='0;
       Sqrt_D3='0;

       Q_sqrt0={13'h0000,Qcnt3[14:3]};
       Q_sqrt1={12'h000,Qcnt3[14:2]};
       Q_sqrt2={11'h000,Qcnt3[14:1]};
       Q_sqrt3={10'h000,Qcnt3[14:0]};

       Q_sqrt_com_0={13'h1fff,Q_cnt_cmp_3[14:3]};
       Q_sqrt_com_1={12'hfff,Q_cnt_cmp_3[14:2]};
       Q_sqrt_com_2={11'h7ff,Q_cnt_cmp_3[14:1]};
       Q_sqrt_com_3={10'h3ff,Q_cnt_cmp_3[14:0]};

       Sqrt_Q0=Quotient_DP[0]?Q_sqrt_com_0:Q_sqrt0;
       Sqrt_Q1=First_iteration_cell_sum_DI[24]?Q_sqrt1:Q_sqrt_com_1;
       Sqrt_Q2=Sec_iteration_cell_sum_DI[24]?Q_sqrt2:Q_sqrt_com_2;
       Sqrt_Q3=Thi_iteration_cell_sum_DI[24]?Q_sqrt3:Q_sqrt_com_3;

    end

    3'b100: begin
       Sqrt_D0='0;
       Sqrt_D1='0;
       Sqrt_D2='0;
       Sqrt_D3='0;

       Q_sqrt0={9'h000,Qcnt4[18:3]};
       Q_sqrt1={8'h00,Qcnt4[18:2]};
       Q_sqrt2={7'h00,Qcnt4[18:1]};
       Q_sqrt3={6'h00,Qcnt4[18:0]};

       Q_sqrt_com_0={9'h1ff,Q_cnt_cmp_4[18:3]};
       Q_sqrt_com_1={8'hff,Q_cnt_cmp_4[18:2]};
       Q_sqrt_com_2={7'h7f,Q_cnt_cmp_4[18:1]};
       Q_sqrt_com_3={6'h3f,Q_cnt_cmp_4[18:0]};

       Sqrt_Q0=Quotient_DP[0]?Q_sqrt_com_0:Q_sqrt0;
       Sqrt_Q1=First_iteration_cell_sum_DI[24]?Q_sqrt1:Q_sqrt_com_1;
       Sqrt_Q2=Sec_iteration_cell_sum_DI[24]?Q_sqrt2:Q_sqrt_com_2;
       Sqrt_Q3=Thi_iteration_cell_sum_DI[24]?Q_sqrt3:Q_sqrt_com_3;

    end

    3'b101: begin
       Sqrt_D0='0;
       Sqrt_D1='0;
       Sqrt_D2='0;
       Sqrt_D3='0;

       Q_sqrt0={5'h00,Qcnt5[22:3]};
       Q_sqrt1={4'h0,Qcnt5[22:2]};
       Q_sqrt2={3'h0,Qcnt5[22:1]};
       Q_sqrt3={2'h0,Qcnt5[22:0]};

       Q_sqrt_com_0={5'h1f,Q_cnt_cmp_5[22:3]};
       Q_sqrt_com_1={4'hf,Q_cnt_cmp_5[22:2]};
       Q_sqrt_com_2={3'h7,Q_cnt_cmp_5[22:1]};
       Q_sqrt_com_3={2'h3,Q_cnt_cmp_5[22:0]};

       Sqrt_Q0=Quotient_DP[0]?Q_sqrt_com_0:Q_sqrt0;
       Sqrt_Q1=First_iteration_cell_sum_DI[24]?Q_sqrt1:Q_sqrt_com_1;
       Sqrt_Q2=Sec_iteration_cell_sum_DI[24]?Q_sqrt2:Q_sqrt_com_2;
       Sqrt_Q3=Thi_iteration_cell_sum_DI[24]?Q_sqrt3:Q_sqrt_com_3;

     end

//  To improve the accuracy
    3'b110: begin
       Sqrt_D0='0;
       Sqrt_D1='0;
       Sqrt_D2='0;
       Sqrt_D3='0;

       Q_sqrt0={2'h0,Qcnt6[26:3]};                  //26bits
       Q_sqrt1={2'h0,Qcnt6[26:2]};                  //27bits
       Q_sqrt2={2'h0,Qcnt6[26:1]};                  //28bits
       Q_sqrt3={2'h0,Qcnt6[26:0]};                  //29bits

       Q_sqrt_com_0={2'h3,Q_cnt_cmp_6[26:3]};       //26bits
       Q_sqrt_com_1={2'h3,Q_cnt_cmp_6[26:2]};       //27bits
       Q_sqrt_com_2={2'h3,Q_cnt_cmp_6[26:1]};       //28bits
       Q_sqrt_com_3={2'h3,Q_cnt_cmp_6[26:0]};       //29bits

       Sqrt_Q0=Quotient_DP[0]?Q_sqrt_com_0:Q_sqrt0;
       Sqrt_Q1=First_iteration_cell_sum_DI[25]?Q_sqrt1:Q_sqrt_com_1;
       Sqrt_Q2=Sec_iteration_cell_sum_DI[26]?Q_sqrt2:Q_sqrt_com_2;
       Sqrt_Q3=Thi_iteration_cell_sum_DI[27]?Q_sqrt3:Q_sqrt_com_3;

     end

   default: begin
       Sqrt_D0='0;
       Sqrt_D1='0;
       Sqrt_D2='0;
       Sqrt_D3='0;

       Q_sqrt0='0;
       Q_sqrt1='0;
       Q_sqrt2='0;
       Q_sqrt3='0;
 //      Q_sqrt4='0;

       Q_sqrt_com_0='0;
       Q_sqrt_com_1='0;
       Q_sqrt_com_2='0;
       Q_sqrt_com_3='0;
//       Q_sqrt_com_4='0;

       Sqrt_Q0='0;
       Sqrt_Q1='0;
       Sqrt_Q2='0;
       Sqrt_Q3='0;

    end
  endcase
 end

  logic                                            Extra_Final_State_S;
  assign Extra_Final_State_S = (Crtl_cnt_S==3'b110)&&Sqrt_enable_SO;
  logic                                            Extra_Near_Final_State_S;
  assign Extra_Near_Final_State_S = (Crtl_cnt_S==3'b101)&&Sqrt_enable_SO&&Accuracy_ctl_Enable_S;

  assign Sqrt_R0=Extra_Final_State_S ? {Partial_remainder_DP[C_DIV_MANT+1],Partial_remainder_DP[C_DIV_MANT+1:0]} : ((Sqrt_start_dly_S)?'0:{1'b0,Partial_remainder_DP[C_DIV_MANT+1:0]});
  assign Sqrt_R1=Extra_Final_State_S ? {First_iteration_cell_sum_DI[25],First_iteration_cell_sum_DI[23:0],Sqrt_Da0} : {2'b00,First_iteration_cell_sum_DI[24],First_iteration_cell_sum_DI[21:0],Sqrt_Da0} ;
  assign Sqrt_R2=Extra_Final_State_S ? {Sec_iteration_cell_sum_DI[26],Sec_iteration_cell_sum_DI[24:0],Sqrt_Da1} : {3'b000,Sec_iteration_cell_sum_DI[24],Sec_iteration_cell_sum_DI[21:0],Sqrt_Da1};
  assign Sqrt_R3=Extra_Final_State_S ? {Thi_iteration_cell_sum_DI[27],Thi_iteration_cell_sum_DI[25:0],Sqrt_Da2} : {4'b0000,Thi_iteration_cell_sum_DI[24],Thi_iteration_cell_sum_DI[21:0],Sqrt_Da2};
  assign Sqrt_R4=Extra_Final_State_S ? {Fou_iteration_cell_sum_DI[28],Fou_iteration_cell_sum_DI[25:0],Sqrt_Da3} : { Extra_Near_Final_State_S ? {3'b000,Fou_iteration_cell_sum_DI[24],Fou_iteration_cell_sum_DI[22:0],Sqrt_Da3} : {4'b0000,Fou_iteration_cell_sum_DI[24],Fou_iteration_cell_sum_DI[21:0],Sqrt_Da3} };

  //                   for           iteration cell_U0
  logic [C_DIV_MANT+1:0]                           First_iteration_cell_div_a_D,First_iteration_cell_div_b_D;
  logic                                            Sel_b_for_first_S;


  assign First_iteration_cell_div_a_D=(Div_start_dly_S)?{1'b0,Numerator_se_D}:{1'b0,Partial_remainder_DP[C_DIV_MANT:0],Quotient_DP[0]};
  assign Sel_b_for_first_S=(Div_start_dly_S)?1:Quotient_DP[0];
  assign First_iteration_cell_div_b_D=Sel_b_for_first_S?{1'b0,Denominator_se_DB}:{1'b0,Denominator_se_D};
  assign First_iteration_cell_a_DO=Sqrt_enable_SO?Sqrt_R0:{1'b0,First_iteration_cell_div_a_D};
  assign First_iteration_cell_b_DO=Sqrt_enable_SO?Sqrt_Q0:{1'b0,First_iteration_cell_div_b_D};


  //                   for           iteration cell_U1
  logic [C_DIV_MANT+1:0]                          Sec_iteration_cell_div_a_D,Sec_iteration_cell_div_b_D;
  logic                                           Sel_b_for_sec_S;

  assign Sec_iteration_cell_div_a_D={2'b00,First_iteration_cell_sum_DI[C_DIV_MANT:0],~First_iteration_cell_sum_DI[24]};
  assign Sel_b_for_sec_S=~First_iteration_cell_sum_DI[24];
  assign Sec_iteration_cell_div_b_D=Sel_b_for_sec_S?{2'b00,Denominator_se_DB}:{2'b00,Denominator_se_D};

  assign Sec_iteration_cell_a_DO=Sqrt_enable_SO?Sqrt_R1:{2'b00,Sec_iteration_cell_div_a_D};
  assign Sec_iteration_cell_b_DO=Sqrt_enable_SO?Sqrt_Q1:{2'b00,Sec_iteration_cell_div_b_D};


  //                   for           iteration cell_U2
  logic [C_DIV_MANT+1:0]                          Thi_iteration_cell_div_a_D,Thi_iteration_cell_div_b_D;
  logic                                           Sel_b_for_thi_S;

  assign Thi_iteration_cell_div_a_D={3'b000,Sec_iteration_cell_sum_DI[C_DIV_MANT:0],~Sec_iteration_cell_sum_DI[24]};
  assign Sel_b_for_thi_S=~Sec_iteration_cell_sum_DI[24];
  assign Thi_iteration_cell_div_b_D=Sel_b_for_thi_S?{3'b000,Denominator_se_DB}:{3'b000,Denominator_se_D};
  assign Thi_iteration_cell_a_DO=Sqrt_enable_SO?Sqrt_R2:{3'b000,Thi_iteration_cell_div_a_D};
  assign Thi_iteration_cell_b_DO=Sqrt_enable_SO?Sqrt_Q2:{3'b000,Thi_iteration_cell_div_b_D};


  //                   for           iteration cell_U3
  logic [C_DIV_MANT+1:0]                          Fou_iteration_cell_div_a_D,Fou_iteration_cell_div_b_D;
  logic                                           Sel_b_for_fou_S;

  assign Fou_iteration_cell_div_a_D={4'b0000,Thi_iteration_cell_sum_DI[C_DIV_MANT:0],~Thi_iteration_cell_sum_DI[24]};
  assign Sel_b_for_fou_S=~Thi_iteration_cell_sum_DI[24];
  assign Fou_iteration_cell_div_b_D=Sel_b_for_fou_S?{4'b0000,Denominator_se_DB}:{4'b0000,Denominator_se_D};
  assign Fou_iteration_cell_a_DO=Sqrt_enable_SO?Sqrt_R3:{4'b0000,Fou_iteration_cell_div_a_D};
  assign Fou_iteration_cell_b_DO=Sqrt_enable_SO?Sqrt_Q3:{4'b0000,Fou_iteration_cell_div_b_D};

  always_comb
    begin  //
     if (Fsm_enable_S)
       Partial_remainder_DN = Sqrt_enable_SO?Sqrt_R4:Fou_iteration_cell_sum_DI;
      else
       Partial_remainder_DN = Partial_remainder_DP;
    end

   always_ff @(posedge Clk_CI, negedge Rst_RBI)   // partial_remainder
     begin
        if(~Rst_RBI)
          begin
             Partial_remainder_DP <= '0;
          end
        else
          begin
             Partial_remainder_DP <= Partial_remainder_DN;
          end
    end

   logic [C_DIV_MANT+4:0] Quotient_DN;

  always_comb
    begin
      if(Fsm_enable_S)
         Quotient_DN=Extra_Final_State_S ? {Quotient_DP[C_DIV_MANT:0],First_iteration_cell_carry_DI,Sec_iteration_cell_carry_DI,Thi_iteration_cell_carry_DI,Fou_iteration_cell_carry_DI} : {Quotient_DP[C_DIV_MANT:0],~First_iteration_cell_sum_DI[24],~Sec_iteration_cell_sum_DI[24],~Thi_iteration_cell_sum_DI[24],~Fou_iteration_cell_sum_DI[24]};
      else
         Quotient_DN=Quotient_DP;
     end

   always_ff @(posedge Clk_CI, negedge Rst_RBI)   // Quotient
     begin
        if(~Rst_RBI)
          begin
          Quotient_DP <= '0;
          end
        else
          Quotient_DP <= Quotient_DN;
    end

   logic                                               Msc_D;
   logic    [C_DIV_MANT+1:0]                           Sum_msc_D;

   assign {Msc_D,Sum_msc_D}=First_iteration_cell_div_a_D[C_DIV_MANT+1:0]+First_iteration_cell_div_b_D[C_DIV_MANT+1:0];  //last iteration for division
   logic [C_DIV_MANT:0]                                Mant_result_prenorm_noncorrect_D; //no correction with MSC
   logic [C_DIV_MANT:0]                                Msc_forcorrect_D;
   logic [C_DIV_MANT+1:0]                              Mant_result_prenorm_correct_D; // correction with MSC

   /////////////////////////////////////////////////////////////////////////////
   // Precision Control for outputs                                          //
   /////////////////////////////////////////////////////////////////////////////


     always_comb
       begin
         if(Precision_ctl_Enable_S==1)
         begin
         case(Precision_ctl_S)
           5'b01000:
             begin
               Mant_result_prenorm_noncorrect_D={Quotient_DP[C_DIV_MANT-12:3],15'b0};
               Msc_forcorrect_D={8'b0,Quotient_DP[2],15'b0};
             end
           5'b01001:
             begin
               Mant_result_prenorm_noncorrect_D={Quotient_DP[C_DIV_MANT-12:2],14'b0};
               Msc_forcorrect_D={9'b0,Quotient_DP[1],14'b0};
             end
           5'b01010:
             begin
               Mant_result_prenorm_noncorrect_D={Quotient_DP[C_DIV_MANT-12:1],13'b0};
               Msc_forcorrect_D={10'b0,Quotient_DP[0],13'b0};
             end
           5'b01011:
             begin
               Mant_result_prenorm_noncorrect_D={Quotient_DP[C_DIV_MANT-12:0],12'b0};
               Msc_forcorrect_D={11'b0,Msc_D,12'b0};
             end
       ///////////////////////////////////////////////////////////////////////
           5'b01100:
             begin
               Mant_result_prenorm_noncorrect_D={Quotient_DP[C_DIV_MANT-8:3],11'b0};
               Msc_forcorrect_D={12'b0,Quotient_DP[2],11'b0};
             end
           5'b01101:
             begin
               Mant_result_prenorm_noncorrect_D={Quotient_DP[C_DIV_MANT-8:2],10'b0};
               Msc_forcorrect_D={13'b0,Quotient_DP[1],10'b0};
             end
           5'b01110:
             begin
               Mant_result_prenorm_noncorrect_D={Quotient_DP[C_DIV_MANT-8:1],9'b0};
               Msc_forcorrect_D={14'b0,Quotient_DP[0],9'b0};
             end
           5'b01111:
             begin
               Mant_result_prenorm_noncorrect_D={Quotient_DP[C_DIV_MANT-8:0],8'b0};
               Msc_forcorrect_D={15'b0,Msc_D,8'b0};
             end
       ///////////////////////////////////////////////////////////////////////
           5'b10000:
             begin
               Mant_result_prenorm_noncorrect_D={Quotient_DP[C_DIV_MANT-4:3],7'b0};
               Msc_forcorrect_D={16'b0,Quotient_DP[2],7'b0};
             end
           5'b10001:
             begin
               Mant_result_prenorm_noncorrect_D={Quotient_DP[C_DIV_MANT-4:2],6'b0};
               Msc_forcorrect_D={17'b0,Quotient_DP[1],6'b0};
             end
           5'b10010:
             begin
               Mant_result_prenorm_noncorrect_D={Quotient_DP[C_DIV_MANT-4:1],5'b0};
               Msc_forcorrect_D={18'b0,Quotient_DP[0],5'b0};
             end
           5'b10011:
             begin
               Mant_result_prenorm_noncorrect_D={Quotient_DP[C_DIV_MANT-4:0],4'b0};
               Msc_forcorrect_D={19'b0,Msc_D,4'b0};
             end
       ///////////////////////////////////////////////////////////////////////
           5'b10100:
             begin
               Mant_result_prenorm_noncorrect_D={Quotient_DP[C_DIV_MANT:3],3'b0};
               Msc_forcorrect_D={20'b0,Quotient_DP[2],3'b0};
             end
           5'b10101:
             begin
               Mant_result_prenorm_noncorrect_D={Quotient_DP[C_DIV_MANT:2],2'b0};
               Msc_forcorrect_D={21'b0,Quotient_DP[1],2'b0};
             end
           5'b10110:
             begin
               Mant_result_prenorm_noncorrect_D={Quotient_DP[C_DIV_MANT:1],1'b0};
               Msc_forcorrect_D={22'b0,Quotient_DP[0],1'b0};
             end
           5'b10111:
             begin
               Mant_result_prenorm_noncorrect_D=Quotient_DP[C_DIV_MANT:0];
               Msc_forcorrect_D={23'b0,Msc_D};
             end
           default:
             begin
               Mant_result_prenorm_noncorrect_D=Quotient_DP[C_DIV_MANT:0];
               Msc_forcorrect_D={23'b0,Msc_D};
             end
           endcase
           end
           else
             begin
               Mant_result_prenorm_noncorrect_D=Quotient_DP[C_DIV_MANT:0];
               Msc_forcorrect_D={23'b0,Msc_D};
             end

       end


   assign Mant_result_prenorm_correct_D= Mant_result_prenorm_noncorrect_D + {Div_enable_SO?Msc_forcorrect_D:24'b0};
   assign Mant_result_prenorm_DO = Accuracy_ctl_Enable_S ? Quotient_DP[C_DIV_MANT+4:4] : {Mant_result_prenorm_correct_D[C_DIV_MANT+1]?Mant_result_prenorm_noncorrect_D:Mant_result_prenorm_correct_D[C_DIV_MANT:0]};

   //logic  [3:0] Sticky_bit_D;
   //assign Round_bit_DO = Accuracy_ctl_Enable_S ? {Div_enable_SO ? {Quotient_DP[3:1],1'b1} : Quotient_DP[3:0]}: 3'b000;
   assign Round_bit_DO = Accuracy_ctl_Enable_S ? {Quotient_DP[3:1],1'b1}: 3'b000;

// resultant exponent
   logic   [C_DIV_EXP+1:0]    Exp_result_prenorm_DN,Exp_result_prenorm_DP;

   logic   [C_DIV_EXP+1:0]                                Exp_add_a_D;
   logic   [C_DIV_EXP+1:0]                                Exp_add_b_D;
   logic   [C_DIV_EXP+1:0]                                Exp_add_c_D;

     assign Exp_add_a_D = {Sqrt_start_dly_S?{Exp_num_DI[C_DIV_EXP],Exp_num_DI[C_DIV_EXP],Exp_num_DI[C_DIV_EXP],Exp_num_DI[C_DIV_EXP:1]}:{Exp_num_DI[C_DIV_EXP],Exp_num_DI[C_DIV_EXP],Exp_num_DI}};
     assign Exp_add_b_D = {Sqrt_start_dly_S?{1'b0,{C_DIV_EXP_ZERO},Exp_num_DI[0]}:{~Exp_den_DI[C_DIV_EXP],~Exp_den_DI[C_DIV_EXP],~Exp_den_DI}};
     assign Exp_add_c_D = {Div_start_dly_S?{2'b00,{C_DIV_BIAS_AONE}}:{2'b00,{C_DIV_HALF_BIAS}}};
     assign Exp_result_prenorm_DN  = (Start_dly_S)?{Exp_add_a_D + Exp_add_b_D + Exp_add_c_D}:Exp_result_prenorm_DP;

    always_ff @(posedge Clk_CI, negedge Rst_RBI)
     begin
        if(~Rst_RBI)
          begin
            Exp_result_prenorm_DP <= '0;
          end
        else
          begin
            Exp_result_prenorm_DP<=  Exp_result_prenorm_DN;
          end
     end

    assign Exp_result_prenorm_DO = Exp_result_prenorm_DP;

endmodule
