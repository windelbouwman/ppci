// Copyright 2015 ETH Zurich and University of Bologna.
// Copyright and related rights are licensed under the Solderpad Hardware
// License, Version 0.51 (the “License”); you may not use this file except in
// compliance with the License.  You may obtain a copy of the License at
// http://solderpad.org/licenses/SHL-0.51. Unless required by applicable law
// or agreed to in writing, software, hardware and materials distributed under
// this License is distributed on an “AS IS” BASIS, WITHOUT WARRANTIES OR
// CONDITIONS OF ANY KIND, either express or implied. See the License for the
// specific language governing permissions and limitations under the License.

`define log2(VALUE) ((VALUE) < ( 1 ) ? 0 : (VALUE) < ( 2 ) ? 1 : (VALUE) < ( 4 ) ? 2 : (VALUE) < ( 8 ) ? 3 : (VALUE) < ( 16 )  ? 4 : (VALUE) < ( 32 )  ? 5 : (VALUE) < ( 64 )  ? 6 : (VALUE) < ( 128 ) ? 7 : (VALUE) < ( 256 ) ? 8 : (VALUE) < ( 512 ) ? 9 : (VALUE) < ( 1024 ) ? 10 : (VALUE) < ( 2048 ) ? 11 : (VALUE) < ( 4096 ) ? 12 : (VALUE) < ( 8192 ) ? 13 : (VALUE) < ( 16384 ) ? 14 : (VALUE) < ( 32768 ) ? 15 : (VALUE) < ( 65536 ) ? 16 : (VALUE) < ( 131072 ) ? 17 : (VALUE) < ( 262144 ) ? 18 : (VALUE) < ( 524288 ) ? 19 : (VALUE) < ( 1048576 ) ? 20 : (VALUE) < ( 1048576 * 2 ) ? 21 : (VALUE) < ( 1048576 * 4 ) ? 22 : (VALUE) < ( 1048576 * 8 ) ? 23 : (VALUE) < ( 1048576 * 16 ) ? 24 : 25)

module axi_spi_master
#(
    parameter AXI4_ADDRESS_WIDTH = 32,
    parameter AXI4_RDATA_WIDTH   = 32,
    parameter AXI4_WDATA_WIDTH   = 32,
    parameter AXI4_USER_WIDTH    = 4,
    parameter AXI4_ID_WIDTH      = 16,
    parameter BUFFER_DEPTH       = 8
)
(
    input  logic                          s_axi_aclk,
    input  logic                          s_axi_aresetn,

    input  logic                          s_axi_awvalid,
    input  logic      [AXI4_ID_WIDTH-1:0] s_axi_awid,
    input  logic                    [7:0] s_axi_awlen,
    input  logic [AXI4_ADDRESS_WIDTH-1:0] s_axi_awaddr,
    input  logic    [AXI4_USER_WIDTH-1:0] s_axi_awuser,
    output logic                          s_axi_awready,

    input  logic                          s_axi_wvalid,
    input  logic   [AXI4_WDATA_WIDTH-1:0] s_axi_wdata,
    input  logic [AXI4_WDATA_WIDTH/8-1:0] s_axi_wstrb,
    input  logic                          s_axi_wlast,
    input  logic    [AXI4_USER_WIDTH-1:0] s_axi_wuser,
    output logic                          s_axi_wready,

    output logic                          s_axi_bvalid,
    output logic      [AXI4_ID_WIDTH-1:0] s_axi_bid,
    output logic                    [1:0] s_axi_bresp,
    output logic    [AXI4_USER_WIDTH-1:0] s_axi_buser,
    input  logic                          s_axi_bready,

    input  logic                          s_axi_arvalid,
    input  logic      [AXI4_ID_WIDTH-1:0] s_axi_arid,
    input  logic                    [7:0] s_axi_arlen,
    input  logic [AXI4_ADDRESS_WIDTH-1:0] s_axi_araddr,
    input  logic    [AXI4_USER_WIDTH-1:0] s_axi_aruser,
    output logic                          s_axi_arready,

    output logic                          s_axi_rvalid,
    output logic      [AXI4_ID_WIDTH-1:0] s_axi_rid,
    output logic   [AXI4_RDATA_WIDTH-1:0] s_axi_rdata,
    output logic                    [1:0] s_axi_rresp,
    output logic                          s_axi_rlast,
    output logic    [AXI4_USER_WIDTH-1:0] s_axi_ruser,
    input  logic                          s_axi_rready,

    output logic                    [1:0] events_o,

    output logic                          spi_clk,
    output logic                          spi_csn0,
    output logic                          spi_csn1,
    output logic                          spi_csn2,
    output logic                          spi_csn3,
    output logic                    [1:0] spi_mode,
    output logic                          spi_sdo0,
    output logic                          spi_sdo1,
    output logic                          spi_sdo2,
    output logic                          spi_sdo3,
    input  logic                          spi_sdi0,
    input  logic                          spi_sdi1,
    input  logic                          spi_sdi2,
    input  logic                          spi_sdi3
);


    localparam LOG_BUFFER_DEPTH = `log2(BUFFER_DEPTH);

    logic   [7:0] spi_clk_div;
    logic         spi_clk_div_valid;
    logic  [31:0] spi_status;
    logic  [31:0] spi_addr;
    logic   [5:0] spi_addr_len;
    logic  [31:0] spi_cmd;
    logic   [5:0] spi_cmd_len;
    logic  [15:0] spi_data_len;
    logic  [15:0] spi_dummy_rd;
    logic  [15:0] spi_dummy_wr;
    logic         spi_swrst;
    logic         spi_rd;
    logic         spi_wr;
    logic         spi_qrd;
    logic         spi_qwr;
    logic   [3:0] spi_csreg;
    logic  [31:0] spi_data_tx;
    logic         spi_data_tx_valid;
    logic         spi_data_tx_ready;
    logic  [31:0] spi_data_rx;
    logic         spi_data_rx_valid;
    logic         spi_data_rx_ready;
    logic   [6:0] spi_ctrl_status;
    logic  [31:0] spi_ctrl_data_tx;
    logic         spi_ctrl_data_tx_valid;
    logic         spi_ctrl_data_tx_ready;
    logic  [31:0] spi_ctrl_data_rx;
    logic         spi_ctrl_data_rx_valid;
    logic         spi_ctrl_data_rx_ready;

    logic         s_eot;

    logic [LOG_BUFFER_DEPTH:0] elements_tx;
    logic [LOG_BUFFER_DEPTH:0] elements_rx;
    logic [LOG_BUFFER_DEPTH:0] elements_tx_old;
    logic [LOG_BUFFER_DEPTH:0] elements_rx_old;

    localparam FILL_BITS = 7-LOG_BUFFER_DEPTH;

    assign spi_status = {{FILL_BITS{1'b0}},elements_tx,{FILL_BITS{1'b0}},elements_rx,9'h0,spi_ctrl_status};
    assign events_o[0] = (((elements_rx==4'b0100) && (elements_rx_old==4'b0101)) || ((elements_tx==4'b0101) && (elements_tx_old==4'b0100)));
    assign events_o[1] = s_eot;

    always_ff @(posedge s_axi_aclk or negedge s_axi_aresetn)
    begin
        if (s_axi_aresetn == 1'b0)
        begin
            elements_rx_old <= 'h0;
            elements_tx_old <= 'h0;
        end
        else
        begin
            elements_rx_old <= elements_rx;
            elements_tx_old <= elements_tx;
        end
    end

    spi_master_axi_if
    #(
        .AXI4_ADDRESS_WIDTH(AXI4_ADDRESS_WIDTH),
        .AXI4_RDATA_WIDTH(AXI4_RDATA_WIDTH),
        .AXI4_WDATA_WIDTH(AXI4_WDATA_WIDTH),
        .AXI4_USER_WIDTH(AXI4_USER_WIDTH),
        .AXI4_ID_WIDTH(AXI4_ID_WIDTH)
    )
    u_axiregs
    (
        .s_axi_aclk(s_axi_aclk),
        .s_axi_aresetn(s_axi_aresetn),

        .s_axi_awvalid(s_axi_awvalid),
        .s_axi_awid(s_axi_awid),
        .s_axi_awlen(s_axi_awlen),
        .s_axi_awaddr(s_axi_awaddr),
        .s_axi_awuser(s_axi_awuser),
        .s_axi_awready(s_axi_awready),

        .s_axi_wvalid(s_axi_wvalid),
        .s_axi_wdata(s_axi_wdata),
        .s_axi_wstrb(s_axi_wstrb),
        .s_axi_wlast(s_axi_wlast),
        .s_axi_wuser(s_axi_wuser),
        .s_axi_wready(s_axi_wready),

        .s_axi_bvalid(s_axi_bvalid),
        .s_axi_bid(s_axi_bid),
        .s_axi_bresp(s_axi_bresp),
        .s_axi_buser(s_axi_buser),
        .s_axi_bready(s_axi_bready),

        .s_axi_arvalid(s_axi_arvalid),
        .s_axi_arid(s_axi_arid),
        .s_axi_arlen(s_axi_arlen),
        .s_axi_araddr(s_axi_araddr),
        .s_axi_aruser(s_axi_aruser),
        .s_axi_arready(s_axi_arready),

        .s_axi_rvalid(s_axi_rvalid),
        .s_axi_rid(s_axi_rid),
        .s_axi_rdata(s_axi_rdata),
        .s_axi_rresp(s_axi_rresp),
        .s_axi_rlast(s_axi_rlast),
        .s_axi_ruser(s_axi_ruser),
        .s_axi_rready(s_axi_rready),

        .spi_clk_div(spi_clk_div),
        .spi_clk_div_valid(spi_clk_div_valid),
        .spi_status(spi_status),
        .spi_addr(spi_addr),
        .spi_addr_len(spi_addr_len),
        .spi_cmd(spi_cmd),
        .spi_cmd_len(spi_cmd_len),
        .spi_data_len(spi_data_len),
        .spi_dummy_rd(spi_dummy_rd),
        .spi_dummy_wr(spi_dummy_wr),
        .spi_swrst(spi_swrst),
        .spi_rd(spi_rd),
        .spi_wr(spi_wr),
        .spi_qrd(spi_qrd),
        .spi_qwr(spi_qwr),
        .spi_csreg(spi_csreg),
        .spi_data_tx(spi_data_tx),
        .spi_data_tx_valid(spi_data_tx_valid),
        .spi_data_tx_ready(spi_data_tx_ready),
        .spi_data_rx(spi_data_rx),
        .spi_data_rx_valid(spi_data_rx_valid),
        .spi_data_rx_ready(spi_data_rx_ready)
    );

    spi_master_fifo
    #(
        .DATA_WIDTH(32),
        .BUFFER_DEPTH(BUFFER_DEPTH)
    )
    u_txfifo
    (
        .clk_i(s_axi_aclk),
        .rst_ni(s_axi_aresetn),
        .clr_i(spi_swrst),

        .elements_o(elements_tx),

        .data_o(spi_ctrl_data_tx),
        .valid_o(spi_ctrl_data_tx_valid),
        .ready_i(spi_ctrl_data_tx_ready),

        .valid_i(spi_data_tx_valid),
        .data_i(spi_data_tx),
        .ready_o(spi_data_tx_ready)
    );

    spi_master_fifo
    #(
        .DATA_WIDTH(32),
        .BUFFER_DEPTH(BUFFER_DEPTH)
    )
    u_rxfifo
    (
        .clk_i(s_axi_aclk),
        .rst_ni(s_axi_aresetn),
        .clr_i(spi_swrst),

        .elements_o(elements_rx),

        .data_o(spi_data_rx),
        .valid_o(spi_data_rx_valid),
        .ready_i(spi_data_rx_ready),

        .valid_i(spi_ctrl_data_rx_valid),
        .data_i(spi_ctrl_data_rx),
        .ready_o(spi_ctrl_data_rx_ready)
    );

    spi_master_controller u_spictrl
    (
        .clk(s_axi_aclk),
        .rstn(s_axi_aresetn),
        .eot(s_eot),
        .spi_clk_div(spi_clk_div),
        .spi_clk_div_valid(spi_clk_div_valid),
        .spi_status(spi_ctrl_status),
        .spi_addr(spi_addr),
        .spi_addr_len(spi_addr_len),
        .spi_cmd(spi_cmd),
        .spi_cmd_len(spi_cmd_len),
        .spi_data_len(spi_data_len),
        .spi_dummy_rd(spi_dummy_rd),
        .spi_dummy_wr(spi_dummy_wr),
        .spi_swrst(spi_swrst),
        .spi_rd(spi_rd),
        .spi_wr(spi_wr),
        .spi_qrd(spi_qrd),
        .spi_qwr(spi_qwr),
        .spi_csreg(spi_csreg),
        .spi_ctrl_data_tx(spi_ctrl_data_tx),
        .spi_ctrl_data_tx_valid(spi_ctrl_data_tx_valid),
        .spi_ctrl_data_tx_ready(spi_ctrl_data_tx_ready),
        .spi_ctrl_data_rx(spi_ctrl_data_rx),
        .spi_ctrl_data_rx_valid(spi_ctrl_data_rx_valid),
        .spi_ctrl_data_rx_ready(spi_ctrl_data_rx_ready),
        .spi_clk(spi_clk),
        .spi_csn0(spi_csn0),
        .spi_csn1(spi_csn1),
        .spi_csn2(spi_csn2),
        .spi_csn3(spi_csn3),
        .spi_mode(spi_mode),
        .spi_sdo0(spi_sdo0),
        .spi_sdo1(spi_sdo1),
        .spi_sdo2(spi_sdo2),
        .spi_sdo3(spi_sdo3),
        .spi_sdi0(spi_sdi0),
        .spi_sdi1(spi_sdi1),
        .spi_sdi2(spi_sdi2),
        .spi_sdi3(spi_sdi3)
    );

endmodule
