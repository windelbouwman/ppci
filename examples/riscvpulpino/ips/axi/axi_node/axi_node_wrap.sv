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

module axi_node_wrap
#(

    parameter                   AXI_ADDRESS_W      = 32,
    parameter                   AXI_DATA_W         = 64,
    parameter                   AXI_NUMBYTES       = AXI_DATA_W/8,
    parameter                   AXI_USER_W         = 6,
`ifdef USE_CFG_BLOCK
  `ifdef USE_AXI_LITE
    parameter                   AXI_LITE_ADDRESS_W = 32,
    parameter                   AXI_LITE_DATA_W    = 32,
  `else
    parameter                   APB_ADDR_WIDTH     = 12,  //APB slaves are 4KB by default
    parameter                   APB_DATA_WIDTH     = 32,
  `endif
`endif
    parameter                   N_MASTER_PORT      = 8,
    parameter                   N_SLAVE_PORT       = 4,
    parameter                   AXI_ID_IN          = 10,
    parameter                   AXI_ID_OUT         = AXI_ID_IN + $clog2(N_SLAVE_PORT),
    parameter                   FIFO_DEPTH_DW      = 8,
    parameter                   N_REGION           = 2
)
(
    input logic                                                          clk,
    input logic                                                          rst_n,

    //MASTER PORTS
    AXI_BUS.Slave                                                        axi_port_slave  [N_SLAVE_PORT-1:0], // modified for verilator-simulation purpose 
    AXI_BUS.Master                                                       axi_port_master [N_MASTER_PORT-1:0], // modified for verilator-simulation purpose 

    `ifdef USE_CFG_BLOCK
        `ifdef USE_AXI_LITE
            AXI_LITE_BUS.Slave                                           cfg_port_slave,
        `else
            APB_BUS.Slave                                                cfg_port_slave,
        `endif
    `endif

    input  logic [N_REGION-1:0][N_MASTER_PORT-1:0][31:0]                 cfg_START_ADDR_i,
    input  logic [N_REGION-1:0][N_MASTER_PORT-1:0][31:0]                 cfg_END_ADDR_i,
    input  logic [N_REGION-1:0][N_MASTER_PORT-1:0]                       cfg_valid_rule_i,
    input  logic [N_SLAVE_PORT-1:0][N_MASTER_PORT-1:0]                   cfg_connectivity_map_i
);


  // ---------------------------------------------------------------
  // AXI TARG Port Declarations -----------------------------------------
  // ---------------------------------------------------------------
  //AXI write address bus -------------- // USED// --------------
  logic [N_SLAVE_PORT-1:0][AXI_ID_IN-1:0]                       slave_awid;
  logic [N_SLAVE_PORT-1:0][AXI_ADDRESS_W-1:0]                   slave_awaddr;
  logic [N_SLAVE_PORT-1:0][ 7:0]                                slave_awlen;
  logic [N_SLAVE_PORT-1:0][ 2:0]                                slave_awsize;
  logic [N_SLAVE_PORT-1:0][ 1:0]                                slave_awburst;
  logic [N_SLAVE_PORT-1:0]                                      slave_awlock;
  logic [N_SLAVE_PORT-1:0][ 3:0]                                slave_awcache;
  logic [N_SLAVE_PORT-1:0][ 2:0]                                slave_awprot;
  logic [N_SLAVE_PORT-1:0][ 3:0]                                slave_awregion;
  logic [N_SLAVE_PORT-1:0][ AXI_USER_W-1:0]                     slave_awuser;
  logic [N_SLAVE_PORT-1:0][ 3:0]                                slave_awqos;
  logic [N_SLAVE_PORT-1:0]                                      slave_awvalid;
  logic [N_SLAVE_PORT-1:0]                                      slave_awready;
  // ---------------------------------------------------------------

  //AXI write data bus -------------- // USED// --------------
  logic [N_SLAVE_PORT-1:0] [AXI_DATA_W-1:0]                     slave_wdata;
  logic [N_SLAVE_PORT-1:0] [AXI_NUMBYTES-1:0]                   slave_wstrb;
  logic [N_SLAVE_PORT-1:0]                                      slave_wlast;
  logic [N_SLAVE_PORT-1:0] [AXI_USER_W-1:0]                     slave_wuser;
  logic [N_SLAVE_PORT-1:0]                                      slave_wvalid;
  logic [N_SLAVE_PORT-1:0]                                      slave_wready;
  // ---------------------------------------------------------------

  //AXI write response bus -------------- // USED// --------------
   logic [N_SLAVE_PORT-1:0]  [AXI_ID_IN-1:0]                    slave_bid;
   logic [N_SLAVE_PORT-1:0]  [ 1:0]                             slave_bresp;
   logic [N_SLAVE_PORT-1:0]                                     slave_bvalid;
   logic [N_SLAVE_PORT-1:0]  [AXI_USER_W-1:0]                   slave_buser;
   logic [N_SLAVE_PORT-1:0]                                     slave_bready;
  // ---------------------------------------------------------------



  //AXI read address bus -------------------------------------------
  logic [N_SLAVE_PORT-1:0][AXI_ID_IN-1:0]                       slave_arid;
  logic [N_SLAVE_PORT-1:0][AXI_ADDRESS_W-1:0]                   slave_araddr;
  logic [N_SLAVE_PORT-1:0][ 7:0]                                slave_arlen;
  logic [N_SLAVE_PORT-1:0][ 2:0]                                slave_arsize;
  logic [N_SLAVE_PORT-1:0][ 1:0]                                slave_arburst;
  logic [N_SLAVE_PORT-1:0]                                      slave_arlock;
  logic [N_SLAVE_PORT-1:0][ 3:0]                                slave_arcache;
  logic [N_SLAVE_PORT-1:0][ 2:0]                                slave_arprot;
  logic [N_SLAVE_PORT-1:0][ 3:0]                                slave_arregion;
  logic [N_SLAVE_PORT-1:0][ AXI_USER_W-1:0]                     slave_aruser;
  logic [N_SLAVE_PORT-1:0][ 3:0]                                slave_arqos;
  logic [N_SLAVE_PORT-1:0]                                      slave_arvalid;
  logic [N_SLAVE_PORT-1:0]                                      slave_arready;
  // ---------------------------------------------------------------


  //AXI read data bus ----------------------------------------------
  logic [N_SLAVE_PORT-1:0][AXI_ID_IN-1:0]                       slave_rid;
  logic [N_SLAVE_PORT-1:0][AXI_DATA_W-1:0]                      slave_rdata;
  logic [N_SLAVE_PORT-1:0][ 1:0]                                slave_rresp;
  logic [N_SLAVE_PORT-1:0]                                      slave_rlast;
  logic [N_SLAVE_PORT-1:0][AXI_USER_W-1:0]                      slave_ruser;
  logic [N_SLAVE_PORT-1:0]                                      slave_rvalid;
  logic [N_SLAVE_PORT-1:0]                                      slave_rready;
  // ---------------------------------------------------------------





  // ---------------------------------------------------------------
  // AXI INIT Port Declarations -----------------------------------------
  // ---------------------------------------------------------------
  //AXI write address bus -------------- // // --------------
  logic [N_MASTER_PORT-1:0][AXI_ID_OUT-1:0]                     master_awid;
  logic [N_MASTER_PORT-1:0][AXI_ADDRESS_W-1:0]                  master_awaddr;
  logic [N_MASTER_PORT-1:0][ 7:0]                               master_awlen;
  logic [N_MASTER_PORT-1:0][ 2:0]                               master_awsize;
  logic [N_MASTER_PORT-1:0][ 1:0]                               master_awburst;
  logic [N_MASTER_PORT-1:0]                                     master_awlock;
  logic [N_MASTER_PORT-1:0][ 3:0]                               master_awcache;
  logic [N_MASTER_PORT-1:0][ 2:0]                               master_awprot;
  logic [N_MASTER_PORT-1:0][ 3:0]                               master_awregion;
  logic [N_MASTER_PORT-1:0][ AXI_USER_W-1:0]                    master_awuser;
  logic [N_MASTER_PORT-1:0][ 3:0]                               master_awqos;
  logic [N_MASTER_PORT-1:0]                                     master_awvalid;
  logic [N_MASTER_PORT-1:0]                                     master_awready;
  // ---------------------------------------------------------------

  //AXI write data bus -------------- // // --------------
  logic [N_MASTER_PORT-1:0] [AXI_DATA_W-1:0]                    master_wdata;
  logic [N_MASTER_PORT-1:0] [AXI_NUMBYTES-1:0]                  master_wstrb;
  logic [N_MASTER_PORT-1:0]                                     master_wlast;
  logic [N_MASTER_PORT-1:0] [ AXI_USER_W-1:0]                   master_wuser;
  logic [N_MASTER_PORT-1:0]                                     master_wvalid;
  logic [N_MASTER_PORT-1:0]                                     master_wready;
  // ---------------------------------------------------------------

  //AXI BACKWARD write response bus -------------- // // --------------
  logic [N_MASTER_PORT-1:0] [AXI_ID_OUT-1:0]                    master_bid;
  logic [N_MASTER_PORT-1:0] [ 1:0]                              master_bresp;
  logic [N_MASTER_PORT-1:0] [ AXI_USER_W-1:0]                   master_buser;
  logic [N_MASTER_PORT-1:0]                                     master_bvalid;
  logic [N_MASTER_PORT-1:0]                                     master_bready;
  // ---------------------------------------------------------------



  //AXI read address bus -------------------------------------------
  logic [N_MASTER_PORT-1:0][AXI_ID_OUT-1:0]                     master_arid;
  logic [N_MASTER_PORT-1:0][AXI_ADDRESS_W-1:0]                  master_araddr;
  logic [N_MASTER_PORT-1:0][ 7:0]                               master_arlen;
  logic [N_MASTER_PORT-1:0][ 2:0]                               master_arsize;
  logic [N_MASTER_PORT-1:0][ 1:0]                               master_arburst;
  logic [N_MASTER_PORT-1:0]                                     master_arlock;
  logic [N_MASTER_PORT-1:0][ 3:0]                               master_arcache;
  logic [N_MASTER_PORT-1:0][ 2:0]                               master_arprot;
  logic [N_MASTER_PORT-1:0][ 3:0]                               master_arregion;
  logic [N_MASTER_PORT-1:0][ AXI_USER_W-1:0]                    master_aruser;
  logic [N_MASTER_PORT-1:0][ 3:0]                               master_arqos;
  logic [N_MASTER_PORT-1:0]                                     master_arvalid;
  logic [N_MASTER_PORT-1:0]                                     master_arready;
  // ---------------------------------------------------------------


  //AXI BACKWARD read data bus ----------------------------------------------
  logic [N_MASTER_PORT-1:0][AXI_ID_OUT-1:0]                     master_rid;
  logic [N_MASTER_PORT-1:0][AXI_DATA_W-1:0]                     master_rdata;
  logic [N_MASTER_PORT-1:0][ 1:0]                               master_rresp;
  logic [N_MASTER_PORT-1:0]                                     master_rlast;
  logic [N_MASTER_PORT-1:0][ AXI_USER_W-1:0]                    master_ruser;
  logic [N_MASTER_PORT-1:0]                                     master_rvalid;
  logic [N_MASTER_PORT-1:0]                                     master_rready;
  // ---------------------------------------------------------------


  `ifdef USE_CFG_BLOCK
    `ifdef USE_AXI_LITE
          //PROGRAMMABLE PORT -- AXI LITE
          logic [AXI_LITE_ADDRESS_W-1:0]                                cfg_awaddr;
          logic                                                         cfg_awvalid;
          logic                                                         cfg_awready;
          logic [AXI_LITE_DATA_W-1:0]                                   cfg_wdata;
          logic [AXI_LITE_DATA_W/8-1:0]                                 cfg_wstrb;
          logic                                                         cfg_wvalid;
          logic                                                         cfg_wready;
          logic [1:0]                                                   cfg_bresp;
          logic                                                         cfg_bvalid;
          logic                                                         cfg_bready;
          logic [AXI_LITE_ADDRESS_W-1:0]                                cfg_araddr;
          logic                                                         cfg_arvalid;
          logic                                                         cfg_arready;
          logic [AXI_LITE_DATA_W-1:0]                                   cfg_rdata;
          logic [1:0]                                                   cfg_rresp;
          logic                                                         cfg_rvalid;
          logic                                                         cfg_rready;
      `else
           logic                                                        HCLK     ;
           logic                                                        HRESETn  ;
           logic [APB_ADDR_WIDTH-1:0]                                   PADDR    ;
           logic [APB_DATA_WIDTH-1:0]                                   PWDATA   ;
           logic                                                        PWRITE   ;
           logic                                                        PSEL     ;
           logic                                                        PENABLE  ;
           logic [APB_DATA_WIDTH-1:0]                                   PRDATA   ;
           logic                                                        PREADY   ;
           logic                                                        PSLVERR  ;
    `endif
`endif


genvar i;

generate
  for(i=0;i<N_SLAVE_PORT;i++)
  begin : SLAVE_PORT_BINDING

        assign slave_awaddr[i]                =  axi_port_slave[i].aw_addr             ;
        assign slave_awprot[i]                =  axi_port_slave[i].aw_prot             ;
        assign slave_awregion[i]              =  axi_port_slave[i].aw_region           ;
        assign slave_awlen[i]                 =  axi_port_slave[i].aw_len              ;
        assign slave_awsize[i]                =  axi_port_slave[i].aw_size             ;
        assign slave_awburst[i]               =  axi_port_slave[i].aw_burst            ;
        assign slave_awlock[i]                =  axi_port_slave[i].aw_lock             ;
        assign slave_awcache[i]               =  axi_port_slave[i].aw_cache            ;
        assign slave_awqos[i]                 =  axi_port_slave[i].aw_qos              ;
        assign slave_awid[i]                  =  axi_port_slave[i].aw_id[AXI_ID_IN-1:0];
        assign slave_awuser[i]                =  axi_port_slave[i].aw_user             ;
        assign slave_awvalid[i]               =  axi_port_slave[i].aw_valid            ;
        assign axi_port_slave[i].aw_ready     =  slave_awready[i]                      ;

        assign slave_araddr[i]                =  axi_port_slave[i].ar_addr             ;
        assign slave_arprot[i]                =  axi_port_slave[i].ar_prot             ;
        assign slave_arregion[i]              =  axi_port_slave[i].ar_region           ;
        assign slave_arlen[i]                 =  axi_port_slave[i].ar_len              ;
        assign slave_arsize[i]                =  axi_port_slave[i].ar_size             ;
        assign slave_arburst[i]               =  axi_port_slave[i].ar_burst            ;
        assign slave_arlock[i]                =  axi_port_slave[i].ar_lock             ;
        assign slave_arcache[i]               =  axi_port_slave[i].ar_cache            ;
        assign slave_arqos[i]                 =  axi_port_slave[i].ar_qos              ;
        assign slave_arid[i]                  =  axi_port_slave[i].ar_id[AXI_ID_IN-1:0];
        assign slave_aruser[i]                =  axi_port_slave[i].ar_user             ;
        assign slave_arvalid[i]               =  axi_port_slave[i].ar_valid            ;
        assign axi_port_slave[i].ar_ready     =  slave_arready[i]                      ;

        assign slave_wvalid[i]                =  axi_port_slave[i].w_valid             ;
        assign slave_wdata[i]                 =  axi_port_slave[i].w_data              ;
        assign slave_wstrb[i]                 =  axi_port_slave[i].w_strb              ;
        assign slave_wuser[i]                 =  axi_port_slave[i].w_user              ;
        assign slave_wlast[i]                 =  axi_port_slave[i].w_last              ;
        assign axi_port_slave[i].w_ready      =  slave_wready[i]                       ;

        assign axi_port_slave[i].b_id[AXI_ID_IN-1:0]         =  slave_bid[i]           ;
        assign axi_port_slave[i].b_resp       =  slave_bresp[i]                        ;
        assign axi_port_slave[i].b_valid      =  slave_bvalid[i]                       ;
        assign axi_port_slave[i].b_user       =  slave_buser[i]                        ;
        assign slave_bready[i]                =  axi_port_slave[i].b_ready             ;

        assign axi_port_slave[i].r_data       =  slave_rdata[i]                        ;
        assign axi_port_slave[i].r_resp       =  slave_rresp[i]                        ;
        assign axi_port_slave[i].r_last       =  slave_rlast[i]                        ;
        assign axi_port_slave[i].r_id[AXI_ID_IN-1:0]         =  slave_rid[i]           ;
        assign axi_port_slave[i].r_user       =  slave_ruser[i]                        ;
        assign axi_port_slave[i].r_valid      =  slave_rvalid[i]                       ;
        assign slave_rready[i]                =  axi_port_slave[i].r_ready             ;

  end

  for(i=0; i<N_MASTER_PORT; i++)
  begin : MASTER_PORT_BINDING

        assign axi_port_master[i].aw_addr              = master_awaddr[i]                ;
        assign axi_port_master[i].aw_prot              = master_awprot[i]                ;
        assign axi_port_master[i].aw_region            = master_awregion[i]              ;
        assign axi_port_master[i].aw_len               = master_awlen[i]                 ;
        assign axi_port_master[i].aw_size              = master_awsize[i]                ;
        assign axi_port_master[i].aw_burst             = master_awburst[i]               ;
        assign axi_port_master[i].aw_lock              = master_awlock[i]                ;
        assign axi_port_master[i].aw_cache             = master_awcache[i]               ;
        assign axi_port_master[i].aw_qos               = master_awqos[i]                 ;
        assign axi_port_master[i].aw_id[AXI_ID_OUT-1:0]= master_awid[i]                  ;
        assign axi_port_master[i].aw_user              = master_awuser[i]                ;
        assign axi_port_master[i].aw_valid             = master_awvalid[i]               ;
        assign master_awready[i]                       = axi_port_master[i].aw_ready     ;

        assign axi_port_master[i].ar_addr              =  master_araddr[i]               ;
        assign axi_port_master[i].ar_prot              =  master_arprot[i]               ;
        assign axi_port_master[i].ar_region            =  master_arregion[i]             ;
        assign axi_port_master[i].ar_len               =  master_arlen[i]                ;
        assign axi_port_master[i].ar_size              =  master_arsize[i]               ;
        assign axi_port_master[i].ar_burst             =  master_arburst[i]              ;
        assign axi_port_master[i].ar_lock              =  master_arlock[i]               ;
        assign axi_port_master[i].ar_cache             =  master_arcache[i]              ;
        assign axi_port_master[i].ar_qos               =  master_arqos[i]                ;
        assign axi_port_master[i].ar_id[AXI_ID_OUT-1:0]=  master_arid[i]                 ;
        assign axi_port_master[i].ar_user              =  master_aruser[i]               ;
        assign axi_port_master[i].ar_valid             =  master_arvalid[i]              ;
        assign master_arready[i]                       =  axi_port_master[i].ar_ready    ;

        assign axi_port_master[i].w_valid              =  master_wvalid[i]               ;
        assign axi_port_master[i].w_data               =  master_wdata[i]                ;
        assign axi_port_master[i].w_strb               =  master_wstrb[i]                ;
        assign axi_port_master[i].w_user               =  master_wuser[i]                ;
        assign axi_port_master[i].w_last               =  master_wlast[i]                ;
        assign master_wready[i]                        =  axi_port_master[i].w_ready     ;

        assign master_bid[i]                           =  axi_port_master[i].b_id[AXI_ID_OUT-1:0]   ;
        assign master_bresp[i]                         =  axi_port_master[i].b_resp                 ;
        assign master_bvalid[i]                        =  axi_port_master[i].b_valid                ;
        assign master_buser[i]                         =  axi_port_master[i].b_user                 ;
        assign axi_port_master[i].b_ready              =  master_bready[i]                          ;

        assign master_rdata[i]                         =  axi_port_master[i].r_data                 ;
        assign master_rresp[i]                         =  axi_port_master[i].r_resp                 ;
        assign master_rlast[i]                         =  axi_port_master[i].r_last                 ;
        assign master_rid[i]                           =  axi_port_master[i].r_id[AXI_ID_OUT-1:0]   ;
        assign master_ruser[i]                         =  axi_port_master[i].r_user                 ;
        assign master_rvalid[i]                        =  axi_port_master[i].r_valid                ;
        assign axi_port_master[i].r_ready              =  master_rready[i]                          ;
  end
endgenerate

`ifdef USE_CFG_BLOCK
    `ifdef USE_AXI_LITE
        assign  cfg_awaddr              = cfg_port_slave.awaddr  ;
        assign  cfg_awvalid             = cfg_port_slave.awvalid ;
        assign  cfg_port_slave.awready  = cfg_awready            ;

        assign  cfg_wdata              = cfg_port_slave.wdata;
        assign  cfg_wstrb              = cfg_port_slave.wstrb;
        assign  cfg_wvalid             = cfg_port_slave.wvalid;
        assign  cfg_port_slave.wready  = cfg_wready;

        assign  cfg_port_slave.bresp   = cfg_bresp;
        assign  cfg_port_slave.bvalid  = cfg_bvalid;
        assign  cfg_bready             = cfg_port_slave.bready;

        assign  cfg_araddr             = cfg_port_slave.araddr;
        assign  cfg_arvalid            = cfg_port_slave.arvalid;
        assign  cfg_port_slave.arready = cfg_arready;

        assign  cfg_port_slave.rdata   = cfg_rdata;
        assign  cfg_port_slave.rresp   = cfg_rresp;
        assign  cfg_port_slave.rvalid  = cfg_rvalid;
        assign  cfg_rready             = cfg_port_slave.rready;
    `else
        assign  HCLK     = cfg_port_slave.HCLK     ;
        assign  HRESETn  = cfg_port_slave.HRESETn  ;
        assign  PADDR    = cfg_port_slave.PADDR    ;
        assign  PWDATA   = cfg_port_slave.PWDATA   ;
        assign  PWRITE   = cfg_port_slave.PWRITE   ;
        assign  PSEL     = cfg_port_slave.PSEL     ;
        assign  PENABLE  = cfg_port_slave.PENABLE  ;
        assign  cfg_port_slave.PRDATA   = PRDATA   ;
        assign  cfg_port_slave.PREADY   = PREADY   ;
        assign  cfg_port_slave.PSLVERR  = PSLVERR  ;
    `endif
`endif




axi_node
#(
    .AXI_ADDRESS_W           ( AXI_ADDRESS_W       ),
    .AXI_DATA_W              ( AXI_DATA_W          ),
    .AXI_ID_IN               ( AXI_ID_IN           ),
    .AXI_USER_W              ( AXI_USER_W          ),
`ifdef USE_CFG_BLOCK
  `ifdef USE_AXI_LITE
        .AXI_LITE_ADDRESS_W  ( AXI_LITE_ADDRESS_W  ),
        .AXI_LITE_DATA_W     ( AXI_LITE_DATA_W     ),
        .AXI_LITE_BE_W       ( AXI_LITE_BE_W       ),
   `else
        .APB_ADDR_WIDTH      ( APB_ADDR_WIDTH      ),
        .APB_DATA_WIDTH      ( APB_DATA_WIDTH      ),
   `endif
`endif
    .N_MASTER_PORT           ( N_MASTER_PORT       ),
    .N_SLAVE_PORT            ( N_SLAVE_PORT        ),
    .N_REGION                ( N_REGION            )
)
AXI4_NODE
(
  .clk(clk),
  .rst_n(rst_n),

  // ---------------------------------------------------------------
  // AXI TARG Port Declarations -----------------------------------------
  // ---------------------------------------------------------------
  //AXI write address bus -------------- // USED// --------------
  .slave_awid_i    (  slave_awid     ),
  .slave_awaddr_i  (  slave_awaddr   ),
  .slave_awlen_i   (  slave_awlen    ),
  .slave_awsize_i  (  slave_awsize   ),
  .slave_awburst_i (  slave_awburst  ),
  .slave_awlock_i  (  slave_awlock   ),
  .slave_awcache_i (  slave_awcache  ),
  .slave_awprot_i  (  slave_awprot   ),
  .slave_awregion_i(  slave_awregion ),
  .slave_awqos_i   (  slave_awqos    ),
  .slave_awuser_i  (  slave_awuser   ),
  .slave_awvalid_i (  slave_awvalid  ),
  .slave_awready_o (  slave_awready  ),
  // ---------------------------------------------------------------

  //AXI write data bus -------------- // USED// --------------
  .slave_wdata_i   (  slave_wdata    ),
  .slave_wstrb_i   (  slave_wstrb    ),
  .slave_wlast_i   (  slave_wlast    ),
  .slave_wuser_i   (  slave_wuser    ),
  .slave_wvalid_i  (  slave_wvalid   ),
  .slave_wready_o  (  slave_wready   ),
  // ---------------------------------------------------------------

  //AXI write response bus -------------- // USED// --------------
  .slave_bid_o     (  slave_bid     ),
  .slave_bresp_o   (  slave_bresp   ),
  .slave_buser_o   (  slave_buser   ),
  .slave_bvalid_o  (  slave_bvalid  ),
  .slave_bready_i  (  slave_bready  ),
  // ---------------------------------------------------------------



  //AXI read address bus -------------------------------------------
  .slave_arid_i    (  slave_arid     ),
  .slave_araddr_i  (  slave_araddr   ),
  .slave_arlen_i   (  slave_arlen    ),   //burst length - 1 to 16
  .slave_arsize_i  (  slave_arsize   ),  //size of each transfer in burst
  .slave_arburst_i (  slave_arburst  ), //for bursts>1(), accept only incr burst=01
  .slave_arlock_i  (  slave_arlock   ),  //only normal access supported axs_awlock=00
  .slave_arcache_i (  slave_arcache  ),
  .slave_arprot_i  (  slave_arprot   ),
  .slave_arregion_i(  slave_arregion ),
  .slave_aruser_i  (  slave_aruser   ),
  .slave_arqos_i   (  slave_arqos    ),
  .slave_arvalid_i (  slave_arvalid  ), //master addr valid
  .slave_arready_o (  slave_arready  ), //slave ready to accept
  // ---------------------------------------------------------------


  //AXI read data bus ----------------------------------------------
  .slave_rid_o     (  slave_rid      ),
  .slave_rdata_o   (  slave_rdata    ),
  .slave_rresp_o   (  slave_rresp    ),
  .slave_rlast_o   (  slave_rlast    ),   //last transfer in burst
  .slave_ruser_o   (  slave_ruser    ),
  .slave_rvalid_o  (  slave_rvalid   ),  //slave data valid
  .slave_rready_i  (  slave_rready   ),   //master ready to accept
  // ---------------------------------------------------------------





  // ---------------------------------------------------------------
  // AXI INIT Port Declarations -----------------------------------------
  // ---------------------------------------------------------------
  //AXI write address bus -------------- // // --------------
  .master_awid_o    (  master_awid     ),         //
  .master_awaddr_o  (  master_awaddr   ),         //
  .master_awlen_o   (  master_awlen    ),         //burst length is 1 + (0 - 15)
  .master_awsize_o  (  master_awsize   ),         //size of each transfer in burst
  .master_awburst_o (  master_awburst  ),         //for bursts>1(), accept only incr burst=01
  .master_awlock_o  (  master_awlock   ),         //only normal access supported axs_awlock=00
  .master_awcache_o (  master_awcache  ),         //
  .master_awprot_o  (  master_awprot   ),         //
  .master_awregion_o(  master_awregion ),         //
  .master_awuser_o  (  master_awuser   ),         //
  .master_awqos_o   (  master_awqos    ),         //
  .master_awvalid_o (  master_awvalid  ),         //master addr valid
  .master_awready_i (  master_awready  ),         //slave ready to accept
  // ---------------------------------------------------------------

  //AXI write data bus -------------- // // --------------
  .master_wdata_o   (  master_wdata    ),
  .master_wstrb_o   (  master_wstrb    ),   //1 strobe per byte
  .master_wlast_o   (  master_wlast    ),   //last transfer in burst
  .master_wuser_o   (  master_wuser    ),  //master data valid
  .master_wvalid_o  (  master_wvalid   ),  //master data valid
  .master_wready_i  (  master_wready   ),  //slave ready to accept
  // ---------------------------------------------------------------

  //AXI BACKWARD write response bus -------------- // // --------------
  .master_bid_i     (  master_bid      ),
  .master_bresp_i   (  master_bresp    ),
  .master_buser_i   (  master_buser    ),
  .master_bvalid_i  (  master_bvalid   ),
  .master_bready_o  (  master_bready   ),
  // ---------------------------------------------------------------



  //AXI read address bus -------------------------------------------
  .master_arid_o    (  master_arid     ),
  .master_araddr_o  (  master_araddr   ),
  .master_arlen_o   (  master_arlen    ),   //burst length - 1 to 16
  .master_arsize_o  (  master_arsize   ),  //size of each transfer in burst
  .master_arburst_o (  master_arburst  ), //for bursts>1(), accept only incr burst=01
  .master_arlock_o  (  master_arlock   ),  //only normal access supported axs_awlock=00
  .master_arcache_o (  master_arcache  ),
  .master_arprot_o  (  master_arprot   ),
  .master_arregion_o(  master_arregion ),
  .master_aruser_o  (  master_aruser   ),
  .master_arqos_o   (  master_arqos    ),
  .master_arvalid_o (  master_arvalid  ), //master addr valid
  .master_arready_i (  master_arready  ), //slave ready to accept
  // ---------------------------------------------------------------


  //AXI BACKWARD read data bus ----------------------------------------------
  .master_rid_i     (  master_rid      ),
  .master_rdata_i   (  master_rdata    ),
  .master_rresp_i   (  master_rresp    ),
  .master_rlast_i   (  master_rlast    ),   //last transfer in burst
  .master_ruser_i   (  master_ruser    ),   //last transfer in burst
  .master_rvalid_i  (  master_rvalid   ),  //slave data valid
  .master_rready_o  (  master_rready   ),   //master ready to accept
  // ---------------------------------------------------------------

`ifdef USE_CFG_BLOCK
  `ifdef USE_AXI_LITE
      // PROGRAMMABLE PORT -- AXI LITE
      .cfg_awaddr_i   (  cfg_awaddr    ),
      .cfg_awvalid_i  (  cfg_awvalid   ),
      .cfg_awready_o  (  cfg_awready   ),
      .cfg_wdata_i    (  cfg_wdata     ),
      .cfg_wstrb_i    (  cfg_wstrb     ),
      .cfg_wvalid_i   (  cfg_wvalid    ),
      .cfg_wready_o   (  cfg_wready    ),
      .cfg_bresp_o    (  cfg_bresp     ),
      .cfg_bvalid_o   (  cfg_bvalid    ),
      .cfg_bready_i   (  cfg_bready    ),
      .cfg_araddr_i   (  cfg_araddr    ),
      .cfg_arvalid_i  (  cfg_arvalid   ),
      .cfg_arready_o  (  cfg_arready   ),
      .cfg_rdata_o    (  cfg_rdata     ),
      .cfg_rresp_o    (  cfg_rresp     ),
      .cfg_rvalid_o   (  cfg_rvalid    ),
      .cfg_rready_i   (  cfg_rready    ),
   `else
       .HCLK          ( HCLK           ),
       .HRESETn       ( HRESETn        ),
       .PADDR_i       ( PADDR          ),
       .PWDATA_i      ( PWDATA         ),
       .PWRITE_i      ( PWRITE         ),
       .PSEL_i        ( PSEL_          ),
       .PENABLE_i     ( PENABLE        ),
       .PRDATA_o      ( PRDATA         ),
       .PREADY_o      ( PREADY         ),
       .PSLVERR_o     ( PSLVERR        ),
   `endif
`endif
  .cfg_START_ADDR_i         (cfg_START_ADDR_i       ),
  .cfg_END_ADDR_i           (cfg_END_ADDR_i         ),
  .cfg_valid_rule_i         (cfg_valid_rule_i       ),
  .cfg_connectivity_map_i   (cfg_connectivity_map_i )
);


endmodule
