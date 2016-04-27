//-----------------------------------------------------------------
//                           AltOR32 
//                Alternative Lightweight OpenRisc 
//                            V2.0
//                     Ultra-Embedded.com
//                   Copyright 2011 - 2013
//
//               Email: admin@ultra-embedded.com
//
//                       License: LGPL
//-----------------------------------------------------------------
//
// Copyright (C) 2011 - 2013 Ultra-Embedded.com
//
// This source file may be used and distributed without         
// restriction provided that this copyright statement is not    
// removed from the file and that any derivative work contains  
// the original copyright notice and the associated disclaimer. 
//
// This source file is free software; you can redistribute it   
// and/or modify it under the terms of the GNU Lesser General   
// Public License as published by the Free Software Foundation; 
// either version 2.1 of the License, or (at your option) any   
// later version.
//
// This source is distributed in the hope that it will be       
// useful, but WITHOUT ANY WARRANTY; without even the implied   
// warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR      
// PURPOSE.  See the GNU Lesser General Public License for more 
// details.
//
// You should have received a copy of the GNU Lesser General    
// Public License along with this source; if not, write to the 
// Free Software Foundation, Inc., 59 Temple Place, Suite 330, 
// Boston, MA  02111-1307  USA
//-----------------------------------------------------------------

//-----------------------------------------------------------------
// Includes
//-----------------------------------------------------------------
`include "uart_defs.v"

//-----------------------------------------------------------------
// Module:
//-----------------------------------------------------------------
module uart_periph
(
    // General - Clocking & Reset
    input               clk_i /*verilator public*/,
    input               rst_i /*verilator public*/,
    output              intr_o /*verilator public*/,

    // UART
    output              tx_o /*verilator public*/,
    input               rx_i /*verilator public*/,

    // Peripheral bus
    input [7:0]         addr_i /*verilator public*/,
    output reg [31:0]   data_o /*verilator public*/,
    input [31:0]        data_i /*verilator public*/,
    input               we_i /*verilator public*/,
    input               stb_i /*verilator public*/
);

//-----------------------------------------------------------------
// Params
//-----------------------------------------------------------------
parameter           UART_DIVISOR        = 1;

//-----------------------------------------------------------------
// Registers / Wires
//-----------------------------------------------------------------
reg [7:0]   uart_tx_data_q;
wire [7:0]  uart_rx_data_w;
reg         uart_wr_q;
reg         uart_rd_q;
wire        uart_tx_busy_w;
wire        uart_rx_ready_w;
wire        uart_break_w;

//-----------------------------------------------------------------
// Instantiation
//-----------------------------------------------------------------

// UART
uart
#(
    .UART_DIVISOR(UART_DIVISOR)
)
u1_uart
(
    .clk_i(clk_i),
    .rst_i(rst_i),
    .data_i(uart_tx_data_q),
    .data_o(uart_rx_data_w),
    .wr_i(uart_wr_q),
    .rd_i(uart_rd_q),
    .tx_busy_o(uart_tx_busy_w),
    .rx_ready_o(uart_rx_ready_w),
    .break_o(uart_break_w),
    .rxd_i(rx_i),
    .txd_o(tx_o)
);

//-----------------------------------------------------------------
// Peripheral Register Write
//-----------------------------------------------------------------
always @ (posedge rst_i or posedge clk_i )
begin
   if (rst_i == 1'b1)
   begin
       uart_tx_data_q     <= 8'h00;
       uart_wr_q          <= 1'b0;
   end
   else
   begin
       uart_wr_q          <= 1'b0;

       // Write Cycle
       if (we_i & stb_i)
       begin
           case (addr_i)

           `UART_UDR :
           begin
               uart_tx_data_q   <= data_i[7:0];
               uart_wr_q        <= 1'b1;
               `ifdef VERMON
                   $write("%c",data_i[7:0]);
	       `endif                   
           end

           default :
               ;
           endcase
        end
   end
end

//-----------------------------------------------------------------
// Peripheral Register Read
//-----------------------------------------------------------------
always @ *
begin
   data_o = 32'h00000000;

   case (addr_i[7:0])

   `UART_USR :
   begin
        data_o[`UART_USR_RX_AVAIL] = uart_rx_ready_w;
        data_o[`UART_USR_TX_BUSY]  = uart_tx_busy_w;
   end
   `UART_UDR :
        data_o[7:0] = uart_rx_data_w;

   default :
        data_o = 32'h00000000;
   endcase
end

always @ (posedge rst_i or posedge clk_i )
begin
   if (rst_i == 1'b1)
   begin
       uart_rd_q        <= 1'b0;
   end
   else
   begin
       // Read UART data register?
       if (!we_i && stb_i && (addr_i[7:0] == `UART_UDR))
          uart_rd_q <= 1'b1;
       else
          uart_rd_q <= 1'b0;
   end
end

//-----------------------------------------------------------------
// Assignments
//-----------------------------------------------------------------
assign intr_o      = uart_rx_ready_w;

endmodule
