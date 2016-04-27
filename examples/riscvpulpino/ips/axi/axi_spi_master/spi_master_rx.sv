// Copyright 2015 ETH Zurich and University of Bologna.
// Copyright and related rights are licensed under the Solderpad Hardware
// License, Version 0.51 (the “License”); you may not use this file except in
// compliance with the License.  You may obtain a copy of the License at
// http://solderpad.org/licenses/SHL-0.51. Unless required by applicable law
// or agreed to in writing, software, hardware and materials distributed under
// this License is distributed on an “AS IS” BASIS, WITHOUT WARRANTIES OR
// CONDITIONS OF ANY KIND, either express or implied. See the License for the
// specific language governing permissions and limitations under the License.

module spi_master_rx
(
    input  logic        clk,
    input  logic        rstn,
    input  logic        en,
    input  logic        rx_edge,
    output logic        rx_done,
    input  logic        sdi0,
    input  logic        sdi1,
    input  logic        sdi2,
    input  logic        sdi3,
    input  logic        en_quad_in,
    input  logic [15:0] counter_in,
    input  logic        counter_in_upd,
    output logic [31:0] data,
    output logic        data_valid
);

    logic [31:0] data_int;
    logic [31:0] data_int_next;
    logic [15:0] counter;
    logic [15:0] counter_trgt;
    logic [15:0] counter_next;
    logic [15:0] counter_trgt_next;
    logic        done;

    assign data = data_int_next;
    assign data_valid = rx_edge & (done | (en & (~en_quad_in & (counter[4:0] == 5'b11111)) | (en_quad_in & (counter[2:0] == 3'b111))));
    assign rx_done = done;

    always_comb
    begin
        if (counter_in_upd)
            counter_trgt_next = (en_quad_in) ? {2'b00,counter_in[15:2]} : counter_in;
        else
            counter_trgt_next = counter_trgt;

        if (counter == counter_trgt-1)
            done = 1'b1 & rx_edge;
        else
            done = 1'b0;

        if (rx_edge)
            if (counter == counter_trgt-1)
                counter_next = 0;
            else if (en)
                    counter_next = counter + 1;
                 else
                    counter_next = counter;
        else
            counter_next = counter;


        if (rx_edge)
        begin
            if (en_quad_in)
                data_int_next = {data_int[27:0],sdi3,sdi2,sdi1,sdi0};
            else
                data_int_next = {data_int[30:0],sdi0};
        end
        else
        begin
            data_int_next = data_int;
        end
    end


    always_ff @(posedge clk, negedge rstn)
    begin
        if (rstn == 0)
        begin
            counter      <= 0;
            counter_trgt <= 'h8;
            data_int     <= 'h0;
        end
        else
        begin
            counter      <= counter_next;
            counter_trgt <= counter_trgt_next;
            data_int     <= data_int_next;
        end
    end




endmodule


