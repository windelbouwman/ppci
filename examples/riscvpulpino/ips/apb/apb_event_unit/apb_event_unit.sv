// Copyright 2015 ETH Zurich and University of Bologna.
// Copyright and related rights are licensed under the Solderpad Hardware
// License, Version 0.51 (the “License”); you may not use this file except in
// compliance with the License.  You may obtain a copy of the License at
// http://solderpad.org/licenses/SHL-0.51. Unless required by applicable law
// or agreed to in writing, software, hardware and materials distributed under
// this License is distributed on an “AS IS” BASIS, WITHOUT WARRANTIES OR
// CONDITIONS OF ANY KIND, either express or implied. See the License for the
// specific language governing permissions and limitations under the License.

`include "defines_event_unit.sv"

module apb_event_unit
#(
    parameter APB_ADDR_WIDTH = 12  //APB slaves are 4KB by default
)
(
    input  logic                      clk_i, //clk bypass for synch ff
    input  logic                      HCLK,
    input  logic                      HRESETn,
    input  logic [APB_ADDR_WIDTH-1:0] PADDR,
    input  logic               [31:0] PWDATA,
    input  logic                      PWRITE,
    input  logic                      PSEL,
    input  logic                      PENABLE,
    output logic               [31:0] PRDATA,
    output logic                      PREADY,
    output logic                      PSLVERR,

    // irq processing
    input  logic               [31:0] irq_i,
    input  logic               [31:0] event_i,
    output logic               [31:0] irq_o,

    // Sleep control
    input  logic                      fetch_enable_i,
    output logic                      fetch_enable_o,
    output logic                      clk_gate_core_o, // output to core's clock gate to
    input  logic                      core_busy_i
);

logic [31:0] events;

// one hot encoding
logic [2:0] psel_int, pready, pslverr;

logic [1:0] slave_address_int;
// output, internal wires
logic [2:0] [31:0] prdata;

logic fetch_enable_ff1, fetch_enable_ff2, fetch_enable_int;

assign fetch_enable_o =  fetch_enable_ff2 & fetch_enable_int;

assign slave_address_int = PADDR[`ADR_MAX_ADR + `REGS_MAX_ADR + 1:`REGS_MAX_ADR + 2];

// address selector - select right peripheral
always_comb
begin
    psel_int = 3'b0;
    psel_int[slave_address_int] = PSEL;
end

// output mux
always_comb
begin

    if (psel_int != 2'b00)
    begin
        PRDATA = prdata[slave_address_int];
        PREADY = pready[slave_address_int];
        PSLVERR = pslverr[slave_address_int];
    end
    else
    begin
        PRDATA = 'b0;
        PREADY = 1'b1;
        PSLVERR = 1'b0;
    end
end

// interrupt unit
generic_service_unit
#(
    .APB_ADDR_WIDTH(APB_ADDR_WIDTH)  //APB slaves are 4KB by default
)
i_interrupt_unit
(
    .HCLK               (HCLK),
    .HRESETn            (HRESETn),
    .PADDR              (PADDR),
    .PWDATA             (PWDATA),
    .PWRITE             (PWRITE),
    .PSEL               (psel_int[0]),
    .PENABLE            (PENABLE),
    .PRDATA             (prdata[0]),
    .PREADY             (pready[0]),
    .PSLVERR            (pslverr[0]),

    .signal_i           (irq_i), // generic signal could be an interrupt or an event
    .irq_o              (irq_o)
);


// event unit
generic_service_unit
#(
    .APB_ADDR_WIDTH(APB_ADDR_WIDTH)  //APB slaves are 4KB by default
)
i_event_unit
(
    .HCLK               (HCLK),
    .HRESETn            (HRESETn),
    .PADDR              (PADDR),
    .PWDATA             (PWDATA),
    .PWRITE             (PWRITE),
    .PSEL               (psel_int[1]),
    .PENABLE            (PENABLE),
    .PRDATA             (prdata[1]),
    .PREADY             (pready[1]),
    .PSLVERR            (pslverr[1]),

    .signal_i           (event_i), // generic signal could be an interrupt or an event
    .irq_o              (events )
);


// sleep unit
sleep_unit
#(
    .APB_ADDR_WIDTH(APB_ADDR_WIDTH)  //APB slaves are 4KB by default
)
i_sleep_unit
(
    .HCLK               (HCLK),
    .HRESETn            (HRESETn),
    .PADDR              (PADDR),
    .PWDATA             (PWDATA),
    .PWRITE             (PWRITE),
    .PSEL               (psel_int[2]),
    .PENABLE            (PENABLE),
    .PRDATA             (prdata[2]),
    .PREADY             (pready[2]),
    .PSLVERR            (pslverr[2]),

    .signal_i           (|(irq_o || events)), // interrupt/event signal - for sleep ctrl
    .core_busy_i        (core_busy_i), // check if core is busy
    .fetch_en_o         (fetch_enable_int),
    .clk_gate_core_o    (clk_gate_core_o) // output to core's clock gate to
                                            //signal in order to give the core enough time after wakeup to catch the signal
);

// fetch enable synchronizer part
always_ff @(posedge clk_i, negedge HRESETn)
begin
    if(~HRESETn)
    begin
        fetch_enable_ff1   <= 1'b0;
        fetch_enable_ff2   <= 1'b0;
    end
    else
    begin
        fetch_enable_ff1  <= fetch_enable_i;
        fetch_enable_ff2  <= fetch_enable_ff1;
    end

end

endmodule
