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

module tb_axi_DP();

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

    logic [AXI4_ID_WIDTH-1:0]        AWID     ;
    logic [AXI4_ADDRESS_WIDTH-1:0]   AWADDR   ;
    logic [ 7:0]                     AWLEN    ;
    logic [ 2:0]                     AWSIZE   ;
    logic [ 1:0]                     AWBURST  ;
    logic                            AWLOCK   ;
    logic [ 3:0]                     AWCACHE  ;
    logic [ 2:0]                     AWPROT   ;
    logic [ 3:0]                     AWREGION ;
    logic [ AXI4_USER_WIDTH-1:0]     AWUSER   ;
    logic [ 3:0]                     AWQOS    ;
    logic                            AWVALID  ;
    logic                            AWREADY  ;

    logic [AXI4_WDATA_WIDTH-1:0]     WDATA    ;
    logic [AXI_NUMBYTES-1:0]         WSTRB    ;
    logic                            WLAST    ;
    logic [AXI4_USER_WIDTH-1:0]      WUSER    ;
    logic                            WVALID   ;
    logic                            WREADY   ;

    logic   [AXI4_ID_WIDTH-1:0]      BID      ;
    logic   [ 1:0]                   BRESP    ;
    logic                            BVALID   ;
    logic   [AXI4_USER_WIDTH-1:0]    BUSER    ;
    logic                            BREADY   ;

    logic                            MEM_CEN  ;
    logic                            MEM_WEN  ;
    logic  [MEM_ADDR_WIDTH-1:0]      MEM_A    ;
    logic  [AXI4_RDATA_WIDTH-1:0]    MEM_D    ;
    logic  [AXI_NUMBYTES-1:0]        MEM_BE   ;
    logic  [AXI4_RDATA_WIDTH-1:0]    MEM_Q    ;




    logic                            grant    ;
    logic                            valid    ;
    logic [31:0]                     temp_aw_address;
    logic [7:0]                      temp_aw_len;
    logic [255:0] [AXI4_WDATA_WIDTH-1:0]   temp_w_data;
    logic [255:0] [AXI_NUMBYTES-1:0]       temp_w_be;

    logic [AXI4_ID_WIDTH-1:0]        temp_id = 0;




    typedef struct {
        logic [AXI4_ADDRESS_WIDTH-1:0]  address;
        logic [7:0]                     len;
        logic [AXI4_ID_WIDTH-1:0]       id;
    } PACKET_type;


    PACKET_type PACKET_QUEUE[$];
    PACKET_type PACKET_IN, PACKET_OUT;



    event grant_aw_event;
    event grant_w_event;
    event grant_b_event;

    always  @(posedge clk )
    begin
        grant  <= $random%2;
        BREADY <=  $random%2;

        if(AWVALID & AWREADY)
            -> grant_aw_event;

        if(WVALID & WREADY)
            -> grant_w_event;

        if(BVALID & BREADY)
            -> grant_b_event;

    end


    always
    begin
        #(`CLK_PERIOD);
        clk = ~clk;
    end


    initial
    begin
        AW_NOP;

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
            temp_len             = $random() & 8'b0000_0111;
            temp_id              = temp_id + 1'b1;

            for (int i = 0; i < 256; i++) begin
                temp_wdata[i] = { temp_address ,32'hCAFE0000 + i*8};
                temp_be[i]    = '1;
            end

            PACKET_IN.address    = temp_address;
            PACKET_IN.len        = temp_len;
            PACKET_IN.id         = temp_id;

            fork
                AW_WRITE ( .address(temp_address),  .len(temp_len) ,     .user('1),     .id(temp_id) );
                W_WRITE  ( .len(temp_len),          .wdata(temp_wdata),  .be(temp_be),  .user('1)    );
            join
        end

        $stop;
    end


    int unsigned counter = 0;





always @(posedge clk)
begin
    if(BVALID & BREADY)
    begin
        $display("[B] at %t[ns] Backward Response is Granted ", $time()/1000.0  );
    end

    if(AWVALID & AWREADY)
    begin
        $display("[AW] at %t[ns], Injecting %d beat Burst at address %8h, ID = %d ", $time()/1000.0, AWLEN, AWADDR, AWID  );
    end

    if(WVALID & WREADY)
    begin
        $display("[W] at %t[ns], Injecting WDATA = 0x%16h, BE= 0x%8h,", $time()/1000.0, WDATA, WSTRB  );
        if(WLAST)
            $display("\n\n");
    end


end

axi_write_only_ctrl
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

    .AWID_i         (  AWID      ),
    .AWADDR_i       (  AWADDR    ),
    .AWLEN_i        (  AWLEN     ),
    .AWSIZE_i       (  AWSIZE    ),
    .AWBURST_i      (  AWBURST   ),
    .AWLOCK_i       (  AWLOCK    ),
    .AWCACHE_i      (  AWCACHE   ),
    .AWPROT_i       (  AWPROT    ),
    .AWREGION_i     (  AWREGION  ),
    .AWUSER_i       (  AWUSER    ),
    .AWQOS_i        (  AWQOS     ),
    .AWVALID_i      (  AWVALID   ),
    .AWREADY_o      (  AWREADY   ),

    //AXI write data bus -------------- // USED// -------------
    .WDATA_i        (  WDATA      ),
    .WSTRB_i        (  WSTRB      ),
    .WLAST_i        (  WLAST      ),
    .WUSER_i        (  WUSER      ),
    .WVALID_i       (  WVALID     ),
    .WREADY_o       (  WREADY     ),

    //AXI write response bus -------------- // USED// ----------
    .BID_o          (  BID        ),
    .BRESP_o        (  BRESP      ),
    .BVALID_o       (  BVALID     ),
    .BUSER_o        (  BUSER      ),
    .BREADY_i       (  BREADY     ),


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






    task AW_NOP;
    begin
        AWID      <= '0;
        AWADDR    <= '0;
        AWLEN     <= '0;
        AWSIZE    <= '0;
        AWBURST   <= '0;
        AWLOCK    <= '0;
        AWCACHE   <= '0;
        AWPROT    <= '0;
        AWREGION  <= '0;
        AWUSER    <= '0;
        AWQOS     <= '0;
        AWVALID   <= '0;
        #(`CLK_PERIOD);
    end
    endtask

    task AW_WRITE;
        input logic [31:0]                  address;
        input logic [7:0]                   len;
        input logic [AXI4_USER_WIDTH-1:0]   user;
        input logic [AXI4_ID_WIDTH-1:0]     id;
        begin
            AWVALID     <= 1'b1;
            AWADDR      <= address;
            AWPROT      <= '0;
            AWREGION    <= '0;
            AWLEN       <= len;
            AWSIZE      <= 3'b010;
            AWBURST     <= 2'b10;
            AWLOCK      <= 1'b0;
            AWCACHE     <= '0;
            AWQOS       <= '0;
            AWID        <= id;
            AWUSER      <= user;
            @(grant_aw_event);
            AWVALID     <= 1'b0;
            AWADDR      <= '0;
            AWPROT      <= '0;
            AWREGION    <= '0;
            AWLEN       <= '0;
            AWSIZE      <= '0;
            AWBURST     <= '0;
            AWLOCK      <= '0;
            AWCACHE     <= '0;
            AWQOS       <= '0;
            AWID        <= '0;
            AWUSER      <= '0;
        end
    endtask


    task W_NOP();
    begin
        WVALID      <= '0;
        WDATA       <= '0;
        WSTRB       <= '0;
        WUSER       <= '0;
        WLAST       <= '0;
        #(`CLK_PERIOD);
    end
    endtask


    task W_WRITE;
    input logic [7:0]                               len;
    input logic [255:0] [AXI4_WDATA_WIDTH-1:0]      wdata;
    input logic [255:0] [AXI_NUMBYTES-1:0]          be;
    input logic [AXI4_USER_WIDTH-1:0]               user;
    begin
        for (int index = 0; index <= len; index++)
        begin
            WDATA       <= wdata[index];
            WSTRB       <= be[index];
            WVALID      <= '1;
            WUSER       <= user;

            if(index == len)
                WLAST <= 1'b1;
            else
                WLAST <= 1'b0;

            @(grant_w_event);
        end

        WVALID      <= '0;
        WDATA       <= '0;
        WSTRB       <= '0;
        WUSER       <= '0;
        WLAST       <= '0;
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
