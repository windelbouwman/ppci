// Copyright 2015 ETH Zurich and University of Bologna.
// Copyright and related rights are licensed under the Solderpad Hardware
// License, Version 0.51 (the “License”); you may not use this file except in
// compliance with the License.  You may obtain a copy of the License at
// http://solderpad.org/licenses/SHL-0.51. Unless required by applicable law
// or agreed to in writing, software, hardware and materials distributed under
// this License is distributed on an “AS IS” BASIS, WITHOUT WARRANTIES OR
// CONDITIONS OF ANY KIND, either express or implied. See the License for the
// specific language governing permissions and limitations under the License.

// ============================================================================= //
// Company:        Multitherman Laboratory @ DEIS - University of Bologna        //
//                    Viale Risorgimento 2 40136                                 //
//                    Bologna - fax 0512093785 -                                 //
//                                                                               //
// Engineer:       Igor Loi - igor.loi@unibo.it                                  //
//                                                                               //
//                                                                               //
// Additional contributions by:                                                  //
//                                                                               //
//                                                                               //
//                                                                               //
// Create Date:    01/02/2014                                                    //
// Design Name:    AXI 4 INTERCONNECT                                            //
// Module Name:    axi_ArbitrationTree                                           //
// Project Name:   PULP                                                          //
// Language:       SystemVerilog                                                 //
//                                                                               //
// Description:   Arbitration tree made of simple atomic fan in primitives. It   //
//                performs a round robin distributed routing. depth of this tree //
//                is log2(number of inputs)                                      //
//                                                                               //
// Revision:                                                                     //
// Revision v0.1 - 01/02/2014 : File Created                                     //
//                                                                               //
//                                                                               //
//                                                                               //
//                                                                               //
//                                                                               //
//                                                                               //
// ============================================================================= //

module axi_ArbitrationTree
#(
      parameter AUX_WIDTH       = 64,
      parameter ID_WIDTH        = 20,
      parameter N_MASTER        = 5,
      parameter LOG_MASTER      = $clog2(N_MASTER)
)
(
      input  logic                                      clk,
      input  logic                                      rst_n,

      // ---------------- REQ_SIDE --------------------------
      input  logic [N_MASTER-1:0]                       data_req_i,
      input  logic [N_MASTER-1:0][AUX_WIDTH-1:0]        data_AUX_i,
      input  logic [N_MASTER-1:0][ID_WIDTH-1:0]         data_ID_i,
      output logic [N_MASTER-1:0]                       data_gnt_o,

      // Outputs
      output logic                                      data_req_o,
      output logic [AUX_WIDTH-1:0]                      data_AUX_o,
      output logic [ID_WIDTH-1:0]                       data_ID_o,
      input  logic                                      data_gnt_i,

      input  logic                                      lock,

      input  logic [LOG_MASTER-1:0]                     SEL_EXCLUSIVE
);



    // THIS ENSURE THAT THE INTERCONNECT IS ALWAYS MADE BY A POWER OF 2 INPUT PORTS
    localparam TOTAL_N_MASTER   =  2**LOG_MASTER;
    localparam N_WIRE           =  TOTAL_N_MASTER - 2;




    logic [LOG_MASTER-1:0]                      RR_FLAG;
    logic [LOG_MASTER-1:0]                      RR_FLAG_FLIPPED;

    logic [TOTAL_N_MASTER-1:0]                  data_req_int;
    logic [TOTAL_N_MASTER-1:0][AUX_WIDTH-1:0]   data_AUX_int;
    logic [TOTAL_N_MASTER-1:0][ID_WIDTH-1:0]    data_ID_int;
    logic [TOTAL_N_MASTER-1:0]                  data_gnt_int;




    genvar j,k,index;
    integer i;



    // FLIP THE ROUND ROBIN FLAG
    always_comb
    begin

        for(i=0; i<LOG_MASTER; i++)
        begin
          RR_FLAG_FLIPPED[i] = RR_FLAG[LOG_MASTER-i-1];
        end

    end



    // CREATE THE ARBITRATION TREE with MUXES EMBEDDED
    generate


      if(N_MASTER != TOTAL_N_MASTER) // Not power of 2 inputs
      begin : ARRAY_INT
          logic [TOTAL_N_MASTER-1:N_MASTER]                     dummy_req_int;
          logic [TOTAL_N_MASTER-1:N_MASTER][AUX_WIDTH-1:0]      dummy_AUX_int;
          logic [TOTAL_N_MASTER-1:N_MASTER][ID_WIDTH-1:0]       dummy_ID_int;
          logic [TOTAL_N_MASTER-1:N_MASTER]                     dummy_gnt_int;

          for(index=N_MASTER; index < TOTAL_N_MASTER; index++)
          begin : ZERO_BINDING
            assign dummy_req_int[index] = 1'b0;
            assign dummy_AUX_int[index] = '0;
            assign dummy_ID_int[index]  = '0;
          end

          for(index=0; index < N_MASTER; index++)
          begin : EXT_PORT
              assign data_req_int[index] = data_req_i[index];
              assign data_AUX_int[index] = data_AUX_i[index];
              assign data_ID_int[index]  = data_ID_i[index];
              assign data_gnt_o[index]   = data_gnt_int[index];
          end

          for(index=N_MASTER; index < TOTAL_N_MASTER; index++)
          begin : DUMMY_PORTS
              assign data_req_int[index]   = dummy_req_int[index];
              assign data_AUX_int[index]   = dummy_AUX_int[index];
              assign data_ID_int[index]    = dummy_ID_int[index];
              assign dummy_gnt_int[index]  = data_gnt_int[index];
          end

      end
      else
      begin
          for(index=0; index < N_MASTER; index++)
          begin : EXT_PORT
              assign data_req_int[index] = data_req_i[index];
              assign data_AUX_int[index] = data_AUX_i[index];
              assign data_ID_int[index]  = data_ID_i[index];
              assign data_gnt_o[index]   = data_gnt_int[index];
          end
      end





      if(TOTAL_N_MASTER == 2)
        begin : INCR // START of  MASTER  == 2
                    // ---------------- FAN IN PRIMITIVE  -------------------------
                    axi_FanInPrimitive_Req #( .AUX_WIDTH(AUX_WIDTH), .ID_WIDTH(ID_WIDTH) ) FAN_IN_REQ
                    (
                        .RR_FLAG(RR_FLAG_FLIPPED),
                        // LEFT SIDE"
                        .data_AUX0_i (  data_AUX_int[0]  ),
                        .data_AUX1_i (  data_AUX_int[1]  ),
                        .data_req0_i (  data_req_int[0]  ),
                        .data_req1_i (  data_req_int[1]  ),
                        .data_ID0_i  (  data_ID_int[0]   ),
                        .data_ID1_i  (  data_ID_int[1]   ),
                        .data_gnt0_o (  data_gnt_int[0]  ),
                        .data_gnt1_o (  data_gnt_int[1]  ),

                        // RIGTH SIDE"
                        .data_AUX_o     (  data_AUX_o    ),
                        .data_req_o     (  data_req_o    ),
                        .data_ID_o      (  data_ID_o     ),
                        .data_gnt_i     (  data_gnt_i    ),
                        .lock_EXCLUSIVE (  lock          ),
                        .SEL_EXCLUSIVE  (  SEL_EXCLUSIVE )
                        );
        end // END OF MASTER  == 2
      else // More than two master
        begin : BINARY_TREE
            //// ---------------------------------------------------------------------- ////
            //// -------               REQ ARBITRATION TREE WIRES           ----------- ////
            //// ---------------------------------------------------------------------- ////
            logic [AUX_WIDTH-1:0]               data_AUX_LEVEL[N_WIRE-1:0];
            logic                               data_req_LEVEL[N_WIRE-1:0];
            logic [ID_WIDTH-1:0]                data_ID_LEVEL[N_WIRE-1:0];
            logic                               data_gnt_LEVEL[N_WIRE-1:0];



              for(j=0; j < LOG_MASTER; j++) // Iteration for the number of the stages minus one
                begin : STAGE
                  for(k=0; k<2**j; k=k+1) // Iteration needed to create the binary tree
                    begin : INCR_VERT

                      if (j == 0 )  // LAST NODE, drives the module outputs
                      begin : LAST_NODE
                          axi_FanInPrimitive_Req #( .AUX_WIDTH(AUX_WIDTH), .ID_WIDTH(ID_WIDTH) ) FAN_IN_REQ
                          (
                          .RR_FLAG(RR_FLAG_FLIPPED[LOG_MASTER-j-1]),
                          // LEFT SIDE
                          .data_AUX0_i  (  data_AUX_LEVEL[2*k]    ),
                          .data_AUX1_i  (  data_AUX_LEVEL[2*k+1]  ),
                          .data_req0_i  (  data_req_LEVEL[2*k]    ),
                          .data_req1_i  (  data_req_LEVEL[2*k+1]  ),
                          .data_ID0_i   (  data_ID_LEVEL[2*k]     ),
                          .data_ID1_i   (  data_ID_LEVEL[2*k+1]   ),
                          .data_gnt0_o  (  data_gnt_LEVEL[2*k]    ),
                          .data_gnt1_o  (  data_gnt_LEVEL[2*k+1]  ),

                          // RIGTH SIDE
                          .data_AUX_o     (  data_AUX_o           ),
                          .data_req_o     (  data_req_o           ),
                          .data_ID_o      (  data_ID_o            ),
                          .data_gnt_i     (  data_gnt_i           ),

                          // LOCK SIGNALS
                          .lock_EXCLUSIVE (  lock                 ),
                          .SEL_EXCLUSIVE  (  SEL_EXCLUSIVE[LOG_MASTER-j-1] )
                          );
                      end
                      else if ( j < LOG_MASTER - 1) // Middle Nodes
                              begin : MIDDLE_NODES // START of MIDDLE LEVELS Nodes
                                  axi_FanInPrimitive_Req #( .AUX_WIDTH(AUX_WIDTH), .ID_WIDTH(ID_WIDTH) ) FAN_IN_REQ
                                  (
                                  .RR_FLAG(RR_FLAG_FLIPPED[LOG_MASTER-j-1]),
                                  // LEFT SIDE
                                  .data_AUX0_i(data_AUX_LEVEL[((2**j)*2-2) + 2*k]),
                                  .data_AUX1_i(data_AUX_LEVEL[((2**j)*2-2) + 2*k +1]),
                                  .data_req0_i(data_req_LEVEL[((2**j)*2-2) + 2*k]),
                                  .data_req1_i(data_req_LEVEL[((2**j)*2-2) + 2*k+1]),
                                  .data_ID0_i(data_ID_LEVEL[((2**j)*2-2) + 2*k]),
                                  .data_ID1_i(data_ID_LEVEL[((2**j)*2-2) + 2*k+1]),
                                  .data_gnt0_o(data_gnt_LEVEL[((2**j)*2-2) + 2*k]),
                                  .data_gnt1_o(data_gnt_LEVEL[((2**j)*2-2) + 2*k+1]),


                                  // RIGTH SIDE
                                  .data_AUX_o(data_AUX_LEVEL[((2**(j-1))*2-2) + k]),
                                  .data_req_o(data_req_LEVEL[((2**(j-1))*2-2) + k]),
                                  .data_ID_o(data_ID_LEVEL[((2**(j-1))*2-2) + k]),
                                  .data_gnt_i(data_gnt_LEVEL[((2**(j-1))*2-2) + k]),

                                  // LOCK SIGNALS
                                  .lock_EXCLUSIVE(lock),
                                  .SEL_EXCLUSIVE(SEL_EXCLUSIVE[LOG_MASTER-j-1])
                                  );
                              end  // END of MIDDLE LEVELS Nodes
                           else // First stage (connected with the Main inputs ) --> ( j == N_MASTER - 1 )
                              begin : LEAF_NODES  // START of FIRST LEVEL Nodes (LEAF)
                                  axi_FanInPrimitive_Req #( .AUX_WIDTH(AUX_WIDTH), .ID_WIDTH(ID_WIDTH) ) FAN_IN_REQ
                                  (
                                  .RR_FLAG(RR_FLAG_FLIPPED[LOG_MASTER-j-1]),
                                  // LEFT SIDE
                                  .data_AUX0_i(data_AUX_int[2*k]),
                                  .data_AUX1_i(data_AUX_int[2*k+1]),
                                  .data_req0_i(data_req_int[2*k]),
                                  .data_req1_i(data_req_int[2*k+1]),
                                  .data_ID0_i(data_ID_int[2*k]),
                                  .data_ID1_i(data_ID_int[2*k+1]),
                                  .data_gnt0_o(data_gnt_int[2*k]),
                                  .data_gnt1_o(data_gnt_int[2*k+1]),


                                  // RIGTH SIDE
                                  .data_AUX_o(data_AUX_LEVEL[((2**(j-1))*2-2) + k]),
                                  .data_req_o(data_req_LEVEL[((2**(j-1))*2-2) + k]),
                                  .data_ID_o(data_ID_LEVEL[((2**(j-1))*2-2) + k]),
                                  .data_gnt_i(data_gnt_LEVEL[((2**(j-1))*2-2) + k]),
                                  // LOCK SIGNALS
                                  .lock_EXCLUSIVE(lock),
                                  .SEL_EXCLUSIVE(SEL_EXCLUSIVE[LOG_MASTER-j-1])
                                  );
                              end // End of FIRST LEVEL Nodes (LEAF)
                    end

                end

    end
    endgenerate


    //COUNTER USED TO SWITCH PERIODICALLY THE PRIORITY FLAG"
    axi_RR_Flag_Req #( .WIDTH(LOG_MASTER), .MAX_COUNT(N_MASTER) )  RR_REQ
    (
        .clk(clk),
        .rst_n(rst_n),
        .RR_FLAG_o(RR_FLAG),
        .data_req_i(data_req_o),
        .data_gnt_i(data_gnt_i)
    );


endmodule
