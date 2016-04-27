//////////////////////////////////////////////////////////////////////
////                                                              ////
////  adbg_wb_biu.v                                               ////
////                                                              ////
////                                                              ////
////  This file is part of the SoC Debug Interface.               ////
////                                                              ////
////  Author(s):                                                  ////
////       Nathan Yawn (nathan.yawn@opencores.org)                ////
////                                                              ////
////                                                              ////
////                                                              ////
//////////////////////////////////////////////////////////////////////
////                                                              ////
//// Copyright (C) 2008-2010        Authors                       ////
////                                                              ////
//// This source file may be used and distributed without         ////
//// restriction provided that this copyright statement is not    ////
//// removed from the file and that any derivative work contains  ////
//// the original copyright notice and the associated disclaimer. ////
////                                                              ////
//// This source file is free software; you can redistribute it   ////
//// and/or modify it under the terms of the GNU Lesser General   ////
//// Public License as published by the Free Software Foundation; ////
//// either version 2.1 of the License, or (at your option) any   ////
//// later version.                                               ////
////                                                              ////
//// This source is distributed in the hope that it will be       ////
//// useful, but WITHOUT ANY WARRANTY; without even the implied   ////
//// warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR      ////
//// PURPOSE.  See the GNU Lesser General Public License for more ////
//// details.                                                     ////
////                                                              ////
//// You should have received a copy of the GNU Lesser General    ////
//// Public License along with this source; if not, download it   ////
//// from http://www.opencores.org/lgpl.shtml                     ////
////                                                              ////
//////////////////////////////////////////////////////////////////////
//
// CVS Revision History
//
// $Log: adbg_wb_biu.v,v $
// Revision 1.5  2010-03-21 01:05:10  Nathan
// Use all 32 address bits - WishBone slaves may use the 2 least-significant address bits instead of the four wb_sel lines, or in addition to them.
//
// Revision 1.4  2010-01-10 22:54:11  Nathan
// Update copyright dates
//
// Revision 1.3  2009/05/17 20:54:57  Nathan
// Changed email address to opencores.org
//
// Revision 1.2  2009/05/04 00:50:10  Nathan
// Changed the WB BIU to use big-endian byte ordering, to match the OR1000.  Kept little-endian ordering as a compile-time option in case this is ever used with a little-endian CPU.
//
// Revision 1.1  2008/07/22 20:28:32  Nathan
// Changed names of all files and modules (prefixed an a, for advanced).  Cleanup, indenting.  No functional changes.
//
// Revision 1.4  2008/07/08 19:04:04  Nathan
// Many small changes to eliminate compiler warnings, no functional changes.
// System will now pass SRAM and CPU self-tests on Altera FPGA using
// altera_virtual_jtag TAP.
//


// Top module
module adbg_axi_biu
#(
    parameter AXI_ADDR_WIDTH = 32,
    parameter AXI_DATA_WIDTH = 64,
    parameter AXI_USER_WIDTH = 6,
    parameter AXI_ID_WIDTH   = 3
)
(
    // Debug interface signals
    input  logic                        tck_i,
    input  logic                        trstn_i,
    input  logic [63:0]                 data_i,
    output logic [63:0]                 data_o,
    input  logic                 [31:0] addr_i,
    input  logic                        strobe_i,
    input  logic                        rd_wrn_i,           // If 0, then write op
    output logic                        rdy_o,
    output logic                        err_o,
    input  logic                  [3:0] word_size_i,  // 1,2, or 4

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

  // Registers
  logic [AXI_DATA_WIDTH/8-1:0]    sel_reg;
  logic   [AXI_ADDR_WIDTH-1:0]    addr_reg;  // Don't really need the two LSB, this info is in the SEL bits
  logic   [AXI_DATA_WIDTH-1:0]    data_in_reg;  // dbg->AXI
  logic   [AXI_DATA_WIDTH-1:0]    data_out_reg;  // AXI->dbg
  logic                           wr_reg;
  logic                           str_sync;  // This is 'active-toggle' rather than -high or -low.
  logic                           rdy_sync;  // ditto, active-toggle
  logic                           err_reg;

  // Sync registers.  TFF indicates TCK domain, WBFF indicates wb_clk domain
  logic     rdy_sync_tff1;
  logic     rdy_sync_tff2;
  logic     rdy_sync_tff2q;  // used to detect toggles
  logic     str_sync_wbff1;
  logic     str_sync_wbff2;
  logic     str_sync_wbff2q;  // used to detect toggles


  // Control Signals
  logic     data_o_en;    // latch wb_data_i
  logic     rdy_sync_en;  // toggle the rdy_sync signal, indicate ready to TCK domain
  logic     err_en;       // latch the wb_err_i signal

  // Internal signals
  logic [AXI_DATA_WIDTH/8-1:0] be_dec;        // word_size and low-order address bits decoded to SEL bits
  logic                        start_toggle;  // AXI domain, indicates a toggle on the start strobe
  logic   [AXI_DATA_WIDTH-1:0] swapped_data_i;
  logic   [AXI_DATA_WIDTH-1:0] swapped_data_out;

  // AXI4 FSM states
  enum logic [1:0] {S_IDLE,S_AXIADDR,S_AXIDATA,S_AXIRESP} axi_fsm_state,next_fsm_state;



  // Create byte enable signals from word_size and address (combinatorial)
  // This uses LITTLE ENDIAN byte ordering...lowest-addressed bytes is the
  // least-significant byte of the 32-bit WB bus.
  always_comb
  begin
    if (AXI_DATA_WIDTH == 64)
    begin
      case (word_size_i)
        4'h1:
          begin
            if(addr_i[2:0] == 3'b000)      be_dec = 8'b00000001;
            else if(addr_i[2:0] == 3'b001) be_dec = 8'b00000010;
            else if(addr_i[2:0] == 3'b010) be_dec = 8'b00000100;
            else if(addr_i[2:0] == 3'b011) be_dec = 8'b00001000;
            else if(addr_i[2:0] == 3'b100) be_dec = 8'b00010000;
            else if(addr_i[2:0] == 3'b101) be_dec = 8'b00100000;
            else if(addr_i[2:0] == 3'b110) be_dec = 8'b01000000;
            else                           be_dec = 8'b10000000;
          end
        4'h2:
          begin
            if(addr_i[2:1] == 2'b00)       be_dec = 8'b00000011;
            else if(addr_i[2:1] == 2'b01)  be_dec = 8'b00001100;
            else if(addr_i[2:1] == 2'b10)  be_dec = 8'b00110000;
            else                           be_dec = 8'b11000000;
          end
        4'h4:
          begin
            if(addr_i[2] == 1'b0)          be_dec = 8'b00001111;
            else                           be_dec = 8'b11110000;
          end
        4'h8:                              be_dec = 8'b11111111;
        default:                           be_dec = 8'b11111111;  // default to 64-bit access
      endcase
    end
    else if (AXI_DATA_WIDTH == 32)
    begin
      case (word_size_i)
        4'h1:
          begin
            if(addr_i[1:0] == 2'b00)       be_dec = 4'b0001;
            else if(addr_i[1:0] == 2'b01)  be_dec = 4'b0010;
            else if(addr_i[1:0] == 2'b10)  be_dec = 4'b0100;
            else                           be_dec = 4'b1000;
          end
        4'h2:
          begin
            if(addr_i[1] == 1'b0)          be_dec = 4'b0011;
            else                           be_dec = 4'b1100;
          end
        4'h4:
                                           be_dec = 4'b1111;
        4'h8:
                                           be_dec = 4'b1111;  //error if it happens
        default:                           be_dec = 4'b1111;  // default to 32-bit access
      endcase // word_size_i
    end
  end


  // Byte- or word-swap data as necessary.  Use the non-latched be_dec signal,
  // since it and the swapped data will be latched at the same time.
  // Remember that since the data is shifted in LSB-first, shorter words
  // will be in the high-order bits. (combinatorial)
  always_comb
  begin
    if (AXI_DATA_WIDTH == 64)
    begin
      case (be_dec)
        8'b00001111: swapped_data_i = {32'h0, data_i[63:32]};
        8'b11110000: swapped_data_i = {       data_i[63:32],  32'h0};
        8'b00000011: swapped_data_i = {48'h0, data_i[63:48]};
        8'b00001100: swapped_data_i = {32'h0, data_i[63:48], 16'h0};
        8'b00110000: swapped_data_i = {16'h0, data_i[63:48], 32'h0};
        8'b11000000: swapped_data_i = {       data_i[63:48], 48'h0};
        8'b00000001: swapped_data_i = {56'h0, data_i[63:56]};
        8'b00000010: swapped_data_i = {48'h0, data_i[63:56],  8'h0};
        8'b00000100: swapped_data_i = {40'h0, data_i[63:56], 16'h0};
        8'b00001000: swapped_data_i = {32'h0, data_i[63:56], 24'h0};
        8'b00010000: swapped_data_i = {24'h0, data_i[63:56], 32'h0};
        8'b00100000: swapped_data_i = {16'h0, data_i[63:56], 40'h0};
        8'b01000000: swapped_data_i = { 8'h0, data_i[63:56], 48'h0};
        8'b10000000: swapped_data_i = {       data_i[63:56], 56'h0};
        default:     swapped_data_i =         data_i;
      endcase
    end
    else if (AXI_DATA_WIDTH == 32)
    begin
      case (be_dec)
        4'b1111: swapped_data_i =         data_i[63:32];
        4'b0011: swapped_data_i = {16'h0, data_i[63:48]};
        4'b1100: swapped_data_i = {       data_i[63:48], 16'h0};
        4'b0001: swapped_data_i = {24'h0, data_i[63:56]};
        4'b0010: swapped_data_i = {16'h0, data_i[63:56],  8'h0};
        4'b0100: swapped_data_i = {8'h0,  data_i[63:56], 16'h0};
        4'b1000: swapped_data_i = {       data_i[63:56], 24'h0};
        default: swapped_data_i =         data_i[63:32];
      endcase
    end
  end

  // Byte- or word-swap the WB->dbg data, as necessary (combinatorial)
  // We assume bits not required by SEL are don't care.  We reuse assignments
  // where possible to keep the MUX smaller.  (combinatorial)
  generate if (AXI_DATA_WIDTH == 64) begin
    always @(*)
    begin
      case (sel_reg)
        8'b00001111: swapped_data_out =         axi_master_r_data;
        8'b11110000: swapped_data_out = {32'h0, axi_master_r_data[63:32]};
        8'b00000011: swapped_data_out =         axi_master_r_data;
        8'b00001100: swapped_data_out = {16'h0, axi_master_r_data[63:16]};
        8'b00110000: swapped_data_out = {32'h0, axi_master_r_data[63:32]};
        8'b11000000: swapped_data_out = {48'h0, axi_master_r_data[63:48]};
        8'b00000001: swapped_data_out =         axi_master_r_data;
        8'b00000010: swapped_data_out = {8'h0,  axi_master_r_data[63:8]};
        8'b00000100: swapped_data_out = {16'h0, axi_master_r_data[63:16]};
        8'b00001000: swapped_data_out = {24'h0, axi_master_r_data[63:24]};
        8'b00010000: swapped_data_out = {32'h0, axi_master_r_data[63:32]};
        8'b00100000: swapped_data_out = {40'h0, axi_master_r_data[63:40]};
        8'b01000000: swapped_data_out = {48'h0, axi_master_r_data[63:48]};
        8'b10000000: swapped_data_out = {56'h0, axi_master_r_data[63:56]};
        default:     swapped_data_out =         axi_master_r_data;
      endcase
    end
  end else if (AXI_DATA_WIDTH == 32) begin
    always @(*)
    begin
      case (sel_reg)
        4'b1111: swapped_data_out =         axi_master_r_data;
        4'b0011: swapped_data_out =         axi_master_r_data;
        4'b1100: swapped_data_out = {16'h0, axi_master_r_data[31:16]};
        4'b0001: swapped_data_out =         axi_master_r_data;
        4'b0010: swapped_data_out = {8'h0,  axi_master_r_data[31:8]};
        4'b0100: swapped_data_out = {16'h0, axi_master_r_data[31:16]};
        4'b1000: swapped_data_out = {24'h0, axi_master_r_data[31:24]};
        default: swapped_data_out =         axi_master_r_data;
      endcase
    end
  end
  endgenerate


  // Latch input data on 'start' strobe, if ready.
  always_ff @(posedge tck_i, negedge trstn_i)
  begin
    if(~trstn_i) begin
      sel_reg     <=  'h0;
      addr_reg    <=  'h0;
      data_in_reg <=  'h0;
      wr_reg      <= 1'b0;
    end
    else
    if(strobe_i && rdy_o) begin
      sel_reg  <= be_dec;
      addr_reg <= addr_i;
      if(!rd_wrn_i) data_in_reg <= swapped_data_i;
      wr_reg <= ~rd_wrn_i;
    end
  end

  // Create toggle-active strobe signal for clock sync.  This will start a transaction
  // on the AXI once the toggle propagates to the FSM in the AXI domain.
  always_ff @(posedge tck_i, negedge trstn_i)
  begin
    if(~trstn_i)               str_sync <= 1'b0;
    else if(strobe_i && rdy_o) str_sync <= ~str_sync;
  end

  // Create rdy_o output.  Set on reset, clear on strobe (if set), set on input toggle
  always_ff @(posedge tck_i, negedge trstn_i)
  begin
    if(~trstn_i) begin
      rdy_sync_tff1  <= 1'b0;
      rdy_sync_tff2  <= 1'b0;
      rdy_sync_tff2q <= 1'b0;
    end else begin
      rdy_sync_tff1  <= rdy_sync;       // Synchronize the ready signal across clock domains
      rdy_sync_tff2  <= rdy_sync_tff1;
      rdy_sync_tff2q <= rdy_sync_tff2;  // used to detect toggles
    end
  end

  always_ff @(posedge tck_i, negedge trstn_i)
  begin
    if(~trstn_i) begin
      rdy_o <= 1'b1;
    end
    else
    begin
      if(strobe_i && rdy_o)
        rdy_o <= 1'b0;
      else if(rdy_sync_tff2 != rdy_sync_tff2q)
        rdy_o <= 1'b1;
    end
  end

  //////////////////////////////////////////////////////////
  // Direct assignments, unsynchronized

  assign axi_master_ar_addr = addr_reg;
  assign axi_master_aw_addr = addr_reg;

  assign axi_master_w_data  = data_in_reg;
  assign axi_master_w_strb  = sel_reg;

  always_comb
  begin
    if (AXI_DATA_WIDTH == 64)
      data_o = data_out_reg;
    else if (AXI_DATA_WIDTH == 32)
      data_o = {32'h0,data_out_reg};
  end

  assign err_o  = err_reg;

  assign axi_master_aw_prot   = 'h0;
  assign axi_master_aw_region = 'h0;
  assign axi_master_aw_len    = 'h0;
  assign axi_master_aw_burst  = 'h0;
  assign axi_master_aw_lock   = 'h0;
  assign axi_master_aw_cache  = 'h0;
  assign axi_master_aw_qos    = 'h0;
  assign axi_master_aw_id     = 'h0;
  assign axi_master_aw_user   = 'h0;

  assign axi_master_ar_prot   = 'h0;
  assign axi_master_ar_region = 'h0;
  assign axi_master_ar_len    = 'h0;
  assign axi_master_ar_burst  = 'h0;
  assign axi_master_ar_lock   = 'h0;
  assign axi_master_ar_cache  = 'h0;
  assign axi_master_ar_qos    = 'h0;
  assign axi_master_ar_id     = 'h0;
  assign axi_master_ar_user   = 'h0;


  assign axi_master_w_user    = 'h0;
  assign axi_master_w_last    = 1'b1;



  always_comb
  begin
    case (word_size_i)
      4'h1:
        begin
          axi_master_aw_size = 3'b000;
          axi_master_ar_size = 3'b000;
        end
      4'h2:
        begin
          axi_master_aw_size = 3'b001;
          axi_master_ar_size = 3'b001;
        end
      4'h4:
        begin
          axi_master_aw_size = 3'b010;
          axi_master_ar_size = 3'b010;
        end
      4'h8:
        begin
          axi_master_aw_size = 3'b011;
          axi_master_ar_size = 3'b011;
        end
      default:
        begin
          axi_master_aw_size = 3'b011;
          axi_master_ar_size = 3'b011;
        end
    endcase
  end

  ///////////////////////////////////////////////////////
  // AXI clock domain

  // synchronize the start strobe
  always_ff @(posedge axi_aclk, negedge axi_aresetn)
  begin
     if(!axi_aresetn) begin
       str_sync_wbff1  <= 1'b0;
       str_sync_wbff2  <= 1'b0;
       str_sync_wbff2q <= 1'b0;
     end else begin
       str_sync_wbff1  <= str_sync;
       str_sync_wbff2  <= str_sync_wbff1;
       str_sync_wbff2q <= str_sync_wbff2;  // used to detect toggles
     end
  end

  assign start_toggle = (str_sync_wbff2 != str_sync_wbff2q);

  // Error indicator register
  always_ff @(posedge axi_aclk, negedge axi_aresetn)
  begin
      if(!axi_aresetn) err_reg <= 1'b0;
      else if(err_en) err_reg <= wr_reg ? ((axi_master_b_resp == 2'b00) ? 1'b0 : 1'b1) : ((axi_master_r_resp == 2'b00) ? 1'b0 : 1'b1);
  end

  // WB->dbg data register
  always_ff @ (posedge axi_aclk, negedge axi_aresetn)
  begin
    if(!axi_aresetn)   data_out_reg <= 32'h0;
    else if(data_o_en) data_out_reg <= swapped_data_out;
  end

  // Create a toggle-active ready signal to send to the TCK domain
  always_ff @(posedge axi_aclk, negedge axi_aresetn)
  begin
    if(!axi_aresetn)     rdy_sync <= 1'b0;
    else if(rdy_sync_en) rdy_sync <= ~rdy_sync;
  end

   /////////////////////////////////////////////////////
   // Small state machine to create AXI accesses
   // Not much more that an 'in_progress' bit, but easier
   // to read.  Deals with single-cycle and multi-cycle
   // accesses.

  // Sequential bit
  always_ff @(posedge axi_aclk, negedge axi_aresetn)
  begin
    if(~axi_aresetn) axi_fsm_state <= S_IDLE;
    else             axi_fsm_state <= next_fsm_state;
  end

  // Determination of next state (combinatorial)
  always_comb
  begin
    axi_master_aw_valid = 1'b0;
    axi_master_w_valid  = 1'b0;
    axi_master_ar_valid = 1'b0;
    axi_master_b_ready  = 1'b0;
    axi_master_r_ready  = 1'b0;
    next_fsm_state      = axi_fsm_state;
    rdy_sync_en         = 1'b0;
    data_o_en           = 1'b0;
    err_en              = 1'b0;

    case (axi_fsm_state)
      S_IDLE:
      begin
        if(start_toggle)
          next_fsm_state = S_AXIADDR;  // Don't go to next state for 1-cycle transfer
        else
          next_fsm_state = S_IDLE;
      end
      S_AXIADDR:
      begin
        if (wr_reg)
          axi_master_aw_valid = 1'b1;
        else
          axi_master_ar_valid = 1'b1;
        if (wr_reg && axi_master_aw_ready)
          next_fsm_state = S_AXIDATA;
        else if (!wr_reg && axi_master_ar_ready)
          next_fsm_state = S_AXIRESP;
      end
      S_AXIDATA:
      begin
        axi_master_w_valid = 1'b1;
        if (axi_master_w_ready)
          next_fsm_state = S_AXIRESP;
      end
      S_AXIRESP:
      begin
        if (wr_reg)
          axi_master_b_ready = 1'b1;
        else
          axi_master_r_ready = 1'b1;
        if (wr_reg && axi_master_b_valid)
        begin
          next_fsm_state = S_IDLE;
          rdy_sync_en    = 1'b1;
          err_en         = 1'b1;
        end
        else if (!wr_reg && axi_master_r_valid)
        begin
          data_o_en      = 1'b1;
          next_fsm_state = S_IDLE;
          rdy_sync_en    = 1'b1;
          err_en         = 1'b1;
        end
      end
    endcase
  end

endmodule
