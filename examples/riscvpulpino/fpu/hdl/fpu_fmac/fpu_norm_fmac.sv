// Copyright 2017 ETH Zurich and University of Bologna.
// Copyright and related rights are licensed under the Solderpad Hardware
// License, Version 0.51 (the “License”); you may not use this file except in
// compliance with the License.  You may obtain a copy of the License at
// http://solderpad.org/licenses/SHL-0.51. Unless required by applicable law
// or agreed to in writing, software, hardware and materials distributed under
// this License is distributed on an “AS IS” BASIS, WITHOUT WARRANTIES OR
// CONDITIONS OF ANY KIND, either express or implied. See the License for the
// specific language governing permissions and limitations under the License.
////////////////////////////////////////////////////////////////////////////////
// Company:        IIS @ ETHZ - Federal Institute of Technology               //
//                                                                            //
// Engineers:      Lei Li  lile@iis.ee.ethz.ch                                //
//                                                                            //
// Additional contributions by:                                               //
//                 Torbjørn Viem Ness -- torbjovn@stud.ntnu.no                //
//                                                                            //
//                                                                            //
// Create Date:    01/12/2016                                                 //
// Design Name:    fmac                                                       //
// Module Name:    fpu_norm_fmac.sv                                           //
// Project Name:   Private FPU                                                //
// Language:       SystemVerilog                                              //
//                                                                            //
// Description:    normalization and rounding                                 //
//                                                                            //
//                                                                            //
// Revision:        28/06/2017                                                //
// Revision:        04/09/2017                                                //
//                  Fix a bug in normalization by Lei Li                      //
// Revision:                                                                  //
//                15/05/2018                                                  //
//                Pass package parameters as default args instead of using    //
//                them directly, improves compatibility with tools like       //
//                Synopsys Spyglass and DC (GitHub #7) - Torbjørn Viem Ness   //
////////////////////////////////////////////////////////////////////////////////

import fpu_defs_fmac::*;

module fpu_norm_fmac
#(
   parameter C_LEADONE_WIDTH = fpu_defs_fmac::C_LEADONE_WIDTH,
   parameter C_EXP           = fpu_defs_fmac::C_EXP,
   parameter C_MANT          = fpu_defs_fmac::C_MANT,
   parameter C_RM            = fpu_defs_fmac::C_RM,
   parameter C_RM_NEAREST    = fpu_defs_fmac::C_RM_NEAREST,
   parameter C_RM_TRUNC      = fpu_defs_fmac::C_RM_TRUNC,
   parameter C_RM_PLUSINF    = fpu_defs_fmac::C_RM_PLUSINF,
   parameter C_RM_MINUSINF   = fpu_defs_fmac::C_RM_MINUSINF,
   parameter C_MANT_NAN      = fpu_defs_fmac::C_MANT_NAN
)
  (//Inputs
   input logic [3*C_MANT+4:0]              Mant_in_DI,
   input logic signed [C_EXP+1:0]          Exp_in_DI,
   input logic                             Sign_in_DI,
   input logic [C_LEADONE_WIDTH-1:0]       Leading_one_DI,
   input logic                             No_one_SI,
   input logic                             Sign_amt_DI,
   input  logic                            Sub_SI,
   input logic [C_EXP-1:0]                 Exp_a_DI,
   input logic [C_MANT:0]                  Mant_a_DI,
   input logic                             Sign_a_DI,
   input logic                             DeN_a_SI,
   input logic [C_RM-1:0]                  RM_SI,
   input logic                             Inf_a_SI,
   input logic                             Inf_b_SI,
   input logic                             Inf_c_SI,
   input logic                             Zero_a_SI,
   input logic                             Zero_b_SI,
   input logic                             Zero_c_SI, 
   input logic                             NaN_a_SI,
   input logic                             NaN_b_SI,
   input logic                             NaN_c_SI,
   input logic                             Mant_sticky_sft_out_SI,
   input logic                             Minus_sticky_bit_SI,
   //Outputs
   output logic [C_MANT-1:0]               Mant_res_DO,
   output logic [C_EXP-1:0]                Exp_res_DO,
   output logic                            Sign_res_DO,
   output logic                            Exp_OF_SO,
   output logic                            Exp_UF_SO,
   output logic                            Flag_Inexact_SO,
   output logic                            Flag_Invalid_SO   
   );

   logic [C_MANT:0]                        Mant_res_norm_D;
   logic [C_EXP-1:0]                       Exp_res_norm_D;
   logic [1:0]                             Mant_lower_D;
   logic                                   Stick_one_HD;

   /////////////////////////////////////////////////////////////////////////////
   // Exponent correction using LZA                                           //
   /////////////////////////////////////////////////////////////////////////////
  logic [3*C_MANT+4:0]             Mant_postsft_D; 
  logic [C_EXP+1:0]                Exp_postsft_D;
  logic [C_EXP+1:0]                Exp_postsft_addone_D;
  logic [C_LEADONE_WIDTH-1:0]      Leading_one_D;
  logic [C_EXP:0]                  LSt_Mant_D;

  assign Leading_one_D =  (Sign_amt_DI | Mant_in_DI[3*C_MANT+4]) ? 0 :  (Leading_one_DI);
  assign Exp_lg_S = Exp_in_DI>Leading_one_D; 
  assign LSt_Mant_D = Exp_in_DI[C_EXP+1]?0:((Exp_lg_S)?(Leading_one_D):(Exp_in_DI[C_EXP:0]-1));
  assign Mant_postsft_D = Mant_in_DI<<(LSt_Mant_D);
  assign Exp_postsft_D  = Exp_in_DI[C_EXP+1]?0:((Exp_lg_S)?(Exp_in_DI-Leading_one_D):(1)); //1 for denormal numbers
  assign Exp_postsft_addone_D  = Exp_in_DI-Leading_one_D-1;

   /////////////////////////////////////////////////////////////////////////////
   // Right shift operations for negtive exponents                            //
   /////////////////////////////////////////////////////////////////////////////
  logic [C_EXP+1:0]                      Exp_Max_RS_D;
  assign Exp_Max_RS_D=Exp_in_DI[C_EXP:0]+74; // to check exponent after 74-bit >> when Exp_in_DI is negative
  logic  [C_EXP+1:0]                     Num_RS_D;
  assign Num_RS_D=~Exp_in_DI+1+1;            // How many right shifts(RS) are needed to generated a denormal number? >> is need only when Exp_in_DI is negative
  logic [3*C_MANT+6:0]                   Mant_RS_D;
  assign  Mant_RS_D={Mant_in_DI,1'b0,1'b0}>>(Num_RS_D); // The LSB 2 bits for rounding

   /////////////////////////////////////////////////////////////////////////////
   // Sticky bit                                                              //
   /////////////////////////////////////////////////////////////////////////////

  logic [2*C_MANT+1:0]                   Mant_StickCh_D; 
  assign Mant_StickCh_D = Exp_postsft_D[C_EXP+1]? Mant_RS_D[2*C_MANT+3:2] :
                         ((Exp_postsft_D[C_EXP+1:0]=='0) ? Mant_postsft_D[2*C_MANT+2:1]:
                         (((Mant_postsft_D[3*C_MANT+4] | (Exp_postsft_D==0))?Mant_postsft_D[2*C_MANT+1:0]:{Mant_postsft_D[2*C_MANT:0],1'b0})));
  assign Stick_one_HD = | Mant_StickCh_D;
  assign Stick_one_D = Stick_one_HD | Mant_sticky_sft_out_SI | Minus_sticky_bit_SI;

  logic  Mant_sticky_D;

  assign Flag_Invalid_SO = NaN_a_SI | NaN_b_SI | NaN_c_SI | (Zero_b_SI&&Inf_c_SI) | (Zero_c_SI&&Inf_b_SI) | (Sub_SI && Inf_a_SI &&( Inf_b_SI | Inf_c_SI ));

  always@(*)
    begin
       if(Flag_Invalid_SO)  //   NaN
         begin        
           Exp_OF_SO=1'b0;
           Exp_UF_SO=1'b0;
           Mant_res_norm_D={1'b0,C_MANT_NAN};
           Exp_res_norm_D='1;
           Mant_lower_D={1'b0,1'b0};
           Sign_res_DO=1'b0;
           Mant_sticky_D=1'b0;
         end

      else if(Inf_a_SI | Inf_b_SI | Inf_c_SI)  // Inf
        begin 
          Exp_OF_SO=1'b1;
          Exp_UF_SO=1'b0;
          Mant_res_norm_D= '0;
          Exp_res_norm_D='1;
          Mant_lower_D={1'b0,1'b0};
          Sign_res_DO=Sign_in_DI;
          Mant_sticky_D=1'b0;
        end

      else if(Sign_amt_DI)  // Operand_a_DI
        begin 
          Exp_OF_SO=1'b0;
          Exp_UF_SO=DeN_a_SI;
          Mant_res_norm_D= Mant_a_DI;
          Exp_res_norm_D=Exp_a_DI;
          Mant_lower_D={1'b0,1'b0};
          Sign_res_DO=Sign_a_DI;
          Mant_sticky_D=Stick_one_D; //when Sign_amt_DI, there is some Mant_sticky_bit
        end 

      else if(No_one_SI)  
        begin 
          Exp_OF_SO=1'b0;
          Exp_UF_SO=1'b0;
          Mant_res_norm_D= '0;
          Exp_res_norm_D='0;
          Mant_lower_D={1'b0,1'b0};  
          Sign_res_DO=Sign_in_DI; 
          Mant_sticky_D=1'b0;
        end

      else if(Exp_in_DI[C_EXP+1]) //minus 
        begin          
          if(~Exp_Max_RS_D[C_EXP+1])    //OF EXP<0 after RS
            begin   
              Exp_OF_SO=1'b1;
              Exp_UF_SO=1'b0;
              Mant_res_norm_D='0;
              Exp_res_norm_D='0;
              Mant_lower_D={1'b0,1'b0};
              Sign_res_DO=Sign_in_DI;
              Mant_sticky_D=1'b0;
            end
          else                    //denormal
            begin 
              Exp_OF_SO=1'b0;
              Exp_UF_SO=1'b1;          
              Mant_res_norm_D={1'b0,Mant_RS_D[3*C_MANT+6:2*C_MANT+6]}; 
              Exp_res_norm_D='0;
              Mant_lower_D=Mant_RS_D[2*C_MANT+5:2*C_MANT+4];
              Sign_res_DO=Sign_in_DI;
              Mant_sticky_D=Stick_one_D;   
            end    
        end 

      else if((Exp_postsft_D[C_EXP:0]==256)&&(~Mant_postsft_D[3*C_MANT+4])&&(Mant_postsft_D[3*C_MANT+3:2*C_MANT+3]!='0))         //NaN
         begin        
           Exp_OF_SO=1'b0;
           Exp_UF_SO=1'b0;
           Mant_res_norm_D={1'b0,C_MANT_NAN};
           Exp_res_norm_D='1;
           Mant_lower_D={1'b0,1'b0};
           Sign_res_DO=1'b0;
           Mant_sticky_D=1'b0;
         end

      else if(Exp_postsft_D[C_EXP-1:0]=='1)         //255
        begin
          if(Mant_postsft_D[3*C_MANT+4]) // NaN
            begin         
              Exp_OF_SO=1'b1;
              Exp_UF_SO=1'b0;
              Mant_res_norm_D= {1'b0,C_MANT_NAN};
              Exp_res_norm_D='1;
              Mant_lower_D={1'b0,1'b0};
              Sign_res_DO=Sign_in_DI;
              Mant_sticky_D=1'b0;
            end
          else if (Mant_postsft_D[3*C_MANT+4:2*C_MANT+4]=='0)                      // Inf
            begin 
              Exp_OF_SO=1'b1;
              Exp_UF_SO=1'b0;
              Mant_res_norm_D= '0;
              Exp_res_norm_D='1;
              Mant_lower_D={1'b0,1'b0};
              Sign_res_DO=Sign_in_DI;
              Mant_sticky_D=1'b0;
            end 
          else                                    //normal numbers
            begin
              Exp_OF_SO=1'b0;
              Exp_UF_SO=1'b0;
              Mant_res_norm_D=Mant_postsft_D[3*C_MANT+3:2*C_MANT+3] ;
              Exp_res_norm_D=254;
              Mant_lower_D=Mant_postsft_D[2*C_MANT+2:2*C_MANT+1];  
              Sign_res_DO=Sign_in_DI; 
              Mant_sticky_D=Stick_one_D; 
            end 
        end 

      else if(Exp_postsft_D[C_EXP])                                       //Inf
        begin 
          Exp_OF_SO=1'b1;
          Exp_UF_SO=1'b0;
          Mant_res_norm_D= '0;
          Exp_res_norm_D='1;
          Mant_lower_D={1'b0,1'b0};
          Sign_res_DO=Sign_in_DI;
          Mant_sticky_D=1'b0;
        end  

      else if(Exp_postsft_D[C_EXP+1:0]=='0)         //0
        begin                                   //denormal
            begin
              Exp_OF_SO=1'b0;
              Exp_UF_SO=1'b1;
              Mant_res_norm_D= {1'b0,Mant_postsft_D[3*C_MANT+4:2*C_MANT+5]};
              Exp_res_norm_D='0;
              Mant_lower_D=Mant_postsft_D[2*C_MANT+4:2*C_MANT+3];
              Sign_res_DO=Sign_in_DI;
              Mant_sticky_D=Stick_one_D;
            end
        end

      else if(Exp_postsft_D[C_EXP+1:0]==1)         //0
        begin 
          if(Mant_postsft_D[3*C_MANT+4])                                   //normal number
            begin
              Exp_OF_SO=1'b0;
              Exp_UF_SO=1'b0; 
              Mant_res_norm_D= {Mant_postsft_D[3*C_MANT+4:2*C_MANT+4]};
              Exp_res_norm_D=1;
              Mant_lower_D=Mant_postsft_D[2*C_MANT+3:2*C_MANT+2];
              Sign_res_DO=Sign_in_DI;
              Mant_sticky_D=Stick_one_D;
            end
          else 
            begin                                                        //denormal number
              Exp_OF_SO=1'b0;
              Exp_UF_SO=1'b1; 
              Mant_res_norm_D= {Mant_postsft_D[3*C_MANT+4:2*C_MANT+4]};
              Exp_res_norm_D='0;
              Mant_lower_D=Mant_postsft_D[2*C_MANT+3:2*C_MANT+2];
              Sign_res_DO=Sign_in_DI;
              Mant_sticky_D=Stick_one_D;
            end
        end

      else if (~Mant_postsft_D[3*C_MANT+4])                        // normal number with 0X.XX
        begin
          Exp_OF_SO=1'b0;
          Exp_UF_SO=1'b0; 
          Mant_res_norm_D= Mant_postsft_D[3*C_MANT+3:2*C_MANT+3];
          Exp_res_norm_D=Exp_postsft_addone_D[C_EXP-1:0];
          Mant_lower_D=Mant_postsft_D[2*C_MANT+2:2*C_MANT+1];
          Sign_res_DO=Sign_in_DI;
          Mant_sticky_D=Stick_one_D;
        end

      else                                                       // normal number with 1X.XX
        begin   
          Exp_OF_SO=1'b0;
          Exp_UF_SO=1'b0; 
          Mant_res_norm_D= Mant_postsft_D[3*C_MANT+4:2*C_MANT+4];
          Exp_res_norm_D=Exp_postsft_D[C_EXP-1:0];
          Mant_lower_D=Mant_postsft_D[2*C_MANT+3:2*C_MANT+2];
          Sign_res_DO=Sign_in_DI;
          Mant_sticky_D=Stick_one_D;
        end

    end

   /////////////////////////////////////////////////////////////////////////////
   // Rounding                                                                //
   /////////////////////////////////////////////////////////////////////////////

   logic [C_MANT:0]                   Mant_upper_D;
   logic [C_MANT+1:0]                 Mant_upperRounded_D;
   logic                              Mant_roundUp_S;
   logic                              Mant_rounded_S;

   assign Mant_upper_D    = Mant_res_norm_D;
   assign Flag_Inexact_SO = Mant_rounded_S;
   
   assign Mant_rounded_S = (|(Mant_lower_D))| Mant_sticky_D;
   
   always_comb //determine whether to round up or not
     begin
        Mant_roundUp_S = 1'b0;
        case (RM_SI)
          C_RM_NEAREST : 
            Mant_roundUp_S = Mant_lower_D[1] && ((Mant_lower_D[0]| Mant_sticky_D ) || Mant_upper_D[0]);
          C_RM_TRUNC   : 
            Mant_roundUp_S = 0;
          C_RM_PLUSINF : 
            Mant_roundUp_S = Mant_rounded_S & ~Sign_in_DI;
          C_RM_MINUSINF:
            Mant_roundUp_S = Mant_rounded_S & Sign_in_DI;
          default     :
            Mant_roundUp_S = 0;
        endcase // case (RM_DI)
     end // always_comb begin

   logic                          Mant_renorm_S;

   assign Mant_upperRounded_D = Mant_upper_D + Mant_roundUp_S;
   assign Mant_renorm_S       = Mant_upperRounded_D[C_MANT+1];

   /////////////////////////////////////////////////////////////////////////////
   // Renormalization and Output Assignments
   /////////////////////////////////////////////////////////////////////////////
   logic                          Rounded_SO;
   assign Mant_res_DO = (Mant_renorm_S)?Mant_upperRounded_D[C_MANT:1]:Mant_upperRounded_D[C_MANT-1:0];
   assign Exp_res_DO  = Exp_res_norm_D+Mant_renorm_S;
   assign Rounded_SO  = Mant_rounded_S;

endmodule
