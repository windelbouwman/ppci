

module  axi2apb_mux 
		#(
			parameter NUM_SLAVES = 8
		) (
			input  logic  [3:0]                   ctrl_addr_mux,
			input  logic                          ctrl_psel,
			output logic [31:0]                   ctrl_prdata,
			output logic                          ctrl_pready,
			output logic                          ctrl_pslverr,
			
			output logic [NUM_SLAVES-1:0]         slv_psel,
			input  logic [NUM_SLAVES-1:0]         slv_pready,
			input  logic [NUM_SLAVES-1:0]         slv_pslverr,
			input  logic [NUM_SLAVES-1:0] [31:0]  slv_prdata
		);
	
	logic dec_err; //IGOR FIX, not declared
	
	assign dec_err = (ctrl_addr_mux >= NUM_SLAVES);
	
	always_comb
	begin
		for (int i=0; i<NUM_SLAVES; i++)
		begin
			slv_psel[i] = ctrl_psel & (ctrl_addr_mux == i) & ~dec_err;
		end
	end
	
	always_comb
	begin
		if (!dec_err)
			ctrl_pready = slv_pready[ctrl_addr_mux];
		else
			ctrl_pready = 1'b1;
	end
			
	always_comb
	begin
		if (!dec_err)
			ctrl_pslverr = slv_pslverr[ctrl_addr_mux];
		else
			ctrl_pslverr = 1'b1;
	end
   
	always_comb
	begin
		if (!dec_err)
			ctrl_prdata = slv_prdata[ctrl_addr_mux];
		else
			ctrl_prdata = 32'h0;
	end
   

endmodule

   


