// Copyright 2016 ETH Zurich and University of Bologna.
// Copyright and related rights are licensed under the Solderpad Hardware
// License, Version 0.51 (the “License”); you may not use this file except in
// compliance with the License.  You may obtain a copy of the License at
// http://solderpad.org/licenses/SHL-0.51. Unless required by applicable law
// or agreed to in writing, software, hardware and materials distributed under
// this License is distributed on an “AS IS” BASIS, WITHOUT WARRANTIES OR
// CONDITIONS OF ANY KIND, either express or implied. See the License for the
// specific language governing permissions and limitations under the License.

// ============================================================================= //
// Engineer:       Igor Loi - igor.loi@unibo.it                                  //
//                                                                               //
// Design Name:    AXI 4 (32bit) to APB (32bit) Bridge                           //
// Module Name:    AXI_2_APB_32                                                  //
// Project Name:   PULPino                                                       //
// Language:       SystemVerilog                                                 //
//                                                                               //
// Description:    This Bridge performs a protocol translation between AXI4 to   //
//                 APB. BURST across the APB are not supported                   //
//                                                                               //
// ============================================================================= //

`define OKAY   2'b00
`define EXOKAY 2'b01
`define SLVERR 2'b10
`define DECERR 2'b11

module AXI_2_APB_32
#(
    parameter AXI4_ADDRESS_WIDTH = 32,
    parameter AXI4_RDATA_WIDTH   = 32,
    parameter AXI4_WDATA_WIDTH   = 32,
    parameter AXI4_ID_WIDTH      = 16,
    parameter AXI4_USER_WIDTH    = 10,
    parameter AXI_NUMBYTES       = AXI4_WDATA_WIDTH/8,

    parameter BUFF_DEPTH_SLAVE   = 4,
    parameter APB_NUM_SLAVES     = 8,
    parameter APB_ADDR_WIDTH     = 12  //APB slaves are 4KB by default
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
    input  logic [AXI4_WDATA_WIDTH-1:0]             WDATA_i    ,
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

    output logic                                    PENABLE    ,
    output logic                                    PWRITE     ,
    output logic        [APB_ADDR_WIDTH-1:0]        PADDR      ,
    output logic        [APB_NUM_SLAVES-1:0]        PSEL       ,
    output logic                      [31:0]        PWDATA     ,
    input  logic [APB_NUM_SLAVES-1:0] [31:0]        PRDATA     ,
    input  logic        [APB_NUM_SLAVES-1:0]        PREADY     ,
    input  logic        [APB_NUM_SLAVES-1:0]        PSLVERR
);

  // -----------------------------------------------------------
  // AXI TARG Port Declarations --------------------------------
  // -----------------------------------------------------------
  //AXI write address bus --------------------------------------
  logic [AXI4_ID_WIDTH-1:0]                         AWID       ;
  logic [AXI4_ADDRESS_WIDTH-1:0]                    AWADDR     ;
  logic [ 7:0]                                      AWLEN      ;
  logic [ 2:0]                                      AWSIZE     ;
  logic [ 1:0]                                      AWBURST    ;
  logic                                             AWLOCK     ;
  logic [ 3:0]                                      AWCACHE    ;
  logic [ 2:0]                                      AWPROT     ;
  logic [ 3:0]                                      AWREGION   ;
  logic [ AXI4_USER_WIDTH-1:0]                      AWUSER     ;
  logic [ 3:0]                                      AWQOS      ;
  logic                                             AWVALID    ;
  logic                                             AWREADY    ;
  // -----------------------------------------------------------

  //AXI write data bus ------------------------ ----------------
  logic [AXI4_WDATA_WIDTH-1:0]                      WDATA      ; // from FIFO
  logic [AXI_NUMBYTES-1:0]                          WSTRB      ; // from FIFO
  logic                                             WLAST      ; // from FIFO
  logic [AXI4_USER_WIDTH-1:0]                       WUSER      ; // from FIFO
  logic                                             WVALID     ; // from FIFO
  logic                                             WREADY     ; // TO FIFO
  // -----------------------------------------------------------

  //AXI write response bus -------------------------------------
  logic   [AXI4_ID_WIDTH-1:0]                       BID        ;
  logic   [ 1:0]                                    BRESP      ;
  logic                                             BVALID     ;
  logic   [AXI4_USER_WIDTH-1:0]                     BUSER      ;
  logic                                             BREADY     ;
  // -----------------------------------------------------------

  //AXI read address bus ---------------------------------------
  logic [AXI4_ID_WIDTH-1:0]                         ARID       ;
  logic [AXI4_ADDRESS_WIDTH-1:0]                    ARADDR     ;
  logic [ 7:0]                                      ARLEN      ;
  logic [ 2:0]                                      ARSIZE     ;
  logic [ 1:0]                                      ARBURST    ;
  logic                                             ARLOCK     ;
  logic [ 3:0]                                      ARCACHE    ;
  logic [ 2:0]                                      ARPROT     ;
  logic [ 3:0]                                      ARREGION   ;
  logic [ AXI4_USER_WIDTH-1:0]                      ARUSER     ;
  logic [ 3:0]                                      ARQOS      ;
  logic                                             ARVALID    ;
  logic                                             ARREADY    ;
  // -----------------------------------------------------------

  //AXI read data bus ------------------------------------------
  logic [AXI4_ID_WIDTH-1:0]                         RID        ;
  logic [AXI4_RDATA_WIDTH-1:0]                      RDATA      ;
  logic [ 1:0]                                      RRESP      ;
  logic                                             RLAST      ;
  logic [AXI4_USER_WIDTH-1:0]                       RUSER      ;
  logic                                             RVALID     ;
  logic                                             RREADY     ;
  // -----------------------------------------------------------

  enum logic [2:0] {    IDLE,
                        DONE_SINGLE_RD,
                        WAIT_W_PREADY,
                        WAIT_R_PREADY,
                        SEND_B_RESP
                    } CS,NS;



  logic [$clog2(APB_NUM_SLAVES) + APB_ADDR_WIDTH-1:0] address;
  logic                                         sample_RDATA;
  logic [31:0]                                  RDATA_Q;

  logic                                         read_req;
  logic                                         write_req;


  logic [$clog2(APB_NUM_SLAVES)-1:0]           TARGET_SLAVE;   // identifies the target APB slave




  assign PENABLE    = write_req | read_req;
  assign PWRITE     = write_req;
  assign PADDR      = address[APB_ADDR_WIDTH-1:0];

  assign PWDATA     = WDATA;

  assign TARGET_SLAVE = address[APB_ADDR_WIDTH+$clog2(APB_NUM_SLAVES)-1:APB_ADDR_WIDTH];


  always_comb
  begin
    PSEL = '0;
    PSEL[TARGET_SLAVE] = 1'b1;
  end

   // AXI WRITE ADDRESS CHANNEL BUFFER
   axi_aw_buffer
   #(
       .ID_WIDTH     ( AXI4_ID_WIDTH      ),
       .ADDR_WIDTH   ( AXI4_ADDRESS_WIDTH ),
       .USER_WIDTH   ( AXI4_USER_WIDTH    ),
       .BUFFER_DEPTH ( BUFF_DEPTH_SLAVE   )
   )
   Slave_aw_buffer
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
   Slave_ar_buffer
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
   Slave_w_buffer
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
   Slave_r_buffer
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
   Slave_b_buffer
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


    always_ff @(posedge ACLK, negedge ARESETn)
    begin
      if(ARESETn == 1'b0)
      begin
          CS       <= IDLE;
          RDATA_Q  <= '0;
      end
      else
      begin
          CS      <= NS;

          if(sample_RDATA)
            RDATA_Q <= PRDATA[TARGET_SLAVE];
      end
    end




    always_comb
    begin

      read_req   = 1'b0;
      write_req  = 1'b0;
      address    = 'x;

      sample_RDATA = 1'b0;

      ARREADY    = 1'b0;
      AWREADY    = 1'b0;
      WREADY     = 1'b0;

      //-----------------//
      BVALID     = 1'b0;
      BRESP      = `OKAY;
      BID        = AWID;
      BUSER      = AWUSER;
      //-----------------//
      RVALID     = 1'b0;
      RLAST      = 1'b0;
      RID        = ARID;
      RUSER      = ARUSER;
      RRESP      = `OKAY;
      RDATA      = RDATA_Q;

      case(CS)

         WAIT_R_PREADY:
         begin
            read_req       = 1'b1;
            address        = ARADDR[$clog2(APB_NUM_SLAVES) + APB_ADDR_WIDTH  - 1 : 0];
            sample_RDATA   = PREADY[TARGET_SLAVE];

            if(PREADY[TARGET_SLAVE] == 1'b1) // APB is READY --> RDATA is AVAILABLE
            begin
               NS = DONE_SINGLE_RD;
            end
            else
            begin // APB not ready
               NS = WAIT_R_PREADY;
            end
         end //~WAIT_R_PREADY

         WAIT_W_PREADY:
         begin
            write_req   = 1'b1;
            address     = AWADDR[$clog2(APB_NUM_SLAVES) + APB_ADDR_WIDTH - 1:0];
            // There is a Pending WRITE!!
            if(PREADY[TARGET_SLAVE] == 1'b1) // APB is READY --> WDATA is LAtched
            begin
              NS = SEND_B_RESP;
            end
            else // APB not READY
            begin
              NS = WAIT_W_PREADY;
            end
         end //~WAIT_W_PREADY


        IDLE:
        begin
            if(ARVALID == 1'b1)
            begin
                read_req     = 1'b1;
                address      = ARADDR[$clog2(APB_NUM_SLAVES) + APB_ADDR_WIDTH  - 1 : 0];
                sample_RDATA = PREADY[TARGET_SLAVE];

                if(PREADY[TARGET_SLAVE] == 1'b1) // APB is READY --> RDATA is AVAILABLE
                begin
                  NS   = DONE_SINGLE_RD;
                end
                else
                begin // APB not ready
                   NS = WAIT_R_PREADY;
                end
            end
            else
            begin
                if(AWVALID)
                begin
                      address =  AWADDR[$clog2(APB_NUM_SLAVES) + APB_ADDR_WIDTH - 1:0];
                      if(WVALID)
                      begin
                          write_req = 1'b1;

                          // There is a Pending WRITE!!
                          if(PREADY[TARGET_SLAVE] == 1'b1) // APB is READY --> WDATA is LAtched
                          begin
                             NS = SEND_B_RESP;
                          end
                          else // APB not READY
                          begin
                             NS = WAIT_W_PREADY;
                          end

                      end
                      else // GOT ADDRESS WRITE, not DATA
                      begin
                          write_req       = 1'b0;
                          address         = '0;
                          NS              = IDLE;
                      end
                      ////////////////////////////////////////////////////////////
                end
                else // No requests
                begin
                  NS      = IDLE;
                  address =  '0;
                end
            end
        end //~IDLE

         SEND_B_RESP:
         begin
            BVALID   = 1'b1;
            address  = '0;

            if(BREADY)
            begin
               NS      = IDLE;
               AWREADY = 1'b1;
               WREADY  = 1'b1;
            end
            else
            begin
               NS = SEND_B_RESP;
            end
         end //~SINGLE_WR

        DONE_SINGLE_RD:
        begin
              RVALID    = 1'b1;
              RLAST     = 1;
              address   = '0;

              if(RREADY)
              begin // ready to send back the rdata
                  NS = IDLE;
                  ARREADY = 1'b1;
              end
              else // NOT ready to send back the rdata
              begin
                  NS = DONE_SINGLE_RD;
              end
        end //~SINGLE_RD


        default:
        begin
            NS      = IDLE;
        end //~default

      endcase
    end

endmodule //~AXI_2_APB
