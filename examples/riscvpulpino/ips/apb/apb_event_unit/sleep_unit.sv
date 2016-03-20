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

module sleep_unit
#(
    parameter APB_ADDR_WIDTH = 12  //APB slaves are 4KB by default
)
(
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

    input  logic                      signal_i, // interrupt or event signal
    input  logic                      core_busy_i, // check if core is busy
    output logic                      fetch_en_o,
    output logic                      clk_gate_core_o // output to core's clock gate - blocking the clock when low
);

    enum    logic[1:0]      {RUN, SHUTDOWN, SLEEP} SLEEP_STATE_N, SLEEP_STATE_Q;
    // registers
    logic [0:`REGS_SLEEP_MAX_IDX] [31:0]  regs_q, regs_n;

    ////////////////////////////////
    //   _____ _                  //
    //  / ____| |                 //
    // | (___ | | ___  ___ _ __   //
    //  \___ \| |/ _ \/ _ \ '_ \  //
    //  ____) | |  __/  __/ |_) | //
    // |_____/|_|\___|\___| .__/  //
    //                    | |     //
    //                    |_|     //
    //                            //
    ////////////////////////////////

    logic core_sleeping_int;

    // next state logic
    always_comb
    begin
        SLEEP_STATE_N = SLEEP_STATE_Q;

        case(SLEEP_STATE_Q)

            RUN:
            begin
                // if sleep is enforced by writing one to the sleep control register
                // and currently no interrupt/event is pending
                if (regs_q[`REG_SLEEP_CTRL][`SLEEP_ENABLE] && !signal_i)
                    SLEEP_STATE_N = SHUTDOWN;
            end

            // wait for shutdown
            SHUTDOWN:
            begin
                // if an interrupt occured while waiting - switch back to running
                if (signal_i)
                    SLEEP_STATE_N = RUN;
                // if no interrupt occured and the core has finished processing go to sleep
                else if (~core_busy_i)
                    SLEEP_STATE_N = SLEEP;

            end

            SLEEP:
            begin
                // wake up when an interrupt is present
                if (signal_i)
                    SLEEP_STATE_N = RUN;
            end

            default:
                SLEEP_STATE_N = RUN;
        endcase

    end

    // output logic
    always_comb
    begin
        fetch_en_o = 1'b1;
        clk_gate_core_o = 1'b1;
        core_sleeping_int = 1'b0;

        unique case(SLEEP_STATE_Q)

            RUN:
            begin
                // try to go to sleep immediately - necessary if wfi is called
                // directly after setting the sleep register.
                if (regs_q[`REG_SLEEP_CTRL][`SLEEP_ENABLE] && !signal_i)
                    fetch_en_o = 1'b0;
                else
                    fetch_en_o = 1'b1;
            end
            SHUTDOWN:
            begin
                // stop fetching instructions and wait until the core has finished processing
                fetch_en_o = 1'b0;
            end
            SLEEP:
            begin
                // switch off core clock
                clk_gate_core_o = (signal_i) ? 1'b1 : 1'b0;
                core_sleeping_int = 1'b1;
            end

            default:
            begin
                fetch_en_o = 1'b1;
                clk_gate_core_o = 1'b1;
                core_sleeping_int = 1'b0;
            end
        endcase

    end

    /////////////////////////////
    //           _____  ____   //
    //     /\   |  __ \|  _ \  //
    //    /  \  | |__) | |_) | //
    //   / /\ \ |  ___/|  _ <  //
    //  / ____ \| |    | |_) | //
    // /_/    \_\_|    |____/  //
    //                         //
    /////////////////////////////

    // APB register interface
    logic [`REGS_SLEEP_MAX_IDX-1:0]       register_adr;
    assign register_adr = PADDR[`REGS_SLEEP_MAX_IDX + 2:2];

    // APB logic: we are always ready to capture the data into our regs
    // not supporting transfare failure
    assign PREADY = 1'b1;
    assign PSLVERR = 1'b0;

    // register write logic
    always_comb
    begin
        regs_n = regs_q;

        // update sleeping status register
        regs_n[`REG_SLEEP_STATUS][`SLEEP_STATUS] = core_sleeping_int;

        // clear ctrl bit if core is asleep or an interrupt/event is present
        if (core_sleeping_int || signal_i)
            regs_n[`REG_SLEEP_CTRL][`SLEEP_ENABLE] =  1'b0;

        // written from APB bus
        if (PSEL && PENABLE && PWRITE)
        begin

            case (register_adr)
                `REG_SLEEP_CTRL:
                    regs_n[`REG_SLEEP_CTRL] = PWDATA;

                // can't write sleeping status reg
            endcase
        end


    end

    // register read logic
    always_comb
    begin
        PRDATA = 'b0;

        if (PSEL && PENABLE && !PWRITE)
        begin

            case (register_adr)
                `REG_SLEEP_CTRL:
                    PRDATA = regs_q[`REG_SLEEP_CTRL];

                `REG_SLEEP_STATUS:
                    PRDATA = regs_q[`REG_SLEEP_STATUS];

                default:
                    PRDATA = 'b0;
            endcase
        end
    end



    // synchronouse part
    always_ff @(posedge HCLK, negedge HRESETn)
    begin
        if(~HRESETn)
        begin
            SLEEP_STATE_Q   <= RUN;
            regs_q          <= '{default: 32'b0};

        end
        else
        begin
            SLEEP_STATE_Q   <= SLEEP_STATE_N;
            regs_q          <= regs_n;
        end

    end

endmodule
