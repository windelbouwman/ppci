`timescale 1 ns / 1 ps
//`define DEBUG
module system_tb;
        integer i;	   
	reg clk = 1;
	always #5 clk = ~clk;

	reg resetn = 0;
	initial begin
		if ($test$plusargs("vcd")) begin
			$dumpfile("system.vcd");
		        $dumpvars(0, system_tb);
                        for (i = 0; i < 32; i = i + 1) begin
		           $dumpvars(0,system_tb.uut.picorv32_core.cpuregs[i]);
			end  		
		end
		repeat (100) @(posedge clk);
		resetn <= 1;
	end

	wire trap;
	wire [7:0] out_byte;
	wire out_byte_en;

	system uut (
		.clk        (clk        ),
		.resetn     (resetn     ),
		.trap       (trap       ),
                .out_byte   (out_byte   ),
		.out_byte_en(out_byte_en)
	);

	always @(posedge clk) begin
		if (resetn && trap) begin
			$finish;
		end
	end
endmodule
