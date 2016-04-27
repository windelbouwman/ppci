// Copyright 2015 ETH Zurich and University of Bologna.
// Copyright and related rights are licensed under the Solderpad Hardware
// License, Version 0.51 (the “License”); you may not use this file except in
// compliance with the License.  You may obtain a copy of the License at
// http://solderpad.org/licenses/SHL-0.51. Unless required by applicable law
// or agreed to in writing, software, hardware and materials distributed under
// this License is distributed on an “AS IS” BASIS, WITHOUT WARRANTIES OR
// CONDITIONS OF ANY KIND, either express or implied. See the License for the
// specific language governing permissions and limitations under the License.

module dc_data_buffer(clk, rstn, write_pointer, write_data, read_pointer, read_data);

    parameter DATA_WIDTH   = 32;
    parameter BUFFER_DEPTH = 8;

    `ifndef PULP_FPGA_EMUL
        function integer log2(input integer value);
        begin
            value = value - 1;
            for (log2 = 0; value > 0; log2 = log2 + 1)
                value = value >> 1;
        end
        endfunction
        `define log2(N) log2(N)
    `else
        `define log2(N) ((N)<=(1) ? 0 : (N)<=(2) ? 1 : (N)<=(4) ? 2 : (N)<=(8) ? 3 : (N)<=(16) ? 4 : (N)<=(32) ? 5 : (N)<=(64) ? 6 : (N)<=(128) ? 7 : (N)<=(256) ? 8 : (N)<=(512) ? 9 : (N)<=(1024) ? 10 : -1)
    `endif

    input                          clk;
    input                          rstn;

    input  [BUFFER_DEPTH - 1 : 0]  write_pointer;
    input  [DATA_WIDTH - 1 : 0]    write_data;
    input  [BUFFER_DEPTH - 1 : 0]  read_pointer;
    output [DATA_WIDTH - 1 : 0]    read_data;

    reg [DATA_WIDTH - 1 : 0]       data[BUFFER_DEPTH - 1 : 0];

    integer loop;

    always @(posedge clk  or negedge rstn)
    begin: read_write_data
        if (rstn == 1'b0)
            for (loop = 0; loop < BUFFER_DEPTH; loop = loop + 1)
                data[loop] <= 'h0;
        else
            data[`log2(write_pointer)] <= write_data;
    end

    assign read_data = data[`log2(read_pointer)];

endmodule
