`timescale 1 ns / 1 ps

module system (
	input            clk,
	input            resetn,
        `ifndef verilator
            output  sck,
            output  cs,
            output mosi,
            input miso,
            output txd,
	    input rxd,
        `endif
       	output           trap
);

	// 32768 32bit words = 128kB memory
	parameter MEM_SIZE = 32768;

        integer            tb_idx;

	wire mem_valid;
	wire mem_instr;
	reg mem_ready;
	wire [31:0] mem_addr;
	wire [31:0] mem_wdata;
	wire [3:0] mem_wstrb;
	reg [31:0] mem_rdata;
   

        wire [31:0] irqs;
        wire [31:0] eois;
        wire spi_cs;
        wire uart_cs;
        wire uart_done;
        wire mem_cs;
        wire [3:0] wstrb;
        wire wr;
        wire rd;        
        wire [31:0] spi_rdata;
        wire spi_done;
        wire [31:0] uart_rdata;
		  

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
                .irq(irqs),
                .eoi(eois)
	);

        `ifdef verilator
            simsd sd(
		.clk(clk),
		.cs(spi_cs),
		.bus_addr(mem_addr),
		.bus_wr_val(mem_wdata),
		.bus_bytesel(mem_wstrb && mem_ready),
		.bus_ack(spi_done),
		.bus_data(spi_rdata)
             );
        `else
          spi #(
                .CLOCK_FREQ_HZ(50000000),
                .CS_LENGTH(1)
                ) sd (
		.clk(clk),
                .resetn(resetn),
                .ctrl_addr(mem_addr),
                .ctrl_wdat(mem_wdata),
                .ctrl_rdat(spi_rdata),
                .ctrl_wr(spi_cs && wr),
                .ctrl_rd(spi_cs && rd),
                .ctrl_done(spi_done),
                .sclk(sck),
                .mosi(mosi),
                .miso(miso),
                .cs(cs)
             );
				 
		 rs232 uart(
		 .clk(clk),
		 .resetn(resetn),
		 .ctrl_wr(uart_cs && wr),
		 .ctrl_rd(uart_cs && rd),
		 .ctrl_addr(mem_addr),
		 .ctrl_wdat(mem_wdata),
		 .ctrl_rdat(uart_rdata),
		 .ctrl_done(uart_done),
		 .rxd(rxd),
		 .txd(txd)
		 );
         `endif

       assign irqs[31:1] = 31'b0;
       assign spi_cs =  mem_addr[31:4] == 28'h4000000 && mem_valid;
       assign uart_cs = mem_addr[31:4] == 32'h2000000 && mem_valid;
       assign mem_cs = (mem_addr >> 2) < MEM_SIZE && mem_valid;
       assign wr = |mem_wstrb && !mem_ready;
       assign rd = !mem_wstrb && !mem_ready;

		 
   
        reg [3:0][7:0] memory [0:MEM_SIZE-1];
	initial begin
              //  for (tb_idx=0; tb_idx < MEM_SIZE; tb_idx=tb_idx+1)
              //         memory[tb_idx] = 32'b0;
                       $readmemh("../firmware.hex", memory);
        end

	reg [31:0] m_read_data;
	reg m_read_en;

	always @(posedge clk) begin
			m_read_en <= 0;
			mem_ready <= mem_valid && !mem_ready && m_read_en;

			(* parallel_case *)
			case (1)
				mem_cs:
                                begin
                                if(wr) begin
                                        if (mem_wstrb[0]) memory[mem_addr >> 2][0] <= mem_wdata[ 7: 0];
					if (mem_wstrb[1]) memory[mem_addr >> 2][1] <= mem_wdata[15: 8];
					if (mem_wstrb[2]) memory[mem_addr >> 2][2] <= mem_wdata[23:16];
					if (mem_wstrb[3]) memory[mem_addr >> 2][3] <= mem_wdata[31:24];
					mem_ready <= 1;
                                end
                                       	m_read_en <= 1;
				        m_read_data <= memory[mem_addr >> 2];
				        mem_rdata <= m_read_data;
				end
				

                                spi_cs : begin
                                if(rd) begin
					m_read_en <= spi_done;
                                        mem_rdata <= spi_rdata;
                                end
                                if(wr) mem_ready <= spi_done;

				end

				uart_cs: begin
                                    if(rd) begin
                                	m_read_en <= uart_done;
                                        mem_rdata <= uart_rdata;
                                    end
                                    if(wr) begin
                                       mem_ready <= uart_done;
                                      `ifdef verilator
                                           if (resetn) $write("%c", mem_wdata);
	  				   mem_ready <= 1;
				       `endif
			            end
                                end
			endcase
		end
endmodule
