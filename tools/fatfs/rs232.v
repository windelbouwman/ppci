module rs232 (
	input clk,
	input resetn,

	input [ 3:0] ctrl_wr,
	input        ctrl_rd,
	input [15:0] ctrl_addr,
	input [31:0] ctrl_wdat,
	output reg [31:0] ctrl_rdat,
	output reg ctrl_done,
   input rxd,
	output reg txd
);
	parameter integer BAUD_RATE = 115200;
	parameter integer CLOCK_FREQ_HZ = 50000000;
	localparam integer HALF_PERIOD = CLOCK_FREQ_HZ / (2 * BAUD_RATE);

	reg [7:0] send_din;
	wire [7:0] send_dout;
	reg send_shift_in;
	reg send_shift_out;
	wire [7:0] send_used_slots;
	wire [7:0] send_free_slots;

	reg [7:0] recv_din;
	wire [7:0] recv_dout;
	reg recv_shift_in;
	reg recv_shift_out;
	wire [7:0] recv_used_slots;
	wire [7:0] recv_free_slots;

	
	reg [$clog2(3*HALF_PERIOD):0] rx_cnt;
	reg [3:0] rx_state;
	reg rxd_q;

	always @(posedge clk) begin
		rxd_q <= rxd;
		recv_shift_in <= 0;

		if (!resetn) begin
			rx_state <= 0;
			rx_cnt <= 0;
		end else
		if (rx_cnt) begin
			rx_cnt <= rx_cnt - |1;
		end else
		if (rx_state == 0) begin
			if (rxd_q && !rxd) begin
				rx_state <= rx_state + |1;
				rx_cnt <= 3*HALF_PERIOD;
			end
		end else begin
			recv_din <= {rxd, recv_din[7:1]};
			rx_state <= rx_state + |1;
			rx_cnt <= 2*HALF_PERIOD;

			if (rx_state == 8) begin
				recv_shift_in <= 1;
				rx_state <= 0;
			end
		end
	end

	reg [$clog2(2*HALF_PERIOD):0] tx_cnt;
	reg [3:0] tx_state;
	reg [7:0] tx_byte;

	always @(posedge clk) begin
		send_shift_out <= 0;
		if (!resetn) begin
			txd <= 1;
			tx_state <= 0;
			tx_cnt <= 0;
		end else
		if (tx_cnt) begin
			tx_cnt <= tx_cnt - |1;
		end else
		if (tx_state == 0) begin
			if (|send_used_slots) begin
				txd <= 0;
				send_shift_out <= 1;
				tx_byte <= send_dout;
				tx_cnt <= 2*HALF_PERIOD;
				tx_state <= 1;
			end
		end else begin
			txd <= tx_byte[0];
			tx_byte <= tx_byte[7:1];
			tx_cnt <= 2*HALF_PERIOD;
			tx_state <= tx_state + |1;

			if (tx_state == 9) begin
				txd <= 1;
				tx_state <= 0;
			end
		end
	end

	icosoc_mod_rs232_fifo send_fifo (
		.clk       (clk            ),
		.resetn    (resetn         ),
		.din       (send_din       ),
		.dout      (send_dout      ),
		.shift_in  (send_shift_in  ),
		.shift_out (send_shift_out ),
		.used_slots(send_used_slots),
		.free_slots(send_free_slots)
	);

	icosoc_mod_rs232_fifo recv_fifo (
		.clk       (clk            ),
		.resetn    (resetn         ),
		.din       (recv_din       ),
		.dout      (recv_dout      ),
		.shift_in  (recv_shift_in  ),
		.shift_out (recv_shift_out ),
		.used_slots(recv_used_slots),
		.free_slots(recv_free_slots)
	);

	always @(posedge clk) begin
		ctrl_rdat <= 'bx;
		ctrl_done <= 0;

		recv_shift_out <= 0;
		send_shift_in <= 0;
		send_din <= 'bx;

		// Register file:
		//   0x00 shift data to/from send/recv fifos
		//   0x04 number of unread bytes in recv fifo (read-only)
		//   0x08 number of free bytes in send fifo (read-only)
		if (resetn && !ctrl_done) begin
			if (|ctrl_wr) begin
				if (ctrl_addr == 0) begin
					send_shift_in <= 1;
					send_din <= ctrl_wdat;
				end
				ctrl_done <= 1;
			end
			if (ctrl_rd) begin
				if (ctrl_addr == 0) begin
					recv_shift_out <= 1;
					ctrl_rdat <= recv_dout;
				end
				if (ctrl_addr == 4) ctrl_rdat <= recv_used_slots;
				if (ctrl_addr == 8) ctrl_rdat <= send_free_slots;
				ctrl_done <= 1;
			end
		end
	end
endmodule

module icosoc_mod_rs232_fifo (
	input clk,
	input resetn,

	input [7:0] din,
	output [7:0] dout,

	input shift_in,
	input shift_out,
	output reg [7:0] used_slots,
	output reg [7:0] free_slots
);
	reg [7:0] memory [0:255];
	reg [7:0] wptr, rptr;

	reg [7:0] memory_dout;
	reg [7:0] pass_dout;
	reg use_pass_dout;

	assign dout = use_pass_dout ? pass_dout : memory_dout;

	wire do_shift_in = shift_in && |free_slots;
	wire do_shift_out = shift_out && |used_slots;

	always @(posedge clk) begin
		if (!resetn) begin
			wptr <= 0;
			rptr <= 0;
			used_slots <= 0;
			free_slots <= 255;
		end else begin
			memory[wptr] <= din;
			wptr <= wptr + do_shift_in;

			memory_dout <= memory[rptr + do_shift_out];
			rptr <= rptr + do_shift_out;

			use_pass_dout <= wptr == rptr;
			pass_dout <= din;

			if (do_shift_in && !do_shift_out) begin
				used_slots <= used_slots + 1;
				free_slots <= free_slots - 1;
			end

			if (!do_shift_in && do_shift_out) begin
				used_slots <= used_slots - 1;
				free_slots <= free_slots + 1;
			end
		end
	end
endmodule

