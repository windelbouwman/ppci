// Copyright 2015 ETH Zurich and University of Bologna.
// Copyright and related rights are licensed under the Solderpad Hardware
// License, Version 0.51 (the “License”); you may not use this file except in
// compliance with the License.  You may obtain a copy of the License at
// http://solderpad.org/licenses/SHL-0.51. Unless required by applicable law
// or agreed to in writing, software, hardware and materials distributed under
// this License is distributed on an “AS IS” BASIS, WITHOUT WARRANTIES OR
// CONDITIONS OF ANY KIND, either express or implied. See the License for the
// specific language governing permissions and limitations under the License.

module apb_fll_if
#(
    parameter APB_ADDR_WIDTH = 12
)
(
    input  logic                      HCLK,
    input  logic                      HRESETn,
    input  logic [APB_ADDR_WIDTH-1:0] PADDR,
    input  logic               [31:0] PWDATA,
    input  logic                      PWRITE,
    input  logic                      PSEL,
    input  logic                      PENABLE,
    output logic               [31:0] PRDATA,
    output logic                      PREADY,
    output logic                      PSLVERR,

    output logic                      fll1_req,
    output logic                      fll1_wrn,
    output logic                [1:0] fll1_add,
    output logic               [31:0] fll1_data,
    input  logic                      fll1_ack,
    input  logic               [31:0] fll1_r_data,
    input  logic                      fll1_lock,
    output logic                      fll2_req,
    output logic                      fll2_wrn,
    output logic                [1:0] fll2_add,
    output logic               [31:0] fll2_data,
    input  logic                      fll2_ack,
    input  logic               [31:0] fll2_r_data,
    input  logic                      fll2_lock
);

    logic        fll1_rd_access;
    logic        fll1_wr_access;
    logic        fll2_rd_access;
    logic        fll2_wr_access;

    logic        read_ready;
    logic        write_ready;
    logic [31:0] read_data;

    logic        rvalid;

    logic        fll1_ack_sync0;
    logic        fll1_ack_sync;
    logic        fll2_ack_sync0;
    logic        fll2_ack_sync;
    logic        fll1_lock_sync0;
    logic        fll1_lock_sync;
    logic        fll2_lock_sync0;
    logic        fll2_lock_sync;

    logic        fll1_valid;
    logic        fll2_valid;

    enum logic [2:0] { IDLE, CVP1_PHASE1, CVP1_PHASE2, CVP2_PHASE1, CVP2_PHASE2} state,state_next;

    always_ff @(posedge HCLK, negedge HRESETn)
    begin
        if (!HRESETn)
        begin
            fll1_ack_sync0  <= 1'b0;
            fll1_ack_sync   <= 1'b0;
            fll2_ack_sync0  <= 1'b0;
            fll2_ack_sync   <= 1'b0;
            fll1_lock_sync0 <= 1'b0;
            fll1_lock_sync  <= 1'b0;
            fll2_lock_sync0 <= 1'b0;
            fll2_lock_sync  <= 1'b0;
            state           <= IDLE;
        end
        else
        begin
            fll1_ack_sync0  <= fll1_ack;
            fll1_ack_sync   <= fll1_ack_sync0;
            fll2_ack_sync0  <= fll2_ack;
            fll2_ack_sync   <= fll2_ack_sync0;
            fll1_lock_sync0 <= fll1_lock;
            fll1_lock_sync  <= fll1_lock_sync0;
            fll2_lock_sync0 <= fll2_lock;
            fll2_lock_sync  <= fll2_lock_sync0;
            state           <= state_next;
        end
    end

    always_comb
    begin
        state_next    = IDLE;
        rvalid        = 1'b0;
        fll1_req      = 1'b0;
        fll2_req      = 1'b0;
        fll1_valid    = 1'b0;
        fll2_valid    = 1'b0;

        case(state)
        IDLE:
        begin
            if (fll2_rd_access || fll2_wr_access)
            begin
                fll2_valid = 1'b1;
                state_next = CVP2_PHASE1;
            end
            else if (fll1_rd_access || fll1_wr_access)
            begin
                fll1_valid = 1'b1;
                state_next = CVP1_PHASE1;
            end
        end

        CVP1_PHASE1:
        begin
            if (fll1_ack_sync)
            begin
                fll1_req   = 1'b0;
                fll1_valid = 1'b0;
                state_next = CVP1_PHASE2;
                rvalid = 1'b1;
            end
            else
            begin
                fll1_req   = 1'b1;
                fll1_valid = 1'b1;
                state_next = CVP1_PHASE1;
            end
        end

        CVP1_PHASE2:
        begin
            if (!fll1_ack_sync)
                state_next = IDLE;
            else
                state_next = CVP1_PHASE2;
        end

        CVP2_PHASE1:
        begin
            if (fll2_ack_sync)
            begin
                fll2_req   = 1'b0;
                fll2_valid = 1'b0;
                state_next = CVP2_PHASE2;
                rvalid     = 1'b1;
            end
            else
            begin
                fll2_req   = 1'b1;
                fll2_valid = 1'b1;
                state_next = CVP2_PHASE1;
            end
        end

        CVP2_PHASE2:
        begin
            if (!fll2_ack_sync)
                state_next = IDLE;
            else
                state_next = CVP2_PHASE2;
        end
        endcase
    end

    // write logic
    always_comb
    begin
      // default assignments
      fll1_wr_access = 1'b0;
      fll2_wr_access = 1'b0;
      write_ready    = 1'b0;

      if (PSEL && PENABLE && PWRITE) begin
        unique case (PADDR[5:2])
          // Direct access to FLL1
          4'b0000,
          4'b0001,
          4'b0010,
          4'b0011: begin
            fll1_wr_access = 1'b1;
            write_ready    = rvalid;
          end

          // Direct access to FLL2
          4'b0100,
          4'b0101,
          4'b0110,
          4'b0111: begin
            fll2_wr_access = 1'b1;
            write_ready    = rvalid;
          end

          // There are no additional registers to write
          default: begin
            write_ready = 1'b1;
          end
        endcase
      end
    end

    // read logic
    always_comb
    begin
      // default assignments
      fll1_rd_access = 1'b0;
      fll2_rd_access = 1'b0;
      read_ready     = 1'b0;
      read_data      = '0;

      if (PSEL && PENABLE && (~PWRITE)) begin
        unique case (PADDR[5:2])
          // Direct FLL access to FLL1
          4'b0000,
          4'b0001,
          4'b0010,
          4'b0011: begin
            fll1_rd_access = 1'b1;
            read_data      = fll1_r_data;
            read_ready     = rvalid;
          end

          // Direct FLL access to FLL2
          4'b0100,
          4'b0101,
          4'b0110,
          4'b0111: begin
            fll2_rd_access = 1'b1;
            read_data      = fll2_r_data;
            read_ready     = rvalid;
          end

          4'b1000: begin
            read_data[1:0] = {fll2_lock_sync, fll1_lock_sync};
            read_ready     = 1'b1;
          end

          // There are no additional registers to read
          default: begin
            read_ready = 1'b1;
          end
        endcase
      end
    end


    assign fll1_wrn   = fll1_valid ? ~PWRITE    : 1'b0;
    assign fll1_add   = fll1_valid ? PADDR[3:2] : '0;
    assign fll1_data  = fll1_valid ? PWDATA     : '0;

    assign fll2_wrn   = fll2_valid ? ~PWRITE    : 1'b0;
    assign fll2_add   = fll2_valid ? PADDR[3:2] : '0;
    assign fll2_data  = fll2_valid ? PWDATA     : '0;

    assign PREADY     = PWRITE ? write_ready : read_ready;
    assign PRDATA     = read_data;
    assign PSLVERR    = 1'b0;

endmodule
