// Copyright 2017 ETH Zurich and University of Bologna.
// Copyright and related rights are licensed under the Solderpad Hardware
// License, Version 0.51 (the “License”); you may not use this file except in
// compliance with the License.  You may obtain a copy of the License at
// http://solderpad.org/licenses/SHL-0.51. Unless required by applicable law
// or agreed to in writing, software, hardware and materials distributed under
// this License is distributed on an “AS IS” BASIS, WITHOUT WARRANTIES OR
// CONDITIONS OF ANY KIND, either express or implied. See the License for the
// specific language governing permissions and limitations under the License.
///////////////////////////////////////////////////////////////////////////////
// This file contains all fmac parameters                                    //
//                                                                           //
// Authors    : Lei Li  (lile@iis.ee.ethz.ch)                                //
//                                                                           //
//                                                                           //
// Copyright (c) 2017 Integrated Systems Laboratory, ETH Zurich              //
///////////////////////////////////////////////////////////////////////////////


package fpu_defs_fmac;

   parameter C_RM            = 2;
   parameter C_RM_NEAREST    = 2'h0;
   parameter C_RM_TRUNC      = 2'h1;
   parameter C_RM_PLUSINF    = 2'h2;
   parameter C_RM_MINUSINF   = 2'h3;
   parameter C_PC            = 5;
   parameter C_OP            = 32;
   parameter C_MANT          = 23;
   parameter C_EXP           = 8;
   parameter C_BIAS          = 127;
   parameter C_HALF_BIAS     = 63;
   parameter C_LEADONE_WIDTH = 7;
   parameter C_MANT_PRENORM  = C_MANT+1;
   parameter C_EXP_ZERO      = 8'h00;
   parameter C_EXP_ONE       = 8'h01;
   parameter C_EXP_INF       = 8'hff;
   parameter C_MANT_ZERO     = 23'h0;
   parameter C_MANT_NAN      = 23'h400000;

endpackage : fpu_defs_fmac
