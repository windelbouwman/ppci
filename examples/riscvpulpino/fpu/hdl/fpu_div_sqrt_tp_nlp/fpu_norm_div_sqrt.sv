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
// Engineers:      Lei Li    lile@iis.ee.ethz.ch                              //
//                                                                            //
// Additional contributions by:                                               //
//                                                                            //
//                                                                            //
//                                                                            //
// Create Date:    01/12/2016                                                 //
// Design Name:    div_sqrt                                                   //
// Module Name:    fpu_norm_div_sqrt.sv                                       //
// Project Name:   FPU                                                        //
// Language:       SystemVerilog                                              //
//                                                                            //
// Description:    Floating point Normalizer/Rounding unit                    //
//                                                                            //
//                                                                            //
//                                                                            //
// Revision:        04/05/2017                                                //
//                  Update the normalization for special cases  by Lei Li     //
//                  25/07/2017                                                //
//                  Update some rounding by Lei Li                            //
//                                                                            //
//                                                                            //
//                                                                            //
//                                                                            //
//                                                                            //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

import fpu_defs_div_sqrt_tp::*;

module fpu_norm_div_sqrt
  (//Inputs
   input logic        [C_DIV_MANT_PRENORM-1:0] Mant_in_DI,
   input logic [3:0]                           Round_bit_DI,
   input logic signed [C_DIV_EXP+1:0]          Exp_in_DI,
   input logic                                 Sign_in_DI,
   input logic                                 Div_enable_SI,
   input logic                                 Sqrt_enable_SI,
   input logic                                 Inf_a_SI,
   input logic                                 Inf_b_SI,
   input logic                                 Zero_a_SI,
   input logic                                 Zero_b_SI,
   input logic                                 NaN_a_SI,
   input logic                                 NaN_b_SI,
   input logic [C_DIV_RM-1:0]                  RM_SI,
   //Outputs
   output logic [C_DIV_MANT-1:0]               Mant_res_DO,
   output logic [C_DIV_EXP-1:0]                Exp_res_DO,
   output logic                                Sign_res_DO,
   output logic                                Exp_OF_SO,
   output logic                                Exp_UF_SO,
   output logic                                Div_zero_SO
   );

   /////////////////////////////////////////////////////////////////////////////
   // Normalization                                                           //
   /////////////////////////////////////////////////////////////////////////////
   logic [C_DIV_MANT:0]                        Mant_res_norm_D;
   logic [C_DIV_EXP-1:0]                       Exp_res_norm_D;

   /////////////////////////////////////////////////////////////////////////////
   // Right shift operations for negtive exponents                            //
   /////////////////////////////////////////////////////////////////////////////

  logic  [C_DIV_EXP+1:0]                       Exp_Max_RS_D;
  assign Exp_Max_RS_D=Exp_in_DI[C_DIV_EXP:0]+C_DIV_MANT+1; // to check exponent after 24-bit >> when Exp_in_DI is negative
  logic  [C_DIV_EXP+1:0]                       Num_RS_D;
  assign Num_RS_D=~Exp_in_DI+1+1;            // How many right shifts(RS) are needed to generated a denormal number? >> is need only when Exp_in_DI is negative
  logic  [C_DIV_MANT_PRENORM+1:0]              Mant_RS_D;
  logic  [C_DIV_MANT-2:0]                      Mant_forsticky_D;
  assign  {Mant_RS_D,Mant_forsticky_D} ={Mant_in_DI,Round_bit_DI,20'h00000}>>(Num_RS_D); //
//  assign  Mant_DeN_sticky_D =(Exp_in_DI[C_DIV_EXP+1]&&Exp_Max_RS_D[C_DIV_EXP+1]) && (| Mant_forsticky_D) ;


   //normalization
   logic [1:0]        Mant_lower_D;
   logic              Mant_sticky_bit_D;

   always_comb
     begin

       if(NaN_a_SI)  //  if a is NaN, return a
         begin
           Div_zero_SO=1'b0;
           Exp_OF_SO=1'b0;
           Exp_UF_SO=1'b0;
           Mant_res_norm_D={1'b0,C_DIV_MANT_NAN};
           Exp_res_norm_D='1;
           Mant_lower_D={1'b0,1'b0};
           Mant_sticky_bit_D =1'b0;
           Sign_res_DO=1'b0;
         end

      else if(NaN_b_SI)   //if b is NaN, return b
        begin
          Div_zero_SO=1'b0;
          Exp_OF_SO=1'b0;
          Exp_UF_SO=1'b0;
          Mant_res_norm_D={1'b0,C_DIV_MANT_NAN};
          Exp_res_norm_D='1;
          Mant_lower_D={1'b0,1'b0};
          Mant_sticky_bit_D =1'b0;
          Sign_res_DO=1'b0;
        end

      else if(Inf_a_SI)
        begin
          if(Div_enable_SI&&Inf_b_SI)                     //Inf/Inf
            begin
              Div_zero_SO=1'b0;
              Exp_OF_SO=1'b0;
              Exp_UF_SO=1'b0;
              Mant_res_norm_D={1'b0,C_DIV_MANT_NAN};
              Exp_res_norm_D='1;
              Mant_lower_D={1'b0,1'b0};
              Mant_sticky_bit_D =1'b0;
              Sign_res_DO=1'b0;
            end
          else
            begin
              Div_zero_SO=1'b0;
              Exp_OF_SO=1'b1;
              Exp_UF_SO=1'b0;
              Mant_res_norm_D= '0;
              Exp_res_norm_D='1;
              Mant_lower_D={1'b0,1'b0};
              Mant_sticky_bit_D =1'b0;
              Sign_res_DO=Sign_in_DI;
            end
        end

      else if(Div_enable_SI&&Inf_b_SI)
        begin
          Div_zero_SO=1'b0;
          Exp_OF_SO=1'b1;
          Exp_UF_SO=1'b0;
          Mant_res_norm_D= '0;
          Exp_res_norm_D='0;
          Mant_lower_D={1'b0,1'b0};
          Mant_sticky_bit_D =1'b0;
          Sign_res_DO=Sign_in_DI;
        end

     else if(Zero_a_SI)
       begin
         if(Div_enable_SI&&Zero_b_SI)
           begin
              Div_zero_SO=1'b1;
              Exp_OF_SO=1'b0;
              Exp_UF_SO=1'b0;
              Mant_res_norm_D={1'b0,C_DIV_MANT_NAN};
              Exp_res_norm_D='1;
              Mant_lower_D={1'b0,1'b0};
              Mant_sticky_bit_D =1'b0;
              Sign_res_DO=1'b0;
           end
         else
           begin
             Div_zero_SO=1'b0;
             Exp_OF_SO=1'b0;
             Exp_UF_SO=1'b0;
             Mant_res_norm_D='0;
             Exp_res_norm_D='0;
             Mant_lower_D={1'b0,1'b0};
             Mant_sticky_bit_D =1'b0;
             Sign_res_DO=Sign_in_DI;
           end
       end

     else  if(Div_enable_SI&&(Zero_b_SI))  //div Zero
       begin
         Div_zero_SO=1'b1;
         Exp_OF_SO=1'b0;
         Exp_UF_SO=1'b0;
         Mant_res_norm_D='0;
         Exp_res_norm_D='1;
         Mant_lower_D={1'b0,1'b0};
         Mant_sticky_bit_D =1'b0;
         Sign_res_DO=Sign_in_DI;
       end

      else if(Sign_in_DI&&Sqrt_enable_SI)   //sqrt(-a)
        begin
          Div_zero_SO=1'b0;
          Exp_OF_SO=1'b0;
          Exp_UF_SO=1'b0;
          Mant_res_norm_D={1'b0,C_DIV_MANT_NAN};
          Exp_res_norm_D='1;
          Mant_lower_D={1'b0,1'b0};
          Mant_sticky_bit_D =1'b0;
          Sign_res_DO=1'b0;
        end

     else if((Exp_in_DI[C_DIV_EXP:0]=='0))
       begin
         if(Mant_in_DI!='0)       //Exp=0, Mant!=0, it is denormal
           begin
             Div_zero_SO=1'b0;
             Exp_OF_SO=1'b0;
             Exp_UF_SO=1'b1;
             Mant_res_norm_D={1'b0,1'b0,Mant_in_DI[C_DIV_MANT_PRENORM-1:1]};
             Exp_res_norm_D='0;
             Mant_lower_D={Mant_in_DI[0],Round_bit_DI[3]};
             Mant_sticky_bit_D = (| Round_bit_DI[2:0]);
             Sign_res_DO=Sign_in_DI;
           end
         else                 // Zero
           begin
             Div_zero_SO=1'b0;
             Exp_OF_SO=1'b0;
             Exp_UF_SO=1'b0;
             Mant_res_norm_D='0;
             Exp_res_norm_D='0;
             Mant_lower_D={1'b0,1'b0};
             Mant_sticky_bit_D =1'b0;
             Sign_res_DO=Sign_in_DI;
           end
        end

      else if((Exp_in_DI[C_DIV_EXP:0]==C_DIV_EXP_ONE)&&(~Mant_in_DI[C_DIV_MANT_PRENORM-1]))  //denormal
        begin
          Div_zero_SO=1'b0;
          Exp_OF_SO=1'b0;
          Exp_UF_SO=1'b1;
          Mant_res_norm_D=Mant_in_DI[C_DIV_MANT_PRENORM-1:0];
          Exp_res_norm_D='0;
          Mant_lower_D={Round_bit_DI[3:2]};
          Mant_sticky_bit_D = (| Round_bit_DI[1:0]);
          Sign_res_DO=Sign_in_DI;
        end

      else if(Exp_in_DI[C_DIV_EXP+1])    //minus
        begin
          if(~Exp_Max_RS_D[C_DIV_EXP+1])    //OF EXP<0 after RS
            begin
              Div_zero_SO=1'b0;
              Exp_OF_SO=1'b1;
              Exp_UF_SO=1'b0;
              Mant_res_norm_D='0;
              Exp_res_norm_D='0;
              Mant_lower_D={1'b0,1'b0};
              Mant_sticky_bit_D =1'b0;
              Sign_res_DO=Sign_in_DI;
            end
          else                    //denormal
            begin
              Div_zero_SO=1'b0;
              Exp_OF_SO=1'b0;
              Exp_UF_SO=1'b1;
              Mant_res_norm_D={1'b0,Mant_RS_D[C_DIV_MANT+1:2]};
              Exp_res_norm_D='0;
              Mant_lower_D=Mant_RS_D[1:0];
              Mant_sticky_bit_D = (| Mant_forsticky_D);
              Sign_res_DO=Sign_in_DI;
            end
        end

      else if(Exp_in_DI[C_DIV_EXP])            //OF
        begin
          Div_zero_SO=1'b0;
          Exp_OF_SO=1'b1;
          Exp_UF_SO=1'b0;
          Mant_res_norm_D='0;
          Exp_res_norm_D='1;
          Mant_lower_D={1'b0,1'b0};
          Mant_sticky_bit_D =1'b0;
          Sign_res_DO=Sign_in_DI;
        end

      else if(Exp_in_DI[C_DIV_EXP-1:0]=='1)  //255
        begin
          if(~Mant_in_DI[C_DIV_MANT_PRENORM-1]) // MSB=0
            begin
              Div_zero_SO=1'b0;
              Exp_OF_SO=1'b0;
              Exp_UF_SO=1'b0;
              Mant_res_norm_D={Mant_in_DI[C_DIV_MANT_PRENORM-2:0],Round_bit_DI[3]};
              Exp_res_norm_D=Exp_in_DI[C_DIV_EXP-1:0]-1;
              Mant_lower_D=Round_bit_DI[2:1];
              Mant_sticky_bit_D = ( Round_bit_DI[0]);
              Sign_res_DO=Sign_in_DI;
            end
          else if(Mant_in_DI!='0)         //NaN
            begin
              Div_zero_SO=1'b0;
              Exp_OF_SO=1'b1;
              Exp_UF_SO=1'b0;
              Mant_res_norm_D= '0;
              Exp_res_norm_D='1;
              Mant_lower_D={1'b0,1'b0};
              Mant_sticky_bit_D =1'b0;
              Sign_res_DO=Sign_in_DI;
            end
          else                         //infinity
            begin
              Div_zero_SO=1'b0;
              Exp_OF_SO=1'b1;
              Exp_UF_SO=1'b0;
              Mant_res_norm_D= '0;
              Exp_res_norm_D='1;
              Mant_lower_D={1'b0,1'b0};
              Mant_sticky_bit_D =1'b0;
              Sign_res_DO=Sign_in_DI;
            end
         end

      else if(Mant_in_DI[C_DIV_MANT_PRENORM-1])  //normal numbers with 1.XXX
        begin
           Div_zero_SO=1'b0;
           Exp_OF_SO=1'b0;
           Exp_UF_SO=1'b0;
           Mant_res_norm_D= Mant_in_DI[C_DIV_MANT_PRENORM-1:0];
           Exp_res_norm_D=Exp_in_DI[C_DIV_EXP-1:0];
           Mant_lower_D=Round_bit_DI[3:2];
           Mant_sticky_bit_D =(| Round_bit_DI[1:0]);
           Sign_res_DO=Sign_in_DI;
        end

      else                                   //normal numbers with 0.1XX
         begin
           Div_zero_SO=1'b0;
           Exp_OF_SO=1'b0;
           Exp_UF_SO=1'b0;
           Mant_res_norm_D={Mant_in_DI[C_DIV_MANT_PRENORM-2:0],Round_bit_DI[3]};
           Exp_res_norm_D=Exp_in_DI[C_DIV_EXP-1:0]-1;
           Mant_lower_D=Round_bit_DI[2:1];
           Mant_sticky_bit_D =Round_bit_DI[0];
           Sign_res_DO=Sign_in_DI;
         end

     end

   /////////////////////////////////////////////////////////////////////////////
   // Rounding                                                                //
   /////////////////////////////////////////////////////////////////////////////

   logic [C_DIV_MANT:0]                   Mant_upper_D;
   logic [C_DIV_MANT+1:0]                 Mant_upperRounded_D;
   logic                                  Mant_roundUp_S;
   logic                                  Mant_rounded_S;

   assign Mant_upper_D = Mant_res_norm_D;
   assign Mant_rounded_S = (|(Mant_lower_D))| Mant_sticky_bit_D;

   always_comb //determine whether to round up or not
     begin
        Mant_roundUp_S = 1'b0;
        case (RM_SI)
          C_DIV_RM_NEAREST :
            Mant_roundUp_S = Mant_lower_D[1] && ((Mant_lower_D[0] | Mant_sticky_bit_D )|| Mant_upper_D[0]);
          C_DIV_RM_TRUNC   :
            Mant_roundUp_S = 0;
          C_DIV_RM_PLUSINF :
            Mant_roundUp_S = Mant_rounded_S & ~Sign_in_DI;
          C_DIV_RM_MINUSINF:
            Mant_roundUp_S = Mant_rounded_S & Sign_in_DI;
          default          :
            Mant_roundUp_S = 0;
        endcase // case (RM_DI)
     end // always_comb begin

   logic                                 Mant_renorm_S;

   assign Mant_upperRounded_D = Mant_upper_D + Mant_roundUp_S;
   assign Mant_renorm_S       = Mant_upperRounded_D[C_DIV_MANT+1];

   /////////////////////////////////////////////////////////////////////////////
   // Renormalization and Output Assignments                                  //
   /////////////////////////////////////////////////////////////////////////////
   logic                                   Rounded_SO;

   assign Mant_res_DO = (Mant_renorm_S)?Mant_upperRounded_D[C_DIV_MANT:1]:Mant_upperRounded_D[C_DIV_MANT-1:0];
   assign Exp_res_DO  = Exp_res_norm_D+Mant_renorm_S;
   assign Rounded_SO  = Mant_rounded_S;

endmodule // fpu_norm_div_sqrt
