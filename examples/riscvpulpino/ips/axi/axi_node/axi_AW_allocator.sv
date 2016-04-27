// Copyright 2015 ETH Zurich and University of Bologna.
// Copyright and related rights are licensed under the Solderpad Hardware
// License, Version 0.51 (the “License”); you may not use this file except in
// compliance with the License.  You may obtain a copy of the License at
// http://solderpad.org/licenses/SHL-0.51. Unless required by applicable law
// or agreed to in writing, software, hardware and materials distributed under
// this License is distributed on an “AS IS” BASIS, WITHOUT WARRANTIES OR
// CONDITIONS OF ANY KIND, either express or implied. See the License for the
// specific language governing permissions and limitations under the License.

// ============================================================================= //
// Company:        Multitherman Laboratory @ DEIS - University of Bologna        //
//                    Viale Risorgimento 2 40136                                 //
//                    Bologna - fax 0512093785 -                                 //
//                                                                               //
// Engineer:       Igor Loi - igor.loi@unibo.it                                  //
//                                                                               //
//                                                                               //
// Additional contributions by:                                                  //
//                                                                               //
//                                                                               //
//                                                                               //
// Create Date:    01/02/2014                                                    //
// Design Name:    AXI 4 INTERCONNECT                                            //
// Module Name:    axi_AW_allocator                                              //
// Project Name:   PULP                                                          //
// Language:       SystemVerilog                                                 //
//                                                                               //
// Description:   Address Write Allocator: it performs a round robin arbitration //
//                between pending write requests from each slave port.           //
//                                                                               //
// Revision:                                                                     //
// Revision v0.1 - 01/02/2014 : File Created                                     //
//                                                                               //
//                                                                               //
//                                                                               //
//                                                                               //
//                                                                               //
//                                                                               //
// ============================================================================= //

module axi_AW_allocator
#(
      parameter  AXI_ADDRESS_W  = 32,
      parameter  AXI_USER_W     = 6,
      parameter  N_TARG_PORT    = 7,
      parameter  LOG_N_TARG     = $clog2(N_TARG_PORT),
      parameter  AXI_ID_IN      = 16,
      parameter  AXI_ID_OUT     = AXI_ID_IN + $clog2(N_TARG_PORT)
)
(
      input  logic                                                          clk,
      input  logic                                                          rst_n,

      //AXI write address bus ----------------------------------------------------------------
      input  logic [N_TARG_PORT-1:0][AXI_ID_IN-1:0]          awid_i,     //
      input  logic [N_TARG_PORT-1:0][AXI_ADDRESS_W-1:0]      awaddr_i,   //
      input  logic [N_TARG_PORT-1:0][ 7:0]                   awlen_i,    //burst length is 1 + (0 - 15)
      input  logic [N_TARG_PORT-1:0][ 2:0]                   awsize_i,   //size of each transfer in burst
      input  logic [N_TARG_PORT-1:0][ 1:0]                   awburst_i,  //for bursts>1, accept only incr burst=01
      input  logic [N_TARG_PORT-1:0]                         awlock_i,   //only normal access supported axs_awlock=00
      input  logic [N_TARG_PORT-1:0][ 3:0]                   awcache_i,  //
      input  logic [N_TARG_PORT-1:0][ 2:0]                   awprot_i,   //
      input  logic [N_TARG_PORT-1:0][ 3:0]                   awregion_i, //
      input  logic [N_TARG_PORT-1:0][ AXI_USER_W-1:0]        awuser_i,   //
      input  logic [N_TARG_PORT-1:0][ 3:0]                   awqos_i,    //

      input  logic [N_TARG_PORT-1:0]                         awvalid_i,  //master addr valid
      output logic [N_TARG_PORT-1:0]                         awready_o,  //slave ready to accept


      //AXI write address bus--> OUT----------------------------------------------------------------
      output  logic [AXI_ID_OUT-1:0]                         awid_o,     // Append the Master ID on the MSB bit
      output  logic [AXI_ADDRESS_W-1:0]                      awaddr_o,   //
      output  logic [ 7:0]                                   awlen_o,    //burst length is 1 + (0 - 15)
      output  logic [ 2:0]                                   awsize_o,   //size of each transfer in burst
      output  logic [ 1:0]                                   awburst_o,  //for bursts>1, accept only incr burst=01
      output  logic                                          awlock_o,   //only normal access supported axs_awlock=00
      output  logic [ 3:0]                                   awcache_o,  //
      output  logic [ 2:0]                                   awprot_o,   //

      output  logic [ 3:0]                                   awregion_o, //
      output  logic [ AXI_USER_W-1:0]                        awuser_o,   //
      output  logic [ 3:0]                                   awqos_o,    //

      output logic                                           awvalid_o,  //master addr valid
      input  logic                                           awready_i,  //slave ready to accept

      // PUSH Interface to DW allocator
      output logic                                           push_ID_o,
      output logic [LOG_N_TARG+N_TARG_PORT-1:0]              ID_o, // {BIN_ID, OH_ID};
      input  logic                                           grant_FIFO_ID_i
);

localparam      AUX_WIDTH = AXI_ID_IN + AXI_ADDRESS_W + 8 + 3 + 2 + 1 + 4 + 3 +    4 + AXI_USER_W + 4;


logic [N_TARG_PORT-1:0][AUX_WIDTH-1:0]                          AUX_VECTOR_IN;
logic [AUX_WIDTH-1:0]                                           AUX_VECTOR_OUT;

logic [N_TARG_PORT-1:0][LOG_N_TARG+N_TARG_PORT-1:0]             ID_in;
logic [N_TARG_PORT-1:0]                                         awready_int; // Back to processor
logic                                                           awvalid_int; //to Slave port



genvar i;


assign        { awqos_o, awuser_o, awregion_o, awprot_o, awcache_o, awlock_o, awburst_o, awsize_o, awlen_o, awaddr_o, awid_o[AXI_ID_IN-1:0] }  =  AUX_VECTOR_OUT;
assign        awid_o[AXI_ID_OUT-1:AXI_ID_IN] = ID_o[LOG_N_TARG+N_TARG_PORT-1:N_TARG_PORT];



assign        awready_o = {N_TARG_PORT{grant_FIFO_ID_i}} & awready_int;
assign        awvalid_o = awvalid_int & grant_FIFO_ID_i;

assign        push_ID_o = awvalid_o & awready_i & grant_FIFO_ID_i;

generate
  for(i=0;i<N_TARG_PORT;i++)
  begin : AUX_VECTOR_BINDING
      assign AUX_VECTOR_IN[i] =  { awqos_i[i], awuser_i[i], awregion_i[i], awprot_i[i], awcache_i[i], awlock_i[i], awburst_i[i], awsize_i[i], awlen_i[i], awaddr_i[i], awid_i[i]};
  end

  for(i=0;i<N_TARG_PORT;i++)
  begin : ID_VECTOR_BINDING
      assign ID_in[i][N_TARG_PORT-1:0] =  2**i; // OH ENCODING
      assign ID_in[i][LOG_N_TARG+N_TARG_PORT-1:N_TARG_PORT] =  i; //BIN ENCODING
  end

endgenerate



      axi_ArbitrationTree
      #(
            .AUX_WIDTH     ( AUX_WIDTH              ),
            .ID_WIDTH      ( LOG_N_TARG+N_TARG_PORT ),
            .N_MASTER      ( N_TARG_PORT            )
      )
      AW_ARB_TREE
      (
            .clk           (  clk            ),
            .rst_n         (  rst_n          ),

            // ---------------- REQ_SIDE --------------------------
            .data_req_i    (  awvalid_i      ),
            .data_AUX_i    (  AUX_VECTOR_IN  ),
            .data_ID_i     (  ID_in          ),
            .data_gnt_o    (  awready_int    ),

            // Outputs
            .data_req_o    (  awvalid_int    ),
            .data_AUX_o    (  AUX_VECTOR_OUT ),
            .data_ID_o     (  ID_o           ), // --> To be merged with OH to Bin ID
            .data_gnt_i    (  awready_i      ),

            .lock          (  1'b0           ),
            .SEL_EXCLUSIVE (  '0             )
      );

endmodule
