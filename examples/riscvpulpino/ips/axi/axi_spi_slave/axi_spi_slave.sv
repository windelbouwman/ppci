// Copyright 2015 ETH Zurich and University of Bologna.
// Copyright and related rights are licensed under the Solderpad Hardware
// License, Version 0.51 (the “License”); you may not use this file except in
// compliance with the License.  You may obtain a copy of the License at
// http://solderpad.org/licenses/SHL-0.51. Unless required by applicable law
// or agreed to in writing, software, hardware and materials distributed under
// this License is distributed on an “AS IS” BASIS, WITHOUT WARRANTIES OR
// CONDITIONS OF ANY KIND, either express or implied. See the License for the
// specific language governing permissions and limitations under the License.

module axi_spi_slave
#(
    parameter AXI_ADDR_WIDTH = 32,
    parameter AXI_DATA_WIDTH = 64,
    parameter AXI_USER_WIDTH = 6,
    parameter AXI_ID_WIDTH   = 3,
    parameter DUMMY_CYCLES   = 32
)
(
    input  logic                        test_mode,
    input  logic                        spi_sclk,
    input  logic                        spi_cs,
    output logic  [1:0]                 spi_mode,
    input  logic                        spi_sdi0,
    input  logic                        spi_sdi1,
    input  logic                        spi_sdi2,
    input  logic                        spi_sdi3,
    output logic                        spi_sdo0,
    output logic                        spi_sdo1,
    output logic                        spi_sdo2,
    output logic                        spi_sdo3,

    // AXI4 MASTER
    //***************************************
    input  logic                        axi_aclk,
    input  logic                        axi_aresetn,
    // WRITE ADDRESS CHANNEL
    output logic                        axi_master_aw_valid,
    output logic [AXI_ADDR_WIDTH-1:0]   axi_master_aw_addr,
    output logic [2:0]                  axi_master_aw_prot,
    output logic [3:0]                  axi_master_aw_region,
    output logic [7:0]                  axi_master_aw_len,
    output logic [2:0]                  axi_master_aw_size,
    output logic [1:0]                  axi_master_aw_burst,
    output logic                        axi_master_aw_lock,
    output logic [3:0]                  axi_master_aw_cache,
    output logic [3:0]                  axi_master_aw_qos,
    output logic [AXI_ID_WIDTH-1:0]     axi_master_aw_id,
    output logic [AXI_USER_WIDTH-1:0]   axi_master_aw_user,
    input  logic                        axi_master_aw_ready,

    // READ ADDRESS CHANNEL
    output logic                        axi_master_ar_valid,
    output logic [AXI_ADDR_WIDTH-1:0]   axi_master_ar_addr,
    output logic [2:0]                  axi_master_ar_prot,
    output logic [3:0]                  axi_master_ar_region,
    output logic [7:0]                  axi_master_ar_len,
    output logic [2:0]                  axi_master_ar_size,
    output logic [1:0]                  axi_master_ar_burst,
    output logic                        axi_master_ar_lock,
    output logic [3:0]                  axi_master_ar_cache,
    output logic [3:0]                  axi_master_ar_qos,
    output logic [AXI_ID_WIDTH-1:0]     axi_master_ar_id,
    output logic [AXI_USER_WIDTH-1:0]   axi_master_ar_user,
    input  logic                        axi_master_ar_ready,

    // WRITE DATA CHANNEL
    output logic                        axi_master_w_valid,
    output logic [AXI_DATA_WIDTH-1:0]   axi_master_w_data,
    output logic [AXI_DATA_WIDTH/8-1:0] axi_master_w_strb,
    output logic [AXI_USER_WIDTH-1:0]   axi_master_w_user,
    output logic                        axi_master_w_last,
    input  logic                        axi_master_w_ready,

    // READ DATA CHANNEL
    input  logic                        axi_master_r_valid,
    input  logic [AXI_DATA_WIDTH-1:0]   axi_master_r_data,
    input  logic [1:0]                  axi_master_r_resp,
    input  logic                        axi_master_r_last,
    input  logic [AXI_ID_WIDTH-1:0]     axi_master_r_id,
    input  logic [AXI_USER_WIDTH-1:0]   axi_master_r_user,
    output logic                        axi_master_r_ready,

    // WRITE RESPONSE CHANNEL
    input  logic                        axi_master_b_valid,
    input  logic [1:0]                  axi_master_b_resp,
    input  logic [AXI_ID_WIDTH-1:0]     axi_master_b_id,
    input  logic [AXI_USER_WIDTH-1:0]   axi_master_b_user,
    output logic                        axi_master_b_ready
);

    logic        en_quad;
    logic  [7:0] rx_counter;
    logic        rx_counter_upd;
    logic [31:0] rx_data;
    logic        rx_data_valid;

    logic  [7:0] tx_counter;
    logic        tx_counter_upd;
    logic [31:0] tx_data;
    logic        tx_data_valid;

    logic        ctrl_rd_wr;

    logic [31:0] ctrl_addr;
    logic        ctrl_addr_valid;

    logic [31:0] ctrl_data_rx;
    logic        ctrl_data_rx_valid;
    logic        ctrl_data_rx_ready;
    logic [31:0] ctrl_data_tx;
    logic        ctrl_data_tx_valid;
    logic        ctrl_data_tx_ready;

    logic [31:0] fifo_data_rx;
    logic        fifo_data_rx_valid;
    logic        fifo_data_rx_ready;
    logic [31:0] fifo_data_tx;
    logic        fifo_data_tx_valid;
    logic        fifo_data_tx_ready;

    logic [AXI_ADDR_WIDTH-1:0] addr_sync;
    logic                      addr_valid_sync;
    logic                      cs_sync;

    logic        tx_done;
    logic        rd_wr_sync;

    logic [15:0] wrap_length;

    spi_slave_rx u_rxreg
    (
        .sclk           ( spi_sclk       ),
        .cs             ( spi_cs         ),
        .sdi0           ( spi_sdi0       ),
        .sdi1           ( spi_sdi1       ),
        .sdi2           ( spi_sdi2       ),
        .sdi3           ( spi_sdi3       ),
        .en_quad_in     ( en_quad        ),
        .counter_in     ( rx_counter     ),
        .counter_in_upd ( rx_counter_upd ),
        .data           ( rx_data        ),
        .data_ready     ( rx_data_valid  )
    );

    spi_slave_tx u_txreg
    (
        .test_mode      ( test_mode      ),
        .sclk           ( spi_sclk       ),
        .cs             ( spi_cs         ),
        .sdo0           ( spi_sdo0       ),
        .sdo1           ( spi_sdo1       ),
        .sdo2           ( spi_sdo2       ),
        .sdo3           ( spi_sdo3       ),
        .en_quad_in     ( en_quad        ),
        .counter_in     ( tx_counter     ),
        .counter_in_upd ( tx_counter_upd ),
        .data           ( tx_data        ),
        .data_valid     ( tx_data_valid  ),
        .done           ( tx_done        )
    );

    spi_slave_controller
    #(
        .DUMMY_CYCLES ( DUMMY_CYCLES )
    )
    u_slave_sm
    (
        .sclk               ( spi_sclk           ),
        .sys_rstn           ( axi_aresetn        ),
        .cs                 ( spi_cs             ),
        .en_quad            ( en_quad            ),
        .pad_mode           ( spi_mode           ),
        .rx_counter         ( rx_counter         ),
        .rx_counter_upd     ( rx_counter_upd     ),
        .rx_data            ( rx_data            ),
        .rx_data_valid      ( rx_data_valid      ),
        .tx_counter         ( tx_counter         ),
        .tx_counter_upd     ( tx_counter_upd     ),
        .tx_data            ( tx_data            ),
        .tx_data_valid      ( tx_data_valid      ),
        .tx_done            ( tx_done            ),
        .ctrl_rd_wr         ( ctrl_rd_wr         ),
        .ctrl_addr          ( ctrl_addr          ),
        .ctrl_addr_valid    ( ctrl_addr_valid    ),
        .ctrl_data_rx       ( ctrl_data_rx       ),
        .ctrl_data_rx_valid ( ctrl_data_rx_valid ),
        .ctrl_data_rx_ready ( ctrl_data_rx_ready ),
        .ctrl_data_tx       ( ctrl_data_tx       ),
        .ctrl_data_tx_valid ( ctrl_data_tx_valid ),
        .ctrl_data_tx_ready ( ctrl_data_tx_ready ),
        .wrap_length        ( wrap_length        )
    );

    spi_slave_dc_fifo
    #(
        .DATA_WIDTH   ( 32 ),
        .BUFFER_DEPTH ( 8  )
    )
    u_dcfifo_rx
    (
        .clk_a   ( spi_sclk           ),
        .rstn_a  ( axi_aresetn        ),
        .data_a  ( ctrl_data_rx       ),
        .valid_a ( ctrl_data_rx_valid ),
        .ready_a ( ctrl_data_rx_ready ),
        .clk_b   ( axi_aclk           ),
        .rstn_b  ( axi_aresetn        ),
        .data_b  ( fifo_data_rx       ),
        .valid_b ( fifo_data_rx_valid ),
        .ready_b ( fifo_data_rx_ready )
    );

    spi_slave_dc_fifo
    #(
        .DATA_WIDTH   ( 32 ),
        .BUFFER_DEPTH ( 8  )
    )
    u_dcfifo_tx
    (
        .clk_a   ( axi_aclk           ),
        .rstn_a  ( axi_aresetn        ),
        .data_a  ( fifo_data_tx       ),
        .valid_a ( fifo_data_tx_valid ),
        .ready_a ( fifo_data_tx_ready ),
        .clk_b   ( spi_sclk           ),
        .rstn_b  ( axi_aresetn        ),
        .data_b  ( ctrl_data_tx       ),
        .valid_b ( ctrl_data_tx_valid ),
        .ready_b ( ctrl_data_tx_ready )
    );

    spi_slave_axi_plug
    #(
        .AXI_ADDR_WIDTH ( AXI_ADDR_WIDTH ),
        .AXI_DATA_WIDTH ( AXI_DATA_WIDTH ),
        .AXI_USER_WIDTH ( AXI_USER_WIDTH ),
        .AXI_ID_WIDTH   ( AXI_ID_WIDTH   )
    )
    u_axiplug
    (
        .axi_aclk             ( axi_aclk                     ),
        .axi_aresetn          ( axi_aresetn                  ),
        .axi_master_aw_valid  ( axi_master_aw_valid          ),
        .axi_master_aw_addr   ( axi_master_aw_addr           ),
        .axi_master_aw_prot   ( axi_master_aw_prot           ),
        .axi_master_aw_region ( axi_master_aw_region         ),
        .axi_master_aw_len    ( axi_master_aw_len            ),
        .axi_master_aw_size   ( axi_master_aw_size           ),
        .axi_master_aw_burst  ( axi_master_aw_burst          ),
        .axi_master_aw_lock   ( axi_master_aw_lock           ),
        .axi_master_aw_cache  ( axi_master_aw_cache          ),
        .axi_master_aw_qos    ( axi_master_aw_qos            ),
        .axi_master_aw_id     ( axi_master_aw_id             ),
        .axi_master_aw_user   ( axi_master_aw_user           ),
        .axi_master_aw_ready  ( axi_master_aw_ready          ),
        .axi_master_ar_valid  ( axi_master_ar_valid          ),
        .axi_master_ar_addr   ( axi_master_ar_addr           ),
        .axi_master_ar_prot   ( axi_master_ar_prot           ),
        .axi_master_ar_region ( axi_master_ar_region         ),
        .axi_master_ar_len    ( axi_master_ar_len            ),
        .axi_master_ar_size   ( axi_master_ar_size           ),
        .axi_master_ar_burst  ( axi_master_ar_burst          ),
        .axi_master_ar_lock   ( axi_master_ar_lock           ),
        .axi_master_ar_cache  ( axi_master_ar_cache          ),
        .axi_master_ar_qos    ( axi_master_ar_qos            ),
        .axi_master_ar_id     ( axi_master_ar_id             ),
        .axi_master_ar_user   ( axi_master_ar_user           ),
        .axi_master_ar_ready  ( axi_master_ar_ready          ),
        .axi_master_w_valid   ( axi_master_w_valid           ),
        .axi_master_w_data    ( axi_master_w_data            ),
        .axi_master_w_strb    ( axi_master_w_strb            ),
        .axi_master_w_user    ( axi_master_w_user            ),
        .axi_master_w_last    ( axi_master_w_last            ),
        .axi_master_w_ready   ( axi_master_w_ready           ),
        .axi_master_r_valid   ( axi_master_r_valid           ),
        .axi_master_r_data    ( axi_master_r_data            ),
        .axi_master_r_resp    ( axi_master_r_resp            ),
        .axi_master_r_last    ( axi_master_r_last            ),
        .axi_master_r_id      ( axi_master_r_id              ),
        .axi_master_r_user    ( axi_master_r_user            ),
        .axi_master_r_ready   ( axi_master_r_ready           ),
        .axi_master_b_valid   ( axi_master_b_valid           ),
        .axi_master_b_resp    ( axi_master_b_resp            ),
        .axi_master_b_id      ( axi_master_b_id              ),
        .axi_master_b_user    ( axi_master_b_user            ),
        .axi_master_b_ready   ( axi_master_b_ready           ),
        .rxtx_addr            ( addr_sync                    ),
        .rxtx_addr_valid      ( addr_valid_sync              ),
        .start_tx             ( rd_wr_sync & addr_valid_sync ),
        .cs                   ( cs_sync                      ),
        .tx_data              ( fifo_data_tx                 ),
        .tx_valid             ( fifo_data_tx_valid           ),
        .tx_ready             ( fifo_data_tx_ready           ),
        .rx_data              ( fifo_data_rx                 ),
        .rx_valid             ( fifo_data_rx_valid           ),
        .rx_ready             ( fifo_data_rx_ready           ),
        .wrap_length          ( wrap_length                  )
    );

    spi_slave_syncro
    #(
        .AXI_ADDR_WIDTH ( AXI_ADDR_WIDTH )
    )
    u_syncro
    (
        .sys_clk            ( axi_aclk        ),
        .rstn               ( axi_aresetn     ),
        .cs                 ( spi_cs          ),
        .address            ( ctrl_addr       ),
        .address_valid      ( ctrl_addr_valid ),
        .rd_wr              ( ctrl_rd_wr      ),
        .cs_sync            ( cs_sync         ),
        .address_sync       ( addr_sync       ),
        .address_valid_sync ( addr_valid_sync ),
        .rd_wr_sync         ( rd_wr_sync      )
    );

endmodule
