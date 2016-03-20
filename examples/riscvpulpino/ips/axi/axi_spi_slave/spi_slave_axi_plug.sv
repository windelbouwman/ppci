// Copyright 2015 ETH Zurich and University of Bologna.
// Copyright and related rights are licensed under the Solderpad Hardware
// License, Version 0.51 (the “License”); you may not use this file except in
// compliance with the License.  You may obtain a copy of the License at
// http://solderpad.org/licenses/SHL-0.51. Unless required by applicable law
// or agreed to in writing, software, hardware and materials distributed under
// this License is distributed on an “AS IS” BASIS, WITHOUT WARRANTIES OR
// CONDITIONS OF ANY KIND, either express or implied. See the License for the
// specific language governing permissions and limitations under the License.

module spi_slave_axi_plug
#(
    parameter AXI_ADDR_WIDTH = 32,
    parameter AXI_DATA_WIDTH = 64,
    parameter AXI_USER_WIDTH = 6,
    parameter AXI_ID_WIDTH   = 3
)
(
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
    output logic                        axi_master_b_ready,

    input  logic [AXI_ADDR_WIDTH-1:0]   rxtx_addr,
    input  logic                        rxtx_addr_valid,
    input  logic                        start_tx,
    input  logic                        cs,
    output logic                 [31:0] tx_data,
    output logic                        tx_valid,
    input  logic                        tx_ready,
    input  logic                 [31:0] rx_data,
    input  logic                        rx_valid,
    output logic                        rx_ready,

    input  logic                 [15:0] wrap_length
    );

  logic [AXI_ADDR_WIDTH-1:0] curr_addr;
  logic [AXI_ADDR_WIDTH-1:0] next_addr;
  logic [31:0]               curr_data_rx;
  logic [AXI_DATA_WIDTH-1:0] curr_data_tx;
  logic                      incr_addr_w;
  logic                      incr_addr_r;
  logic                      sample_fifo;
  logic                      sample_axidata;

  // up to 64 kwords (256kB)
  logic [15:0] tx_counter;

  enum logic [2:0] {IDLE,DATA,AXIADDR,AXIDATA,AXIRESP} AR_CS,AR_NS,AW_CS,AW_NS;

  always_ff @(posedge axi_aclk or negedge axi_aresetn)
  begin
    if (axi_aresetn == 0)
    begin
      AW_CS         <= IDLE;
      AR_CS         <= IDLE;
      curr_data_rx  <=  'h0;
      curr_data_tx  <=  'h0;
      curr_addr     <=  'h0;
    end
    else
    begin
      AW_CS <= AW_NS;
      AR_CS <= AR_NS;
      if (sample_fifo)
      begin
        curr_data_rx <= rx_data;
      end
      if (sample_axidata)
        curr_data_tx <= axi_master_r_data;
      if (rxtx_addr_valid)
        curr_addr <= rxtx_addr;
      else if (incr_addr_w | incr_addr_r)
        curr_addr <= next_addr;
    end
  end

  always_ff @(posedge axi_aclk or negedge axi_aresetn)
  begin
    if (axi_aresetn == 1'b0)
      tx_counter <= 16'h0;
    else if(start_tx)
      tx_counter <= 16'h0;
    else if(incr_addr_w | incr_addr_r) begin
      if(tx_counter == wrap_length-1)
        tx_counter <= 16'h0;
      else
        tx_counter <= tx_counter + 16'h1;
    end
  end

  always_comb
  begin
    next_addr = 32'b0;
    if(rxtx_addr_valid)
      next_addr = rxtx_addr;
    else if(tx_counter == wrap_length-1)
      next_addr = rxtx_addr;
    else
      next_addr = curr_addr + 32'h4;
  end

  always_comb
  begin
    AW_NS      = IDLE;
    sample_fifo = 1'b0;
    rx_ready   = 1'b0;
    axi_master_aw_valid = 1'b0;
    axi_master_w_valid  = 1'b0;
    axi_master_b_ready  = 1'b0;
    incr_addr_w         = 1'b0;
    case(AW_CS)
      IDLE:
      begin
        if(rx_valid)
        begin
          sample_fifo = 1'b1;
          rx_ready    = 1'b1;
          AW_NS       = AXIADDR;
        end
        else
        begin
          AW_NS      = IDLE;
        end
      end
      AXIADDR:
      begin
        axi_master_aw_valid = 1'b1;
        if (axi_master_aw_ready)
          AW_NS = AXIDATA;
        else
          AW_NS = AXIADDR;
      end
      AXIDATA:
      begin
        axi_master_w_valid = 1'b1;
        if (axi_master_w_ready)
        begin
          incr_addr_w         = 1'b1;
          AW_NS = AXIRESP;
        end
        else
          AW_NS = AXIDATA;
      end
      AXIRESP:
      begin
        axi_master_b_ready = 1'b1;
        if (axi_master_b_valid)
          AW_NS = IDLE;
        else
          AW_NS = AXIRESP;
      end

    endcase
  end

  always_comb
  begin
    AR_NS               = IDLE;
    tx_valid            = 1'b0;
    axi_master_ar_valid = 1'b0;
    axi_master_r_ready  = 1'b0;
    incr_addr_r         = 1'b0;
    sample_axidata      = 1'b0;
    case(AR_CS)
      IDLE:
      begin
        if(start_tx && !cs)
        begin
          AR_NS      = AXIADDR;
        end
        else
        begin
          AR_NS      = IDLE;
        end
      end
      DATA:
      begin
        tx_valid = 1'b1;
        if (cs)
        begin
          AR_NS = IDLE;
        end
        else
        begin
          if(tx_ready)
          begin
            incr_addr_r = 1'b1;
            AR_NS       = AXIADDR;
          end
          else
          begin
            AR_NS      = DATA;
          end
        end
      end
      AXIADDR:
      begin
        axi_master_ar_valid = 1'b1;
        if (axi_master_ar_ready)
          AR_NS = AXIRESP;
        else
          AR_NS = AXIADDR;
      end
      AXIRESP:
      begin
        axi_master_r_ready = 1'b1;
        if (axi_master_r_valid)
        begin
          sample_axidata = 1'b1;
          AR_NS = DATA;
        end
        else
          AR_NS = AXIRESP;
      end

    endcase
  end

  // for now, let us support only 32-bit reads!
  generate if (AXI_DATA_WIDTH == 32)
    assign tx_data = curr_data_tx[31:0];
  else
    assign tx_data = curr_addr[2] ? curr_data_tx[63:32] : curr_data_tx[31:0];
  endgenerate

  assign axi_master_aw_addr   =  curr_addr;
  assign axi_master_aw_prot   =  'h0;
  assign axi_master_aw_region =  'h0;
  assign axi_master_aw_len    =  'h0;
  assign axi_master_aw_size   = 3'b010;
  assign axi_master_aw_burst  =  'h0;
  assign axi_master_aw_lock   =  'h0;
  assign axi_master_aw_cache  =  'h0;
  assign axi_master_aw_qos    =  'h0;
  assign axi_master_aw_id     =  'h1;
  assign axi_master_aw_user   =  'h0;

  assign axi_master_w_data    = {AXI_DATA_WIDTH/32{curr_data_rx}}; // replicate curr_data_rx as often as needed
  generate if (AXI_DATA_WIDTH == 32)
    assign axi_master_w_strb    = 4'hF;
  else
    assign axi_master_w_strb    = curr_addr[2] ? 8'hF0 : 8'h0F;
  endgenerate
  assign axi_master_w_user    =  'h0;
  assign axi_master_w_last    = 1'b1;

  assign axi_master_ar_addr   =  curr_addr;
  assign axi_master_ar_prot   =  'h0;
  assign axi_master_ar_region =  'h0;
  assign axi_master_ar_len    =  'h0;
  assign axi_master_ar_size   = 3'b011;
  assign axi_master_ar_burst  =  'h0;
  assign axi_master_ar_lock   =  'h0;
  assign axi_master_ar_cache  =  'h0;
  assign axi_master_ar_qos    =  'h0;
  assign axi_master_ar_id     =  'h1;
  assign axi_master_ar_user   =  'h0;

endmodule
