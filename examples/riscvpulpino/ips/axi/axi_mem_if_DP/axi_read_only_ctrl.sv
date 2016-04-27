// Copyright 2015 ETH Zurich and University of Bologna.
// Copyright and related rights are licensed under the Solderpad Hardware
// License, Version 0.51 (the “License”); you may not use this file except in
// compliance with the License.  You may obtain a copy of the License at
// http://solderpad.org/licenses/SHL-0.51. Unless required by applicable law
// or agreed to in writing, software, hardware and materials distributed under
// this License is distributed on an “AS IS” BASIS, WITHOUT WARRANTIES OR
// CONDITIONS OF ANY KIND, either express or implied. See the License for the
// specific language governing permissions and limitations under the License.

`define OKAY   2'b00
`define EXOKAY 2'b01
`define SLVERR 2'b10
`define DECERR 2'b11

module axi_read_only_ctrl
#(
    parameter AXI4_ADDRESS_WIDTH = 32,
    parameter AXI4_RDATA_WIDTH   = 64,
    parameter AXI4_WDATA_WIDTH   = 64,
    parameter AXI4_ID_WIDTH      = 16,
    parameter AXI4_USER_WIDTH    = 10,
    parameter AXI_NUMBYTES       = AXI4_WDATA_WIDTH/8,
    parameter MEM_ADDR_WIDTH     = 13
)
(
    input logic                                     clk,
    input logic                                     rst_n,

    //AXI read address bus -------------------------------------
    input  logic [AXI4_ID_WIDTH-1:0]                ARID_i     ,
    input  logic [AXI4_ADDRESS_WIDTH-1:0]           ARADDR_i   ,
    input  logic [ 7:0]                             ARLEN_i    ,
    input  logic [ 2:0]                             ARSIZE_i   ,
    input  logic [ 1:0]                             ARBURST_i  ,
    input  logic                                    ARLOCK_i   ,
    input  logic [ 3:0]                             ARCACHE_i  ,
    input  logic [ 2:0]                             ARPROT_i   ,
    input  logic [ 3:0]                             ARREGION_i ,
    input  logic [ AXI4_USER_WIDTH-1:0]             ARUSER_i   ,
    input  logic [ 3:0]                             ARQOS_i    ,
    input  logic                                    ARVALID_i  ,
    output logic                                    ARREADY_o  ,
    // ---------------------------------------------------------

    //AXI read data bus ----------------------------------------
    output  logic [AXI4_ID_WIDTH-1:0]               RID_o      ,
    output  logic [AXI4_RDATA_WIDTH-1:0]            RDATA_o    ,
    output  logic [ 1:0]                            RRESP_o    ,
    output  logic                                   RLAST_o    ,
    output  logic [AXI4_USER_WIDTH-1:0]             RUSER_o    ,
    output  logic                                   RVALID_o   ,
    input   logic                                   RREADY_i   ,

    // Memory Port
    output logic                                    MEM_CEN_o      ,
    output logic                                    MEM_WEN_o      ,
    output logic  [MEM_ADDR_WIDTH-1:0]              MEM_A_o        ,
    output logic  [AXI4_RDATA_WIDTH-1:0]            MEM_D_o        ,
    output logic  [AXI_NUMBYTES-1:0]                MEM_BE_o       ,
    input  logic  [AXI4_RDATA_WIDTH-1:0]            MEM_Q_i        ,

    input   logic                                   grant_i,
    output  logic                                   valid_o
);

    localparam OFFSET_BIT = $clog2(AXI4_RDATA_WIDTH) - 3 ;
    enum logic [2:0] {IDLE, SINGLE_R , BURST_R, WAIT_RREADY, LAST_BURST_R, WAIT_BURST_GRANT,  WAIT_BURST_RREADY, WAIT_LAST_RREADY}      CS, NS;
    logic [8:0]                                       CountBurst_CS, CountBurst_NS;

    logic                                             sample_rdata;
    logic                                             sample_ctrl;

    logic [AXI4_RDATA_WIDTH-1:0]                      RDATA_REG;
    logic [AXI4_USER_WIDTH-1:0]                       RUSER_REG;
    logic [AXI4_ID_WIDTH-1:0]                         RID_REG;
    logic [MEM_ADDR_WIDTH-1:0]                        ARADDR_REG;
    logic [7:0]                                       ARLEN_REG;

    assign MEM_D_o = '0;
    assign MEM_BE_o = '0;


    always_ff @(posedge clk or negedge rst_n)
    begin : _UPDATE_CS_
        if(~rst_n)
        begin
            CS         <= IDLE;
            CountBurst_CS <= '0;

            RDATA_REG   <= '0;
            RID_REG     <= '0;
            RUSER_REG   <= '0;
            ARADDR_REG  <= '0;
            ARLEN_REG   <= '0;
        end
        else
        begin
            CS <= NS;
            CountBurst_CS <= CountBurst_NS;

            if(sample_ctrl)
            begin
                RUSER_REG <= ARUSER_i;
                RID_REG   <= ARID_i;
                ARADDR_REG <= ARADDR_i[MEM_ADDR_WIDTH+OFFSET_BIT-1 : OFFSET_BIT];
                ARLEN_REG  <= ARLEN_i;
            end

            if(sample_rdata)
                RDATA_REG <= MEM_Q_i;

        end
    end


    always_comb
    begin : COMPUTE_NS
        ARREADY_o = 1'b0;

        RDATA_o = MEM_Q_i;
        RUSER_o = RUSER_REG;
        RID_o   = RID_REG;
        RVALID_o = 1'b0;
        RLAST_o  = 1'b0;
        RRESP_o  = `OKAY;


        MEM_CEN_o = 1'b1;
        MEM_WEN_o = 1'b1;
        MEM_A_o   = ARADDR_i[MEM_ADDR_WIDTH+OFFSET_BIT-1 : OFFSET_BIT];

        valid_o   = 1'b0;

        sample_rdata = 1'b0;
        sample_ctrl  = 1'b0;

        CountBurst_NS = CountBurst_CS;

        case (CS)

            IDLE :
            begin
                valid_o   = ARVALID_i;
                MEM_CEN_o = ~ARVALID_i;

                ARREADY_o = grant_i;

                if(ARVALID_i)
                begin
                    sample_ctrl = 1'b1;

                    if(grant_i)
                    begin
                        ARREADY_o = 1'b1;
                        if(ARLEN_i == 0)
                        begin
                            NS = SINGLE_R;
                            CountBurst_NS = '0;
                        end
                        else
                        begin
                            NS = BURST_R;
                            CountBurst_NS = 1'b1;
                        end

                    end
                    else //not grant
                    begin
                        NS = IDLE; //stay here if not granted
                    end

                end
                else
                begin
                    NS = IDLE;
                end

            end

            SINGLE_R:
            begin
                sample_rdata = 1'b1;
                RDATA_o  = MEM_Q_i;
                RVALID_o = 1'b1;
                RLAST_o  = 1'b1;
                RRESP_o  = `OKAY;

                if(RREADY_i)
                begin
                        ARREADY_o = grant_i;
                        valid_o = ARVALID_i;
                        MEM_CEN_o = ~ARVALID_i;

                        if(ARVALID_i)
                        begin
                            sample_ctrl = 1'b1;

                            if(grant_i)
                            begin
                                ARREADY_o = 1'b1;
                                if(ARLEN_i == 0)
                                begin
                                    NS = SINGLE_R;
                                    CountBurst_NS = '0;
                                end
                                else
                                begin
                                    NS = BURST_R;
                                    CountBurst_NS = 1'b1;
                                end

                            end
                            else //not grant
                            begin
                                NS = IDLE; //Come back to IDLE if not granted
                            end

                        end
                        else
                        begin
                            NS = IDLE;
                        end
                end
                else
                begin
                    NS = WAIT_RREADY;
                end
            end


            WAIT_RREADY:
            begin
                RDATA_o  = RDATA_REG;
                RVALID_o = 1'b1;
                RLAST_o  = 1'b1;
                RRESP_o  = `OKAY;


                if(RREADY_i)
                begin
                        ARREADY_o = grant_i;
                        valid_o = ARVALID_i;
                        MEM_CEN_o = ~ARVALID_i;

                        /////////////////////////////////////////
                        if(ARVALID_i)
                        begin
                            sample_ctrl = 1'b1;

                            if(grant_i)
                            begin
                                ARREADY_o = 1'b1;
                                if(ARLEN_i == 0)
                                begin
                                    NS = SINGLE_R;
                                    CountBurst_NS = '0;
                                end
                                else
                                begin
                                    NS = BURST_R;
                                    CountBurst_NS = 1'b1;
                                end

                            end
                            else //not grant
                            begin
                                NS = IDLE; //stay here if not granted
                            end

                        end
                        else
                        begin
                            NS = IDLE;
                        end
                        ///////////////////////
                end
                else
                begin
                    NS = WAIT_RREADY;
                end
            end //~WAIT_RREADY


            BURST_R:
            begin
                sample_rdata = 1'b1;
                RDATA_o  = MEM_Q_i;
                RVALID_o = 1'b1;
                RLAST_o  = 1'b0;
                RRESP_o  = `OKAY;
                MEM_A_o     = ARADDR_REG+CountBurst_CS;

                if(RREADY_i)
                begin

                    sample_ctrl = 1'b0;
                    MEM_CEN_o   = 1'b0;
                    //MEM_A_o     = ARADDR_REG+CountBurst_CS;
                    valid_o     = 1'b1;


                    if(grant_i)
                    begin
                            NS = BURST_R;

                            if(CountBurst_CS == ARLEN_REG)
                            begin
                                CountBurst_NS = '0;
                                NS = LAST_BURST_R;
                            end
                            else
                            begin
                                NS = BURST_R;
                                CountBurst_NS = CountBurst_CS+1'b1;
                            end
                    end
                    else
                    begin
                            NS = WAIT_BURST_GRANT;
                    end

                end
                else
                begin
                    NS = WAIT_BURST_RREADY;
                end
            end //~BURST_R


            WAIT_BURST_GRANT:
            begin
                MEM_CEN_o   = 1'b0;
                MEM_A_o     = ARADDR_REG+CountBurst_CS;
                valid_o     = 1'b1;

                if(grant_i)
                begin
                    if(CountBurst_CS == ARLEN_REG)
                    begin
                        NS = LAST_BURST_R;
                        CountBurst_NS = '0;
                    end
                    else
                    begin
                        NS = BURST_R;
                        CountBurst_NS = CountBurst_CS + 1 ;
                    end
                end
                else
                begin
                    NS = WAIT_BURST_GRANT;
                end
            end




            WAIT_BURST_RREADY:
            begin
                RDATA_o  = RDATA_REG;
                RVALID_o = 1'b1;
                RLAST_o  = 1'b0;
                RRESP_o  = `OKAY;
                MEM_A_o = ARADDR_REG + CountBurst_CS;

                if(RREADY_i)
                begin
                        valid_o = 1'b1;
                        //MEM_A_o = ARADDR_REG + CountBurst_CS;
                        MEM_CEN_o = 1'b0;
                        /////////////////////////////////////////
                        if(grant_i)
                        begin
                            CountBurst_NS = CountBurst_CS + 1 ;

                            if(CountBurst_CS == ARLEN_REG )
                            begin
                                NS = LAST_BURST_R;
                            end
                            else
                            begin
                                NS = BURST_R;
                            end
                        end
                        else //not grant
                        begin
                            NS = WAIT_BURST_GRANT; //stay here if not granted
                        end
                        ///////////////////////
                end
                else
                begin
                    NS = WAIT_BURST_RREADY;
                end
            end //~WAIT_BURST_RREADY


            LAST_BURST_R:
            begin
                RVALID_o = 1'b1;
                RLAST_o  = 1'b1;
                RDATA_o  = MEM_Q_i;
                sample_rdata = 1'b1;

                if(RREADY_i)
                begin
                        valid_o   = ARVALID_i;
                        MEM_CEN_o = ~ARVALID_i;

                        ARREADY_o = grant_i;

                        if(ARVALID_i)
                        begin
                            sample_ctrl = 1'b1;

                            if(grant_i)
                            begin
                                ARREADY_o = 1'b1;
                                if(ARLEN_i == 0)
                                begin
                                    NS = SINGLE_R;
                                    CountBurst_NS = '0;
                                end
                                else
                                begin
                                    NS = BURST_R;
                                    CountBurst_NS = 1'b1;
                                end

                            end
                            else //not grant
                            begin
                                NS = IDLE; //stay here if not granted
                            end

                        end
                        else
                        begin
                            NS = IDLE;
                        end

                end
                else
                begin
                    NS = WAIT_LAST_RREADY;
                end

            end




            WAIT_LAST_RREADY:
            begin
                RVALID_o = 1'b1;
                RLAST_o  = 1'b1;
                RDATA_o  = RDATA_REG;
                sample_rdata = 1'b0;

                if(RREADY_i)
                begin
                        valid_o   = ARVALID_i;
                        MEM_CEN_o = ~ARVALID_i;

                        ARREADY_o = grant_i;

                        if(ARVALID_i)
                        begin
                            sample_ctrl = 1'b1;

                            if(grant_i)
                            begin
                                ARREADY_o = 1'b1;
                                if(ARLEN_i == 0)
                                begin
                                    NS = SINGLE_R;
                                    CountBurst_NS = '0;
                                end
                                else
                                begin
                                    NS = BURST_R;
                                    CountBurst_NS = 1'b1;
                                end

                            end
                            else //not grant
                            begin
                                NS = IDLE; //stay here if not granted
                            end

                        end
                        else
                        begin
                            NS = IDLE;
                        end

                end
                else
                begin
                    NS = WAIT_LAST_RREADY;
                end

            end





            default :
            begin
                NS = IDLE;
            end
        endcase // CS

    end

endmodule // axi_read_only_ctrl
