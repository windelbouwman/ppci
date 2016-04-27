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
`define OKAY   2'b00
`define EXOKAY 2'b01
`define SLVERR 2'b10
`define DECERR 2'b11

`define REG_STATUS 3'b000
`define REG_CLKDIV 3'b001
`define REG_SPICMD 3'b010
`define REG_SPIADR 3'b011
`define REG_SPILEN 3'b100
`define REG_SPIDUM 3'b101

module spi_master_axi_if #(
      parameter AXI4_ADDRESS_WIDTH = 32,
      parameter AXI4_RDATA_WIDTH   = 32,
      parameter AXI4_WDATA_WIDTH   = 32,
      parameter AXI4_USER_WIDTH    = 4,
      parameter AXI4_ID_WIDTH      = 16
  ) (
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

    output logic                    [7:0] spi_clk_div,
    output logic                          spi_clk_div_valid,
    input  logic                   [31:0] spi_status,
    output logic                   [31:0] spi_addr,
    output logic                    [5:0] spi_addr_len,
    output logic                   [31:0] spi_cmd,
    output logic                    [5:0] spi_cmd_len,
    output logic                    [3:0] spi_csreg,
    output logic                   [15:0] spi_data_len,
    output logic                   [15:0] spi_dummy_rd,
    output logic                   [15:0] spi_dummy_wr,
    output logic                          spi_swrst,
    output logic                          spi_rd,
    output logic                          spi_wr,
    output logic                          spi_qrd,
    output logic                          spi_qwr,
    output logic                   [31:0] spi_data_tx,
    output logic                          spi_data_tx_valid,
    input  logic                          spi_data_tx_ready,
    input  logic                   [31:0] spi_data_rx,
    input  logic                          spi_data_rx_valid,
    output logic                          spi_data_rx_ready
    );

  localparam WR_ADDR_CMP = `log2(AXI4_WDATA_WIDTH/8)-1;
  localparam RD_ADDR_CMP = `log2(AXI4_RDATA_WIDTH/8)-1;

  localparam OFFSET_BIT  =  ( `log2(AXI4_WDATA_WIDTH-1) - 3 );  // Address Offset: OFFSET IS 32bit--> 2bit; 64bit--> 3bit; 128bit--> 4bit and so on

  logic                 [4:0] wr_addr;
  logic                 [4:0] rd_addr;

  logic                       is_tx_fifo_sel;
  logic                       is_rx_fifo_sel;
  logic                       is_tx_fifo_sel_q;
  logic                       is_rx_fifo_sel_q;

  logic                       read_req;
  logic                 [4:0] read_address;
  logic                       sample_AR;
  logic                 [4:0] ARADDR_Q;
  logic                 [7:0] ARLEN_Q;
  logic                       decr_ARLEN;
  logic                 [7:0] CountBurstCS;
  logic                 [7:0] CountBurstNS;
  logic   [AXI4_ID_WIDTH-1:0] ARID_Q;
  logic [AXI4_USER_WIDTH-1:0] ARUSER_Q;


  logic                       write_req;
  logic                 [4:0] write_address;
  logic                       sample_AW;
  logic                 [4:0] AWADDR_Q;
  logic                 [7:0] AWLEN_Q;
  logic                       decr_AWLEN;
  logic                 [7:0] CountBurst_AW_CS;
  logic                 [7:0] CountBurst_AW_NS;
  logic   [AXI4_ID_WIDTH-1:0] AWID_Q;
  logic [AXI4_USER_WIDTH-1:0] AWUSER_Q;

  enum logic [2:0] { IDLE, SINGLE, BURST, WAIT_WDATA_BURST, WAIT_WDATA_SINGLE, BURST_RESP } AR_CS, AR_NS, AW_CS, AW_NS;

  assign wr_addr = s_axi_awaddr[WR_ADDR_CMP+4:WR_ADDR_CMP];
  assign rd_addr = s_axi_araddr[RD_ADDR_CMP+4:RD_ADDR_CMP];

  assign is_tx_fifo_sel = (wr_addr[3] == 1'b1);
  assign is_rx_fifo_sel = (rd_addr[4] == 1'b1);

  assign spi_data_tx = s_axi_wdata[31:0];

  //read fsm
  always_ff @(posedge s_axi_aclk, negedge s_axi_aresetn)
  begin
    if(s_axi_aresetn == 1'b0)
    begin
      AR_CS        <= IDLE;
      ARADDR_Q     <= '0;
      CountBurstCS <= '0;
      ARID_Q       <= '0;
      ARUSER_Q     <= '0;
      is_tx_fifo_sel_q <= '0;
      is_rx_fifo_sel_q <= '0;
    end
    else
    begin
      AR_CS <= AR_NS;
      CountBurstCS <= CountBurstNS;

      is_tx_fifo_sel_q <= is_tx_fifo_sel;
      is_rx_fifo_sel_q <= is_rx_fifo_sel;

      if(sample_AR)
        ARLEN_Q  <=  s_axi_arlen;
      else
      if(decr_ARLEN)
        ARLEN_Q  <=  ARLEN_Q -1'b1;

      if(sample_AR)
      begin
        ARID_Q   <=  s_axi_arid;
        ARADDR_Q <=  read_address;
        ARUSER_Q <=  s_axi_aruser;
      end
    end
  end

  always_comb
  begin
    s_axi_arready  = 1'b0;
    read_address   = '0;
    read_req       = 1'b0;
    sample_AR      = 1'b0;
    decr_ARLEN     = 1'b0;
    CountBurstNS   = CountBurstCS;
    spi_data_rx_ready = 1'b0;
    s_axi_rvalid         = 1'b0;
    s_axi_rresp          = `OKAY;
    s_axi_ruser          = '0;
    s_axi_rlast          = 1'b0;
    s_axi_rid            = '0;
    AR_NS = AR_CS;

    case(AR_CS)
      IDLE:
      begin
        s_axi_arready        = 1'b1;
        if(s_axi_arvalid)
        begin
          sample_AR      = 1'b1;
          read_req       = 1'b1;
          read_address   = rd_addr;
          if(s_axi_arlen == 0)
          begin
            AR_NS = SINGLE;
            CountBurstNS   = '0;
          end
          else
          begin
            AR_NS = BURST;
            CountBurstNS   = CountBurstCS + 1'b1;
          end
        end
        else
        begin
          AR_NS = IDLE;
          CountBurstNS   = '0;
        end
      end //~ IDLE

      SINGLE:
      begin

        s_axi_rresp  = `OKAY;
        s_axi_rid    = ARID_Q;
        s_axi_ruser  = ARUSER_Q;
        s_axi_rlast  = 1'b1;
        read_address   =  ARADDR_Q;
        // if RX FIFO selected rvalid if valid data in FIFO
        if (is_rx_fifo_sel_q)
          s_axi_rvalid = spi_data_rx_valid;
        else
          s_axi_rvalid = 1'b1;
        // we have a valid response here, waiting to be delivered
        // valid response is either no RX FIFO selected or RX FIFO selected and data available in FIFO
        if( (s_axi_rready && !is_rx_fifo_sel_q) | (s_axi_rready && is_rx_fifo_sel_q && spi_data_rx_valid))
        begin
          if (is_rx_fifo_sel_q)
            spi_data_rx_ready = 1'b1;

          s_axi_arready = 1'b1;
          if(s_axi_arvalid)
          begin
            sample_AR      = 1'b1;
            read_req       = 1'b1;
            read_address   =  rd_addr;

            if(s_axi_arlen == 0)
            begin
              AR_NS          = SINGLE;
              CountBurstNS   = '0;
            end
            else
            begin
              AR_NS          = BURST;
              CountBurstNS   = CountBurstCS + 1'b1;
            end
          end
          else
          begin
            AR_NS = IDLE;
            CountBurstNS   = '0;
          end
        end
        else // NOt ready: stay here untile RR RADY is OK
        begin
          AR_NS          = SINGLE;
          read_req       = 1'b1;
          read_address   =  ARADDR_Q;
          CountBurstNS   = '0;
        end

      end //~ SINGLE

      BURST:
      begin
        s_axi_rresp  = `OKAY;
        s_axi_rid    = ARID_Q;
        s_axi_ruser  = ARUSER_Q;
        read_address   =  ARADDR_Q;

        if (is_rx_fifo_sel_q)
          s_axi_rvalid = spi_data_rx_valid;
        else
          s_axi_rvalid = 1'b1;

        if( (s_axi_rready && !is_rx_fifo_sel_q) | (s_axi_rready && is_rx_fifo_sel_q && spi_data_rx_valid))
        begin
          if (is_rx_fifo_sel_q)
            spi_data_rx_ready = 1'b1;

          if(ARLEN_Q > 0)
          begin
            AR_NS         = BURST;
            read_req      = 1'b1; // read the previous address
            decr_ARLEN    = 1'b1;
            read_address  =  ARADDR_Q + CountBurstCS ;
            s_axi_rlast         = 1'b0;
            s_axi_arready       = 1'b0;
          end
          else //BURST_LAST
          begin
            s_axi_rlast         = 1'b1;
            s_axi_arready       = 1'b1;
            // Check if there are any pending request
            if(s_axi_arvalid)
            begin
              sample_AR      = 1'b1;
              read_req       = 1'b1;
              read_address   = rd_addr;

              if(s_axi_arlen == 0)
              begin
                AR_NS = SINGLE;
                CountBurstNS   = 0;
              end
              else
              begin
                AR_NS = BURST;
                CountBurstNS   = 1;
              end
            end
            else
            begin
              AR_NS = IDLE;
              CountBurstNS   = 0;
            end

          end
        end
        else
        begin
          AR_NS          = BURST;
          read_req     = 1'b1; // read the previous address
          decr_ARLEN   = 1'b0;
          read_address =  ARADDR_Q + CountBurstCS;
          s_axi_arready      = 1'b0;
        end

      end //~ BURST
      default : begin

      end //~default
    endcase
  end

  //Write FSM
  always_ff @(posedge s_axi_aclk, negedge s_axi_aresetn)
  begin
    if(s_axi_aresetn == 1'b0)
    begin
      AW_CS            <= IDLE;
      AWADDR_Q         <= '0;
      CountBurst_AW_CS <= '0;
      AWID_Q           <= '0;
      AWUSER_Q         <= '0;
    end
    else
    begin
      AW_CS <= AW_NS;
      CountBurst_AW_CS <= CountBurst_AW_NS;
      if(sample_AW)
      begin
        AWLEN_Q  <=  s_axi_awlen;
        AWADDR_Q <=  wr_addr;
        AWID_Q   <=  s_axi_awid;
        AWUSER_Q <=  s_axi_awuser;
      end
      else
      if(decr_AWLEN)
      begin
        AWLEN_Q  <=  AWLEN_Q -1'b1;
      end
    end
  end

  always_comb
  begin
    s_axi_awready        = 1'b0;
    s_axi_wready         = 1'b0;
    write_address  = '0;
    write_req       = 1'b0;
    sample_AW      = 1'b0;
    decr_AWLEN     = 1'b0;
    CountBurst_AW_NS   = CountBurst_AW_CS;
    s_axi_bid   = '0;
    s_axi_bresp = `OKAY;
    s_axi_buser = '0;
    s_axi_bvalid = 1'b0;
    AW_NS = AW_CS;

    case(AW_CS)
      IDLE:
      begin
        s_axi_awready        = 1'b1;

        if(s_axi_awvalid)
        begin
          sample_AW       = 1'b1;

          if(s_axi_wvalid)
          begin
              s_axi_wready    = 1'b1;
              write_req       = 1'b1;
              write_address   =  wr_addr;
              if(s_axi_awlen == 0)
              begin
                AW_NS = SINGLE;
                CountBurst_AW_NS   = 0;
              end
              else
              begin
                AW_NS = BURST;
                CountBurst_AW_NS   = 1;
              end
          end
          else // GOT ADDRESS WRITE, not DATA
          begin
            s_axi_wready    = 1'b1;
            write_req       = 1'b0;
            write_address   = '0;

            if(s_axi_awlen == 0)
            begin
              AW_NS             =  WAIT_WDATA_SINGLE;
              CountBurst_AW_NS  = 0;
            end
            else
            begin
              AW_NS =  WAIT_WDATA_BURST;
              CountBurst_AW_NS    = 0;
            end
          end
        end
        else
        begin
          s_axi_wready         = 1'b1;
          AW_NS              = IDLE;
          CountBurst_AW_NS   = '0;
        end

      end //~ IDLE


      WAIT_WDATA_BURST :
      begin
        s_axi_awready        = 1'b0;

        if(s_axi_wvalid)
        begin
            s_axi_wready     = 1'b1;
            write_req        = 1'b1;
            write_address    = AWADDR_Q;
            AW_NS            = BURST;
            CountBurst_AW_NS = 1;
            decr_AWLEN       = 1'b1;
        end
        else
        begin
          s_axi_wready         = 1'b1;
          write_req              =  1'b0;
          AW_NS                  = WAIT_WDATA_BURST; // wait for data
          CountBurst_AW_NS       = '0;
        end

      end //~WAIT_WDATA_BURST

      WAIT_WDATA_SINGLE :
      begin
        s_axi_awready        = 1'b0;
        CountBurst_AW_NS = '0;

        if(s_axi_wvalid)
        begin
            s_axi_wready         = 1'b1;
            write_req        = 1'b1;
            write_address    = AWADDR_Q;
            AW_NS            = SINGLE;
        end
        else
        begin
          s_axi_wready         = 1'b1;
          write_req        = 1'b0;
          AW_NS = WAIT_WDATA_SINGLE; // wait for data
        end
      end

      SINGLE: begin
        s_axi_bid    = AWID_Q;
        s_axi_bresp  = `OKAY;
        s_axi_buser  = AWUSER_Q;
        s_axi_bvalid = 1'b1;

        // we have a valid response here, waiting to be delivered
        if(s_axi_bready)
        begin
          s_axi_awready = 1'b1;
          if(s_axi_awvalid)
          begin
            sample_AW       =   1'b1;
            write_req       =   1'b1;
            write_address   =   wr_addr;

            if(s_axi_awlen == 0)
            begin
              AW_NS          = SINGLE;
              CountBurst_AW_NS   = '0;
            end
            else
            begin
              AW_NS          = BURST;
              CountBurst_AW_NS   = CountBurst_AW_CS + 1'b1;
            end
          end
          else
          begin
            AW_NS = IDLE;
            CountBurst_AW_NS   = '0;
          end
        end
        else // NOt ready: stay here untile RR RADY is OK
        begin
          AW_NS            = SINGLE;
          CountBurst_AW_NS = '0;
          s_axi_awready          = 1'b0;
        end

      end //~ SINGLE

      BURST:
      begin

        CountBurst_AW_NS = CountBurst_AW_CS;
        s_axi_awready        = 1'b0;

        //write_address  =  AWADDR_Q + CountBurst_AW_CS ;
        write_address  =  AWADDR_Q; //TODO check burst type

        if(s_axi_wvalid)
        begin
            s_axi_wready = 1'b1;
            write_req      = 1'b1; // read the previous address
            decr_AWLEN     = 1'b1;
            CountBurst_AW_NS   = CountBurst_AW_CS + 1'b1;
        end
        else
        begin
          s_axi_wready = 1'b1;
          write_req      = 1'b0; // read the previous address
          decr_AWLEN     = 1'b0;

        end
        if(AWLEN_Q > 0)
        begin
          AW_NS          = BURST;
          //    AWREADY        = 1'b0;
        end
        else
        begin
          AW_NS          = BURST_RESP;
          //    AWREADY        = 1'b1;
        end
      end //~ BURST


      BURST_RESP :
      begin
        s_axi_bvalid  = 1'b1;
        s_axi_bid     = AWID_Q;
        s_axi_bresp   = `OKAY;
        s_axi_buser   = AWUSER_Q;
        if(s_axi_bready)
        begin
          s_axi_awready = 1'b1;
          // Check if there are any pending request
          if(s_axi_awvalid)
          begin
            sample_AW = 1'b1;
            if(s_axi_wvalid)
            begin
                s_axi_wready = 1'b1;
                write_req       = 1'b1;
                write_address   = wr_addr;
                if(s_axi_awlen == 0)
                begin
                  AW_NS            = SINGLE;
                  CountBurst_AW_NS = 0;
                end
                else
                begin
                  AW_NS = BURST;
                  CountBurst_AW_NS   = 1;
                end
            end
            else // GOT ADDRESS WRITE, not DATA
            begin
              s_axi_wready = 1'b1;
              write_req       = 1'b0;
              write_address   = '0;

              if(s_axi_awlen == 0)
              begin
                AW_NS             =  WAIT_WDATA_SINGLE;
                CountBurst_AW_NS  = 0;
              end
              else
              begin
                AW_NS            = WAIT_WDATA_BURST;
                CountBurst_AW_NS = 0;
              end
            end
          end
          else
          begin
            s_axi_wready = 1'b1;
            AW_NS            = IDLE;
            CountBurst_AW_NS = '0;
          end
        end
        else //~BREADY
        begin
          AW_NS         = BURST_RESP;
          s_axi_awready = 1'b0;
          s_axi_wready = 1'b0;
        end
      end
    endcase
  end

  always @( posedge s_axi_aclk or negedge s_axi_aresetn )
  begin
    if ( s_axi_aresetn == 1'b0 )
    begin
      spi_swrst         = 1'b0;
      spi_rd            = 1'b0;
      spi_wr            = 1'b0;
      spi_qrd           = 1'b0;
      spi_qwr           = 1'b0;
      spi_clk_div_valid = 1'b0;
      spi_clk_div       =  'h0;
      spi_cmd           =  'h0;
      spi_addr          =  'h0;
      spi_cmd_len       =  'h0;
      spi_addr_len      =  'h0;
      spi_data_len      =  'h0;
      spi_dummy_rd    =  'h0;
      spi_dummy_wr      =  'h0;
      spi_csreg         =  'h0;
    end
    else if (write_req)
    begin
      spi_swrst = 1'b0;
      spi_rd    = 1'b0;
      spi_wr    = 1'b0;
      spi_qrd   = 1'b0;
      spi_qwr   = 1'b0;
      spi_clk_div_valid = 1'b0;
      case(write_address)
        `REG_STATUS:
        begin
          if ( s_axi_wstrb[0] == 1 )
          begin
            spi_rd = s_axi_wdata[0];
            spi_wr = s_axi_wdata[1];
            spi_qrd = s_axi_wdata[2];
            spi_qwr = s_axi_wdata[3];
            spi_swrst = s_axi_wdata[4];
          end
          if ( s_axi_wstrb[1] == 1 )
          begin
            spi_csreg = s_axi_wdata[11:8];
          end
        end
        `REG_CLKDIV:
          if ( s_axi_wstrb[0] == 1 )
          begin
            spi_clk_div = s_axi_wdata[7:0];
            spi_clk_div_valid = 1'b1;
          end
        `REG_SPICMD:
          for ( int byte_index = 0; byte_index < 4; byte_index = byte_index+1 )
            if ( s_axi_wstrb[byte_index] == 1 )
              spi_cmd[byte_index*8 +: 8] = s_axi_wdata[(byte_index*8) +: 8];
        `REG_SPIADR:
          for ( int byte_index = 0; byte_index < 4; byte_index = byte_index+1 )
            if ( s_axi_wstrb[byte_index] == 1 )
              spi_addr[byte_index*8 +: 8] = s_axi_wdata[(byte_index*8) +: 8];
        `REG_SPILEN:
        begin
          if ( s_axi_wstrb[0] == 1 )
            spi_cmd_len = s_axi_wdata[7:0];
          if ( s_axi_wstrb[1] == 1 )
            spi_addr_len = s_axi_wdata[15:8];
          if ( s_axi_wstrb[2] == 1 )
            spi_data_len[7:0] = s_axi_wdata[23:16];
          if ( s_axi_wstrb[3] == 1 )
            spi_data_len[15:8] = s_axi_wdata[31:24];
        end
        `REG_SPIDUM:
        begin
          if ( s_axi_wstrb[0] == 1 )
            spi_dummy_rd[7:0] = s_axi_wdata[7:0];
          if ( s_axi_wstrb[1] == 1 )
            spi_dummy_rd[15:8] = s_axi_wdata[15:8];
          if ( s_axi_wstrb[2] == 1 )
            spi_dummy_wr[7:0] = s_axi_wdata[23:16];
          if ( s_axi_wstrb[3] == 1 )
            spi_dummy_wr[15:8] = s_axi_wdata[31:24];
        end
      endcase
    end
    else
    begin
      spi_swrst = 1'b0;
      spi_rd = 1'b0;
      spi_wr = 1'b0;
      spi_qrd = 1'b0;
      spi_qwr = 1'b0;
      spi_clk_div_valid = 1'b0;
    end
  end // SLAVE_REG_WRITE_PROC


  // implement slave model register read mux
  always_comb
    begin
      s_axi_rdata = {32'h0,spi_data_rx};
      case(read_address)
        `REG_STATUS:
                s_axi_rdata[31:0] = spi_status;
        `REG_CLKDIV:
                s_axi_rdata[31:0] = {24'h0,spi_clk_div};
        `REG_SPICMD:
          s_axi_rdata[31:0] = spi_cmd;
        `REG_SPIADR:
          s_axi_rdata[31:0] = spi_addr;
        `REG_SPILEN:
          s_axi_rdata[31:0] = {spi_data_len,2'b00,spi_addr_len,2'b00,spi_cmd_len};
        `REG_SPIDUM:
                s_axi_rdata[31:0] = {spi_dummy_wr,spi_dummy_rd};
      endcase
    end // SLAVE_REG_READ_PROC

  assign spi_data_tx_valid = write_req & (write_address[3] == 1'b1);

endmodule
