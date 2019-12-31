// Copyright 2017, 2018 ETH Zurich and University of Bologna.
// Copyright and related rights are licensed under the Solderpad Hardware
// License, Version 0.51 (the "License"); you may not use this file except in
// compliance with the License.  You may obtain a copy of the License at
// http://solderpad.org/licenses/SHL-0.51. Unless required by applicable law
// or agreed to in writing, software, hardware and materials distributed under
// this License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
// CONDITIONS OF ANY KIND, either express or implied. See the License for the
// specific language governing permissions and limitations under the License.
///////////////////////////////////////////////////////////////////////////////
// This file contains all FPU parameters                                     //
//                                                                           //
// Authors    : Michael Gautschi  (gautschi@iis.ee.ethz.ch)                  //
//              Michael Schaffner (schaffner@iis.ee.ethz.ch)                 //
//              Lei Li            (lile@iis.ee.ethz.ch)                      //
// Copyright (c) 2015 Integrated Systems Laboratory, ETH Zurich              //
///////////////////////////////////////////////////////////////////////////////


package fpu_defs;

   // op command
   parameter C_CMD               = 4;
   parameter C_FPU_ADD_CMD       = 4'h0;
   parameter C_FPU_SUB_CMD       = 4'h1;
   parameter C_FPU_MUL_CMD       = 4'h2;
   parameter C_FPU_DIV_CMD       = 4'h3;
   parameter C_FPU_I2F_CMD       = 4'h4;
   parameter C_FPU_F2I_CMD       = 4'h5;
   parameter C_FPU_SQRT_CMD      = 4'h6;
   parameter C_FPU_NOP_CMD       = 4'h7;
   parameter C_FPU_FMADD_CMD     = 4'h8;
   parameter C_FPU_FMSUB_CMD     = 4'h9;
   parameter C_FPU_FNMADD_CMD    = 4'hA;
   parameter C_FPU_FNMSUB_CMD    = 4'hB;

   parameter C_RM           = 3;
   parameter C_RM_NEAREST   = 3'h0;
   parameter C_RM_TRUNC     = 3'h1;
   parameter C_RM_PLUSINF   = 3'h3;
   parameter C_RM_MINUSINF  = 3'h2;
   parameter C_RM_NEAREST_MAX = 3'h4;

   parameter C_PC           = 5;


// to be verified if it works in half precision mode!!!
//`define HALFPREC

`ifdef HALFPREC
   parameter C_OP           = 16;
   parameter C_MANT         = 10;
   parameter C_EXP          = 5;

   parameter C_EXP_PRENORM  = 7;
   parameter C_MANT_PRENORM = 22;
   parameter C_MANT_ADDIN   = 14;
   parameter C_MANT_ADDOUT  = 15;
   parameter C_MANT_SHIFTIN = 13;
   parameter C_MANT_SHIFTED = 14;
   parameter C_MANT_INT     = 15;
   parameter C_INF          = 32'h7fff;
   parameter C_MINF         = 32'h8000;
   parameter C_EXP_SHIFT    = 7;
   parameter C_SHIFT_BIAS   = 6'd15;
   parameter C_BIAS         = 7'd15;
   parameter C_UNKNOWN      = 8'd157;
   parameter C_PADMANT      = 6'b0;
   parameter C_EXP_ZERO     = 5'h00;
   parameter C_EXP_INF      = 5'hff;
   parameter C_MANT_ZERO    = 11'h0;
   parameter C_MANT_NoHB_ZERO   = 10'h0;
   parameter C_MANT_PRENORM_IND = 5;
   parameter F_QNAN         =16'h7E00;

`else
   parameter C_OP           = 32;
   parameter C_MANT         = 23;
   parameter C_EXP          = 8;

   parameter C_EXP_PRENORM  = C_EXP+2;
   parameter C_MANT_PRENORM = C_MANT*2+2;
   parameter C_MANT_ADDIN   = C_MANT+4;
   parameter C_MANT_ADDOUT  = C_MANT+5;
   parameter C_MANT_SHIFTIN = C_MANT+3;
   parameter C_MANT_SHIFTED = C_MANT+4;
   parameter C_MANT_INT     = C_OP-1;
   parameter C_INF          = 32'h7fffffff;
   parameter C_MINF         = 32'h80000000;
   parameter C_EXP_SHIFT    = C_EXP_PRENORM;
   parameter C_SHIFT_BIAS   = 9'd127;
   parameter C_BIAS         = 10'd127;
   parameter C_UNKNOWN      = 8'd157;
   parameter C_PADMANT      = 16'b0;
   parameter C_EXP_ZERO     = 8'h00;
   parameter C_EXP_INF      = 8'hff;
   parameter C_MANT_ZERO    = 24'h0;
   parameter C_MANT_NoHB_ZERO   = 23'h0;
   parameter C_MANT_PRENORM_IND = 6;
   parameter F_QNAN         =32'h7FC00000;
`endif

   parameter C_FFLAG         = 5;

endpackage : fpu_defs
