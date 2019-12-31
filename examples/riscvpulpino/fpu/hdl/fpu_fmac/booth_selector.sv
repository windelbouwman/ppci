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
//		                                                              //
// Additional contributions by:                                               //
//                                                                            //
//                                                                            //
//                                                                            //
// Create Date:    01/12/2016                                                 //
// Design Name:    fmac                                                       //
// Module Name:    booth_selector.sv                                          //
// Project Name:   Private FPU                                                //
// Language:       SystemVerilog                                              //
//                                                                            //
// Description:    Booth Seletor                                              //
//                                                                            //
//                                                                            //
//                                                                            //
// Revision:        20/06/2017                                                //
////////////////////////////////////////////////////////////////////////////////

import fpu_defs_fmac::*;

module booth_selector
  (//Inputs
   input logic [1:0]               Booth_a_DI,
   input  logic                    Sel_1x_SI,
   input logic                     Sel_2x_SI,
   input logic                     Sel_sign_SI,
   //Outputs
   output logic                    Booth_pp_DO
   );

assign      Booth_pp_DO  =~((~((Sel_1x_SI&&Booth_a_DI[1]) | (Sel_2x_SI&&Booth_a_DI[0])))^(Sel_sign_SI));

endmodule
