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
// Module:
//-----------------------------------------------------------------
module uart
(
    // Clock & Reset
    clk_i,
    rst_i,
    // Status
    tx_busy_o,
    rx_ready_o,
    break_o,
    // Data
    data_i,
    wr_i,
    data_o,
    rd_i,
    // UART pins
    rxd_i,
    txd_o
);
//-----------------------------------------------------------------
// Params
//-----------------------------------------------------------------
parameter  [31:0]    UART_DIVISOR = 278;

//-----------------------------------------------------------------
// I/O
//-----------------------------------------------------------------
input               clk_i /*verilator public*/;
input               rst_i /*verilator public*/;
input [7:0]         data_i /*verilator public*/;
output [7:0]        data_o /*verilator public*/;
input               wr_i /*verilator public*/;
input               rd_i /*verilator public*/;
output              tx_busy_o /*verilator public*/;
output              rx_ready_o /*verilator public*/;
output              break_o /*verilator public*/;
input               rxd_i /*verilator public*/;
output              txd_o /*verilator public*/;

//-----------------------------------------------------------------
// Registers
//-----------------------------------------------------------------
parameter           FULL_BIT = UART_DIVISOR;
parameter           HALF_BIT = (FULL_BIT / 2);

// TX Signals
reg [7:0]           tx_buf;
reg                 tx_buf_full;
reg                 tx_busy;
reg [3:0]           tx_bits;
integer             tx_count;
reg [7:0]           tx_shift_reg;
reg                 txd_o;

// RX Signals
reg                 i_rxd;
reg [7:0]           data_o;
reg [3:0]           rx_bits;
integer             rx_count;
reg [7:0]           rx_shift_reg;
reg                 rx_ready_o;
reg                 break_o;

//-----------------------------------------------------------------
// Re-sync RXD
//-----------------------------------------------------------------
always @ (posedge rst_i or posedge clk_i )
begin
   if (rst_i == 1'b1)
       i_rxd <= 1'b1;
   else
       i_rxd <= rxd_i;
end

//-----------------------------------------------------------------
// RX Process
//-----------------------------------------------------------------
always @ (posedge clk_i or posedge rst_i )
begin
   if (rst_i == 1'b1)
   begin
       rx_bits      <= 0;
       rx_count     <= 0;
       rx_ready_o   <= 1'b0;
       rx_shift_reg <= 8'h00;
       data_o       <= 8'h00;
       break_o      <= 1'b0;
   end
   else
   begin

       // If reading data, reset data ready state
       if (rd_i == 1'b1)
           rx_ready_o <= 1'b0;

       // Rx bit timer
       if (rx_count != 0)
           rx_count    <= (rx_count - 1);
       else
       begin
           //-------------------------------
           // Start bit detection
           //-------------------------------
           if (rx_bits == 0)
           begin
               break_o  <= 1'b0;

               // If RXD low, check again in half bit time
               if (i_rxd == 1'b0)
               begin
                   rx_count <= HALF_BIT;
                   rx_bits  <= 1;
               end
           end
           //-------------------------------
           // Start bit (mid bit time point)
           //-------------------------------
           else if (rx_bits == 1)
           begin
               // RXD should still be low at mid point of bit period
               if (i_rxd == 1'b0)
               begin
                   rx_count     <= FULL_BIT;
                   rx_bits      <= rx_bits + 1'b1;
                   rx_shift_reg <= 8'h00;
               end
               // Start bit not still low, reset RX process
               else
               begin
                   rx_bits      <= 0;
               end
           end
           //-------------------------------
           // Stop bit
           //-------------------------------
           else if (rx_bits == 10)
           begin
               // RXD should be still high
               if (i_rxd == 1'b1)
               begin
                   rx_count     <= 0;
                   rx_bits      <= 0;
                   data_o       <= rx_shift_reg;
                   rx_ready_o   <= 1'b1;
               end
               // Bad Stop bit - wait for a full bit period
               // before allowing start bit detection again
               else
               begin
                   rx_count     <= FULL_BIT;
                   rx_bits      <= 0;

                   // Interpret this as a break
                   break_o      <= 1'b1;
               end
           end
           //-------------------------------
           // Data bits
           //-------------------------------
           else
           begin
               // Receive data LSB first
               rx_shift_reg[7]  <= i_rxd;
               rx_shift_reg[6:0]<= rx_shift_reg[7:1];
               rx_count         <= FULL_BIT;
               rx_bits          <= rx_bits + 1'b1;
           end
       end
   end
end

//-----------------------------------------------------------------
// TX Process
//-----------------------------------------------------------------
always @ (posedge clk_i or posedge rst_i )
begin
   if (rst_i == 1'b1)
   begin
       tx_count     <= 0;
       tx_bits      <= 0;
       tx_busy      <= 1'b0;
       txd_o        <= 1'b1;
       tx_shift_reg <= 8'h00;
       tx_buf       <= 8'h00;
       tx_buf_full  <= 1'b0;
   end
   else
   begin

       // Buffer data to transmit
       if (wr_i == 1'b1)
       begin
           tx_buf       <= data_i;
           tx_buf_full  <= 1'b1;
       end

       // Tx bit timer
       if (tx_count != 0)
           tx_count     <= (tx_count - 1);
       else
       begin

           //-------------------------------
           // Start bit (TXD = L)
           //-------------------------------
           if (tx_bits == 0)
           begin

               tx_busy <= 1'b0;

               // Data in buffer ready to transmit?
               if (tx_buf_full == 1'b1)
               begin
                   tx_shift_reg <= tx_buf;
                   tx_busy      <= 1'b1;
                   txd_o        <= 1'b0;
                   tx_buf_full  <= 1'b0;
                   tx_bits      <= 1;
                   tx_count     <= FULL_BIT;
               end
           end
           //-------------------------------
           // Stop bit (TXD = H)
           //-------------------------------
           else if (tx_bits == 9)
           begin
               txd_o    <= 1'b1;
               tx_bits  <= 0;
               tx_count <= FULL_BIT;
           end
           //-------------------------------
           // Data bits
           //-------------------------------
           else
           begin
               // Shift data out LSB first
               txd_o            <= tx_shift_reg[0];
               tx_shift_reg[6:0]<= tx_shift_reg[7:1];
               tx_bits          <= tx_bits + 1'b1;
               tx_count         <= FULL_BIT;
           end
        end
    end
end

//-----------------------------------------------------------------
// Combinatorial
//-----------------------------------------------------------------
assign tx_busy_o = (tx_busy | tx_buf_full | wr_i);

endmodule
