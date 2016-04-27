

module  axi2apb_cmd 
		#(
			parameter AXI_ID_WIDTH = 6,
			parameter AXI_ADDR_WIDTH = 32,
			parameter APB_ADDR_WIDTH = 12  //APB slaves are 4KB by default
   		) (

   input   logic                 clk,
   input   logic                 rstn,

   input   logic   [AXI_ID_WIDTH-1:0] AWID,
   input   logic [AXI_ADDR_WIDTH-1:0] AWADDR,
   input   logic                [7:0] AWLEN,
   input   logic                [2:0] AWSIZE,
   input   logic                      AWVALID,
   output  logic                      AWREADY,
   input   logic   [AXI_ID_WIDTH-1:0] ARID,
   input   logic [AXI_ADDR_WIDTH-1:0] ARADDR,
   input   logic                [7:0] ARLEN,
   input   logic                [2:0] ARSIZE,
   input   logic                      ARVALID,
   output  logic                      ARREADY,
   input   logic                      finish_wr,
   input   logic                      finish_rd,

   output  logic                      cmd_empty,
   output  logic                      cmd_read,
   output  logic   [AXI_ID_WIDTH-1:0] cmd_id,
   output  logic [3+APB_ADDR_WIDTH:0] cmd_addr,
   output  logic                      cmd_err
   ); 
   
   logic   [AXI_ID_WIDTH-1:0] AID;
   logic [3+APB_ADDR_WIDTH:0] AADDR;
   logic                [7:0] ALEN;
   logic                [2:0] ASIZE;
   logic                      AVALID;
   logic                      AREADY;
   
   logic                      cmd_push;
   logic                      cmd_pop;
   logic                      cmd_full;
   logic                      read;
   
   logic                      wreq, rreq;
   logic                      wack, rack;
   logic                      AERR;
  
   assign wreq = AWVALID;
   assign rreq = ARVALID;
   assign wack = AWVALID & AWREADY;
   assign rack = ARVALID & ARREADY;
         
   always @(posedge clk or negedge rstn)
   	if (!rstn)
   		read <=  1'b1;
   	else if (wreq & (rack | (~rreq)))
   		read <=  1'b0;
   	else if (rreq & (wack | (~wreq)))
   		read <=  1'b1;

   		//command mux
   assign AID    = read ? ARID    : AWID;
   assign AADDR  = read ? ARADDR[3+APB_ADDR_WIDTH:0]  : AWADDR[3+APB_ADDR_WIDTH:0];
   assign ALEN   = read ? ARLEN   : AWLEN;
   assign ASIZE  = read ? ARSIZE  : AWSIZE;
   assign AVALID = read ? ARVALID : AWVALID;
   assign AREADY = read ? ARREADY : AWREADY;
   assign AERR   = (ASIZE != 'd2) | (ALEN != 'd0); //support only 32 bit single AXI commands
   
   assign ARREADY = (~cmd_full) & read;
   assign AWREADY = (~cmd_full) & (~read);
   
   assign               cmd_push  = AVALID & AREADY;
   assign               cmd_pop   = cmd_read ? finish_rd : finish_wr;
   
   prgen_fifo #(AXI_ID_WIDTH+4+APB_ADDR_WIDTH+2, 2) 
   	cmd_fifo(
   		.clk(clk),
   		.rstn(rstn),
   		.push(cmd_push),
   		.pop(cmd_pop),
   		.din({AID,AADDR,AERR,read}),
   		.dout({cmd_id,cmd_addr,cmd_err,cmd_read}),
   		.empty(cmd_empty),
   		.full(cmd_full)
   		);

        
   
endmodule




