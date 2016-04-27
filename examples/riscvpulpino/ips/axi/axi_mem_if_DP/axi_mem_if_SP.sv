// Copyright 2015 ETH Zurich and University of Bologna.
// Copyright and related rights are licensed under the Solderpad Hardware
// License, Version 0.51 (the “License”); you may not use this file except in
// compliance with the License.  You may obtain a copy of the License at
// http://solderpad.org/licenses/SHL-0.51. Unless required by applicable law
// or agreed to in writing, software, hardware and materials distributed under
// this License is distributed on an “AS IS” BASIS, WITHOUT WARRANTIES OR
// CONDITIONS OF ANY KIND, either express or implied. See the License for the
// specific language governing permissions and limitations under the License.

module axi_mem_if_SP
#(
    parameter AXI4_ADDRESS_WIDTH = 32,
    parameter AXI4_RDATA_WIDTH   = 32,
    parameter AXI4_WDATA_WIDTH   = 32,
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


    // ---------------------------------------------------------
    // AXI TARG Port Declarations ------------------------------
    // ---------------------------------------------------------
    //AXI write address bus -------------- // USED// -----------
    input  logic [AXI4_ID_WIDTH-1:0]                AWID_i     ,
    input  logic [AXI4_ADDRESS_WIDTH-1:0]           AWADDR_i   ,
    input  logic [ 7:0]                             AWLEN_i    ,
    input  logic [ 2:0]                             AWSIZE_i   ,
    input  logic [ 1:0]                             AWBURST_i  ,
    input  logic                                    AWLOCK_i   ,
    input  logic [ 3:0]                             AWCACHE_i  ,
    input  logic [ 2:0]                             AWPROT_i   ,
    input  logic [ 3:0]                             AWREGION_i ,
    input  logic [ AXI4_USER_WIDTH-1:0]             AWUSER_i   ,
    input  logic [ 3:0]                             AWQOS_i    ,
    input  logic                                    AWVALID_i  ,
    output logic                                    AWREADY_o  ,
    // ---------------------------------------------------------

    //AXI write data bus -------------- // USED// --------------
    input  logic [AXI_NUMBYTES-1:0][7:0]            WDATA_i    ,
    input  logic [AXI_NUMBYTES-1:0]                 WSTRB_i    ,
    input  logic                                    WLAST_i    ,
    input  logic [AXI4_USER_WIDTH-1:0]              WUSER_i    ,
    input  logic                                    WVALID_i   ,
    output logic                                    WREADY_o   ,
    // ---------------------------------------------------------

    //AXI write response bus -------------- // USED// ----------
    output logic   [AXI4_ID_WIDTH-1:0]              BID_o      ,
    output logic   [ 1:0]                           BRESP_o    ,
    output logic                                    BVALID_o   ,
    output logic   [AXI4_USER_WIDTH-1:0]            BUSER_o    ,
    input  logic                                    BREADY_i   ,
    // ---------------------------------------------------------

    //AXI read address bus -------------------------------------
    input  logic [AXI4_ID_WIDTH-1:0]                ARID_i     ,
    input  logic [AXI4_ADDRESS_WIDTH-1:0]           ARADDR_i   ,
    input  logic [ 7:0]                             ARLEN_i    ,
    input  logic [ 2:0]                             ARSIZE_i   ,
    input  logic [ 1:0]                             ARBURST_i  ,
    input  logic                                    ARLOCK_i   ,
    input  logic [ 3:0]                             ARCACHE_i  ,
    input  logic [ 2:0]                             ARPROT_i   ,
    input  logic [ 3:0]                             ARREGION_i ,
    input  logic [ AXI4_USER_WIDTH-1:0]             ARUSER_i   ,
    input  logic [ 3:0]                             ARQOS_i    ,
    input  logic                                    ARVALID_i  ,
    output logic                                    ARREADY_o  ,
    // ---------------------------------------------------------

    //AXI read data bus ----------------------------------------
    output  logic [AXI4_ID_WIDTH-1:0]               RID_o      ,
    output  logic [AXI4_RDATA_WIDTH-1:0]            RDATA_o    ,
    output  logic [ 1:0]                            RRESP_o    ,
    output  logic                                   RLAST_o    ,
    output  logic [AXI4_USER_WIDTH-1:0]             RUSER_o    ,
    output  logic                                   RVALID_o   ,
    input   logic                                   RREADY_i   ,
    // ---------------------------------------------------------

    output logic                                    CEN_o        ,
    output logic                                    WEN_o        ,
    output logic  [MEM_ADDR_WIDTH-1:0]              A_o          ,
    output logic  [AXI4_WDATA_WIDTH-1:0]            D_o          ,
    output logic  [AXI_NUMBYTES-1:0]                BE_o         ,
    input  logic  [AXI4_RDATA_WIDTH-1:0]            Q_i
);

    logic valid_R, valid_W;
    logic grant_R, grant_W;
    logic RR_FLAG;

	// -----------------------------------------------------------
	// AXI TARG Port Declarations --------------------------------
	// -----------------------------------------------------------
	//AXI write address bus --------------------------------------
	logic [AXI4_ID_WIDTH-1:0]                         AWID     ;
	logic [AXI4_ADDRESS_WIDTH-1:0]                    AWADDR   ;
	logic [ 7:0]                                      AWLEN    ;
	logic [ 2:0]                                      AWSIZE   ;
	logic [ 1:0]                                      AWBURST  ;
	logic                                             AWLOCK   ;
	logic [ 3:0]                                      AWCACHE  ;
	logic [ 2:0]                                      AWPROT   ;
	logic [ 3:0]                                      AWREGION ;
	logic [ AXI4_USER_WIDTH-1:0]                      AWUSER   ;
	logic [ 3:0]                                      AWQOS    ;
	logic                                             AWVALID  ;
	logic                                             AWREADY  ;
	// -----------------------------------------------------------
	//AXI write data bus ------------------------ ----------------
	logic [AXI_NUMBYTES-1:0][7:0]                     WDATA    ;
	logic [AXI_NUMBYTES-1:0]                          WSTRB    ;
	logic                                             WLAST    ;
	logic [AXI4_USER_WIDTH-1:0]                       WUSER    ;
	logic                                             WVALID   ;
	logic                                             WREADY   ;
	// -----------------------------------------------------------
	//AXI write response bus -------------------------------------
	logic   [AXI4_ID_WIDTH-1:0]                       BID      ;
	logic   [ 1:0]                                    BRESP    ;
	logic                                             BVALID   ;
	logic   [AXI4_USER_WIDTH-1:0]                     BUSER    ;
	logic                                             BREADY   ;
	// -----------------------------------------------------------
	//AXI read address bus ---------------------------------------
	logic [AXI4_ID_WIDTH-1:0]                         ARID     ;
	logic [AXI4_ADDRESS_WIDTH-1:0]                    ARADDR   ;
	logic [ 7:0]                                      ARLEN    ;
	logic [ 2:0]                                      ARSIZE   ;
	logic [ 1:0]                                      ARBURST  ;
	logic                                             ARLOCK   ;
	logic [ 3:0]                                      ARCACHE  ;
	logic [ 2:0]                                      ARPROT   ;
	logic [ 3:0]                                      ARREGION ;
	logic [ AXI4_USER_WIDTH-1:0]                      ARUSER   ;
	logic [ 3:0]                                      ARQOS    ;
	logic                                             ARVALID  ;
	logic                                             ARREADY  ;
	// -----------------------------------------------------------
	//AXI read data bus ------------------------------------------
	logic [AXI4_ID_WIDTH-1:0]                         RID      ;
	logic [AXI4_RDATA_WIDTH-1:0]                      RDATA    ;
	logic [ 1:0]                                      RRESP    ;
	logic                                             RLAST    ;
	logic [AXI4_USER_WIDTH-1:0]                       RUSER    ;
	logic                                             RVALID   ;
	logic                                             RREADY   ;
	// -----------------------------------------------------------


    logic                         W_cen    , R_cen    ;
    logic                         W_wen    , R_wen    ;
    logic [MEM_ADDR_WIDTH-1:0]    W_addr   , R_addr   ;
    logic [AXI4_WDATA_WIDTH-1:0]  W_wdata  , R_wdata  ;
    logic [AXI_NUMBYTES-1:0]      W_be     , R_be     ;


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

      .slave_valid_i   ( AWVALID_i   ),
      .slave_addr_i    ( AWADDR_i    ),
      .slave_prot_i    ( AWPROT_i    ),
      .slave_region_i  ( AWREGION_i  ),
      .slave_len_i     ( AWLEN_i     ),
      .slave_size_i    ( AWSIZE_i    ),
      .slave_burst_i   ( AWBURST_i   ),
      .slave_lock_i    ( AWLOCK_i    ),
      .slave_cache_i   ( AWCACHE_i   ),
      .slave_qos_i     ( AWQOS_i     ),
      .slave_id_i      ( AWID_i      ),
      .slave_user_i    ( AWUSER_i    ),
      .slave_ready_o   ( AWREADY_o   ),

      .master_valid_o  ( AWVALID     ),
      .master_addr_o   ( AWADDR      ),
      .master_prot_o   ( AWPROT      ),
      .master_region_o ( AWREGION    ),
      .master_len_o    ( AWLEN       ),
      .master_size_o   ( AWSIZE      ),
      .master_burst_o  ( AWBURST     ),
      .master_lock_o   ( AWLOCK      ),
      .master_cache_o  ( AWCACHE     ),
      .master_qos_o    ( AWQOS       ),
      .master_id_o     ( AWID        ),
      .master_user_o   ( AWUSER      ),
      .master_ready_i  ( AWREADY     )
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
      .clk_i           ( ACLK       ),
      .rst_ni          ( ARESETn    ),
      .test_en_i       ( test_en_i  ),

      .slave_valid_i   ( ARVALID_i  ),
      .slave_addr_i    ( ARADDR_i   ),
      .slave_prot_i    ( ARPROT_i   ),
      .slave_region_i  ( ARREGION_i ),
      .slave_len_i     ( ARLEN_i    ),
      .slave_size_i    ( ARSIZE_i   ),
      .slave_burst_i   ( ARBURST_i  ),
      .slave_lock_i    ( ARLOCK_i   ),
      .slave_cache_i   ( ARCACHE_i  ),
      .slave_qos_i     ( ARQOS_i    ),
      .slave_id_i      ( ARID_i     ),
      .slave_user_i    ( ARUSER_i   ),
      .slave_ready_o   ( ARREADY_o  ),

      .master_valid_o  ( ARVALID    ),
      .master_addr_o   ( ARADDR     ),
      .master_prot_o   ( ARPROT     ),
      .master_region_o ( ARREGION   ),
      .master_len_o    ( ARLEN      ),
      .master_size_o   ( ARSIZE     ),
      .master_burst_o  ( ARBURST    ),
      .master_lock_o   ( ARLOCK     ),
      .master_cache_o  ( ARCACHE    ),
      .master_qos_o    ( ARQOS      ),
      .master_id_o     ( ARID       ),
      .master_user_o   ( ARUSER     ),
      .master_ready_i  ( ARREADY    )
   );


   axi_w_buffer
   #(
       .DATA_WIDTH(AXI4_WDATA_WIDTH),
       .USER_WIDTH(AXI4_USER_WIDTH),
       .BUFFER_DEPTH(BUFF_DEPTH_SLAVE)
   )
   Slave_w_buffer_LP
   (
        .clk_i          ( ACLK      ),
        .rst_ni         ( ARESETn   ),
        .test_en_i      ( test_en_i ),

        .slave_valid_i  ( WVALID_i  ),
        .slave_data_i   ( WDATA_i   ),
        .slave_strb_i   ( WSTRB_i   ),
        .slave_user_i   ( WUSER_i   ),
        .slave_last_i   ( WLAST_i   ),
        .slave_ready_o  ( WREADY_o  ),

        .master_valid_o ( WVALID    ),
        .master_data_o  ( WDATA     ),
        .master_strb_o  ( WSTRB     ),
        .master_user_o  ( WUSER     ),
        .master_last_o  ( WLAST     ),
        .master_ready_i ( WREADY    )
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
        .clk_i          ( ACLK       ),
        .rst_ni         ( ARESETn    ),
        .test_en_i      ( test_en_i  ),

        .slave_valid_i  ( RVALID     ),
        .slave_data_i   ( RDATA      ),
        .slave_resp_i   ( RRESP      ),
        .slave_user_i   ( RUSER      ),
        .slave_id_i     ( RID        ),
        .slave_last_i   ( RLAST      ),
        .slave_ready_o  ( RREADY     ),

        .master_valid_o ( RVALID_o   ),
        .master_data_o  ( RDATA_o    ),
        .master_resp_o  ( RRESP_o    ),
        .master_user_o  ( RUSER_o    ),
        .master_id_o    ( RID_o      ),
        .master_last_o  ( RLAST_o    ),
        .master_ready_i ( RREADY_i   )
   );

   axi_b_buffer
   #(
        .ID_WIDTH(AXI4_ID_WIDTH),
        .USER_WIDTH(AXI4_USER_WIDTH),
        .BUFFER_DEPTH(BUFF_DEPTH_SLAVE)
   )
   Slave_b_buffer_LP
   (
        .clk_i          ( ACLK      ),
        .rst_ni         ( ARESETn   ),
        .test_en_i      ( test_en_i ),

        .slave_valid_i  ( BVALID    ),
        .slave_resp_i   ( BRESP     ),
        .slave_id_i     ( BID       ),
        .slave_user_i   ( BUSER     ),
        .slave_ready_o  ( BREADY    ),

        .master_valid_o ( BVALID_o  ),
        .master_resp_o  ( BRESP_o   ),
        .master_id_o    ( BID_o     ),
        .master_user_o  ( BUSER_o   ),
        .master_ready_i ( BREADY_i  )
   );


	// High Priority Write FSM
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
	WRITE_CTRL
	(
	    .clk            (  ACLK         ),
	    .rst_n          (  ARESETn      ),

	    .AWID_i         (  AWID         ),
	    .AWADDR_i       (  AWADDR       ),
	    .AWLEN_i        (  AWLEN        ),
	    .AWSIZE_i       (  AWSIZE       ),
	    .AWBURST_i      (  AWBURST      ),
	    .AWLOCK_i       (  AWLOCK       ),
	    .AWCACHE_i      (  AWCACHE      ),
	    .AWPROT_i       (  AWPROT       ),
	    .AWREGION_i     (  AWREGION     ),
	    .AWUSER_i       (  AWUSER       ),
	    .AWQOS_i        (  AWQOS        ),
	    .AWVALID_i      (  AWVALID      ),
	    .AWREADY_o      (  AWREADY      ),

	    //AXI write data bus ------   -------- // USED// -------------
	    .WDATA_i        (  WDATA         ),
	    .WSTRB_i        (  WSTRB         ),
	    .WLAST_i        (  WLAST         ),
	    .WUSER_i        (  WUSER         ),
	    .WVALID_i       (  WVALID        ),
	    .WREADY_o       (  WREADY        ),

	    //AXI write response bus --   ------------ // USED// ----------
	    .BID_o          (  BID           ),
	    .BRESP_o        (  BRESP         ),
	    .BVALID_o       (  BVALID        ),
	    .BUSER_o        (  BUSER         ),
	    .BREADY_i       (  BREADY        ),

	    .MEM_CEN_o      (  W_cen         ),
	    .MEM_WEN_o      (  W_wen         ),
	    .MEM_A_o        (  W_addr        ),
	    .MEM_D_o        (  W_wdata       ),
	    .MEM_BE_o       (  W_be          ),
	    .MEM_Q_i        (  '0            ),

	    .grant_i        (  grant_W       ),
	    .valid_o        (  valid_W       )
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
	READ_CTRL
	(
	    .clk            (  ACLK       ),
	    .rst_n          (  ARESETn    ),

	    .ARID_i         (  ARID      ),
	    .ARADDR_i       (  ARADDR    ),
	    .ARLEN_i        (  ARLEN     ),
	    .ARSIZE_i       (  ARSIZE    ),
	    .ARBURST_i      (  ARBURST   ),
	    .ARLOCK_i       (  ARLOCK    ),
	    .ARCACHE_i      (  ARCACHE   ),
	    .ARPROT_i       (  ARPROT    ),
	    .ARREGION_i     (  ARREGION  ),
	    .ARUSER_i       (  ARUSER    ),
	    .ARQOS_i        (  ARQOS     ),
	    .ARVALID_i      (  ARVALID   ),
	    .ARREADY_o      (  ARREADY   ),

	    .RID_o          (  RID       ),
	    .RDATA_o        (  RDATA     ),
	    .RRESP_o        (  RRESP     ),
	    .RLAST_o        (  RLAST     ),
	    .RUSER_o        (  RUSER     ),
	    .RVALID_o       (  RVALID    ),
	    .RREADY_i       (  RREADY    ),

	    .MEM_CEN_o      (  R_cen     ),
	    .MEM_WEN_o      (  R_wen     ),
	    .MEM_A_o        (  R_addr    ),
	    .MEM_D_o        (  R_wdata   ),
	    .MEM_BE_o       (  R_be      ),
	    .MEM_Q_i        (  Q_i       ),

	    .grant_i        (  grant_R   ),
	    .valid_o        (  valid_R   )
	);


	always_comb
	begin : _MUX_MEM_
		  if(valid_R & grant_R)
		  begin
		    CEN_o   = R_cen   ;
		    WEN_o   = 1'b1       ;
		    A_o     = R_addr  ;
		    D_o     = R_wdata ;
		    BE_o    = R_be    ;
		  end
		  else
		  begin
		    CEN_o   = W_cen   ;
		    WEN_o   = 1'b0       ;
		    A_o     = W_addr  ;
		    D_o     = W_wdata ;
		    BE_o    = W_be    ;
		  end
	end


//Low Priority RR Arbiter
always_comb
begin
  grant_R = 1'b0;
  grant_W = 1'b0;

  case (RR_FLAG)

  1'b0: //Priority on Write
  begin
    if(valid_W)
      grant_W = 1'b1;
    else
      grant_R = 1'b1;
  end


  1'b1: //Priority on Read
  begin
    if(valid_R)
      grant_R = 1'b1;
    else
      grant_W = 1'b1;
  end
  endcase
end


always_ff @(posedge ACLK or negedge ARESETn)
begin
  if(~ARESETn) begin
     RR_FLAG <= 0;
  end
  else
  begin
  		if(CEN_o == 1'b0)
      	   RR_FLAG  <= ~RR_FLAG;
  end
end


endmodule // axi_mem_if_SP_32
