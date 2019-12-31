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
//                                                                            //
//                                                                            //
//                                                                            //
// Create Date:    01/12/2016                                                 //
// Design Name:    fmac                                                       //
// Module Name:    booth_enocder.sv                                           //
// Project Name:   Private FPU                                                //
// Language:       SystemVerilog                                              //
//                                                                            //
// Description:    Booth encoding                                             //
//                                                                            //
//                                                                            //
//                                                                            //
// Revision:        20/06/2017                                                //
////////////////////////////////////////////////////////////////////////////////

import fpu_defs_fmac::*;

module booth_encoder
  (//Inputs
   input logic [2:0]               Booth_b_DI,
   //Outputs
   output logic                    Sel_1x_SO,
   output logic                    Sel_2x_SO,
   output logic                    Sel_sign_SO
   );
   
  logic                            Sel_xnor_S;

assign      Sel_1x_SO  =(^Booth_b_DI[1:0]);
assign      Sel_xnor_S =~(^Booth_b_DI[2:1]);
assign      Sel_2x_SO  =~(Sel_1x_SO | Sel_xnor_S);
assign      Sel_sign_SO= Booth_b_DI[2];

endmodule
