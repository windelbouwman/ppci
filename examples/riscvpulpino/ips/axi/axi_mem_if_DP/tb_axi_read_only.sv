// Copyright 2015 ETH Zurich and University of Bologna.
// Copyright and related rights are licensed under the Solderpad Hardware
// License, Version 0.51 (the “License”); you may not use this file except in
// compliance with the License.  You may obtain a copy of the License at
// http://solderpad.org/licenses/SHL-0.51. Unless required by applicable law
// or agreed to in writing, software, hardware and materials distributed under
// this License is distributed on an “AS IS” BASIS, WITHOUT WARRANTIES OR
// CONDITIONS OF ANY KIND, either express or implied. See the License for the
// specific language governing permissions and limitations under the License.

`timescale 1ns/1ps
`define CLK_PERIOD 1.0

module tb_axi_read_only();

    parameter AXI4_ADDRESS_WIDTH = 32;
    parameter AXI4_RDATA_WIDTH   = 64;
    parameter AXI4_WDATA_WIDTH   = 64;
    parameter AXI4_ID_WIDTH      = 16;
    parameter AXI4_USER_WIDTH    = 10;
    parameter AXI_NUMBYTES       = AXI4_WDATA_WIDTH/8;
    parameter MEM_ADDR_WIDTH     = 16;


    logic                            clk      ;
    logic                            rst_n    ;

    logic [AXI4_ID_WIDTH-1:0]        ARID     ;
    logic [AXI4_ADDRESS_WIDTH-1:0]   ARADDR   ;
    logic [ 7:0]                     ARLEN    ;
    logic [ 2:0]                     ARSIZE   ;
    logic [ 1:0]                     ARBURST  ;
    logic                            ARLOCK   ;
    logic [ 3:0]                     ARCACHE  ;
    logic [ 2:0]                     ARPROT   ;
    logic [ 3:0]                     ARREGION ;
    logic [ AXI4_USER_WIDTH-1:0]     ARUSER   ;
    logic [ 3:0]                     ARQOS    ;
    logic                            ARVALID  ;
    logic                            ARREADY  ;

    logic [AXI4_ID_WIDTH-1:0]        RID      ;
    logic [AXI4_RDATA_WIDTH-1:0]     RDATA    ;
    logic [ 1:0]                     RRESP    ;
    logic                            RLAST    ;
    logic [AXI4_USER_WIDTH-1:0]      RUSER    ;
    logic                            RVALID   ;
    logic                            RREADY   ;

    logic                            MEM_CEN  ;
    logic                            MEM_WEN  ;
    logic  [MEM_ADDR_WIDTH-1:0]      MEM_A    ;
    logic  [AXI4_RDATA_WIDTH-1:0]    MEM_D    ;
    logic  [AXI_NUMBYTES-1:0]        MEM_BE   ;
    logic  [AXI4_RDATA_WIDTH-1:0]    MEM_Q    ;

    logic                            grant    ;
    logic                            valid    ;
    logic [31:0]                     temp_address;
    logic [7:0]                      temp_len;
    logic [AXI4_ID_WIDTH-1:0]        temp_id = 0;
    logic                            Pop_Packet = 1'b1;




    typedef struct {
        logic [AXI4_ADDRESS_WIDTH-1:0]  address;
        logic [7:0]                     len;
        logic [AXI4_ID_WIDTH-1:0]       id;
    } PACKET_type;


    PACKET_type PACKET_QUEUE[$];
    PACKET_type PACKET_IN, PACKET_OUT;



    event grant_ar_event;

    always  @(posedge clk )
    begin
        grant <= $random%2;
        RREADY <=  $random%2;

        if(ARVALID & ARREADY)
            -> grant_ar_event;
    end


    always
    begin
        #(`CLK_PERIOD);
        clk = ~clk;
    end


    initial
    begin
        AR_NOP;

        rst_n = 1'b1;
        clk = 1'b1;
        @(negedge clk);
        @(negedge clk);
        @(negedge clk);
        rst_n = 1'b0;
        @(negedge clk);
        @(negedge clk);
        @(negedge clk);
        rst_n = 1'b1;
        @(negedge clk);

        repeat (10000)
        begin
            temp_address         = $random;
            temp_address[2:0]    = '0;
            temp_address[31:16]  = '0;
            temp_len             = $random;
            temp_id              = temp_id + 1'b1;

            PACKET_IN.address    = temp_address;
            PACKET_IN.len        = temp_len;
            PACKET_IN.id         = temp_id;

            AR_READ (.address(temp_address),  .len(temp_len) , .user('1), .id(temp_id) );
            PACKET_QUEUE.push_front(PACKET_IN);
            $display("Push fifo %8h, %d, %d", temp_address, temp_len, temp_id);
        end

        $stop;
    end


    int unsigned counter = 0;


    always @(posedge clk, negedge clk)
    begin

        if(clk == 0)
        begin
            if(Pop_Packet)
            begin
                if(PACKET_QUEUE.size() > 0 )
                begin
                    PACKET_OUT = PACKET_QUEUE.pop_back();
                    Pop_Packet = 1'b0;
                end
            end
        end

        if(clk)
        begin
            if(RREADY & RVALID)
            begin



                if((RDATA != PACKET_OUT.address+counter*8) || (RID != PACKET_OUT.id) )
                begin
                    $error("Error at %t: Read %16h, expected %16h", $time(), RDATA, (PACKET_OUT.address+counter*8)  );
                    $stop;
                end


                if(RLAST)
                begin
                    if(counter != PACKET_OUT.len)
                    begin
                        $error("inject too many packets: injected %d, eexpected %d", counter, PACKET_OUT.len);
                        $stop;
                    end
                    counter = 0;
                    Pop_Packet = 1'b1;

                end
                else
                begin
                    counter =counter + 1;
                end


            end
        end

    end





always @(posedge clk)
begin
    if(RVALID & RREADY)
    begin
        if(RLAST)
                $display(" at %t[ns] read value is 0x%16h\n\n", $time()/1000.0, RDATA  );
        else
                $display(" at %t[ns] read value is 0x%16h", $time()/1000.0, RDATA  );
    end
end

axi_read_only_ctrl
#(
    .AXI4_ADDRESS_WIDTH ( AXI4_ADDRESS_WIDTH  ),
    .AXI4_RDATA_WIDTH   ( AXI4_RDATA_WIDTH    ),
    .AXI4_WDATA_WIDTH   ( AXI4_WDATA_WIDTH    ),
    .AXI4_ID_WIDTH      ( AXI4_ID_WIDTH       ),
    .AXI4_USER_WIDTH    ( AXI4_USER_WIDTH     ),
    .AXI_NUMBYTES       ( AXI_NUMBYTES        ),
    .MEM_ADDR_WIDTH     ( MEM_ADDR_WIDTH      )
)
DUT
(
    .clk            (  clk       ),
    .rst_n          (  rst_n     ),

    .ARID_i         (  ARID      ),
    .ARADDR_i       (  ARADDR    ),
    .ARLEN_i        (  ARLEN     ),
    .ARSIZE_i       (  ARSIZE    ),
    .ARBURST_i      (  ARBURST   ),
    .ARLOCK_i       (  ARLOCK    ),
    .ARCACHE_i      (  ARCACHE   ),
    .ARPROT_i       (  ARPROT    ),
    .ARREGION_i     (  ARREGION  ),
    .ARUSER_i       (  ARUSER    ),
    .ARQOS_i        (  ARQOS     ),
    .ARVALID_i      (  ARVALID   ),
    .ARREADY_o      (  ARREADY   ),

    .RID_o          (  RID       ),
    .RDATA_o        (  RDATA     ),
    .RRESP_o        (  RRESP     ),
    .RLAST_o        (  RLAST     ),
    .RUSER_o        (  RUSER     ),
    .RVALID_o       (  RVALID    ),
    .RREADY_i       (  RREADY    ),

    .MEM_CEN_o      (  MEM_CEN   ),
    .MEM_WEN_o      (  MEM_WEN   ),
    .MEM_A_o        (  MEM_A     ),
    .MEM_D_o        (  MEM_D     ),
    .MEM_BE_o       (  MEM_BE    ),
    .MEM_Q_i        (  MEM_Q     ),

    .grant_i        (  grant     ),
    .valid_o        (  valid     )
);





    generic_memory
    #(
        .ADDR_WIDTH(MEM_ADDR_WIDTH),
        .DATA_WIDTH(AXI4_WDATA_WIDTH)
    )
    MEM
    (
        .CLK   (clk),
        .INITN (rst_n),

        .CEN   (MEM_CEN | ~grant),
        .A     (MEM_A),
        .WEN   (MEM_WEN),
        .D     (MEM_D),
        .BE    (MEM_BE),

        .Q     (MEM_Q)
    );






    task AR_NOP;
    begin
        ARID      <= '0;
        ARADDR    <= '0;
        ARLEN     <= '0;
        ARSIZE    <= '0;
        ARBURST   <= '0;
        ARLOCK    <= '0;
        ARCACHE   <= '0;
        ARPROT    <= '0;
        ARREGION  <= '0;
        ARUSER    <= '0;
        ARQOS     <= '0;
        ARVALID   <= '0;
        #(`CLK_PERIOD);
    end
    endtask

    task AR_READ;
        input logic [31:0]                  address;
        input logic [7:0]                   len;
        input logic [AXI4_USER_WIDTH-1:0] user;
        input logic [AXI4_ID_WIDTH-1:0]   id;
        begin
            ARVALID     <= 1'b1;
            ARADDR      <= address;
            ARPROT      <= '0;
            ARREGION    <= '0;
            ARLEN       <= len;
            ARSIZE      <= 3'b010;
            ARBURST     <= 2'b10;
            ARLOCK      <= 1'b0;
            ARCACHE     <= '0;
            ARQOS       <= '0;
            ARID        <= id;
            ARUSER      <= user;
            @(grant_ar_event);
            ARVALID     <= 1'b0;
            ARADDR      <= '0;
            ARPROT      <= '0;
            ARREGION    <= '0;
            ARLEN       <= '0;
            ARSIZE      <= '0;
            ARBURST     <= '0;
            ARLOCK      <= '0;
            ARCACHE     <= '0;
            ARQOS       <= '0;
            ARID        <= '0;
            ARUSER      <= '0;
        end
    endtask




endmodule // tb_axi_read_only




module generic_memory
#(
    parameter ADDR_WIDTH = 12,
    parameter DATA_WIDTH = 64,
    parameter BE_WIDTH   = DATA_WIDTH/8
)
(
    input  logic                  CLK,
    input  logic                  INITN,

    input  logic                        CEN,
    input  logic [ADDR_WIDTH-1:0]       A,
    input  logic                        WEN,
    input  logic [BE_WIDTH-1:0][7:0]    D,
    input  logic [BE_WIDTH-1:0]         BE,

    output logic [DATA_WIDTH-1:0]       Q
);

   localparam   NUM_WORDS = 2**ADDR_WIDTH;

   logic [BE_WIDTH-1:0][7:0]            MEM [NUM_WORDS-1:0];


   always_ff @(posedge CLK or negedge INITN)
   begin : proc_mem
       if(~INITN)
       begin
            for (int i = 0; i < NUM_WORDS; i++)
            begin
                MEM[i] <= i*8;
            end
       end
       else
       begin
           if(CEN == 1'b0)
           begin
                if(WEN == 1'b0)
                begin
                    for (int j = 0; j < BE_WIDTH; j++)
                    begin
                        if(BE[j])
                        begin
                            MEM[A][j] <= D[j];
                        end
                    end
                    Q <= 'x;
                end
                else // READ
                begin
                    Q <= MEM[A];
                end
           end
           else
           begin
                Q <= 'x;
           end
       end
   end

endmodule
