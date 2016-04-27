// Copyright 2015 ETH Zurich and University of Bologna.
// Copyright and related rights are licensed under the Solderpad Hardware
// License, Version 0.51 (the “License”); you may not use this file except in
// compliance with the License.  You may obtain a copy of the License at
// http://solderpad.org/licenses/SHL-0.51. Unless required by applicable law
// or agreed to in writing, software, hardware and materials distributed under
// this License is distributed on an “AS IS” BASIS, WITHOUT WARRANTIES OR
// CONDITIONS OF ANY KIND, either express or implied. See the License for the
// specific language governing permissions and limitations under the License.

`define HP 1'b1
`define LP 1'b0

module axi_mem_if_DP_hybr
#(
    parameter AXI4_ADDRESS_WIDTH = 32,
    parameter AXI4_RDATA_WIDTH   = 64,
    parameter AXI4_WDATA_WIDTH   = 64,
    parameter AXI4_ID_WIDTH      = 16,
    parameter AXI4_USER_WIDTH    = 10,
    parameter AXI_NUMBYTES       = AXI4_WDATA_WIDTH/8,
    parameter MEM_ADDR_WIDTH     = 13,
    parameter BUFF_DEPTH_SLAVE   = 4
)
(
    input logic                                     ACLK,
    input logic                                     ARESETn,
    input logic                                     test_en_i,

    // ------------------------------------------------------------//
    // ██╗      ██████╗ ██╗    ██╗    ██████╗ ██████╗ ██╗ ██████╗  //
    // ██║     ██╔═══██╗██║    ██║    ██╔══██╗██╔══██╗██║██╔═══██╗ //
    // ██║     ██║   ██║██║ █╗ ██║    ██████╔╝██████╔╝██║██║   ██║ //
    // ██║     ██║   ██║██║███╗██║    ██╔═══╝ ██╔══██╗██║██║   ██║ //
    // ███████╗╚██████╔╝╚███╔███╔╝    ██║     ██║  ██║██║╚██████╔╝ //
    // ╚══════╝ ╚═════╝  ╚══╝╚══╝     ╚═╝     ╚═╝  ╚═╝╚═╝ ╚═════╝  //
    //-------------------------------------------------------------//

    // ---------------------------------------------------------
    // AXI TARG Port Declarations ------------------------------
    // ---------------------------------------------------------
    //AXI write address bus -------------- // USED// -----------
    input  logic [AXI4_ID_WIDTH-1:0]                LP_AWID_i     ,
    input  logic [AXI4_ADDRESS_WIDTH-1:0]           LP_AWADDR_i   ,
    input  logic [ 7:0]                             LP_AWLEN_i    ,
    input  logic [ 2:0]                             LP_AWSIZE_i   ,
    input  logic [ 1:0]                             LP_AWBURST_i  ,
    input  logic                                    LP_AWLOCK_i   ,
    input  logic [ 3:0]                             LP_AWCACHE_i  ,
    input  logic [ 2:0]                             LP_AWPROT_i   ,
    input  logic [ 3:0]                             LP_AWREGION_i ,
    input  logic [ AXI4_USER_WIDTH-1:0]             LP_AWUSER_i   ,
    input  logic [ 3:0]                             LP_AWQOS_i    ,
    input  logic                                    LP_AWVALID_i  ,
    output logic                                    LP_AWREADY_o  ,
    // ---------------------------------------------------------

    //AXI write data bus -------------- // USED// --------------
    input  logic [AXI_NUMBYTES-1:0][7:0]            LP_WDATA_i    ,
    input  logic [AXI_NUMBYTES-1:0]                 LP_WSTRB_i    ,
    input  logic                                    LP_WLAST_i    ,
    input  logic [AXI4_USER_WIDTH-1:0]              LP_WUSER_i    ,
    input  logic                                    LP_WVALID_i   ,
    output logic                                    LP_WREADY_o   ,
    // ---------------------------------------------------------

    //AXI write response bus -------------- // USED// ----------
    output logic   [AXI4_ID_WIDTH-1:0]              LP_BID_o      ,
    output logic   [ 1:0]                           LP_BRESP_o    ,
    output logic                                    LP_BVALID_o   ,
    output logic   [AXI4_USER_WIDTH-1:0]            LP_BUSER_o    ,
    input  logic                                    LP_BREADY_i   ,
    // ---------------------------------------------------------

    //AXI read address bus -------------------------------------
    input  logic [AXI4_ID_WIDTH-1:0]                LP_ARID_i     ,
    input  logic [AXI4_ADDRESS_WIDTH-1:0]           LP_ARADDR_i   ,
    input  logic [ 7:0]                             LP_ARLEN_i    ,
    input  logic [ 2:0]                             LP_ARSIZE_i   ,
    input  logic [ 1:0]                             LP_ARBURST_i  ,
    input  logic                                    LP_ARLOCK_i   ,
    input  logic [ 3:0]                             LP_ARCACHE_i  ,
    input  logic [ 2:0]                             LP_ARPROT_i   ,
    input  logic [ 3:0]                             LP_ARREGION_i ,
    input  logic [ AXI4_USER_WIDTH-1:0]             LP_ARUSER_i   ,
    input  logic [ 3:0]                             LP_ARQOS_i    ,
    input  logic                                    LP_ARVALID_i  ,
    output logic                                    LP_ARREADY_o  ,
    // ---------------------------------------------------------

    //AXI read data bus ----------------------------------------
    output  logic [AXI4_ID_WIDTH-1:0]               LP_RID_o      ,
    output  logic [AXI4_RDATA_WIDTH-1:0]            LP_RDATA_o    ,
    output  logic [ 1:0]                            LP_RRESP_o    ,
    output  logic                                   LP_RLAST_o    ,
    output  logic [AXI4_USER_WIDTH-1:0]             LP_RUSER_o    ,
    output  logic                                   LP_RVALID_o   ,
    input   logic                                   LP_RREADY_i   ,
    // ---------------------------------------------------------

    //---------------------------------------------------------//
    // ██╗  ██╗██╗    ██████╗ ██████╗ ██╗ ██████╗              //
    // ██║  ██║██║    ██╔══██╗██╔══██╗██║██╔═══██╗             //
    // ███████║██║    ██████╔╝██████╔╝██║██║   ██║             //
    // ██╔══██║██║    ██╔═══╝ ██╔══██╗██║██║   ██║             //
    // ██║  ██║██║    ██║     ██║  ██║██║╚██████╔╝             //
    // ╚═╝  ╚═╝╚═╝    ╚═╝     ╚═╝  ╚═╝╚═╝ ╚═════╝              //
    //---------------------------------------------------------//

    input  logic                                  HP_cen_i    ,
    input  logic                                  HP_wen_i    ,
    input  logic  [MEM_ADDR_WIDTH-1:0]            HP_addr_i   ,
    input  logic  [AXI4_WDATA_WIDTH-1:0]          HP_wdata_i  ,
    input  logic  [AXI_NUMBYTES-1:0]              HP_be_i     ,
    output logic  [AXI4_RDATA_WIDTH-1:0]          HP_Q_o      ,


    output logic                                    CEN        ,
    output logic                                    WEN        ,
    output logic  [MEM_ADDR_WIDTH-1:0]              A          ,
    output logic  [AXI4_WDATA_WIDTH-1:0]            D          ,
    output logic  [AXI_NUMBYTES-1:0]                BE         ,
    input  logic  [AXI4_RDATA_WIDTH-1:0]            Q
);


  localparam OFFSET_BIT = ( $clog2(AXI4_WDATA_WIDTH) - 3 );


  // -----------------------------------------------------------
  // AXI TARG Port Declarations --------------------------------
  // -----------------------------------------------------------
  //AXI write address bus --------------------------------------
  logic [AXI4_ID_WIDTH-1:0]                         LP_AWID     ;
  logic [AXI4_ADDRESS_WIDTH-1:0]                    LP_AWADDR   ;
  logic [ 7:0]                                      LP_AWLEN    ;
  logic [ 2:0]                                      LP_AWSIZE   ;
  logic [ 1:0]                                      LP_AWBURST  ;
  logic                                             LP_AWLOCK   ;
  logic [ 3:0]                                      LP_AWCACHE  ;
  logic [ 2:0]                                      LP_AWPROT   ;
  logic [ 3:0]                                      LP_AWREGION ;
  logic [ AXI4_USER_WIDTH-1:0]                      LP_AWUSER   ;
  logic [ 3:0]                                      LP_AWQOS    ;
  logic                                             LP_AWVALID  ;
  logic                                             LP_AWREADY  ;
  // -----------------------------------------------------------

  //AXI write data bus ------------------------ ----------------
  logic [AXI_NUMBYTES-1:0][7:0]                     LP_WDATA    ;
  logic [AXI_NUMBYTES-1:0]                          LP_WSTRB    ;
  logic                                             LP_WLAST    ;
  logic [AXI4_USER_WIDTH-1:0]                       LP_WUSER    ;
  logic                                             LP_WVALID   ;
  logic                                             LP_WREADY   ;
  // -----------------------------------------------------------

  //AXI write response bus -------------------------------------
  logic   [AXI4_ID_WIDTH-1:0]                       LP_BID      ;
  logic   [ 1:0]                                    LP_BRESP    ;
  logic                                             LP_BVALID   ;
  logic   [AXI4_USER_WIDTH-1:0]                     LP_BUSER    ;
  logic                                             LP_BREADY   ;
  // -----------------------------------------------------------

  //AXI read address bus ---------------------------------------
  logic [AXI4_ID_WIDTH-1:0]                         LP_ARID     ;
  logic [AXI4_ADDRESS_WIDTH-1:0]                    LP_ARADDR   ;
  logic [ 7:0]                                      LP_ARLEN    ;
  logic [ 2:0]                                      LP_ARSIZE   ;
  logic [ 1:0]                                      LP_ARBURST  ;
  logic                                             LP_ARLOCK   ;
  logic [ 3:0]                                      LP_ARCACHE  ;
  logic [ 2:0]                                      LP_ARPROT   ;
  logic [ 3:0]                                      LP_ARREGION ;
  logic [ AXI4_USER_WIDTH-1:0]                      LP_ARUSER   ;
  logic [ 3:0]                                      LP_ARQOS    ;
  logic                                             LP_ARVALID  ;
  logic                                             LP_ARREADY  ;
  // -----------------------------------------------------------

  //AXI read data bus ------------------------------------------
  logic [AXI4_ID_WIDTH-1:0]                         LP_RID     ;
  logic [AXI4_RDATA_WIDTH-1:0]                      LP_RDATA   ;
  logic [ 1:0]                                      LP_RRESP   ;
  logic                                             LP_RLAST   ;
  logic [AXI4_USER_WIDTH-1:0]                       LP_RUSER   ;
  logic                                             LP_RVALID  ;
  logic                                             LP_RREADY  ;
  // -----------------------------------------------------------


  logic valid_R_LP, valid_W_LP;
  logic grant_R_LP, grant_W_LP;
  logic RR_FLAG_LP;
  logic main_grant_LP;

  logic                         LP_W_cen    , LP_R_cen    , LP_cen    ;
  logic                         LP_W_wen    , LP_R_wen    , LP_wen    ;
  logic [MEM_ADDR_WIDTH-1:0]    LP_W_addr   , LP_R_addr   , LP_addr   ;
  logic [AXI4_WDATA_WIDTH-1:0]  LP_W_wdata  , LP_R_wdata  , LP_wdata  ;
  logic [AXI_NUMBYTES-1:0]      LP_W_be     , LP_R_be     , LP_be     ;
  logic [AXI_NUMBYTES-1:0]      LP_W_rdata  , LP_R_rdata  , LP_rdata  ;



    // ------------------------------------------------------------//
    // ██╗      ██████╗ ██╗    ██╗    ██████╗ ██████╗ ██╗ ██████╗  //
    // ██║     ██╔═══██╗██║    ██║    ██╔══██╗██╔══██╗██║██╔═══██╗ //
    // ██║     ██║   ██║██║ █╗ ██║    ██████╔╝██████╔╝██║██║   ██║ //
    // ██║     ██║   ██║██║███╗██║    ██╔═══╝ ██╔══██╗██║██║   ██║ //
    // ███████╗╚██████╔╝╚███╔███╔╝    ██║     ██║  ██║██║╚██████╔╝ //
    // ╚══════╝ ╚═════╝  ╚══╝╚══╝     ╚═╝     ╚═╝  ╚═╝╚═╝ ╚═════╝  //
    //-------------------------------------------------------------//
    // AXI WRITE ADDRESS CHANNEL BUFFER
    axi_aw_buffer
    #(
       .ID_WIDTH     ( AXI4_ID_WIDTH      ),
       .ADDR_WIDTH   ( AXI4_ADDRESS_WIDTH ),
       .USER_WIDTH   ( AXI4_USER_WIDTH    ),
       .BUFFER_DEPTH ( BUFF_DEPTH_SLAVE   )
    )
    Slave_aw_buffer_LP
    (
      .clk_i           ( ACLK        ),
      .rst_ni          ( ARESETn     ),
      .test_en_i       ( test_en_i   ),

      .slave_valid_i   ( LP_AWVALID_i   ),
      .slave_addr_i    ( LP_AWADDR_i    ),
      .slave_prot_i    ( LP_AWPROT_i    ),
      .slave_region_i  ( LP_AWREGION_i  ),
      .slave_len_i     ( LP_AWLEN_i     ),
      .slave_size_i    ( LP_AWSIZE_i    ),
      .slave_burst_i   ( LP_AWBURST_i   ),
      .slave_lock_i    ( LP_AWLOCK_i    ),
      .slave_cache_i   ( LP_AWCACHE_i   ),
      .slave_qos_i     ( LP_AWQOS_i     ),
      .slave_id_i      ( LP_AWID_i      ),
      .slave_user_i    ( LP_AWUSER_i    ),
      .slave_ready_o   ( LP_AWREADY_o   ),

      .master_valid_o  ( LP_AWVALID     ),
      .master_addr_o   ( LP_AWADDR      ),
      .master_prot_o   ( LP_AWPROT      ),
      .master_region_o ( LP_AWREGION    ),
      .master_len_o    ( LP_AWLEN       ),
      .master_size_o   ( LP_AWSIZE      ),
      .master_burst_o  ( LP_AWBURST     ),
      .master_lock_o   ( LP_AWLOCK      ),
      .master_cache_o  ( LP_AWCACHE     ),
      .master_qos_o    ( LP_AWQOS       ),
      .master_id_o     ( LP_AWID        ),
      .master_user_o   ( LP_AWUSER      ),
      .master_ready_i  ( LP_AWREADY     )
    );


   // AXI WRITE ADDRESS CHANNEL BUFFER
   axi_ar_buffer
   #(
       .ID_WIDTH     ( AXI4_ID_WIDTH      ),
       .ADDR_WIDTH   ( AXI4_ADDRESS_WIDTH ),
       .USER_WIDTH   ( AXI4_USER_WIDTH    ),
       .BUFFER_DEPTH ( BUFF_DEPTH_SLAVE   )
   )
   Slave_ar_buffer_LP
   (
      .clk_i           ( ACLK          ),
      .rst_ni          ( ARESETn       ),
      .test_en_i       ( test_en_i     ),

      .slave_valid_i   ( LP_ARVALID_i  ),
      .slave_addr_i    ( LP_ARADDR_i   ),
      .slave_prot_i    ( LP_ARPROT_i   ),
      .slave_region_i  ( LP_ARREGION_i ),
      .slave_len_i     ( LP_ARLEN_i    ),
      .slave_size_i    ( LP_ARSIZE_i   ),
      .slave_burst_i   ( LP_ARBURST_i  ),
      .slave_lock_i    ( LP_ARLOCK_i   ),
      .slave_cache_i   ( LP_ARCACHE_i  ),
      .slave_qos_i     ( LP_ARQOS_i    ),
      .slave_id_i      ( LP_ARID_i     ),
      .slave_user_i    ( LP_ARUSER_i   ),
      .slave_ready_o   ( LP_ARREADY_o  ),

      .master_valid_o  ( LP_ARVALID    ),
      .master_addr_o   ( LP_ARADDR     ),
      .master_prot_o   ( LP_ARPROT     ),
      .master_region_o ( LP_ARREGION   ),
      .master_len_o    ( LP_ARLEN      ),
      .master_size_o   ( LP_ARSIZE     ),
      .master_burst_o  ( LP_ARBURST    ),
      .master_lock_o   ( LP_ARLOCK     ),
      .master_cache_o  ( LP_ARCACHE    ),
      .master_qos_o    ( LP_ARQOS      ),
      .master_id_o     ( LP_ARID       ),
      .master_user_o   ( LP_ARUSER     ),
      .master_ready_i  ( LP_ARREADY    )
   );


   axi_w_buffer
   #(
       .DATA_WIDTH(AXI4_WDATA_WIDTH),
       .USER_WIDTH(AXI4_USER_WIDTH),
       .BUFFER_DEPTH(BUFF_DEPTH_SLAVE)
   )
   Slave_w_buffer_LP
   (
        .clk_i          ( ACLK        ),
        .rst_ni         ( ARESETn     ),
        .test_en_i      ( test_en_i   ),

        .slave_valid_i  ( LP_WVALID_i ),
        .slave_data_i   ( LP_WDATA_i  ),
        .slave_strb_i   ( LP_WSTRB_i  ),
        .slave_user_i   ( LP_WUSER_i  ),
        .slave_last_i   ( LP_WLAST_i  ),
        .slave_ready_o  ( LP_WREADY_o ),

        .master_valid_o ( LP_WVALID   ),
        .master_data_o  ( LP_WDATA    ),
        .master_strb_o  ( LP_WSTRB    ),
        .master_user_o  ( LP_WUSER    ),
        .master_last_o  ( LP_WLAST    ),
        .master_ready_i ( LP_WREADY   )
    );

   axi_r_buffer
   #(
        .ID_WIDTH(AXI4_ID_WIDTH),
        .DATA_WIDTH(AXI4_RDATA_WIDTH),
        .USER_WIDTH(AXI4_USER_WIDTH),
        .BUFFER_DEPTH(BUFF_DEPTH_SLAVE)
   )
   Slave_r_buffer_LP
   (
        .clk_i          ( ACLK          ),
        .rst_ni         ( ARESETn       ),
        .test_en_i      ( test_en_i     ),

        .slave_valid_i  ( LP_RVALID     ),
        .slave_data_i   ( LP_RDATA      ),
        .slave_resp_i   ( LP_RRESP      ),
        .slave_user_i   ( LP_RUSER      ),
        .slave_id_i     ( LP_RID        ),
        .slave_last_i   ( LP_RLAST      ),
        .slave_ready_o  ( LP_RREADY     ),

        .master_valid_o ( LP_RVALID_o   ),
        .master_data_o  ( LP_RDATA_o    ),
        .master_resp_o  ( LP_RRESP_o    ),
        .master_user_o  ( LP_RUSER_o    ),
        .master_id_o    ( LP_RID_o      ),
        .master_last_o  ( LP_RLAST_o    ),
        .master_ready_i ( LP_RREADY_i   )
   );

   axi_b_buffer
   #(
        .ID_WIDTH(AXI4_ID_WIDTH),
        .USER_WIDTH(AXI4_USER_WIDTH),
        .BUFFER_DEPTH(BUFF_DEPTH_SLAVE)
   )
   Slave_b_buffer_LP
   (
        .clk_i          ( ACLK         ),
        .rst_ni         ( ARESETn      ),
        .test_en_i      ( test_en_i    ),

        .slave_valid_i  ( LP_BVALID    ),
        .slave_resp_i   ( LP_BRESP     ),
        .slave_id_i     ( LP_BID       ),
        .slave_user_i   ( LP_BUSER     ),
        .slave_ready_o  ( LP_BREADY    ),

        .master_valid_o ( LP_BVALID_o  ),
        .master_resp_o  ( LP_BRESP_o   ),
        .master_id_o    ( LP_BID_o     ),
        .master_user_o  ( LP_BUSER_o   ),
        .master_ready_i ( LP_BREADY_i  )
   );






// Low Priority Write FSM
axi_write_only_ctrl
#(
    .AXI4_ADDRESS_WIDTH ( AXI4_ADDRESS_WIDTH  ),
    .AXI4_RDATA_WIDTH   ( AXI4_RDATA_WIDTH    ),
    .AXI4_WDATA_WIDTH   ( AXI4_WDATA_WIDTH    ),
    .AXI4_ID_WIDTH      ( AXI4_ID_WIDTH       ),
    .AXI4_USER_WIDTH    ( AXI4_USER_WIDTH     ),
    .AXI_NUMBYTES       ( AXI_NUMBYTES        ),
    .MEM_ADDR_WIDTH     ( MEM_ADDR_WIDTH      )
)
W_CTRL_LP
(
    .clk            (  ACLK         ),
    .rst_n          (  ARESETn      ),

    .AWID_i         (  LP_AWID      ),
    .AWADDR_i       (  LP_AWADDR    ),
    .AWLEN_i        (  LP_AWLEN     ),
    .AWSIZE_i       (  LP_AWSIZE    ),
    .AWBURST_i      (  LP_AWBURST   ),
    .AWLOCK_i       (  LP_AWLOCK    ),
    .AWCACHE_i      (  LP_AWCACHE   ),
    .AWPROT_i       (  LP_AWPROT    ),
    .AWREGION_i     (  LP_AWREGION  ),
    .AWUSER_i       (  LP_AWUSER    ),
    .AWQOS_i        (  LP_AWQOS     ),
    .AWVALID_i      (  LP_AWVALID   ),
    .AWREADY_o      (  LP_AWREADY   ),

    //AXI write data buLP_s -------------- // USED// -------------
    .WDATA_i        (  LP_WDATA      ),
    .WSTRB_i        (  LP_WSTRB      ),
    .WLAST_i        (  LP_WLAST      ),
    .WUSER_i        (  LP_WUSER      ),
    .WVALID_i       (  LP_WVALID     ),
    .WREADY_o       (  LP_WREADY     ),

    //AXI write responsLP_e bus -------------- // USED// ----------
    .BID_o          (  LP_BID        ),
    .BRESP_o        (  LP_BRESP      ),
    .BVALID_o       (  LP_BVALID     ),
    .BUSER_o        (  LP_BUSER      ),
    .BREADY_i       (  LP_BREADY     ),

    .MEM_CEN_o      (  LP_W_cen      ),
    .MEM_WEN_o      (  LP_W_wen      ),
    .MEM_A_o        (  LP_W_addr     ),
    .MEM_D_o        (  LP_W_wdata    ),
    .MEM_BE_o       (  LP_W_be       ),
    .MEM_Q_i        (  '0            ),

    .grant_i        (  grant_W_LP & HP_cen_i ),
    .valid_o        (  valid_W_LP   )
);




axi_read_only_ctrl
#(
    .AXI4_ADDRESS_WIDTH ( AXI4_ADDRESS_WIDTH  ),
    .AXI4_RDATA_WIDTH   ( AXI4_RDATA_WIDTH    ),
    .AXI4_WDATA_WIDTH   ( AXI4_WDATA_WIDTH    ),
    .AXI4_ID_WIDTH      ( AXI4_ID_WIDTH       ),
    .AXI4_USER_WIDTH    ( AXI4_USER_WIDTH     ),
    .AXI_NUMBYTES       ( AXI_NUMBYTES        ),
    .MEM_ADDR_WIDTH     ( MEM_ADDR_WIDTH      )
)
R_CTRL_LP
(
    .clk            (  ACLK       ),
    .rst_n          (  ARESETn     ),

    .ARID_i         (  LP_ARID      ),
    .ARADDR_i       (  LP_ARADDR    ),
    .ARLEN_i        (  LP_ARLEN     ),
    .ARSIZE_i       (  LP_ARSIZE    ),
    .ARBURST_i      (  LP_ARBURST   ),
    .ARLOCK_i       (  LP_ARLOCK    ),
    .ARCACHE_i      (  LP_ARCACHE   ),
    .ARPROT_i       (  LP_ARPROT    ),
    .ARREGION_i     (  LP_ARREGION  ),
    .ARUSER_i       (  LP_ARUSER    ),
    .ARQOS_i        (  LP_ARQOS     ),
    .ARVALID_i      (  LP_ARVALID   ),
    .ARREADY_o      (  LP_ARREADY   ),

    .RID_o          (  LP_RID       ),
    .RDATA_o        (  LP_RDATA     ),
    .RRESP_o        (  LP_RRESP     ),
    .RLAST_o        (  LP_RLAST     ),
    .RUSER_o        (  LP_RUSER     ),
    .RVALID_o       (  LP_RVALID    ),
    .RREADY_i       (  LP_RREADY    ),

    .MEM_CEN_o      (  LP_R_cen     ),
    .MEM_WEN_o      (  LP_R_wen     ),
    .MEM_A_o        (  LP_R_addr    ),
    .MEM_D_o        (               ),
    .MEM_BE_o       (               ),
    .MEM_Q_i        (      Q        ),

    .grant_i        (  grant_R_LP  & HP_cen_i ),
    .valid_o        (  valid_R_LP   )
);

assign LP_wdata = LP_W_wdata ;
assign LP_be    = LP_W_be;

always_comb
begin : _MUX_MEM_

  if( HP_cen_i == 1'b0 )
  begin
    CEN = HP_cen_i    ;
    WEN = HP_wen_i    ;
    A   = HP_addr_i   ;
    D   = HP_wdata_i  ;
    BE  = HP_be_i     ;
  end
  else
  begin

      if(grant_R_LP)
      begin
        LP_cen   = LP_R_cen   ;
        LP_wen   = 1'b1       ;
        LP_addr  = LP_R_addr  ;
      end
      else
      begin
        LP_cen   = LP_W_cen   ;
        LP_wen   = ~grant_W_LP       ;
        LP_addr  = LP_W_addr  ;
      end
  
        CEN = LP_cen   ;
        WEN = LP_wen   ;
        A   = LP_addr  ;
        D   = LP_W_wdata ;
        BE  = LP_W_be    ;
  end
end




always_ff @(posedge ACLK or negedge ARESETn)
begin
  if(~ARESETn) begin
     RR_FLAG_LP <= 0;
  end
  else
  begin
      RR_FLAG_LP  <= ~RR_FLAG_LP;
  end
end




//Low Priority RR Arbiter
always_comb
begin
  grant_R_LP = 1'b0;
  grant_W_LP = 1'b0;

  case (RR_FLAG_LP)

  1'b0: //Priority on Write
  begin
    if(valid_W_LP)
      grant_W_LP = 1'b1;
    else
      grant_R_LP = 1'b1;
  end


  1'b1: //Priority on Read
  begin
    if(valid_R_LP)
      grant_R_LP = 1'b1;
    else
      grant_W_LP = 1'b1;
  end
  endcase
end



//MAIN FIXED PRIORITY Arbiter
always_comb
begin
  main_grant_LP = 1'b0;


  if(HP_cen_i == 1'b1) // no requesto on HP port
  begin
      main_grant_LP = 1'b1;
  end
end

assign HP_Q_o = Q;


endmodule // axi_mem_if_DP
