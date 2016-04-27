// Copyright 2015 ETH Zurich and University of Bologna.
// Copyright and related rights are licensed under the Solderpad Hardware
// License, Version 0.51 (the “License”); you may not use this file except in
// compliance with the License.  You may obtain a copy of the License at
// http://solderpad.org/licenses/SHL-0.51. Unless required by applicable law
// or agreed to in writing, software, hardware and materials distributed under
// this License is distributed on an “AS IS” BASIS, WITHOUT WARRANTIES OR
// CONDITIONS OF ANY KIND, either express or implied. See the License for the
// specific language governing permissions and limitations under the License.

`define SPI_STD     2'b00
`define SPI_QUAD_TX 2'b01
`define SPI_QUAD_RX 2'b10

module spi_slave_controller
    #(
    parameter DUMMY_CYCLES = 32
    )
    (input logic        sclk,
    input  logic        sys_rstn,
    input  logic        cs,
    output logic        en_quad,
    output logic  [1:0] pad_mode,
    output logic  [7:0] rx_counter,
    output logic        rx_counter_upd,
    input  logic [31:0] rx_data,
    input  logic        rx_data_valid,
    output logic  [7:0] tx_counter,
    output logic        tx_counter_upd,
    output logic [31:0] tx_data,
    output logic        tx_data_valid,
    input  logic        tx_done,
    output logic        ctrl_rd_wr,
    output logic [31:0] ctrl_addr,
    output logic        ctrl_addr_valid,
    output logic [31:0] ctrl_data_rx,
    output logic        ctrl_data_rx_valid,
    input  logic        ctrl_data_rx_ready,
    input  logic [31:0] ctrl_data_tx,
    input  logic        ctrl_data_tx_valid,
    output logic        ctrl_data_tx_ready,
    output logic [15:0] wrap_length
    );

  localparam REG_SIZE = 8;


  enum logic [2:0] {CMD,ADDR,MODE,DATA_TX,DATA_RX,DUMMY,ERROR} state,state_next;

  logic  [7:0] command;

  logic        decode_cmd_comb;

  logic [31:0] addr_reg;
  logic  [7:0] cmd_reg;
  logic  [7:0] mode_reg;
  logic [31:0] data_reg;

  logic        sample_ADDR;
  logic        sample_MODE;
  logic        sample_CMD;
  logic        sample_DATA;

  logic        get_addr;
  logic        wait_dummy;
  logic        get_mode;
  logic        get_data;
  logic        send_data;
  logic        enable_cont;
  logic        enable_regs;
  logic        cmd_error;
  logic  [1:0] reg_sel;
  logic  [REG_SIZE-1:0] reg_data;
  logic        reg_valid;

  logic        ctrl_data_tx_ready_next;
  logic  [7:0] tx_counter_next;
  logic        tx_counter_upd_next;
  logic        tx_data_valid_next;
  logic        tx_done_reg;
  logic  [1:0] pad_mode_next;

  logic  [7:0] s_dummy_cycles;

  assign command = decode_cmd_comb ? rx_data : cmd_reg;

  spi_slave_cmd_parser u_cmd_parser(
      .cmd(command),
      .get_addr(get_addr),
      .get_mode(get_mode),
      .get_data(get_data),
      .send_data(send_data),
      .wait_dummy(wait_dummy),
      .enable_cont(enable_cont),
      .enable_regs(enable_regs),
      .error(cmd_error),
      .reg_sel(reg_sel)
      );

  spi_slave_regs #(
      .REG_SIZE(REG_SIZE)
    ) u_spiregs(
      .sclk(sclk),
      .rstn(sys_rstn),
      .wr_data(rx_data[REG_SIZE-1:0]),
      .wr_addr(reg_sel),
      .wr_data_valid(reg_valid),
      .rd_data(reg_data),
      .rd_addr(reg_sel),
      .dummy_cycles(s_dummy_cycles),
      .en_qpi(en_quad),
      .wrap_length(wrap_length)
      );
  always_comb
  begin
    pad_mode  = en_quad ? `SPI_QUAD_RX : `SPI_STD;
    rx_counter     = 8'h1F;
    rx_counter_upd = 0;
    tx_counter_next     = 8'h1F;
    tx_counter_upd_next = 0;
    decode_cmd_comb = 1'b0;
    sample_ADDR     = 1'b0;
    sample_MODE     = 1'b0;
    sample_CMD      = 1'b0;
    sample_DATA     = 1'b0;
    ctrl_data_rx_valid = 1'b0;
    ctrl_data_tx_ready_next = 1'b0;
    reg_valid       = 1'b0;
    tx_data_valid_next   = 1'b0;
    state_next           = state;
    case(state)
      CMD:
      begin
        pad_mode  = en_quad ? `SPI_QUAD_RX : `SPI_STD;
        decode_cmd_comb = 1'b1;
        ctrl_data_tx_ready_next = 1'b1; //empty TX fifo if not allready empty
        if(rx_data_valid)
        begin
          sample_CMD = 1'b1;
          if (get_addr)
          begin
            state_next     = ADDR;
            rx_counter_upd = 1;
            rx_counter     = en_quad ? 8'h7 : 8'h1F;
          end
          else if (get_data)
          begin
            state_next     = DATA_RX;
            rx_counter_upd = 1;
            if (enable_regs)
              rx_counter     = en_quad ? 8'h1 : 8'h7;
          end
          else
          begin
            state_next     = DATA_TX;
            tx_counter_upd_next = 1;
            tx_data_valid_next   = 1'b1;
            tx_counter_next     = en_quad ? 8'h7 : 8'h1F;
            if (~enable_regs)
              ctrl_data_tx_ready_next = 1'b1;
          end
        end
        else
        begin
          state_next = CMD;
        end
      end
      ADDR:
      begin
        pad_mode  = en_quad ? `SPI_QUAD_RX : `SPI_STD;
                ctrl_data_tx_ready_next = 1'b1;
        if(rx_data_valid)
        begin
          sample_ADDR     = 1'b1;
          if (wait_dummy)
          begin
            state_next     = DUMMY;
            rx_counter     = s_dummy_cycles;
            rx_counter_upd = 1;
          end
          else if (send_data)
          begin
            state_next     = DATA_TX;
            tx_counter_upd_next = 1;
            tx_counter_next     = en_quad ? 8'h7 : 8'h1F;
          end
          else if (get_data)
          begin
            state_next     = DATA_RX;
            rx_counter_upd = 1;
            rx_counter     = en_quad ? 8'h7 : 8'h1F;
          end
        end
        else
        begin
          state_next = ADDR;
        end
      end
      MODE:
      begin
        pad_mode  = en_quad ? `SPI_QUAD_RX : `SPI_STD;
        if(rx_data_valid)
        begin
          if (wait_dummy)
          begin
            state_next = DUMMY;
            rx_counter     = DUMMY_CYCLES;
            rx_counter_upd = 1;
          end
          else if (get_data)
          begin
            state_next     = DATA_RX;
            rx_counter     = en_quad ? 8'h7 : 8'h1F;
            rx_counter_upd = 1;
          end
          else if (send_data)
          begin
            state_next     = DATA_TX;
            tx_counter_next     = en_quad ? 8'h7 : 8'h1F;
            tx_counter_upd_next = 1;
            tx_data_valid_next   = 1'b1;
            if (~enable_regs)
              ctrl_data_tx_ready_next = 1'b1;
          end
        end
        else
        begin
          state_next = MODE;
        end
      end
      DUMMY:
      begin
        pad_mode  = en_quad ? `SPI_QUAD_RX : `SPI_STD;
        if(rx_data_valid)
        begin
          if (get_data)
          begin
            state_next     = DATA_RX;
            rx_counter     = en_quad ? 8'h7 : 8'h1F;
            rx_counter_upd = 1;
          end
          else
          begin
            if (en_quad)
              pad_mode_next  = `SPI_QUAD_TX;
            state_next     = DATA_TX;
            tx_counter_next     = en_quad ? 8'h7 : 8'h1F;
            tx_counter_upd_next = 1;
            tx_data_valid_next   = 1'b1;
            if (~enable_regs)
              ctrl_data_tx_ready_next = 1'b1;
          end
        end
        else
        begin
          state_next     = DUMMY;
        end
      end
      DATA_RX:
      begin
        pad_mode  = en_quad ? `SPI_QUAD_RX : `SPI_STD;
        if(rx_data_valid)
        begin
          if (enable_regs)
            reg_valid = 1'b1;
          else
            ctrl_data_rx_valid = 1'b1;
          if (enable_cont)
          begin
            state_next     = DATA_RX;
            rx_counter     = en_quad ? 8'h7 : 8'h1F;
            rx_counter_upd = 1;
          end
          else
          begin
            state_next     = CMD;
            rx_counter     = en_quad ? 8'h1 : 8'h7;
            rx_counter_upd = 1;
          end
        end
        else
        begin
          state_next     = DATA_RX;
        end
      end
      DATA_TX:
      begin
        pad_mode  = en_quad ? `SPI_QUAD_TX : `SPI_STD;
        if(tx_done_reg)
        begin
          if (enable_cont)
          begin
            state_next     = DATA_TX;
            tx_counter_next     = en_quad ? 8'h7 : 8'h1F;
            tx_counter_upd_next = 1;
            tx_data_valid_next   = 1'b1;
            if (~enable_regs)
              ctrl_data_tx_ready_next = 1'b1;
          end
          else
          begin
            state_next     = CMD;
            rx_counter     = en_quad ? 8'h1 : 8'h7;
            rx_counter_upd = 1;
          end
        end
        else
        begin
          state_next     = DATA_TX;
        end
      end
      ERROR:
      begin
        state_next = ERROR;
      end
    endcase
  end


  always @(posedge sclk or posedge cs)
  begin
    if (cs == 1'b1)
    begin
      state <= CMD;
    end
    else
    begin
      state <= state_next;
    end
  end

  always @(posedge sclk or posedge cs)
  begin
    if (cs == 1'b1)
    begin
      addr_reg    = 'h0;
      mode_reg    = 'h0;
      data_reg    = 'h0;
      cmd_reg     = 'h0;
      tx_done_reg = 1'b0;
      ctrl_addr_valid = 1'b0;
      tx_counter_upd  = 1'b0;
      tx_data_valid   = 1'b0;
      ctrl_data_tx_ready = 1'b0;
      tx_counter      =  'h0;
      tx_data         =  'h0;
    end
    else
    begin
      if (sample_ADDR) addr_reg = rx_data;
      if (sample_MODE) mode_reg = rx_data[7:0];
      if (sample_CMD)  cmd_reg  = rx_data[7:0];
      if (sample_DATA) data_reg = rx_data;
      ctrl_addr_valid = sample_ADDR;
      tx_counter_upd  = tx_counter_upd_next;
      tx_counter      = tx_counter_next;
      tx_data_valid   = tx_data_valid_next;
      tx_done_reg     = tx_done;
      ctrl_data_tx_ready = ctrl_data_tx_ready_next;
      tx_data      = (enable_regs) ? reg_data : ctrl_data_tx;
    end
  end

    assign ctrl_data_rx = rx_data;
    assign ctrl_addr    = addr_reg;
    assign ctrl_rd_wr   = send_data;

endmodule
