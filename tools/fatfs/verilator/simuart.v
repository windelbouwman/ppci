import "DPI-C" context function int init_socket();
import "DPI-C" context function void close_socket();
import "DPI-C" context function void senduart(input bit[7:0] in);
import "DPI-C" context function bit[8:0] recuart();

module simuart(input wire		clk,
	       input wire		cs,
	       input wire [31:0]	bus_addr,
	       input wire [31:0]	bus_wr_val,	
	       input wire [3:0]		bus_bytesel,
	       output reg		bus_ack,
	       output reg [31:0]	bus_data,
               output reg inter,
               input wire intack
);

reg [8:0] uart_buf;
reg ff;
reg ffold;

initial begin
	bus_ack = 1'b0;
	bus_data = 32'b0;
        inter = 1'b0;
        init_socket();
end

final begin
     close_socket();
end

always @(posedge clk) begin

	bus_data <= 32'b0;
        ff <= 1'b0;
        ffold <= 1'b0;

	if (~uart_buf[8] && ~cs)
	   uart_buf <= recuart();

        ff<=ffold;

        if (uart_buf[8] && (uart_buf[7:0]==8'h3)) begin
           if(intack==1'b0) begin
               inter <=1'b1;
           end else begin
               uart_buf[8]<=1'b0;
           end
        end else begin
           if (cs && bus_bytesel[3:0] == 4'b0001) begin
		if (bus_addr[3:0] == 4'b0000) begin
			senduart(bus_wr_val[7:0]);
		end
                if (bus_addr[3:0] == 4'b1000) begin
			inter<=1'b0;
		end
                if (bus_addr[3:0] == 4'b1100) begin
			inter<=1'b1;
		end
	   end else if (cs) begin
		if (bus_addr[3:0] == 4'b0000) begin
			bus_data <= {24'b0, uart_buf[7:0]};
                        ff <= 1'b1;
                        if (ff && ~ffold) uart_buf[8] <= 1'b0;
                end else if (bus_addr[3:0] == 4'b0100) begin
			/* Status register read. */
			bus_data <= (uart_buf[8] ? 32'b10 : 32'b0);
		end
	   end

        end
	bus_ack <=  cs;

end

endmodule
