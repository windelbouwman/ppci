

module  axi2apb_wr 
		#(
		parameter AXI_ID_WIDTH   = 6
		) (
		input  logic                      clk,
		input  logic                      rstn,
		input  logic                      psel,
		input  logic                      penable,
		input  logic                      pwrite,
		input  logic                      pslverr,
		input  logic                      pready,
		input  logic                      cmd_err,
		input  logic [AXI_ID_WIDTH-1:0]   cmd_id,
		output logic                      finish_wr,
		output logic                      WREADY,
		output logic [AXI_ID_WIDTH-1:0]   BID,
		output logic              [1:0]   BRESP,
		output logic                      BVALID,
		input  logic                      BREADY
		);
   
   
   localparam              RESP_OK     = 2'b00;
   localparam              RESP_SLVERR = 2'b10;
   localparam              RESP_DECERR = 2'b11;
   
   assign                 finish_wr = BVALID & BREADY;
   
   assign                 WREADY = psel & penable & pwrite & pready;
   
   always @(posedge clk or negedge rstn)
     if (!rstn)
       begin
         //BRESP  <=  2'h0;
         BVALID <=  1'b0;
       end
     else if (finish_wr)
       begin
         //BRESP  <=  2'h0;
         BVALID <=  1'b0;
       end
     else if (psel & penable & pwrite & pready)
       begin
         BID    <=  cmd_id;
         BRESP  <=  cmd_err ? RESP_SLVERR : pslverr ? RESP_DECERR : RESP_OK;
         BVALID <=  1'b1;
       end
       
endmodule

   


