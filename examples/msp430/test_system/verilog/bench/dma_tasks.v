//----------------------------------------------------------------------------
// Copyright (C) 2014 Authors
//
// This source file may be used and distributed without restriction provided
// that this copyright statement is not removed from the file and that any
// derivative work contains the original copyright notice and the associated
// disclaimer.
//
// This source file is free software; you can redistribute it and/or modify
// it under the terms of the GNU Lesser General Public License as published
// by the Free Software Foundation; either version 2.1 of the License, or
// (at your option) any later version.
//
// This source is distributed in the hope that it will be useful, but WITHOUT
// ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
// FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public
// License for more details.
//
// You should have received a copy of the GNU Lesser General Public License
// along with this source; if not, write to the Free Software Foundation,
// Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
//
//----------------------------------------------------------------------------
//
// *File Name: dma_tasks.v
//
// *Module Description:
//                      generic tasks for using the Direct Memory Access interface
//
// *Author(s):
//              - Olivier Girard,    olgirard@gmail.com
//
//----------------------------------------------------------------------------
// $Rev$
// $LastChangedBy$
// $LastChangedDate$
//----------------------------------------------------------------------------

//============================================================================
// DMA Write access
//============================================================================
integer    dma_cnt_wr;
integer    dma_cnt_rd;
integer    dma_wr_error;
integer    dma_rd_error;
reg        dma_tfx_cancel;

//---------------------
// Generic write task
//---------------------
task dma_write;
   input  [15:0] addr;   // Address
   input  [15:0] data;   // Data
   input         resp;   // Expected transfer response (0: Okay / 1: Error)
   input         size;   // Access size (0: 8-bit / 1: 16-bit)

   begin
      dma_addr   = addr[15:1];
      dma_en     = 1'b1;
      dma_we     = size    ? 2'b11  :
                   addr[0] ? 2'b10  :  2'b01;
      dma_din    = data;
      @(posedge mclk or posedge dma_tfx_cancel);
      while(~dma_ready & ~dma_tfx_cancel) @(posedge mclk or posedge dma_tfx_cancel);
      dma_en     = 1'b0;
      dma_we     = 2'b00;
      dma_addr   = 15'h0000;
      dma_din    = 16'h0000;
      if (~dma_tfx_cancel) dma_cnt_wr = dma_cnt_wr+1;

      // Check transfer response
      if (~dma_tfx_cancel & (dma_resp != resp))
	begin
	   $display("ERROR: DMA interface write response check -- address: 0x%h -- response: %h / expected: %h (%t ns)", addr, dma_resp, resp, $time);
	   dma_wr_error = dma_wr_error+1;
	end
   end
endtask

//---------------------
// Write 16b task
//---------------------
task dma_write_16b;
   input  [15:0] addr;   // Address
   input  [15:0] data;   // Data
   input         resp;   // Expected transfer response (0: Okay / 1: Error)

   begin
      dma_write(addr, data, resp, 1'b1);
   end
endtask

//---------------------
// Write 8b task
//---------------------
task dma_write_8b;
   input  [15:0] addr;   // Address
   input   [7:0] data;   // Data
   input         resp;   // Expected transfer response (0: Okay / 1: Error)

   begin
      if (addr[0]) dma_write(addr, {data,  8'h00}, resp, 1'b0);
      else         dma_write(addr, {8'h00, data }, resp, 1'b0);
   end
endtask


//============================================================================
// DMA read access
//============================================================================

//---------------------
// Read check process
//---------------------
reg        dma_read_check_active;
reg [15:0] dma_read_check_addr;
reg [15:0] dma_read_check_data;
reg [15:0] dma_read_check_mask;

initial
  begin
     dma_read_check_active =  1'b0;
     dma_read_check_addr   = 16'h0000;
     dma_read_check_data   = 16'h0000;
     dma_read_check_mask   = 16'h0000;
     forever
       begin
	  @(negedge (mclk & dma_read_check_active) or posedge dma_tfx_cancel);
	  if (~dma_tfx_cancel & (dma_read_check_data !== (dma_read_check_mask & dma_dout)) & ~puc_rst)
	    begin
	       $display("ERROR: DMA interface read check -- address: 0x%h -- read: 0x%h / expected: 0x%h (%t ns)", dma_read_check_addr, (dma_read_check_mask & dma_dout), dma_read_check_data, $time);
	       dma_rd_error = dma_rd_error+1;
	    end
	  dma_read_check_active =  1'b0;
       end
  end

//---------------------
// Generic read task
//---------------------
task dma_read;
   input  [15:0] addr;   // Address
   input  [15:0] data;   // Data to check against
   input         resp;   // Expected transfer response (0: Okay / 1: Error)
   input         check;  // Enable/disable read value check
   input         size;   // Access size (0: 8-bit / 1: 16-bit)

   begin
      // Perform read transfer
      dma_addr = addr[15:1];
      dma_en   = 1'b1;
      dma_we   = 2'b00;
      dma_din  = 16'h0000;
      @(posedge mclk or posedge dma_tfx_cancel);
      while(~dma_ready & ~dma_tfx_cancel) @(posedge mclk or posedge dma_tfx_cancel);
      dma_en   = 1'b0;
      dma_addr = 15'h0000;

      // Trigger read check
      dma_read_check_active =  check;
      dma_read_check_addr   =  addr;
      dma_read_check_data   =  data;
      dma_read_check_mask   =  size    ? 16'hFFFF :
                              (addr[0] ? 16'hFF00 : 16'h00FF);
      if (~dma_tfx_cancel) dma_cnt_rd = dma_cnt_rd+1;

      // Check transfer response
      if (~dma_tfx_cancel & (dma_resp != resp))
	begin
	   $display("ERROR: DMA interface read response check -- address: 0x%h -- response: %h / expected: %h (%t ns)", addr, dma_resp, resp, $time);
	   dma_rd_error = dma_rd_error+1;
	end
   end
endtask

//---------------------
// Read 16b task
//---------------------
task dma_read_16b;
   input  [15:0] addr;   // Address
   input  [15:0] data;   // Data to check against
   input         resp;   // Expected transfer response (0: Okay / 1: Error)

   begin
      dma_read(addr, data, resp, 1'b1, 1'b1);
   end
endtask

//---------------------
// Read 8b task
//---------------------
task dma_read_8b;
   input  [15:0] addr;   // Address
   input   [7:0] data;   // Data to check against
   input         resp;   // Expected transfer response (0: Okay / 1: Error)

   begin
      if (addr[0]) dma_read(addr, {data,  8'h00}, resp, 1'b1, 1'b0);
      else         dma_read(addr, {8'h00, data }, resp, 1'b1, 1'b0);
   end
endtask

//--------------------------------
// Read 16b value task (no check)
//--------------------------------
task dma_read_val_16b;
   input  [15:0] addr;   // Address
   input         resp;   // Expected transfer response (0: Okay / 1: Error)

   begin
      dma_read(addr, 16'h0000, resp, 1'b0, 1'b1);
   end
endtask


//============================================================================
// Ramdom DMA access process
//============================================================================

integer    dma_rand_wait;
integer    dma_rand_wait_disable;
reg        dma_rand_rdwr;
reg        dma_rand_if;
integer	   dma_rand_data;
reg  [6:0] dma_rand_addr;
reg [15:0] dma_rand_addr_full;
integer    dma_mem_ref_idx;
reg [15:0] dma_pmem_reference[0:127];
reg [15:0] dma_dmem_reference[0:127];
reg	   dma_verif_on;
reg	   dma_verif_verbose;

initial
  begin
     // Initialize
   `ifdef NO_DMA_VERIF
     dma_verif_on      = 0;
   `else
     `ifdef DMA_IF_EN
     dma_verif_on      = 1;
     `else
     dma_verif_on      = 0;
     `endif     
   `endif
     dma_rand_wait_disable = 0;
     dma_verif_verbose = 0;
     dma_cnt_wr        = 0;
     dma_cnt_rd        = 0;
     dma_wr_error      = 0;
     dma_rd_error      = 0;
     #20;
     dma_rand_wait     = $urandom;
     for (dma_mem_ref_idx=0; dma_mem_ref_idx < 128; dma_mem_ref_idx=dma_mem_ref_idx+1)
       begin
	  dma_pmem_reference[dma_mem_ref_idx]             = $urandom;
	  dma_dmem_reference[dma_mem_ref_idx]		  = $urandom;
	  if (dma_verif_on && (`PMEM_SIZE>=4092) && (`DMEM_SIZE>=1024))
	    begin
	       pmem_0.mem[(`PMEM_SIZE-512)/2+dma_mem_ref_idx] = dma_pmem_reference[dma_mem_ref_idx];
	       dmem_0.mem[(`DMEM_SIZE-256)/2+dma_mem_ref_idx] = dma_dmem_reference[dma_mem_ref_idx];
	    end
       end

     // Wait for reset release
     repeat(1) @(posedge dco_clk);
     @(negedge puc_rst);

     // Perform random read/write 16b memory accesses
     if (dma_verif_on && (`PMEM_SIZE>=4092) && (`DMEM_SIZE>=1024))
       begin
	  forever
	    begin
	       // Randomize 1 or 0 wait states between accesses
	       // (1/3 proba of getting 1 wait state)
	       dma_rand_wait = dma_rand_wait_disable ? 0 : ($urandom_range(2,0)==0);
	       repeat(dma_rand_wait) @(posedge mclk);

	       // Randomize read/write accesses
	       // (1/3 proba of getting a read access)
	       dma_rand_rdwr = ($urandom_range(2,0)==0);

	       // Randomize address to be accessed (between 128 addresses)
	       dma_rand_addr = $urandom;

	       // Randomize access through PMEM or DMEM memories
	       dma_rand_if   = $urandom_range(1,0);

	       // Make sure the core is not in reset
	       while(puc_rst) @(posedge mclk);
	       
	       if (dma_rand_rdwr)
		 begin
		    if (dma_rand_if)            // Read from Program Memory
		      begin
			 dma_rand_addr_full = 16'hFE00+dma_rand_addr*2;
			 if (dma_verif_verbose) $display("READ  DMA interface -- address: 0x%h -- expected data: 0x%h", dma_rand_addr_full, dma_pmem_reference[dma_rand_addr]);
			 dma_read_16b(dma_rand_addr_full,  dma_pmem_reference[dma_rand_addr], 1'b0);
		      end
		    else                        // Read from Data Memory
		      begin
			 dma_rand_addr_full = `PER_SIZE+`DMEM_SIZE-256+dma_rand_addr*2;
			 if (dma_verif_verbose) $display("READ  DMA interface -- address: 0x%h -- expected data: 0x%h", dma_rand_addr_full, dma_dmem_reference[dma_rand_addr]);
			 dma_read_16b(dma_rand_addr_full,  dma_dmem_reference[dma_rand_addr], 1'b0);
		      end
		 end
	       else
		 begin
		    dma_rand_data = $urandom;

		    if (dma_rand_if)            // Write to Program memory
		      begin
			 dma_rand_addr_full = 16'hFE00+dma_rand_addr*2;
			 if (dma_verif_verbose) $display("WRITE DMA interface -- address: 0x%h -- data: 0x%h", dma_rand_addr_full, dma_rand_data[15:0]);
			 dma_write_16b(dma_rand_addr_full, dma_rand_data[15:0], 1'b0);
			 dma_pmem_reference[dma_rand_addr] = dma_rand_data[15:0];
			 #1;
			 if (pmem_0.mem[(`PMEM_SIZE-512)/2+dma_rand_addr] !== dma_rand_data[15:0])
			   begin
			      $display("ERROR: DMA interface write -- address: 0x%h -- wrote: 0x%h / expected: 0x%h (%t ns)", dma_rand_addr_full, dma_rand_data[15:0], pmem_0.mem[(`PMEM_SIZE-512)/2+dma_rand_addr], $time);
			      dma_wr_error = dma_wr_error+1;
			   end
		      end
		    else                        // Write to Data Memory
		      begin
			 dma_rand_addr_full = `PER_SIZE+`DMEM_SIZE-256+dma_rand_addr*2;
			 if (dma_verif_verbose) $display("WRITE DMA interface -- address: 0x%h -- data: 0x%h", dma_rand_addr_full, dma_rand_data[15:0]);
			 dma_write_16b(dma_rand_addr_full, dma_rand_data[15:0], 1'b0);
			 dma_dmem_reference[dma_rand_addr] = dma_rand_data[15:0];
			 #1;
			 if (dmem_0.mem[(`DMEM_SIZE-256)/2+dma_rand_addr] !== dma_rand_data[15:0])
			   begin
			      $display("ERROR: DMA interface write -- address: 0x%h -- wrote: 0x%h / expected: 0x%h (%t ns)", dma_rand_addr_full, dma_rand_data[15:0], dmem_0.mem[(`DMEM_SIZE-256)/2+dma_rand_addr], $time);
			      dma_wr_error = dma_wr_error+1;
			   end
		      end
		 end
	    end
       end
  end
