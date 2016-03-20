

module  axi2apb_ctrl (
   input  logic clk,
   input  logic rstn,

   input  logic finish_wr,
   input  logic finish_rd,

   input  logic cmd_empty,
   input  logic cmd_read,
   input  logic WVALID,

   output logic psel,
   output logic penable,
   output logic pwrite,
   input  logic pready
 );  
   
   logic wstart;
   logic rstart;
   
   logic busy;
   logic pack;
   logic cmd_ready;
   

   assign cmd_ready = (~busy) & (~cmd_empty);
   assign wstart = cmd_ready & (~cmd_read) & (~psel) & WVALID;
   assign rstart = cmd_ready & cmd_read & (~psel);
   
   assign pack = psel & penable & pready;
   
   always @(posedge clk or negedge rstn)
     if (!rstn)
       busy <=  1'b0;
     else if (psel)
       busy <=  1'b1;
     else if (finish_rd | finish_wr)
       busy <=  1'b0;
   
   always @(posedge clk or negedge rstn)
     if (!rstn)
       psel <=  1'b0;
     else if (pack)
       psel <=  1'b0;
     else if (wstart | rstart)
       psel <=  1'b1;
   
   always @(posedge clk or negedge rstn)
     if (!rstn)
       penable <=  1'b0;
     else if (pack)
       penable <=  1'b0;
     else if (psel)
       penable <=  1'b1;

   always @(posedge clk or negedge rstn)
     if (!rstn)
       pwrite  <=  1'b0;
     else if (pack)
       pwrite  <=  1'b0;
     else if (wstart)
       pwrite  <=  1'b1;
   

endmodule

   


