// Copyright 2015 ETH Zurich and University of Bologna.
// Copyright and related rights are licensed under the Solderpad Hardware
// License, Version 0.51 (the “License”); you may not use this file except in
// compliance with the License.  You may obtain a copy of the License at
// http://solderpad.org/licenses/SHL-0.51. Unless required by applicable law
// or agreed to in writing, software, hardware and materials distributed under
// this License is distributed on an “AS IS” BASIS, WITHOUT WARRANTIES OR
// CONDITIONS OF ANY KIND, either express or implied. See the License for the
// specific language governing permissions and limitations under the License.

// Address offset: bit [4:2]
`define REG_PAD_MUX      4'b0000
`define REG_CLK_GATE     4'b0001
`define REG_BOOT_ADR     4'b0010
`define REG_INFO         4'b0100
`define REG_STATUS       4'b0101

// GPIO Map - for simplicity
`define REG_PADCFG0     4'b1000 //BASEADDR+0x20
`define REG_PADCFG1     4'b1001 //BASEADDR+0x24
`define REG_PADCFG2     4'b1010 //BASEADDR+0x28
`define REG_PADCFG3     4'b1011 //BASEADDR+0x2C
`define REG_PADCFG4     4'b1100 //BASEADDR+0x30
`define REG_PADCFG5     4'b1101 //BASEADDR+0x34
`define REG_PADCFG6     4'b1110 //BASEADDR+0x38
`define REG_PADCFG7     4'b1111 //BASEADDR+0x3C

// info reg
`define VERSION          5'b00001 // Version number 1.0
`define DATA_RAM         8'b00000100 //size of data ram in multiples of 8 kBye
`define INSTR_RAM        8'b00000100 //size of instr ram in multiples of 8 kBye
`define ROM              5'b00000 // size of ROM in kByte - floor to nearest
`define ICACHE           1'b0 // has instruction cache
`define DCACHE           1'b0 // has data cache
//`define PERIPHERALS      4'b1
module apb_pulpino
#(
    parameter APB_ADDR_WIDTH = 12,  //APB slaves are 4KB by default
    parameter BOOT_ADDR      = 32'h8000
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

    output logic         [31:0] [5:0] pad_cfg_o,
    output logic               [31:0] clk_gate_o,
    output logic               [31:0] pad_mux_o,
    output logic               [31:0] boot_addr_o
);

    logic [31:0]  pad_mux_q, pad_mux_n;
    logic [31:0]  boot_adr_q, boot_adr_n;
    logic [31:0]  clk_gate_q, clk_gate_n;

    logic [31:0] [5:0] pad_cfg_q, pad_cfg_n;

    logic [APB_ADDR_WIDTH - 1:0]       register_adr;

    logic [1:0]   status_n, status_q;

    assign register_adr = PADDR[5:2];

    // directly output registers
    assign pad_mux_o   = pad_mux_q;
    assign clk_gate_o  = clk_gate_q;
    assign pad_cfg_o   = pad_cfg_q;
    assign boot_addr_o = boot_adr_q;

    // register write logic
    always_comb
    begin
        pad_mux_n = pad_mux_q;
        pad_cfg_n = pad_cfg_q;
        clk_gate_n = clk_gate_q;
        boot_adr_n = boot_adr_q;
        status_n   = status_q;

        if (PSEL && PENABLE && PWRITE)
        begin

            case (register_adr)
                `REG_PAD_MUX:
                    pad_mux_n     = PWDATA;

                `REG_CLK_GATE:
                    clk_gate_n    = PWDATA;

                `REG_BOOT_ADR:
                    boot_adr_n     = PWDATA;

                `REG_PADCFG0:
                begin
                    pad_cfg_n[0]  = PWDATA[4:0];
                    pad_cfg_n[1]  = PWDATA[12:8];
                    pad_cfg_n[2]  = PWDATA[20:16];
                    pad_cfg_n[3]  = PWDATA[28:24];
                end
                `REG_PADCFG1:
                begin
                    pad_cfg_n[4]  = PWDATA[4:0];
                    pad_cfg_n[5]  = PWDATA[12:8];
                    pad_cfg_n[6]  = PWDATA[20:16];
                    pad_cfg_n[7]  = PWDATA[28:24];
                end
                `REG_PADCFG2:
                begin
                    pad_cfg_n[8]  = PWDATA[4:0];
                    pad_cfg_n[9]  = PWDATA[12:8];
                    pad_cfg_n[10] = PWDATA[20:16];
                    pad_cfg_n[11] = PWDATA[28:24];
                end
                `REG_PADCFG3:
                begin
                    pad_cfg_n[12] = PWDATA[4:0];
                    pad_cfg_n[13] = PWDATA[12:8];
                    pad_cfg_n[14] = PWDATA[20:16];
                    pad_cfg_n[15] = PWDATA[28:24];
                end
                `REG_PADCFG4:
                begin
                    pad_cfg_n[16] = PWDATA[4:0];
                    pad_cfg_n[17] = PWDATA[12:8];
                    pad_cfg_n[18] = PWDATA[20:16];
                    pad_cfg_n[19] = PWDATA[28:24];
                end
                `REG_PADCFG5:
                begin
                    pad_cfg_n[20] = PWDATA[4:0];
                    pad_cfg_n[21] = PWDATA[12:8];
                    pad_cfg_n[22] = PWDATA[20:16];
                    pad_cfg_n[23] = PWDATA[28:24];
                end
                `REG_PADCFG6:
                begin
                    pad_cfg_n[24] = PWDATA[4:0];
                    pad_cfg_n[25] = PWDATA[12:8];
                    pad_cfg_n[26] = PWDATA[20:16];
                    pad_cfg_n[27] = PWDATA[28:24];
                end
                `REG_PADCFG7:
                begin
                    pad_cfg_n[28]  = PWDATA[4:0];
                    pad_cfg_n[29]  = PWDATA[12:8];
                    pad_cfg_n[30]  = PWDATA[20:16];
                    pad_cfg_n[31]  = PWDATA[28:24];
                end

                `REG_STATUS: begin
                    status_n = PWDATA[1:0];
                end

                // version reg can't be written to
            endcase
        end

    end

    // register read logic
    always_comb
    begin
        PRDATA = 'b0;

        if (PSEL && PENABLE && !PWRITE)
        begin

            unique case (register_adr)
                `REG_PAD_MUX:
                    PRDATA = pad_mux_q;

                `REG_BOOT_ADR:
                    PRDATA = boot_adr_q;

                `REG_CLK_GATE:
                    PRDATA = clk_gate_q;

                `REG_PADCFG0:
                    PRDATA = {2'b00,pad_cfg_q[3],2'b00,pad_cfg_q[2],2'b00,pad_cfg_q[1],2'b00,pad_cfg_q[0]};

                `REG_PADCFG1:
                    PRDATA = {2'b00,pad_cfg_q[7],2'b00,pad_cfg_q[6],2'b00,pad_cfg_q[5],2'b00,pad_cfg_q[4]};

                `REG_PADCFG2:
                    PRDATA = {2'b00,pad_cfg_q[11],2'b00,pad_cfg_q[10],2'b00,pad_cfg_q[9],2'b00,pad_cfg_q[8]};

                `REG_PADCFG3:
                    PRDATA = {2'b00,pad_cfg_q[15],2'b00,pad_cfg_q[14],2'b00,pad_cfg_q[13],2'b00,pad_cfg_q[12]};

                `REG_PADCFG4:
                    PRDATA = {2'b00,pad_cfg_q[19],2'b00,pad_cfg_q[18],2'b00,pad_cfg_q[17],2'b00,pad_cfg_q[16]};

                `REG_PADCFG5:
                    PRDATA = {2'b00,pad_cfg_q[23],2'b00,pad_cfg_q[22],2'b00,pad_cfg_q[21],2'b00,pad_cfg_q[20]};

                `REG_PADCFG6:
                    PRDATA = {2'b00,pad_cfg_q[27],2'b00,pad_cfg_q[26],2'b00,pad_cfg_q[25],2'b00,pad_cfg_q[24]};

                `REG_PADCFG7:
                    PRDATA = {2'b00,pad_cfg_q[31],2'b00,pad_cfg_q[30],2'b00,pad_cfg_q[29],2'b00,pad_cfg_q[28]};

                `REG_INFO:
                    PRDATA = {4'b0000, `DCACHE, `ICACHE, `ROM, `INSTR_RAM, `DATA_RAM,`VERSION};

                `REG_STATUS:
                    PRDATA = {30'b0, status_q[1:0]};

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
            pad_mux_q          <= 32'b0;
            clk_gate_q         <= '1;
            pad_cfg_q          <= '{default: 32'b0};
            boot_adr_q         <= BOOT_ADDR;
            status_q           <= '1; // should not be 0 because this means OK
            // cfg_pad_int[i][0]: PD, Pull Down
            // cfg_pad_int[i][1]: PU, Pull Up
            // cfg_pad_int[i][2]: SMT, Schmitt Trigger
            // cfg_pad_int[i][3]: SR, Slew Rate
            // cfg_pad_int[i][4]: PIN1, Drive Strength Select 1
            // cfg_pad_int[i][5]: PIN2, Drive Strength Select 2

            pad_cfg_q[0]       <= 6'b000000; // always GPIO - seperate config
            pad_cfg_q[1]       <= 6'b000000; // always GPIO - seperate config
            pad_cfg_q[2]       <= 6'b000000; // always GPIO - seperate config
            pad_cfg_q[3]       <= 6'b000000; // always GPIO - seperate config
            pad_cfg_q[4]       <= 6'b000000; // always GPIO - seperate config
            pad_cfg_q[5]       <= 6'b000000; // SPI Slave CS
            pad_cfg_q[6]       <= 6'b000000; // SPI Slave IO0
            pad_cfg_q[7]       <= 6'b000000; // SPI Slave IO1
            pad_cfg_q[8]       <= 6'b000000; // SPI Slave IO2
            pad_cfg_q[9]       <= 6'b000000; // SPI Slave IO3
            pad_cfg_q[10]      <= 6'b000000; // UART CTS
            pad_cfg_q[11]      <= 6'b000000; // UART RTS
            pad_cfg_q[12]      <= 6'b000000; // UART TX
            pad_cfg_q[13]      <= 6'b000000; // UART RX
            pad_cfg_q[14]      <= 6'b000000; // SPI Master IO3
            pad_cfg_q[15]      <= 6'b000000; // SPI Master IO2
            pad_cfg_q[16]      <= 6'b000000; // SPI Master IO1
            pad_cfg_q[17]      <= 6'b000000; // SPI Master IO0
            pad_cfg_q[18]      <= 6'b000000; // SPI Master CS
            pad_cfg_q[19]      <= 6'b000000; // I2C SDA
            pad_cfg_q[20]      <= 6'b000000; // I2C SCLK
        end
        else
        begin
            pad_mux_q          <=  pad_mux_n;
            clk_gate_q         <=  clk_gate_n;
            pad_cfg_q          <=  pad_cfg_n;
            boot_adr_q         <=  boot_adr_n;
            status_q           <=  status_n;
        end
    end

    // APB logic: we are always ready to capture the data into our regs
    // not supporting transfare failure
    assign PREADY  = 1'b1;
    assign PSLVERR = 1'b0;

endmodule
