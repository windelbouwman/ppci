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

module axi_write_only_ctrl
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

    //AXI Write address bus -------------------------------------
    input  logic [AXI4_ID_WIDTH-1:0]                AWID_i     ,
    input  logic [AXI4_ADDRESS_WIDTH-1:0]           AWADDR_i   ,
    input  logic [ 7:0]                             AWLEN_i    ,
    input  logic [ 2:0]                             AWSIZE_i   ,
    input  logic [ 1:0]                             AWBURST_i  ,
    input  logic                                    AWLOCK_i   ,
    input  logic [ 3:0]                             AWCACHE_i  ,
    input  logic [ 2:0]                             AWPROT_i   ,
    input  logic [ 3:0]                             AWREGION_i ,
    input  logic [ AXI4_USER_WIDTH-1:0]             AWUSER_i   ,
    input  logic [ 3:0]                             AWQOS_i    ,
    input  logic                                    AWVALID_i  ,
    output logic                                    AWREADY_o  ,
    // ---------------------------------------------------------

    //AXI write data bus -------------- // USED// -------------
    input  logic [AXI4_WDATA_WIDTH-1:0]             WDATA_i    ,
    input  logic [AXI_NUMBYTES-1:0]                 WSTRB_i    ,
    input  logic                                    WLAST_i    ,
    input  logic [AXI4_USER_WIDTH-1:0]              WUSER_i    ,
    input  logic                                    WVALID_i   ,
    output logic                                    WREADY_o   ,

    //AXI write response bus -------------- // USED// ----------
    output logic   [AXI4_ID_WIDTH-1:0]              BID_o      ,
    output logic   [ 1:0]                           BRESP_o    ,
    output logic                                    BVALID_o   ,
    output logic   [AXI4_USER_WIDTH-1:0]            BUSER_o    ,
    input  logic                                    BREADY_i   ,



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

    localparam OFFSET_BIT = $clog2(AXI4_WDATA_WIDTH) - 3 ;
    enum logic [2:0] {IDLE,  DISPATCH_RESP,  BURST, WAIT_W_GRANT_VALID, ERROR }     CS, NS;
    logic [8:0]                                       CountBurst_CS, CountBurst_NS;

    logic                                             sample_ctrl;
    logic                                             sample_backward;

    logic [AXI4_USER_WIDTH-1:0]                       AWUSER_REG;
    logic [AXI4_ID_WIDTH-1:0]                         AWID_REG;
    logic [MEM_ADDR_WIDTH-1:0]                        AWADDR_REG,AWADDR_REG_incr;
    logic [7:0]                                       AWLEN_REG;


    // next address
    //AWADDR_REG+CountBurst_CS;

    always_ff @(posedge clk or negedge rst_n)
    begin : _UPDATE_CS_
        if(~rst_n)
        begin
            CS         <= IDLE;
            CountBurst_CS <= '0;
            AWADDR_REG_incr <= '0;
            AWID_REG    <= '0;
            AWUSER_REG   <= '0;
            AWADDR_REG  <= '0;
            AWLEN_REG   <= '0;
        end
        else
        begin
            CS <= NS;
            CountBurst_CS <= CountBurst_NS;

            if(sample_ctrl)
            begin
                AWUSER_REG  <= AWUSER_i;
                AWID_REG    <= AWID_i;
                AWADDR_REG  <= AWADDR_i[MEM_ADDR_WIDTH+OFFSET_BIT-1 : OFFSET_BIT];
                AWLEN_REG   <= AWLEN_i;
            end

            // if(sample_backward)
            // begin
            //     BUSER_o = AWUSER_REG;
            //     BID_o   = AWID_REG;
            // end

        end
    end

    assign BUSER_o =  AWUSER_REG;
    assign BID_o   =  AWID_REG;

    always_comb
    begin : COMPUTE_NS
        sample_ctrl = 1'b0;
        //sample_backward = 1'b0;

        valid_o   = 1'b0;
        AWREADY_o = 1'b0;
        WREADY_o  = 1'b0;

        BRESP_o   = `OKAY;
        BVALID_o  =  1'b0;

        MEM_CEN_o = 1'b1;
        MEM_WEN_o = 1'b0;
        MEM_A_o   = AWADDR_i[MEM_ADDR_WIDTH+OFFSET_BIT-1 : OFFSET_BIT];
        MEM_D_o   = WDATA_i;
        MEM_BE_o  = WSTRB_i;

        NS = CS;
        CountBurst_NS = CountBurst_CS;


        case (CS)

            IDLE:
            begin
                AWREADY_o = 1'b1;
                sample_ctrl = AWVALID_i;
                //MOved Here
                MEM_A_o   = AWADDR_i[MEM_ADDR_WIDTH+OFFSET_BIT-1 : OFFSET_BIT];


                if(AWVALID_i)
                begin
                        valid_o = WVALID_i;
                        MEM_CEN_o = ~WVALID_i;
                        //MEM_A_o   = AWADDR_i[MEM_ADDR_WIDTH+OFFSET_BIT-1 : OFFSET_BIT];

                        WREADY_o = grant_i;

                        if(WVALID_i & grant_i)
                        begin
                                if(AWLEN_i == 0) //Singlr Beat Write
                                begin
                                    NS = DISPATCH_RESP;
                                    CountBurst_NS = '0;
                                end
                                else // Burst Write
                                begin
                                    NS = BURST;
                                    CountBurst_NS = 1;
                                end
                        end
                        else // not WVALID
                        begin
                                //AW req is granted but not get any valid WDATA, move t wait WVALID
                                NS = WAIT_W_GRANT_VALID;
                                CountBurst_NS = '0;
                        end

                end
                else // not AWVALID
                begin
                    NS = IDLE;
                end

            end //~IDLE





            WAIT_W_GRANT_VALID:
            begin
                WREADY_o  = grant_i;
                valid_o   = WVALID_i;
                MEM_CEN_o = ~(WVALID_i & grant_i);
                MEM_A_o   = AWADDR_REG+CountBurst_CS;



                if(grant_i & WVALID_i)
                begin
                    if(AWLEN_REG == CountBurst_CS)
                    begin
                        NS = DISPATCH_RESP;
                        CountBurst_NS = '0;
                    end
                    else
                    begin // WRITE!!!!
                        NS = BURST;
                        CountBurst_NS = CountBurst_CS + 1;
                    end

                end
                else // not grant
                begin
                    NS = WAIT_W_GRANT_VALID;
                end
            end




            DISPATCH_RESP:
            begin
                BRESP_o = `OKAY;
                BVALID_o = 1'b1;
                //moved here
                MEM_A_o   = AWADDR_i[MEM_ADDR_WIDTH+OFFSET_BIT-1 : OFFSET_BIT];

                if(BREADY_i)
                begin
                        AWREADY_o = 1'b1;
                        sample_ctrl = AWVALID_i;

                        if(AWVALID_i)
                        begin
                                valid_o = WVALID_i;
                                MEM_CEN_o = ~WVALID_i;
                                //MEM_A_o   = AWADDR_i[MEM_ADDR_WIDTH+OFFSET_BIT-1 : OFFSET_BIT];


                                WREADY_o = grant_i;

                                if(WVALID_i & grant_i)
                                begin
                                        if(AWLEN_i == 0) //Singlr Beat Write
                                        begin
                                            CountBurst_NS = '0;

                                            if(WLAST_i == 1'b1)
                                            begin
                                                NS = DISPATCH_RESP;
                                            end
                                            else
                                            begin
                                                NS = ERROR;
                                            end
                                        end
                                        else // Burst Write
                                        begin
                                            NS = BURST;
                                            CountBurst_NS = 1;
                                        end
                                end
                                else // not WVALID
                                begin
                                        //AW req is granted but not get any valid WDATA, move t wait WVALID
                                        NS = WAIT_W_GRANT_VALID;
                                        CountBurst_NS = '0;
                                end

                        end
                        else // not AWVALID
                        begin
                            NS = IDLE;
                        end

                end
                else
                begin
                    NS = DISPATCH_RESP;
                end
            end //~ DISPATCH_RESP




            BURST:
            begin
                   WREADY_o = grant_i;
                   MEM_CEN_o = ~(WVALID_i & grant_i);
                   valid_o   = 1'b1;

                   MEM_A_o   = AWADDR_REG + CountBurst_CS;


                    if(WVALID_i & grant_i)
                    begin
                            if(AWLEN_REG == CountBurst_CS)
                            begin
                                if(WLAST_i == 1'b1)
                                begin
                                    NS = DISPATCH_RESP;
                                    CountBurst_NS = '0;
                                end
                                else
                                begin
                                    NS = ERROR;
                                    CountBurst_NS = '0;
                                end

                            end
                            else // Burst Write
                            begin
                                NS = BURST;
                                CountBurst_NS = CountBurst_CS + 1;
                            end
                    end
                    else // not WVALID
                    begin
                            //AW req is granted but not get any valid WDATA, move t wait WVALID
                            NS = WAIT_W_GRANT_VALID;;
                    end
            end //~ BURST


            ERROR:
            begin
                NS = ERROR;
            end


            default :
            begin
                NS = IDLE;
            end //~default

        endcase // CS

    end

endmodule // axi_read_only_ctrl
