`timescale 1 ns / 1 ps

module system (
	input            clk,
	input            resetn,
	output           trap,
        output reg [7:0] out_byte,
	output reg       out_byte_en
);
	// set this to 0 for better timing but less performance/MHz
	parameter FAST_MEMORY = 0;

	// 4096 32bit words = 16kB memory
	parameter MEM_SIZE = 16384;

        integer            tb_idx;

	wire mem_valid;
	wire mem_instr;
	reg mem_ready;
	wire [31:0] mem_addr;
	wire [31:0] mem_wdata;
	wire [3:0] mem_wstrb;
	reg [31:0] mem_rdata;

	wire mem_la_read;
	wire mem_la_write;
	wire [31:0] mem_la_addr;
	wire [31:0] mem_la_wdata;
	wire [3:0] mem_la_wstrb;

        wire uart_cs;
       	wire [3:0] uart_wstrb;
        wire [31:0] uart_rdata;
        wire [31:0] irqs;
        wire [31:0] eois;

	picorv32 picorv32_core (
		.clk         (clk         ),
		.resetn      (resetn      ),
		.trap        (trap        ),
		.mem_valid   (mem_valid   ),
		.mem_instr   (mem_instr   ),
		.mem_ready   (mem_ready   ),
		.mem_addr    (mem_addr    ),
		.mem_wdata   (mem_wdata   ),
		.mem_wstrb   (mem_wstrb   ),
		.mem_rdata   (mem_rdata   ),
		.mem_la_read (mem_la_read ),
		.mem_la_write(mem_la_write),
		.mem_la_addr (mem_la_addr ),
		.mem_la_wdata(mem_la_wdata),
		.mem_la_wstrb(mem_la_wstrb),
                .irq(irqs),
                .eoi(eois)
	);

      `ifndef MEM_FILENAME
             simuart uart(
		.clk(clk),
		.cs(uart_cs),
		.bus_addr(mem_addr),
		.bus_wr_val(mem_wdata),
		.bus_bytesel(uart_wstrb),
		.bus_ack(),
		.bus_data(uart_rdata),
                .inter(irqs[0]),
                .intack(eois[0])
             );
      `else
           assign uart_rdata = 32'b0;
           assign irqs = 32'b0;
      `endif



       assign irqs[31:1] = 31'b0;
       assign uart_cs =  mem_addr[31:4] == 28'h1000000 && mem_valid;
       assign uart_wstrb = mem_wstrb & mem_ready;
   
	reg [31:0] memory [0:MEM_SIZE-1];
	initial begin
                for (tb_idx=0; tb_idx < MEM_SIZE; tb_idx=tb_idx+1)
                       memory[tb_idx] = 32'b0;
                `ifdef MEM_FILENAME
                     $readmemh(`MEM_FILENAME, memory);
                `else
                     $readmemh("../firmware.hex", memory);
                `endif
        end

	reg [31:0] m_read_data;
	reg m_read_en;

	generate if (FAST_MEMORY) begin
		always @(posedge clk) begin
			mem_ready <= 1;
			mem_rdata <= memory[mem_la_addr >> 2];
			if (mem_la_write && (mem_la_addr >> 2) < MEM_SIZE) begin
				if (mem_la_wstrb[0]) memory[mem_la_addr >> 2][ 7: 0] <= mem_la_wdata[ 7: 0];
				if (mem_la_wstrb[1]) memory[mem_la_addr >> 2][15: 8] <= mem_la_wdata[15: 8];
				if (mem_la_wstrb[2]) memory[mem_la_addr >> 2][23:16] <= mem_la_wdata[23:16];
				if (mem_la_wstrb[3]) memory[mem_la_addr >> 2][31:24] <= mem_la_wdata[31:24];
			end
			else
			if (mem_la_write && mem_la_addr == 32'h1000_0000) begin				
			end
		end
	end else begin
		always @(posedge clk) begin
			m_read_en <= 0;
			mem_ready <= mem_valid && !mem_ready && m_read_en;

                        out_byte_en <= 0;
                   			
			(* parallel_case *)
			case (1)
				mem_valid && !mem_ready && !mem_wstrb && (mem_addr >> 2) < MEM_SIZE: begin
					m_read_en <= 1;
				        m_read_data <= memory[mem_addr >> 2];
				        mem_rdata <= m_read_data;
				end
				mem_valid && !mem_ready && |mem_wstrb && (mem_addr >> 2) < MEM_SIZE: begin
					if (mem_wstrb[0]) memory[mem_addr >> 2][ 7: 0] <= mem_wdata[ 7: 0];
					if (mem_wstrb[1]) memory[mem_addr >> 2][15: 8] <= mem_wdata[15: 8];
					if (mem_wstrb[2]) memory[mem_addr >> 2][23:16] <= mem_wdata[23:16];
					if (mem_wstrb[3]) memory[mem_addr >> 2][31:24] <= mem_wdata[31:24];
					mem_ready <= 1;
				end
				
			        mem_valid && !mem_ready && !mem_wstrb && uart_cs: begin
					m_read_en <= 1;
                                        mem_rdata <= uart_rdata;
                                        //mem_rdata <= m_read_data;
				end
                                mem_valid && !mem_ready && |mem_wstrb && mem_addr == 32'h2000_0000: begin
					out_byte_en <= 1;
					out_byte <= mem_wdata;
					mem_ready <= 1;
				end
				mem_valid && !mem_ready && |mem_wstrb : begin
					mem_ready <= 1;
				end
			endcase
                        if (resetn && out_byte_en) begin
			   $write("%c", out_byte);
		        end
		end
	end endgenerate
endmodule
