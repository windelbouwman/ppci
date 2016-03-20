
module axi2apb
#(
    parameter AXI_ID_WIDTH   = 6,
    parameter AXI_ADDR_WIDTH = 32,
    parameter AXI_DATA_WIDTH = 64,
    parameter APB_NUM_SLAVES = 8,
    parameter APB_ADDR_WIDTH = 12  //APB slaves are 4KB by default
)
(
    input                                       clk,
    input                                       rstn,

    input  logic          [AXI_ID_WIDTH-1:0]    AWID,
    input  logic        [AXI_ADDR_WIDTH-1:0]    AWADDR,
    input  logic                       [7:0]    AWLEN,
    input  logic                       [2:0]    AWSIZE,
    input  logic                                AWVALID,
    output logic                                AWREADY,

    input  logic        [AXI_DATA_WIDTH-1:0]    WDATA,
    input  logic      [AXI_DATA_WIDTH/8-1:0]    WSTRB,
    input  logic                                WLAST,
    input  logic                                WVALID,
    output logic                                WREADY,

    output logic          [AXI_ID_WIDTH-1:0]    BID,
    output logic                       [1:0]    BRESP,
    output logic                                BVALID,
    input  logic                                BREADY,

    input  logic          [AXI_ID_WIDTH-1:0]    ARID,
    input  logic        [AXI_ADDR_WIDTH-1:0]    ARADDR,
    input  logic                       [7:0]    ARLEN,
    input  logic                       [2:0]    ARSIZE,
    input  logic                                ARVALID,
    output logic                                ARREADY,

    output logic          [AXI_ID_WIDTH-1:0]    RID,
    output logic        [AXI_DATA_WIDTH-1:0]    RDATA,
    output logic                       [1:0]    RRESP,
    output logic                                RLAST,
    output logic                                RVALID,
    input  logic                                RREADY,

    output logic                                penable,
    output logic                                pwrite,
    output logic        [APB_ADDR_WIDTH-1:0]    paddr,
    output logic        [APB_NUM_SLAVES-1:0]    psel,
    output logic                      [31:0]    pwdata,
    input  logic [APB_NUM_SLAVES-1:0] [31:0]    prdata,
    input  logic        [APB_NUM_SLAVES-1:0]    pready,
    input  logic        [APB_NUM_SLAVES-1:0]    pslverr
);

    logic                        int_psel;
    logic                        int_penable;
    logic                        int_pwrite;
    logic                [31:0]  int_prdata;
    logic                        int_pready;
    logic                        int_pslverr;

    logic                        cmd_empty;
    logic                        cmd_read;
    logic    [AXI_ID_WIDTH-1:0]  cmd_id;
    logic  [3+APB_ADDR_WIDTH:0]  cmd_addr;
    logic                 [3:0]  cmd_addr_mux;
    logic                        cmd_err;

    logic                        finish_wr;
    logic                        finish_rd;

    logic [AXI_DATA_WIDTH/32-1:0][31:0] wdata_words;

    assign cmd_addr_mux = cmd_addr[3+APB_ADDR_WIDTH:APB_ADDR_WIDTH];
    assign paddr        = cmd_addr[APB_ADDR_WIDTH-1:0];

    genvar i;
    generate
      for (i = 0; i < AXI_DATA_WIDTH/32; i++)
        assign wdata_words[i] = WDATA[32*i+31:32*i];
    endgenerate

    generate if (AXI_DATA_WIDTH/32 == 1)
      assign pwdata = wdata_words[0];
    else
      assign pwdata = wdata_words[cmd_addr[2+(AXI_DATA_WIDTH/32)-1:2]];
    endgenerate

    assign penable = int_penable;
    assign pwrite  = int_pwrite;

    axi2apb_cmd
    #(
        .AXI_ID_WIDTH(AXI_ID_WIDTH),
        .AXI_ADDR_WIDTH(AXI_ADDR_WIDTH),
        .APB_ADDR_WIDTH(APB_ADDR_WIDTH)
    )
    axi2apb_cmd
    (
        .clk(clk),
        .rstn(rstn),
        .AWID(AWID),
        .AWADDR(AWADDR),
        .AWLEN(AWLEN),
        .AWSIZE(AWSIZE),
        .AWVALID(AWVALID),
        .AWREADY(AWREADY),
        .ARID(ARID),
        .ARADDR(ARADDR),
        .ARLEN(ARLEN),
        .ARSIZE(ARSIZE),
        .ARVALID(ARVALID),
        .ARREADY(ARREADY),
        .finish_wr(finish_wr),
        .finish_rd(finish_rd),
        .cmd_empty(cmd_empty),
        .cmd_read(cmd_read),
        .cmd_id(cmd_id),
        .cmd_addr(cmd_addr),
        .cmd_err(cmd_err)
    );


    axi2apb_rd
    #(
        .AXI_ID_WIDTH(AXI_ID_WIDTH),
        .AXI_DATA_WIDTH(AXI_DATA_WIDTH)
    )
    axi2apb_rd
    (
        .clk(clk),
        .rstn(rstn),
        .psel(int_psel),
        .penable(int_penable),
        .pwrite(int_pwrite),
        .prdata(int_prdata),
        .pslverr(int_pslverr),
        .pready(int_pready),
        .cmd_err(cmd_err),
        .cmd_id(cmd_id),
        .cmd_addr(cmd_addr),
        .finish_rd(finish_rd),
        .RID(RID),
        .RDATA(RDATA),
        .RRESP(RRESP),
        .RLAST(RLAST),
        .RVALID(RVALID),
        .RREADY(RREADY)
    );

    axi2apb_wr
    #(
        .AXI_ID_WIDTH(AXI_ID_WIDTH)
    )
    axi2apb_wr
    (
        .clk(clk),
        .rstn(rstn),
        .psel(int_psel),
        .penable(int_penable),
        .pwrite(int_pwrite),
        .pslverr(int_pslverr),
        .pready(int_pready),
        .cmd_err(cmd_err),
        .cmd_id(cmd_id),
        .finish_wr(finish_wr),
        .WREADY(WREADY),
        .BID(BID),
        .BRESP(BRESP),
        .BVALID(BVALID),
        .BREADY(BREADY)
    );



    axi2apb_ctrl axi2apb_ctrl
    (
        .clk(clk),
        .rstn(rstn),
        .finish_wr(finish_wr),
        .finish_rd(finish_rd),
        .cmd_empty(cmd_empty),
        .cmd_read(cmd_read),
        .WVALID(WVALID),
        .psel(int_psel),
        .penable(int_penable),
        .pwrite(int_pwrite),
        .pready(int_pready)
    );


    axi2apb_mux
    #(
        .NUM_SLAVES(APB_NUM_SLAVES)
    )
    axi2apb_mux
    (
        .ctrl_addr_mux(cmd_addr_mux),
        .ctrl_psel(int_psel),
        .ctrl_prdata(int_prdata),
        .ctrl_pready(int_pready),
        .ctrl_pslverr(int_pslverr),
        .slv_psel(psel),
        .slv_pready(pready),
        .slv_pslverr(pslverr),
        .slv_prdata(prdata)
    );

endmodule




