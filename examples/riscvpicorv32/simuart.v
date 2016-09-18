module simuart(input wire		clk,
	       input wire		cs,
	       input wire [31:0]	bus_addr,
	       input wire [31:0]	bus_wr_val,	
	       input wire [3:0]		bus_bytesel,
	       output reg		bus_ack,
	       output reg [31:0]	bus_data,
               output reg int,
               input wire intack
);


task write_data;
begin
	$uart_put(bus_wr_val[7:0]);
end
endtask


task read_data;
begin
	$uart_get(uart_buf);
end
endtask

reg [8:0]	uart_buf = 9'b0;
wire uart_rdy	= uart_buf[8];

wire [31:0] status_reg = (uart_rdy ? 32'b10 : 32'b0);
reg ff;
reg ffold;

initial begin
	bus_ack = 1'b0;
	bus_data = 32'b0;
        int = 1'b0;
end

always @(posedge clk) begin
	bus_data <= 32'b0;
   //     int <= 1'b0;
        ff <= 1'b0;
        ffold <= 1'b0;

	if (~uart_rdy && ~cs)
		read_data();

        ff<=ffold;

        if (uart_rdy && (uart_buf[7:0]==8'h3)) begin
           if(intack==1'b0) begin
               int <=1'b1;
           end else begin
          //    int<=1'b0;
              uart_buf[8]<=1'b0;
           end
        end else begin
           if (cs && bus_bytesel[3:0] == 4'b0001) begin
		if (bus_addr[3:0] == 4'b0000) begin
			write_data();
		end
                if (bus_addr[3:0] == 4'b1000) begin
			int<=1'b0;
		end
	   end else if (cs) begin
		if (bus_addr[3:0] == 4'b0000) begin
			bus_data <= {24'b0, uart_buf[7:0]};
                        ff <= 1'b1;
                        if (ff && ~ffold) uart_buf[8] <= 1'b0;
                end else if (bus_addr[3:0] == 4'b0100) begin
			/* Status register read. */
			bus_data <= status_reg;
		end
	   end

        end
	bus_ack <=  cs;
end

endmodule
