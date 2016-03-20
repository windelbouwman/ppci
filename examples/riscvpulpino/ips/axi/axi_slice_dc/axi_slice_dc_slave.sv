// Copyright 2015 ETH Zurich and University of Bologna.
// Copyright and related rights are licensed under the Solderpad Hardware
// License, Version 0.51 (the “License”); you may not use this file except in
// compliance with the License.  You may obtain a copy of the License at
// http://solderpad.org/licenses/SHL-0.51. Unless required by applicable law
// or agreed to in writing, software, hardware and materials distributed under
// this License is distributed on an “AS IS” BASIS, WITHOUT WARRANTIES OR
// CONDITIONS OF ANY KIND, either express or implied. See the License for the
// specific language governing permissions and limitations under the License.

module axi_slice_dc_slave
#(
    parameter AXI_ADDR_WIDTH = 32,
    parameter AXI_DATA_WIDTH = 64,
    parameter AXI_USER_WIDTH = 6,
    parameter AXI_ID_WIDTH   = 6,
    parameter BUFFER_WIDTH   = 8
)
(
    input logic                         clk_i,
    input logic                         rst_ni,
    input  logic                        axi_slave_aw_valid,
    input  logic [AXI_ADDR_WIDTH-1:0]   axi_slave_aw_addr,
    input  logic [2:0]                  axi_slave_aw_prot,
    input  logic [3:0]                  axi_slave_aw_region,
    input  logic [7:0]                  axi_slave_aw_len,
    input  logic [2:0]                  axi_slave_aw_size,
    input  logic [1:0]                  axi_slave_aw_burst,
    input  logic                        axi_slave_aw_lock,
    input  logic [3:0]                  axi_slave_aw_cache,
    input  logic [3:0]                  axi_slave_aw_qos,
    input  logic [AXI_ID_WIDTH-1:0]     axi_slave_aw_id,
    input  logic [AXI_USER_WIDTH-1:0]   axi_slave_aw_user,
    output logic                        axi_slave_aw_ready,

    // READ ADDRESS CHANNEL
    input  logic                        axi_slave_ar_valid,
    input  logic [AXI_ADDR_WIDTH-1:0]   axi_slave_ar_addr,
    input  logic [2:0]                  axi_slave_ar_prot,
    input  logic [3:0]                  axi_slave_ar_region,
    input  logic [7:0]                  axi_slave_ar_len,
    input  logic [2:0]                  axi_slave_ar_size,
    input  logic [1:0]                  axi_slave_ar_burst,
    input  logic                        axi_slave_ar_lock,
    input  logic [3:0]                  axi_slave_ar_cache,
    input  logic [3:0]                  axi_slave_ar_qos,
    input  logic [AXI_ID_WIDTH-1:0]     axi_slave_ar_id,
    input  logic [AXI_USER_WIDTH-1:0]   axi_slave_ar_user,
    output logic                        axi_slave_ar_ready,

    // WRITE DATA CHANNEL
    input  logic                        axi_slave_w_valid,
    input  logic [AXI_DATA_WIDTH-1:0]   axi_slave_w_data,
    input  logic [AXI_DATA_WIDTH/8-1:0] axi_slave_w_strb,
    input  logic [AXI_USER_WIDTH-1:0]   axi_slave_w_user,
    input  logic                        axi_slave_w_last,
    output logic                        axi_slave_w_ready,

    // READ DATA CHANNEL
    output logic                        axi_slave_r_valid,
    output logic [AXI_DATA_WIDTH-1:0]   axi_slave_r_data,
    output logic [1:0]                  axi_slave_r_resp,
    output logic                        axi_slave_r_last,
    output logic [AXI_ID_WIDTH-1:0]     axi_slave_r_id,
    output logic [AXI_USER_WIDTH-1:0]   axi_slave_r_user,
    input  logic                        axi_slave_r_ready,

    // WRITE RESPONSE CHANNEL
    output logic                        axi_slave_b_valid,
    output logic [1:0]                  axi_slave_b_resp,
    output logic [AXI_ID_WIDTH-1:0]     axi_slave_b_id,
    output logic [AXI_USER_WIDTH-1:0]   axi_slave_b_user,
    input  logic                        axi_slave_b_ready,

    // AXI4 MASTER
    //***************************************
    // WRITE ADDRESS CHANNEL
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
    output logic [BUFFER_WIDTH-1:0]     axi_master_aw_writetoken,
    input  logic [BUFFER_WIDTH-1:0]     axi_master_aw_readpointer,
    // READ ADDRESS CHANNEL
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
    output logic [BUFFER_WIDTH-1:0]     axi_master_ar_writetoken,
    input  logic [BUFFER_WIDTH-1:0]     axi_master_ar_readpointer,

    // WRITE DATA CHANNEL
    output logic [AXI_DATA_WIDTH-1:0]   axi_master_w_data,
    output logic [AXI_DATA_WIDTH/8-1:0] axi_master_w_strb,
    output logic [AXI_USER_WIDTH-1:0]   axi_master_w_user,
    output logic                        axi_master_w_last,
    output logic [BUFFER_WIDTH-1:0]     axi_master_w_writetoken,
    input  logic [BUFFER_WIDTH-1:0]     axi_master_w_readpointer,

    // READ DATA CHANNEL
    input  logic [AXI_DATA_WIDTH-1:0]   axi_master_r_data,
    input  logic [1:0]                  axi_master_r_resp,
    input  logic                        axi_master_r_last,
    input  logic [AXI_ID_WIDTH-1:0]     axi_master_r_id,
    input  logic [AXI_USER_WIDTH-1:0]   axi_master_r_user,
    input  logic [BUFFER_WIDTH-1:0]     axi_master_r_writetoken,
    output logic [BUFFER_WIDTH-1:0]     axi_master_r_readpointer,

    // WRITE RESPONSE CHANNEL
    input  logic [1:0]                axi_master_b_resp,
    input  logic [AXI_ID_WIDTH-1:0]   axi_master_b_id,
    input  logic [AXI_USER_WIDTH-1:0] axi_master_b_user,
    input  logic [BUFFER_WIDTH-1:0]   axi_master_b_writetoken,
    output logic [BUFFER_WIDTH-1:0]   axi_master_b_readpointer
);

      localparam DATA_STRB_WIDTH      = AXI_DATA_WIDTH + AXI_DATA_WIDTH/8;
      localparam DATA_USER_STRB_WIDTH = AXI_DATA_WIDTH + AXI_DATA_WIDTH/8 + AXI_ID_WIDTH;

      localparam DATA_ID_WIDTH        = AXI_DATA_WIDTH + AXI_ID_WIDTH;
      localparam DATA_USER_ID_WIDTH   = AXI_DATA_WIDTH + AXI_ID_WIDTH + AXI_USER_WIDTH;

      localparam ADDR_ID_WIDTH        = AXI_ADDR_WIDTH + AXI_ID_WIDTH;
      localparam ADDR_USER_ID_WIDTH   = AXI_ADDR_WIDTH + AXI_ID_WIDTH + AXI_USER_WIDTH;

      localparam USER_ID_WIDTH        = AXI_USER_WIDTH + AXI_ID_WIDTH;

      localparam WIDTH_FIFO_AW        = 30+ADDR_USER_ID_WIDTH;
      localparam WIDTH_FIFO_AR        = 30+ADDR_USER_ID_WIDTH;
      localparam WIDTH_FIFO_W         = 1+DATA_USER_STRB_WIDTH;
      localparam WIDTH_FIFO_R         = 3+DATA_USER_ID_WIDTH;
      localparam WIDTH_FIFO_B         = 2+USER_ID_WIDTH;

      logic      [WIDTH_FIFO_AW-1:0]  data_aw;
      logic      [WIDTH_FIFO_AW-1:0]  data_async_aw;
      logic      [WIDTH_FIFO_AR-1:0]  data_ar;
      logic      [WIDTH_FIFO_AR-1:0]  data_async_ar;
      logic      [WIDTH_FIFO_W-1:0]   data_w;
      logic      [WIDTH_FIFO_W-1:0]   data_async_w;
      logic      [WIDTH_FIFO_R-1:0]   data_r;
      logic      [WIDTH_FIFO_R-1:0]   data_async_r;
      logic      [WIDTH_FIFO_B-1:0]   data_b;
      logic      [WIDTH_FIFO_B-1:0]   data_async_b;

      assign data_aw[3:0]                                    = axi_slave_aw_cache;
      assign data_aw[6:4]                                    = axi_slave_aw_prot;
      assign data_aw[8:7]                                    = axi_slave_aw_lock;
      assign data_aw[10:9]                                   = axi_slave_aw_burst;
      assign data_aw[13:11]                                  = axi_slave_aw_size;
      assign data_aw[21:14]                                  = axi_slave_aw_len;
      assign data_aw[25:22]                                  = axi_slave_aw_region;
      assign data_aw[29:26]                                  = axi_slave_aw_qos;
      assign data_aw[29+AXI_ADDR_WIDTH:30]                   = axi_slave_aw_addr;
      assign data_aw[29+ADDR_ID_WIDTH:30+AXI_ADDR_WIDTH]     = axi_slave_aw_id;
      assign data_aw[29+ADDR_USER_ID_WIDTH:30+ADDR_ID_WIDTH] = axi_slave_aw_user;

      assign axi_master_aw_cache                             = data_async_aw[3:0];
      assign axi_master_aw_prot                              = data_async_aw[6:4];
      assign axi_master_aw_lock                              = data_async_aw[8:7];
      assign axi_master_aw_burst                             = data_async_aw[10:9];
      assign axi_master_aw_size                              = data_async_aw[13:11];
      assign axi_master_aw_len                               = data_async_aw[21:14];
      assign axi_master_aw_region                            = data_async_aw[25:22];
      assign axi_master_aw_qos                               = data_async_aw[29:26];
      assign axi_master_aw_addr                              = data_async_aw[29+AXI_ADDR_WIDTH:30];
      assign axi_master_aw_id                                = data_async_aw[29+ADDR_ID_WIDTH:30+AXI_ADDR_WIDTH];
      assign axi_master_aw_user                              = data_async_aw[29+ADDR_USER_ID_WIDTH:30+ADDR_ID_WIDTH];


      //assign data_ar = {  axi_slave_ar_user , axi_slave_ar_id , axi_slave_ar_addr , axi_slave_ar_qos , axi_slave_ar_region , axi_slave_ar_len , axi_slave_ar_size , axi_slave_ar_burst , axi_slave_ar_lock , axi_slave_ar_prot, axi_slave_ar_cache };

      assign data_ar[3:0]                                    = axi_slave_ar_cache;
      assign data_ar[6:4]                                    = axi_slave_ar_prot;
      assign data_ar[8:7]                                    = axi_slave_ar_lock;
      assign data_ar[10:9]                                   = axi_slave_ar_burst;
      assign data_ar[13:11]                                  = axi_slave_ar_size;
      assign data_ar[21:14]                                  = axi_slave_ar_len;
      assign data_ar[25:22]                                  = axi_slave_ar_region;
      assign data_ar[29:26]                                  = axi_slave_ar_qos;
      assign data_ar[29+AXI_ADDR_WIDTH:30]                   = axi_slave_ar_addr;
      assign data_ar[29+ADDR_ID_WIDTH:30+AXI_ADDR_WIDTH]     = axi_slave_ar_id;
      assign data_ar[29+ADDR_USER_ID_WIDTH:30+ADDR_ID_WIDTH] = axi_slave_ar_user;
      assign axi_master_ar_cache                             = data_async_ar[3:0];
      assign axi_master_ar_prot                              = data_async_ar[6:4];
      assign axi_master_ar_lock                              = data_async_ar[8:7];
      assign axi_master_ar_burst                             = data_async_ar[10:9];
      assign axi_master_ar_size                              = data_async_ar[13:11];
      assign axi_master_ar_len                               = data_async_ar[21:14];
      assign axi_master_ar_region                            = data_async_ar[25:22];
      assign axi_master_ar_qos                               = data_async_ar[29:26];
      assign axi_master_ar_addr                              = data_async_ar[29+AXI_ADDR_WIDTH:30];
      assign axi_master_ar_id                                = data_async_ar[29+ADDR_ID_WIDTH:30+AXI_ADDR_WIDTH];
      assign axi_master_ar_user                              = data_async_ar[29+ADDR_USER_ID_WIDTH:30+ADDR_ID_WIDTH];


      assign data_async_r[0]                                    = axi_master_r_last;
      assign data_async_r[2:1]                                  = axi_master_r_resp;
      assign data_async_r[2+AXI_DATA_WIDTH:3]                   = axi_master_r_data;
      assign data_async_r[2+DATA_ID_WIDTH:3+AXI_DATA_WIDTH]     = axi_master_r_id;
      assign data_async_r[2+DATA_USER_ID_WIDTH:3+DATA_ID_WIDTH] = axi_master_r_user;
      assign axi_slave_r_last                                   = data_r[0];
      assign axi_slave_r_resp                                   = data_r[2:1];
      assign axi_slave_r_data                                   = data_r[2+AXI_DATA_WIDTH:3];
      assign axi_slave_r_id                                     = data_r[2+DATA_ID_WIDTH:3+AXI_DATA_WIDTH];
      assign axi_slave_r_user                                   = data_r[2+DATA_USER_ID_WIDTH:3+DATA_ID_WIDTH];

      assign data_w[0]                                      = axi_slave_w_last;
      assign data_w[AXI_DATA_WIDTH:1]                       = axi_slave_w_data;
      assign data_w[DATA_STRB_WIDTH:1+AXI_DATA_WIDTH]       = axi_slave_w_strb;
      assign data_w[DATA_USER_STRB_WIDTH:1+DATA_STRB_WIDTH] = axi_slave_w_user;
      assign axi_master_w_last                              = data_async_w[0];
      assign axi_master_w_data                              = data_async_w[AXI_DATA_WIDTH:1];
      assign axi_master_w_strb                              = data_async_w[DATA_STRB_WIDTH:1+AXI_DATA_WIDTH];
      assign axi_master_w_user                              = data_async_w[DATA_USER_STRB_WIDTH:1+DATA_STRB_WIDTH];

      assign data_async_b[1:0]                              = axi_master_b_resp;
      assign data_async_b[1+AXI_ID_WIDTH:2]                 = axi_master_b_id;
      assign data_async_b[1+USER_ID_WIDTH:2+AXI_ID_WIDTH]   = axi_master_b_user;
      assign axi_slave_b_resp                               = data_b[1:0];
      assign axi_slave_b_id                                 = data_b[1+AXI_ID_WIDTH:2];
      assign axi_slave_b_user                               = data_b[1+USER_ID_WIDTH:2+AXI_ID_WIDTH];

      dc_token_ring_fifo_din #(WIDTH_FIFO_AW,BUFFER_WIDTH)
      dc_awchan
      (
        .clk          ( clk_i                     ),
        .rstn         ( rst_ni                    ),
        .data         ( data_aw                   ),
        .valid        ( axi_slave_aw_valid        ),
        .ready        ( axi_slave_aw_ready        ),
        .write_token  ( axi_master_aw_writetoken  ),
        .read_pointer ( axi_master_aw_readpointer ),
        .data_async   ( data_async_aw             )
      );

      dc_token_ring_fifo_din #(WIDTH_FIFO_AR,BUFFER_WIDTH)
      dc_archan
      (
        .clk          ( clk_i                     ),
        .rstn         ( rst_ni                    ),
        .data         ( data_ar                   ),
        .valid        ( axi_slave_ar_valid        ),
        .ready        ( axi_slave_ar_ready        ),
        .write_token  ( axi_master_ar_writetoken  ),
        .read_pointer ( axi_master_ar_readpointer ),
        .data_async   ( data_async_ar             )
      );

      dc_token_ring_fifo_din #(WIDTH_FIFO_W,BUFFER_WIDTH)
      dc_wchan
      (
        .clk          ( clk_i                    ),
        .rstn         ( rst_ni                   ),
        .data         ( data_w                   ),
        .valid        ( axi_slave_w_valid        ),
        .ready        ( axi_slave_w_ready        ),
        .write_token  ( axi_master_w_writetoken  ),
        .read_pointer ( axi_master_w_readpointer ),
        .data_async   ( data_async_w             )
      );

      dc_token_ring_fifo_dout #(WIDTH_FIFO_R,BUFFER_WIDTH)
      dc_rchan
      (
        .clk          ( clk_i                    ),
        .rstn         ( rst_ni                   ),
        .data         ( data_r                   ),
        .valid        ( axi_slave_r_valid        ),
        .ready        ( axi_slave_r_ready        ),
        .write_token  ( axi_master_r_writetoken  ),
        .read_pointer ( axi_master_r_readpointer ),
        .data_async   ( data_async_r             )
      );

      dc_token_ring_fifo_dout #(WIDTH_FIFO_B,BUFFER_WIDTH)
      dc_bchan
      (
        .clk          ( clk_i                    ),
        .rstn         ( rst_ni                   ),
        .data         ( data_b                   ),
        .valid        ( axi_slave_b_valid        ),
        .ready        ( axi_slave_b_ready        ),
        .write_token  ( axi_master_b_writetoken  ),
        .read_pointer ( axi_master_b_readpointer ),
        .data_async   ( data_async_b             )
      );

endmodule

