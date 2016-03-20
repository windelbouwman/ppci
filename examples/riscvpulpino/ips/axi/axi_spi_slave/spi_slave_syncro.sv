// Copyright 2015 ETH Zurich and University of Bologna.
// Copyright and related rights are licensed under the Solderpad Hardware
// License, Version 0.51 (the “License”); you may not use this file except in
// compliance with the License.  You may obtain a copy of the License at
// http://solderpad.org/licenses/SHL-0.51. Unless required by applicable law
// or agreed to in writing, software, hardware and materials distributed under
// this License is distributed on an “AS IS” BASIS, WITHOUT WARRANTIES OR
// CONDITIONS OF ANY KIND, either express or implied. See the License for the
// specific language governing permissions and limitations under the License.

module spi_slave_syncro
    #(
    parameter AXI_ADDR_WIDTH = 32
    )
    (
    input  logic                       sys_clk,
    input  logic                       rstn,
    input  logic                       cs,
    input  logic [AXI_ADDR_WIDTH-1:0]  address,
    input  logic                       address_valid,
    input  logic                       rd_wr,
    output logic                       cs_sync,
    output logic [AXI_ADDR_WIDTH-1:0]  address_sync,
    output logic                       address_valid_sync,
    output logic                       rd_wr_sync
    );

  logic [1:0] cs_reg;
  logic [2:0] valid_reg;
  logic [1:0] rdwr_reg;

  assign cs_sync = cs_reg[1];
  assign address_valid_sync = ~valid_reg[2] & valid_reg[1]; //detect rising edge of addr valid
  assign address_sync = address;
  assign rd_wr_sync = rdwr_reg[1];

  always @(posedge sys_clk or negedge rstn)
  begin
    if(rstn == 1'b0)
    begin
      cs_reg     <=  2'b11;
      valid_reg  <=  3'b000;
      rdwr_reg   <=  2'b00;
    end
    else
    begin
      cs_reg     <= {cs_reg[0],cs};
      valid_reg  <= {valid_reg[1:0],address_valid};
      rdwr_reg   <= {rdwr_reg[0],rd_wr};
    end
  end

endmodule
