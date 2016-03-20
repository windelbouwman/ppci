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
// Module Name:    axi_node_wrap                                                 //
// Project Name:   PULP                                                          //
// Language:       SystemVerilog                                                 //
//                                                                               //
// Description:    Axi Node wrapper with system verilog interfaces as IO ports   //
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
// file modified for verilator-simulation purpose                                //
// ============================================================================= //

`include "defines.v"

module axi_node_wrap_with_slices
#(

    parameter                   AXI_ADDRESS_W      = 32,
    parameter                   AXI_DATA_W         = 64,
    parameter                   AXI_NUMBYTES       = AXI_DATA_W/8,
    parameter                   AXI_USER_W         = 6,
`ifdef USE_CFG_BLOCK
  `ifdef USE_AXI_LITE
    parameter                   AXI_LITE_ADDRESS_W = 32,
    parameter                   AXI_LITE_DATA_W    = 32,
    parameter                   AXI_LITE_BE_W      = AXI_LITE_DATA_W/8,
  `else
    parameter                   APB_ADDR_WIDTH     = 12,  //APB slaves are 4KB by default
    parameter                   APB_DATA_WIDTH     = 32,
  `endif
`endif
    parameter                   N_MASTER_PORT      = 8,
    parameter                   N_SLAVE_PORT       = 4,
    parameter                   AXI_ID_IN          = 4,
    parameter                   AXI_ID_OUT         = AXI_ID_IN + $clog2(N_SLAVE_PORT),
    parameter                   FIFO_DEPTH_DW      = 4,
    parameter                   N_REGION           = 4,
    parameter                   MASTER_SLICE_DEPTH = 2,
    parameter                   SLAVE_SLICE_DEPTH  = 2
)
(
    input logic                                                          clk,
    input logic                                                          rst_n,

    //MASTER PORTS
    AXI_BUS.Slave                                                        axi_port_slave  [N_SLAVE_PORT-1:0],  // modified for verilator-simulation purpose
    AXI_BUS.Master                                                       axi_port_master [N_MASTER_PORT-1:0], // modified for verilator-simulation purpose

`ifdef USE_CFG_BLOCK
	`ifdef USE_AXI_LITE
		AXI_LITE_BUS.Slave                                               cfg_port_slave,
	`else
    	APB_BUS.Slave                                                    cfg_port_slave,
    `endif
`endif

    input  logic [N_REGION-1:0][N_MASTER_PORT-1:0][31:0]  				 cfg_START_ADDR_i,
    input  logic [N_REGION-1:0][N_MASTER_PORT-1:0][31:0]  				 cfg_END_ADDR_i,
    input  logic [N_REGION-1:0][N_MASTER_PORT-1:0]                       cfg_valid_rule_i,
    input  logic [N_SLAVE_PORT-1:0][N_MASTER_PORT-1:0]                   cfg_connectivity_map_i
);

    genvar i;

     AXI_BUS
     #(
       .AXI_ADDR_WIDTH (AXI_ADDRESS_W),
       .AXI_DATA_WIDTH (AXI_DATA_W   ),
       .AXI_ID_WIDTH   (AXI_ID_IN    ),
       .AXI_USER_WIDTH (AXI_USER_W   )
     )
     axi_slave[N_SLAVE_PORT]();

    AXI_BUS
     #(
       .AXI_ADDR_WIDTH (AXI_ADDRESS_W),
       .AXI_DATA_WIDTH (AXI_DATA_W   ),
       .AXI_ID_WIDTH   (AXI_ID_OUT   ),
       .AXI_USER_WIDTH (AXI_USER_W   )
     ) axi_master [N_MASTER_PORT]();


    axi_node_wrap
    #(

        .AXI_ADDRESS_W      ( AXI_ADDRESS_W      ),
        .AXI_DATA_W         ( AXI_DATA_W         ),
        .AXI_USER_W         ( AXI_USER_W         ),
`ifdef USE_CFG_BLOCK
  `ifdef USE_AXI_LITE
        .AXI_LITE_ADDRESS_W ( AXI_LITE_ADDRESS_W ),
        .AXI_LITE_DATA_W    ( AXI_LITE_DATA_W    ),
        .AXI_LITE_BE_W      ( AXI_LITE_BE_W      ),
   `else
   		.APB_ADDR_WIDTH     ( APB_ADDR_WIDTH     ),
		.APB_DATA_WIDTH     ( APB_DATA_WIDTH     ),
   `endif
`endif
        .N_MASTER_PORT      ( N_MASTER_PORT      ),
        .N_SLAVE_PORT       ( N_SLAVE_PORT       ),
        .AXI_ID_IN          ( AXI_ID_IN          ),
        .AXI_ID_OUT         ( AXI_ID_OUT         ),
        .FIFO_DEPTH_DW      ( FIFO_DEPTH_DW      ),
        .N_REGION           ( N_REGION           )
    )
    i_axi_node_wrap
    (
        .clk                    ( clk                     ),
        .rst_n                  ( rst_n                   ),
        .axi_port_slave         ( axi_slave               ),
        .axi_port_master        ( axi_master              ),
    `ifdef USE_CFG_BLOCK
        .cfg_port_slave         ( cfg_port_slave          ),
    `endif
        .cfg_END_ADDR_i         ( cfg_END_ADDR_i          ),
        .cfg_START_ADDR_i       ( cfg_START_ADDR_i        ),
        .cfg_valid_rule_i       ( cfg_valid_rule_i        ),
        .cfg_connectivity_map_i ( cfg_connectivity_map_i  )
    );



    generate

        for( i=0; i<N_MASTER_PORT; i++ )
        begin : AXI_SLICE_MASTER_PORT
            axi_slice_wrap
            #(
                .AXI_ADDR_WIDTH ( AXI_ADDRESS_W      ),
                .AXI_DATA_WIDTH ( AXI_DATA_W         ),
                .AXI_USER_WIDTH ( AXI_USER_W         ),
                .AXI_ID_WIDTH   ( AXI_ID_OUT         ),
                .SLICE_DEPTH    ( MASTER_SLICE_DEPTH )
            )
            i_axi_slice_wrap_master
            (
                .clk_i          ( clk                ),
                .rst_ni         ( rst_n              ),
                .axi_slave      ( axi_master[i]      ), // from the node
                .axi_master     ( axi_port_master[i] )  // to IO ports
            );
        end

        for( i=0; i<N_SLAVE_PORT; i++ )
        begin : AXI_SLICE_SLAVE_PORT
            axi_slice_wrap
            #(
                .AXI_ADDR_WIDTH ( AXI_ADDRESS_W     ),
                .AXI_DATA_WIDTH ( AXI_DATA_W        ),
                .AXI_USER_WIDTH ( AXI_USER_W        ),
                .AXI_ID_WIDTH   ( AXI_ID_IN         ),
                .SLICE_DEPTH    ( SLAVE_SLICE_DEPTH )
            )
            i_axi_slice_wrap_slave
            (
                .clk_i          ( clk               ),
                .rst_ni         ( rst_n             ),
                .axi_slave      ( axi_port_slave[i] ), // from IO_ports
                .axi_master     ( axi_slave[i]      )  // to axi_node
            );
        end

    endgenerate

endmodule
