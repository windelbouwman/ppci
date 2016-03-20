// Copyright 2015 ETH Zurich and University of Bologna.
// Copyright and related rights are licensed under the Solderpad Hardware
// License, Version 0.51 (the “License”); you may not use this file except in
// compliance with the License.  You may obtain a copy of the License at
// http://solderpad.org/licenses/SHL-0.51. Unless required by applicable law
// or agreed to in writing, software, hardware and materials distributed under
// this License is distributed on an “AS IS” BASIS, WITHOUT WARRANTIES OR
// CONDITIONS OF ANY KIND, either express or implied. See the License for the
// specific language governing permissions and limitations under the License.

module spi_slave_tx
(
    input  logic        test_mode,
    input  logic        sclk,
    input  logic        cs,
    output logic        sdo0,
    output logic        sdo1,
    output logic        sdo2,
    output logic        sdo3,
    input  logic        en_quad_in,
    input  logic  [7:0] counter_in,
    input  logic        counter_in_upd,
    input  logic [31:0] data,
    input  logic        data_valid,
    output logic        done
);

    reg [31:0] data_int;
    reg [31:0] data_int_next;
    reg  [7:0] counter;
    reg  [7:0] counter_trgt;
    reg  [7:0] counter_next;
    reg  [7:0] counter_trgt_next;
    logic running;
    logic running_next;

    logic sclk_inv;
    logic sclk_test;

    assign sdo0 = (en_quad_in) ? data_int[28] : data_int[31];
    assign sdo1 = (en_quad_in) ? data_int[29] : 1'b0;
    assign sdo2 = (en_quad_in) ? data_int[30] : 1'b0;
    assign sdo3 = (en_quad_in) ? data_int[31] : 1'b0;

    always_comb
    begin
        done = 1'b0;
        if (counter_in_upd)
                counter_trgt_next = counter_in;
        else
                counter_trgt_next = counter_trgt;

        if (counter_in_upd)
                running_next = 1'b1;
        else if (counter == counter_trgt)
                running_next = 1'b0;
        else
                running_next = running;

        if (running || counter_in_upd)
        begin
                if (counter == counter_trgt)
                begin
                        done = 1'b1;
                        counter_next = 0;
                end
                else
                        counter_next = counter + 1;

                if (data_valid)
                        data_int_next = data;
                else
                begin
                        if (en_quad_in)
                                data_int_next = {data_int[27:0],4'b0000};
                        else
                                data_int_next = {data_int[30:0],1'b0};
                end
        end
        else
        begin
                counter_next  = counter;
                data_int_next = data_int;
        end
    end

    pulp_clock_inverter clk_inv_i
    (
        .clk_i(sclk),
        .clk_o(sclk_inv)
    );

    pulp_clock_mux2 clk_mux_i
    (
        .clk0_i(sclk_inv),
        .clk1_i(sclk),
        .clk_sel_i(test_mode),
        .clk_o(sclk_test)
    );

    always @(posedge sclk_test or posedge cs)
    begin
        if (cs == 1'b1)
        begin
            counter      = 'h0;
            counter_trgt = 'h7;
            data_int     = 'h0;
            running      = 1'b0;
        end
        else
        begin
            counter      = counter_next;
            counter_trgt = counter_trgt_next;
            data_int     = data_int_next;
            running      = running_next;
        end
    end
endmodule
