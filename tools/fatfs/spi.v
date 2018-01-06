module spi #(
	parameter integer CLOCK_FREQ_HZ = 0,
	parameter integer CS_LENGTH = 32
) (
	input clk,
	input resetn,

	input ctrl_wr,
	input ctrl_rd,
	input [ 7:0] ctrl_addr,
	input [31:0] ctrl_wdat,
	output reg [31:0] ctrl_rdat,
	output reg ctrl_done,

	output [CS_LENGTH-1:0] cs,
   output mosi,
   input miso,
   output sclk
);
	wire spi_miso;
	reg spi_mosi, spi_sclk;
	reg [CS_LENGTH-1:0] spi_cs;

	reg mode_cpol;
	reg mode_cpha;

	reg [7:0] prescale_cnt;
	reg [7:0] prescale_cfg;
	reg [7:0] spi_data;
	reg [4:0] spi_state;

        assign sclk = spi_sclk ^ ~mode_cpol;
        assign cs = spi_cs;
        assign spi_miso = miso;
		  assign mosi = spi_mosi;

	always @(posedge clk) begin
		ctrl_rdat <= 'bx;
		ctrl_done <= 0;
		if (!resetn) begin
			spi_mosi <= 0;
			spi_sclk <= 1;
			spi_cs <= ~0;

			mode_cpol <= 1;
			mode_cpha <= 1;
			prescale_cnt <= 0;
			prescale_cfg <= 4;
			spi_state <= 0;
		end else
		if (!ctrl_done) begin
			if (ctrl_wr) begin
				ctrl_done <= 1;
				if (ctrl_addr == 'h00) prescale_cfg <= ctrl_wdat;
				if (ctrl_addr == 'h04) begin
					spi_cs <= ctrl_wdat;
					ctrl_done <= prescale_cnt == prescale_cfg;
					prescale_cnt <= prescale_cnt == prescale_cfg ? 0 : prescale_cnt + 1;
				end
				if (ctrl_addr == 'h08) begin
					if (!prescale_cnt) begin
						if (spi_state == 0) begin
							spi_data <= ctrl_wdat;
							spi_mosi <= ctrl_wdat[7];
						end else begin
							if (spi_state[0])
								spi_data <= {spi_data, spi_miso};
							else if (spi_state < 16)
								spi_mosi <= spi_data[7];
						end
					end
					spi_sclk <= spi_state[0] ^ ~mode_cpha;
					ctrl_done <= spi_state == (mode_cpha ? 15 : 16) && prescale_cnt == prescale_cfg;
					spi_state <= prescale_cnt == prescale_cfg ? (spi_state[4] ? 0 : spi_state + 1) : spi_state;
					if (mode_cpha) spi_state[4] <= 0;
					prescale_cnt <= prescale_cnt == prescale_cfg ? 0 : prescale_cnt + 1;
				end
				if (ctrl_addr == 'h0c) begin
					{mode_cpol, mode_cpha} <= ctrl_wdat;
					ctrl_done <= prescale_cnt == prescale_cfg;
					prescale_cnt <= prescale_cnt == prescale_cfg ? 0 : prescale_cnt + 1;
				end
			end
			if (ctrl_rd) begin
				ctrl_done <= 1;
				if (ctrl_addr == 'h00) ctrl_rdat <= prescale_cfg;
				if (ctrl_addr == 'h04) ctrl_rdat <= spi_cs;
				if (ctrl_addr == 'h08) ctrl_rdat <= spi_data;
				if (ctrl_addr == 'h0c) ctrl_rdat <= {mode_cpol, mode_cpha};
			end
		end
	end
endmodule

