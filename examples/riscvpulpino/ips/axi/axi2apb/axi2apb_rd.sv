`define log2(VALUE) ((VALUE) <= ( 1 ) ? 0 : (VALUE) <= ( 2 ) ? 1 : (VALUE) <= ( 4 ) ? 2 : (VALUE)<= (8) ? 3:(VALUE) <= ( 16 )  ? 4 : (VALUE) <= ( 32 )  ? 5 : (VALUE) <= ( 64 )  ? 6 : (VALUE) <= ( 128 ) ? 7 : (VALUE) <= ( 256 ) ? 8 : (VALUE) <= ( 512 ) ? 9 : 10)


module  axi2apb_rd
#(
    parameter AXI_ID_WIDTH   = 6,
    parameter AXI_DATA_WIDTH = 64,
    parameter APB_ADDR_WIDTH = 12  //APB slaves are 4KB by default
)
(
    input  logic                        clk,
    input  logic                        rstn,

    input  logic                        psel,
    input  logic                        penable,
    input  logic                        pwrite,

    input  logic               [31:0]   prdata,
    input  logic                        pslverr,
    input  logic                        pready,

    input  logic                        cmd_err,
    input  logic   [AXI_ID_WIDTH-1:0]   cmd_id,
    input  logic [3+APB_ADDR_WIDTH:0]   cmd_addr,
    output logic                        finish_rd,

    output logic   [AXI_ID_WIDTH-1:0]   RID,
    output logic [AXI_DATA_WIDTH-1:0]   RDATA,
    output logic                [1:0]   RRESP,
    output logic                        RLAST,
    output logic                        RVALID,
    input  logic                        RREADY
);

    localparam           EXTRA_LANES = `log2(AXI_DATA_WIDTH/32);
    localparam           RESP_OK     = 2'b00;
    localparam           RESP_SLVERR = 2'b10;
    localparam           RESP_DECERR = 2'b11;

    logic    [EXTRA_LANES:0] bytelane;
    logic             [31:0] r_RDATA;

    generate if (EXTRA_LANES == 0)
      assign bytelane = 'h0;
    else
      assign bytelane =    cmd_addr[2+EXTRA_LANES-1:2];
    endgenerate

    always_comb
    begin
        RDATA = 'h0;
        for (int i=0; i <= EXTRA_LANES; i=i+1)
        begin
            if (i == bytelane)
              RDATA[32*i +: 32] = r_RDATA;
        end
    end

    assign                 finish_rd = RVALID & RREADY & RLAST;

    always_ff @(posedge clk or negedge rstn)
    begin
        if (~rstn)
        begin
            r_RDATA <=  'h0;
            RID    <=   'h0;
            RRESP  <=   'h0;
            RLAST  <=   'h0;
            RVALID <=  1'b0;
        end
        else 
        begin
            if (finish_rd)
            begin
                //RRESP  <=  2'h0;
                //RLAST  <=  1'b0;
                RVALID <=  1'b0;
            end
            else if (psel & penable & (~pwrite) & pready)
            begin
                RID      <=  cmd_id;
                r_RDATA  <=  prdata;
                RRESP    <=  cmd_err ? RESP_SLVERR : pslverr ? RESP_DECERR : RESP_OK;
                RLAST    <=  1'b1;
                RVALID   <=  1'b1;
            end
        end
    end

endmodule
