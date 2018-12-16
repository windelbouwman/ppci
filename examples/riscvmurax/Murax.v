// Generator : SpinalHDL v1.2.0    git head : cf3b44dbd881428e70669e5b623479c23b2d0ddd
// Date      : 07/11/2018, 09:09:46
// Component : Murax


`define JtagState_defaultEncoding_type [3:0]
`define JtagState_defaultEncoding_RESET 4'b0000
`define JtagState_defaultEncoding_IDLE 4'b0001
`define JtagState_defaultEncoding_IR_SELECT 4'b0010
`define JtagState_defaultEncoding_IR_CAPTURE 4'b0011
`define JtagState_defaultEncoding_IR_SHIFT 4'b0100
`define JtagState_defaultEncoding_IR_EXIT1 4'b0101
`define JtagState_defaultEncoding_IR_PAUSE 4'b0110
`define JtagState_defaultEncoding_IR_EXIT2 4'b0111
`define JtagState_defaultEncoding_IR_UPDATE 4'b1000
`define JtagState_defaultEncoding_DR_SELECT 4'b1001
`define JtagState_defaultEncoding_DR_CAPTURE 4'b1010
`define JtagState_defaultEncoding_DR_SHIFT 4'b1011
`define JtagState_defaultEncoding_DR_EXIT1 4'b1100
`define JtagState_defaultEncoding_DR_PAUSE 4'b1101
`define JtagState_defaultEncoding_DR_EXIT2 4'b1110
`define JtagState_defaultEncoding_DR_UPDATE 4'b1111

`define Src1CtrlEnum_defaultEncoding_type [1:0]
`define Src1CtrlEnum_defaultEncoding_RS 2'b00
`define Src1CtrlEnum_defaultEncoding_IMU 2'b01
`define Src1CtrlEnum_defaultEncoding_PC_INCREMENT 2'b10

`define UartCtrlTxState_defaultEncoding_type [2:0]
`define UartCtrlTxState_defaultEncoding_IDLE 3'b000
`define UartCtrlTxState_defaultEncoding_START 3'b001
`define UartCtrlTxState_defaultEncoding_DATA 3'b010
`define UartCtrlTxState_defaultEncoding_PARITY 3'b011
`define UartCtrlTxState_defaultEncoding_STOP 3'b100

`define Src2CtrlEnum_defaultEncoding_type [1:0]
`define Src2CtrlEnum_defaultEncoding_RS 2'b00
`define Src2CtrlEnum_defaultEncoding_IMI 2'b01
`define Src2CtrlEnum_defaultEncoding_IMS 2'b10
`define Src2CtrlEnum_defaultEncoding_PC 2'b11

`define BranchCtrlEnum_defaultEncoding_type [1:0]
`define BranchCtrlEnum_defaultEncoding_INC 2'b00
`define BranchCtrlEnum_defaultEncoding_B 2'b01
`define BranchCtrlEnum_defaultEncoding_JAL 2'b10
`define BranchCtrlEnum_defaultEncoding_JALR 2'b11

`define ShiftCtrlEnum_defaultEncoding_type [1:0]
`define ShiftCtrlEnum_defaultEncoding_DISABLE_1 2'b00
`define ShiftCtrlEnum_defaultEncoding_SLL_1 2'b01
`define ShiftCtrlEnum_defaultEncoding_SRL_1 2'b10
`define ShiftCtrlEnum_defaultEncoding_SRA_1 2'b11

`define UartCtrlRxState_defaultEncoding_type [2:0]
`define UartCtrlRxState_defaultEncoding_IDLE 3'b000
`define UartCtrlRxState_defaultEncoding_START 3'b001
`define UartCtrlRxState_defaultEncoding_DATA 3'b010
`define UartCtrlRxState_defaultEncoding_PARITY 3'b011
`define UartCtrlRxState_defaultEncoding_STOP 3'b100

`define UartParityType_defaultEncoding_type [1:0]
`define UartParityType_defaultEncoding_NONE 2'b00
`define UartParityType_defaultEncoding_EVEN 2'b01
`define UartParityType_defaultEncoding_ODD 2'b10

`define UartStopType_defaultEncoding_type [0:0]
`define UartStopType_defaultEncoding_ONE 1'b0
`define UartStopType_defaultEncoding_TWO 1'b1

`define AluBitwiseCtrlEnum_defaultEncoding_type [1:0]
`define AluBitwiseCtrlEnum_defaultEncoding_XOR_1 2'b00
`define AluBitwiseCtrlEnum_defaultEncoding_OR_1 2'b01
`define AluBitwiseCtrlEnum_defaultEncoding_AND_1 2'b10
`define AluBitwiseCtrlEnum_defaultEncoding_SRC1 2'b11

`define EnvCtrlEnum_defaultEncoding_type [2:0]
`define EnvCtrlEnum_defaultEncoding_NONE 3'b000
`define EnvCtrlEnum_defaultEncoding_EBREAK 3'b001
`define EnvCtrlEnum_defaultEncoding_MRET 3'b010
`define EnvCtrlEnum_defaultEncoding_WFI 3'b011
`define EnvCtrlEnum_defaultEncoding_ECALL 3'b100

`define AluCtrlEnum_defaultEncoding_type [1:0]
`define AluCtrlEnum_defaultEncoding_ADD_SUB 2'b00
`define AluCtrlEnum_defaultEncoding_SLT_SLTU 2'b01
`define AluCtrlEnum_defaultEncoding_BITWISE 2'b10

module BufferCC (
      input   io_initial,
      input   io_dataIn,
      output  io_dataOut,
      input   io_mainClk,
      input   resetCtrl_systemReset);
  reg  buffers_0;
  reg  buffers_1;
  assign io_dataOut = buffers_1;
  always @ (posedge io_mainClk or posedge resetCtrl_systemReset) begin
    if (resetCtrl_systemReset) begin
      buffers_0 <= io_initial;
      buffers_1 <= io_initial;
    end else begin
      buffers_0 <= io_dataIn;
      buffers_1 <= buffers_0;
    end
  end

endmodule

module BufferCC_1_ (
      input   io_dataIn,
      output  io_dataOut,
      input   io_mainClk,
      input   resetCtrl_mainClkReset);
  reg  buffers_0;
  reg  buffers_1;
  assign io_dataOut = buffers_1;
  always @ (posedge io_mainClk) begin
    buffers_0 <= io_dataIn;
    buffers_1 <= buffers_0;
  end

endmodule

module UartCtrlTx (
      input  [2:0] io_configFrame_dataLength,
      input  `UartStopType_defaultEncoding_type io_configFrame_stop,
      input  `UartParityType_defaultEncoding_type io_configFrame_parity,
      input   io_samplingTick,
      input   io_write_valid,
      output reg  io_write_ready,
      input  [7:0] io_write_payload,
      output  io_txd,
      input   io_mainClk,
      input   resetCtrl_systemReset);
  wire  _zz_1_;
  wire [0:0] _zz_2_;
  wire [2:0] _zz_3_;
  wire [0:0] _zz_4_;
  wire [2:0] _zz_5_;
  reg  clockDivider_counter_willIncrement;
  wire  clockDivider_counter_willClear;
  reg [2:0] clockDivider_counter_valueNext;
  reg [2:0] clockDivider_counter_value;
  wire  clockDivider_counter_willOverflowIfInc;
  wire  clockDivider_willOverflow;
  reg [2:0] tickCounter_value;
  reg `UartCtrlTxState_defaultEncoding_type stateMachine_state;
  reg  stateMachine_parity;
  reg  stateMachine_txd;
  reg  stateMachine_txd_regNext;
  assign _zz_1_ = (tickCounter_value == io_configFrame_dataLength);
  assign _zz_2_ = clockDivider_counter_willIncrement;
  assign _zz_3_ = {2'd0, _zz_2_};
  assign _zz_4_ = ((io_configFrame_stop == `UartStopType_defaultEncoding_ONE) ? (1'b0) : (1'b1));
  assign _zz_5_ = {2'd0, _zz_4_};
  always @ (*) begin
    clockDivider_counter_willIncrement = 1'b0;
    if(io_samplingTick)begin
      clockDivider_counter_willIncrement = 1'b1;
    end
  end

  assign clockDivider_counter_willClear = 1'b0;
  assign clockDivider_counter_willOverflowIfInc = (clockDivider_counter_value == (3'b100));
  assign clockDivider_willOverflow = (clockDivider_counter_willOverflowIfInc && clockDivider_counter_willIncrement);
  always @ (*) begin
    if(clockDivider_willOverflow)begin
      clockDivider_counter_valueNext = (3'b000);
    end else begin
      clockDivider_counter_valueNext = (clockDivider_counter_value + _zz_3_);
    end
    if(clockDivider_counter_willClear)begin
      clockDivider_counter_valueNext = (3'b000);
    end
  end

  always @ (*) begin
    stateMachine_txd = 1'b1;
    io_write_ready = 1'b0;
    case(stateMachine_state)
      `UartCtrlTxState_defaultEncoding_IDLE : begin
      end
      `UartCtrlTxState_defaultEncoding_START : begin
        stateMachine_txd = 1'b0;
      end
      `UartCtrlTxState_defaultEncoding_DATA : begin
        stateMachine_txd = io_write_payload[tickCounter_value];
        if(clockDivider_willOverflow)begin
          if(_zz_1_)begin
            io_write_ready = 1'b1;
          end
        end
      end
      `UartCtrlTxState_defaultEncoding_PARITY : begin
        stateMachine_txd = stateMachine_parity;
      end
      default : begin
      end
    endcase
  end

  assign io_txd = stateMachine_txd_regNext;
  always @ (posedge io_mainClk or posedge resetCtrl_systemReset) begin
    if (resetCtrl_systemReset) begin
      clockDivider_counter_value <= (3'b000);
      stateMachine_state <= `UartCtrlTxState_defaultEncoding_IDLE;
      stateMachine_txd_regNext <= 1'b1;
    end else begin
      clockDivider_counter_value <= clockDivider_counter_valueNext;
      case(stateMachine_state)
        `UartCtrlTxState_defaultEncoding_IDLE : begin
          if((io_write_valid && clockDivider_willOverflow))begin
            stateMachine_state <= `UartCtrlTxState_defaultEncoding_START;
          end
        end
        `UartCtrlTxState_defaultEncoding_START : begin
          if(clockDivider_willOverflow)begin
            stateMachine_state <= `UartCtrlTxState_defaultEncoding_DATA;
          end
        end
        `UartCtrlTxState_defaultEncoding_DATA : begin
          if(clockDivider_willOverflow)begin
            if(_zz_1_)begin
              if((io_configFrame_parity == `UartParityType_defaultEncoding_NONE))begin
                stateMachine_state <= `UartCtrlTxState_defaultEncoding_STOP;
              end else begin
                stateMachine_state <= `UartCtrlTxState_defaultEncoding_PARITY;
              end
            end
          end
        end
        `UartCtrlTxState_defaultEncoding_PARITY : begin
          if(clockDivider_willOverflow)begin
            stateMachine_state <= `UartCtrlTxState_defaultEncoding_STOP;
          end
        end
        default : begin
          if(clockDivider_willOverflow)begin
            if((tickCounter_value == _zz_5_))begin
              stateMachine_state <= (io_write_valid ? `UartCtrlTxState_defaultEncoding_START : `UartCtrlTxState_defaultEncoding_IDLE);
            end
          end
        end
      endcase
      stateMachine_txd_regNext <= stateMachine_txd;
    end
  end

  always @ (posedge io_mainClk) begin
    if(clockDivider_willOverflow)begin
      tickCounter_value <= (tickCounter_value + (3'b001));
    end
    if(clockDivider_willOverflow)begin
      stateMachine_parity <= (stateMachine_parity ^ stateMachine_txd);
    end
    case(stateMachine_state)
      `UartCtrlTxState_defaultEncoding_IDLE : begin
      end
      `UartCtrlTxState_defaultEncoding_START : begin
        if(clockDivider_willOverflow)begin
          stateMachine_parity <= (io_configFrame_parity == `UartParityType_defaultEncoding_ODD);
          tickCounter_value <= (3'b000);
        end
      end
      `UartCtrlTxState_defaultEncoding_DATA : begin
        if(clockDivider_willOverflow)begin
          if(_zz_1_)begin
            tickCounter_value <= (3'b000);
          end
        end
      end
      `UartCtrlTxState_defaultEncoding_PARITY : begin
        if(clockDivider_willOverflow)begin
          tickCounter_value <= (3'b000);
        end
      end
      default : begin
      end
    endcase
  end

endmodule

module UartCtrlRx (
      input  [2:0] io_configFrame_dataLength,
      input  `UartStopType_defaultEncoding_type io_configFrame_stop,
      input  `UartParityType_defaultEncoding_type io_configFrame_parity,
      input   io_samplingTick,
      output  io_read_valid,
      output [7:0] io_read_payload,
      input   io_rxd,
      input   io_mainClk,
      input   resetCtrl_systemReset);
  wire  _zz_1_;
  wire  _zz_2_;
  wire  _zz_3_;
  wire  _zz_4_;
  wire  _zz_5_;
  wire [0:0] _zz_6_;
  wire [2:0] _zz_7_;
  wire  sampler_syncroniser;
  wire  sampler_samples_0;
  reg  sampler_samples_1;
  reg  sampler_samples_2;
  reg  sampler_value;
  reg  sampler_tick;
  reg [2:0] bitTimer_counter;
  reg  bitTimer_tick;
  reg [2:0] bitCounter_value;
  reg `UartCtrlRxState_defaultEncoding_type stateMachine_state;
  reg  stateMachine_parity;
  reg [7:0] stateMachine_shifter;
  reg  stateMachine_validReg;
  assign _zz_3_ = (bitTimer_counter == (3'b000));
  assign _zz_4_ = (sampler_tick && (! sampler_value));
  assign _zz_5_ = (bitCounter_value == io_configFrame_dataLength);
  assign _zz_6_ = ((io_configFrame_stop == `UartStopType_defaultEncoding_ONE) ? (1'b0) : (1'b1));
  assign _zz_7_ = {2'd0, _zz_6_};
  BufferCC bufferCC_3_ ( 
    .io_initial(_zz_1_),
    .io_dataIn(io_rxd),
    .io_dataOut(_zz_2_),
    .io_mainClk(io_mainClk),
    .resetCtrl_systemReset(resetCtrl_systemReset) 
  );
  assign _zz_1_ = 1'b0;
  assign sampler_syncroniser = _zz_2_;
  assign sampler_samples_0 = sampler_syncroniser;
  always @ (*) begin
    bitTimer_tick = 1'b0;
    if(sampler_tick)begin
      if(_zz_3_)begin
        bitTimer_tick = 1'b1;
      end
    end
  end

  assign io_read_valid = stateMachine_validReg;
  assign io_read_payload = stateMachine_shifter;
  always @ (posedge io_mainClk or posedge resetCtrl_systemReset) begin
    if (resetCtrl_systemReset) begin
      sampler_samples_1 <= 1'b1;
      sampler_samples_2 <= 1'b1;
      sampler_value <= 1'b1;
      sampler_tick <= 1'b0;
      stateMachine_state <= `UartCtrlRxState_defaultEncoding_IDLE;
      stateMachine_validReg <= 1'b0;
    end else begin
      if(io_samplingTick)begin
        sampler_samples_1 <= sampler_samples_0;
      end
      if(io_samplingTick)begin
        sampler_samples_2 <= sampler_samples_1;
      end
      sampler_value <= (((1'b0 || ((1'b1 && sampler_samples_0) && sampler_samples_1)) || ((1'b1 && sampler_samples_0) && sampler_samples_2)) || ((1'b1 && sampler_samples_1) && sampler_samples_2));
      sampler_tick <= io_samplingTick;
      stateMachine_validReg <= 1'b0;
      case(stateMachine_state)
        `UartCtrlRxState_defaultEncoding_IDLE : begin
          if(_zz_4_)begin
            stateMachine_state <= `UartCtrlRxState_defaultEncoding_START;
          end
        end
        `UartCtrlRxState_defaultEncoding_START : begin
          if(bitTimer_tick)begin
            stateMachine_state <= `UartCtrlRxState_defaultEncoding_DATA;
            if((sampler_value == 1'b1))begin
              stateMachine_state <= `UartCtrlRxState_defaultEncoding_IDLE;
            end
          end
        end
        `UartCtrlRxState_defaultEncoding_DATA : begin
          if(bitTimer_tick)begin
            if(_zz_5_)begin
              if((io_configFrame_parity == `UartParityType_defaultEncoding_NONE))begin
                stateMachine_state <= `UartCtrlRxState_defaultEncoding_STOP;
                stateMachine_validReg <= 1'b1;
              end else begin
                stateMachine_state <= `UartCtrlRxState_defaultEncoding_PARITY;
              end
            end
          end
        end
        `UartCtrlRxState_defaultEncoding_PARITY : begin
          if(bitTimer_tick)begin
            if((stateMachine_parity == sampler_value))begin
              stateMachine_state <= `UartCtrlRxState_defaultEncoding_STOP;
              stateMachine_validReg <= 1'b1;
            end else begin
              stateMachine_state <= `UartCtrlRxState_defaultEncoding_IDLE;
            end
          end
        end
        default : begin
          if(bitTimer_tick)begin
            if((! sampler_value))begin
              stateMachine_state <= `UartCtrlRxState_defaultEncoding_IDLE;
            end else begin
              if((bitCounter_value == _zz_7_))begin
                stateMachine_state <= `UartCtrlRxState_defaultEncoding_IDLE;
              end
            end
          end
        end
      endcase
    end
  end

  always @ (posedge io_mainClk) begin
    if(sampler_tick)begin
      bitTimer_counter <= (bitTimer_counter - (3'b001));
      if(_zz_3_)begin
        bitTimer_counter <= (3'b100);
      end
    end
    if(bitTimer_tick)begin
      bitCounter_value <= (bitCounter_value + (3'b001));
    end
    if(bitTimer_tick)begin
      stateMachine_parity <= (stateMachine_parity ^ sampler_value);
    end
    case(stateMachine_state)
      `UartCtrlRxState_defaultEncoding_IDLE : begin
        if(_zz_4_)begin
          bitTimer_counter <= (3'b001);
        end
      end
      `UartCtrlRxState_defaultEncoding_START : begin
        if(bitTimer_tick)begin
          bitCounter_value <= (3'b000);
          stateMachine_parity <= (io_configFrame_parity == `UartParityType_defaultEncoding_ODD);
        end
      end
      `UartCtrlRxState_defaultEncoding_DATA : begin
        if(bitTimer_tick)begin
          stateMachine_shifter[bitCounter_value] <= sampler_value;
          if(_zz_5_)begin
            bitCounter_value <= (3'b000);
          end
        end
      end
      `UartCtrlRxState_defaultEncoding_PARITY : begin
        if(bitTimer_tick)begin
          bitCounter_value <= (3'b000);
        end
      end
      default : begin
      end
    endcase
  end

endmodule

module StreamFifoLowLatency (
      input   io_push_valid,
      output  io_push_ready,
      input   io_push_payload_error,
      input  [31:0] io_push_payload_inst,
      output reg  io_pop_valid,
      input   io_pop_ready,
      output reg  io_pop_payload_error,
      output reg [31:0] io_pop_payload_inst,
      input   io_flush,
      output [0:0] io_occupancy,
      input   io_mainClk,
      input   resetCtrl_systemReset);
  wire [0:0] _zz_5_;
  reg  _zz_1_;
  reg  pushPtr_willIncrement;
  reg  pushPtr_willClear;
  wire  pushPtr_willOverflowIfInc;
  wire  pushPtr_willOverflow;
  reg  popPtr_willIncrement;
  reg  popPtr_willClear;
  wire  popPtr_willOverflowIfInc;
  wire  popPtr_willOverflow;
  wire  ptrMatch;
  reg  risingOccupancy;
  wire  empty;
  wire  full;
  wire  pushing;
  wire  popping;
  wire [32:0] _zz_2_;
  wire [32:0] _zz_3_;
  reg [32:0] _zz_4_;
  assign _zz_5_ = _zz_2_[0 : 0];
  always @ (*) begin
    _zz_1_ = 1'b0;
    pushPtr_willIncrement = 1'b0;
    if(pushing)begin
      _zz_1_ = 1'b1;
      pushPtr_willIncrement = 1'b1;
    end
  end

  always @ (*) begin
    pushPtr_willClear = 1'b0;
    popPtr_willClear = 1'b0;
    if(io_flush)begin
      pushPtr_willClear = 1'b1;
      popPtr_willClear = 1'b1;
    end
  end

  assign pushPtr_willOverflowIfInc = 1'b1;
  assign pushPtr_willOverflow = (pushPtr_willOverflowIfInc && pushPtr_willIncrement);
  always @ (*) begin
    popPtr_willIncrement = 1'b0;
    if(popping)begin
      popPtr_willIncrement = 1'b1;
    end
  end

  assign popPtr_willOverflowIfInc = 1'b1;
  assign popPtr_willOverflow = (popPtr_willOverflowIfInc && popPtr_willIncrement);
  assign ptrMatch = 1'b1;
  assign empty = (ptrMatch && (! risingOccupancy));
  assign full = (ptrMatch && risingOccupancy);
  assign pushing = (io_push_valid && io_push_ready);
  assign popping = (io_pop_valid && io_pop_ready);
  assign io_push_ready = (! full);
  always @ (*) begin
    if((! empty))begin
      io_pop_valid = 1'b1;
      io_pop_payload_error = _zz_5_[0];
      io_pop_payload_inst = _zz_2_[32 : 1];
    end else begin
      io_pop_valid = io_push_valid;
      io_pop_payload_error = io_push_payload_error;
      io_pop_payload_inst = io_push_payload_inst;
    end
  end

  assign _zz_2_ = _zz_3_;
  assign io_occupancy = (risingOccupancy && ptrMatch);
  assign _zz_3_ = _zz_4_;
  always @ (posedge io_mainClk or posedge resetCtrl_systemReset) begin
    if (resetCtrl_systemReset) begin
      risingOccupancy <= 1'b0;
    end else begin
      if((pushing != popping))begin
        risingOccupancy <= pushing;
      end
      if(io_flush)begin
        risingOccupancy <= 1'b0;
      end
    end
  end

  always @ (posedge io_mainClk) begin
    if(_zz_1_)begin
      _zz_4_ <= {io_push_payload_inst,io_push_payload_error};
    end
  end

endmodule

module FlowCCByToggle (
      input   io_input_valid,
      input   io_input_payload_last,
      input  [0:0] io_input_payload_fragment,
      output  io_output_valid,
      output  io_output_payload_last,
      output [0:0] io_output_payload_fragment,
      input   io_jtag_tck,
      input   io_mainClk,
      input   resetCtrl_mainClkReset);
  wire  _zz_1_;
  wire  outHitSignal;
  reg  inputArea_target = 0;
  reg  inputArea_data_last;
  reg [0:0] inputArea_data_fragment;
  wire  outputArea_target;
  reg  outputArea_hit;
  wire  outputArea_flow_valid;
  wire  outputArea_flow_payload_last;
  wire [0:0] outputArea_flow_payload_fragment;
  reg  outputArea_flow_regNext_valid;
  reg  outputArea_flow_regNext_payload_last;
  reg [0:0] outputArea_flow_regNext_payload_fragment;
  BufferCC_1_ bufferCC_3_ ( 
    .io_dataIn(inputArea_target),
    .io_dataOut(_zz_1_),
    .io_mainClk(io_mainClk),
    .resetCtrl_mainClkReset(resetCtrl_mainClkReset) 
  );
  assign outputArea_target = _zz_1_;
  assign outputArea_flow_valid = (outputArea_target != outputArea_hit);
  assign outputArea_flow_payload_last = inputArea_data_last;
  assign outputArea_flow_payload_fragment = inputArea_data_fragment;
  assign io_output_valid = outputArea_flow_regNext_valid;
  assign io_output_payload_last = outputArea_flow_regNext_payload_last;
  assign io_output_payload_fragment = outputArea_flow_regNext_payload_fragment;
  always @ (posedge io_jtag_tck) begin
    if(io_input_valid)begin
      inputArea_target <= (! inputArea_target);
      inputArea_data_last <= io_input_payload_last;
      inputArea_data_fragment <= io_input_payload_fragment;
    end
  end

  always @ (posedge io_mainClk) begin
    outputArea_hit <= outputArea_target;
    outputArea_flow_regNext_payload_last <= outputArea_flow_payload_last;
    outputArea_flow_regNext_payload_fragment <= outputArea_flow_payload_fragment;
  end

  always @ (posedge io_mainClk or posedge resetCtrl_mainClkReset) begin
    if (resetCtrl_mainClkReset) begin
      outputArea_flow_regNext_valid <= 1'b0;
    end else begin
      outputArea_flow_regNext_valid <= outputArea_flow_valid;
    end
  end

endmodule

module UartCtrl (
      input  [2:0] io_config_frame_dataLength,
      input  `UartStopType_defaultEncoding_type io_config_frame_stop,
      input  `UartParityType_defaultEncoding_type io_config_frame_parity,
      input  [19:0] io_config_clockDivider,
      input   io_write_valid,
      output  io_write_ready,
      input  [7:0] io_write_payload,
      output  io_read_valid,
      output [7:0] io_read_payload,
      output  io_uart_txd,
      input   io_uart_rxd,
      input   io_mainClk,
      input   resetCtrl_systemReset);
  wire  _zz_1_;
  wire  _zz_2_;
  wire  _zz_3_;
  wire [7:0] _zz_4_;
  reg [19:0] clockDivider_counter;
  wire  clockDivider_tick;
  UartCtrlTx tx ( 
    .io_configFrame_dataLength(io_config_frame_dataLength),
    .io_configFrame_stop(io_config_frame_stop),
    .io_configFrame_parity(io_config_frame_parity),
    .io_samplingTick(clockDivider_tick),
    .io_write_valid(io_write_valid),
    .io_write_ready(_zz_1_),
    .io_write_payload(io_write_payload),
    .io_txd(_zz_2_),
    .io_mainClk(io_mainClk),
    .resetCtrl_systemReset(resetCtrl_systemReset) 
  );
  UartCtrlRx rx ( 
    .io_configFrame_dataLength(io_config_frame_dataLength),
    .io_configFrame_stop(io_config_frame_stop),
    .io_configFrame_parity(io_config_frame_parity),
    .io_samplingTick(clockDivider_tick),
    .io_read_valid(_zz_3_),
    .io_read_payload(_zz_4_),
    .io_rxd(io_uart_rxd),
    .io_mainClk(io_mainClk),
    .resetCtrl_systemReset(resetCtrl_systemReset) 
  );
  assign clockDivider_tick = (clockDivider_counter == (20'b00000000000000000000));
  assign io_write_ready = _zz_1_;
  assign io_read_valid = _zz_3_;
  assign io_read_payload = _zz_4_;
  assign io_uart_txd = _zz_2_;
  always @ (posedge io_mainClk or posedge resetCtrl_systemReset) begin
    if (resetCtrl_systemReset) begin
      clockDivider_counter <= (20'b00000000000000000000);
    end else begin
      clockDivider_counter <= (clockDivider_counter - (20'b00000000000000000001));
      if(clockDivider_tick)begin
        clockDivider_counter <= io_config_clockDivider;
      end
    end
  end

endmodule

module StreamFifo (
      input   io_push_valid,
      output  io_push_ready,
      input  [7:0] io_push_payload,
      output  io_pop_valid,
      input   io_pop_ready,
      output [7:0] io_pop_payload,
      input   io_flush,
      output [4:0] io_occupancy,
      output [4:0] io_availability,
      input   io_mainClk,
      input   resetCtrl_systemReset);
  reg [7:0] _zz_3_;
  wire [0:0] _zz_4_;
  wire [3:0] _zz_5_;
  wire [0:0] _zz_6_;
  wire [3:0] _zz_7_;
  wire [3:0] _zz_8_;
  wire  _zz_9_;
  reg  _zz_1_;
  reg  pushPtr_willIncrement;
  reg  pushPtr_willClear;
  reg [3:0] pushPtr_valueNext;
  reg [3:0] pushPtr_value;
  wire  pushPtr_willOverflowIfInc;
  wire  pushPtr_willOverflow;
  reg  popPtr_willIncrement;
  reg  popPtr_willClear;
  reg [3:0] popPtr_valueNext;
  reg [3:0] popPtr_value;
  wire  popPtr_willOverflowIfInc;
  wire  popPtr_willOverflow;
  wire  ptrMatch;
  reg  risingOccupancy;
  wire  pushing;
  wire  popping;
  wire  empty;
  wire  full;
  reg  _zz_2_;
  wire [3:0] ptrDif;
  reg [7:0] ram [0:15];
  assign _zz_4_ = pushPtr_willIncrement;
  assign _zz_5_ = {3'd0, _zz_4_};
  assign _zz_6_ = popPtr_willIncrement;
  assign _zz_7_ = {3'd0, _zz_6_};
  assign _zz_8_ = (popPtr_value - pushPtr_value);
  assign _zz_9_ = 1'b1;
  always @ (posedge io_mainClk) begin
    if(_zz_1_) begin
      ram[pushPtr_value] <= io_push_payload;
    end
  end

  always @ (posedge io_mainClk) begin
    if(_zz_9_) begin
      _zz_3_ <= ram[popPtr_valueNext];
    end
  end

  always @ (*) begin
    _zz_1_ = 1'b0;
    pushPtr_willIncrement = 1'b0;
    if(pushing)begin
      _zz_1_ = 1'b1;
      pushPtr_willIncrement = 1'b1;
    end
  end

  always @ (*) begin
    pushPtr_willClear = 1'b0;
    popPtr_willClear = 1'b0;
    if(io_flush)begin
      pushPtr_willClear = 1'b1;
      popPtr_willClear = 1'b1;
    end
  end

  assign pushPtr_willOverflowIfInc = (pushPtr_value == (4'b1111));
  assign pushPtr_willOverflow = (pushPtr_willOverflowIfInc && pushPtr_willIncrement);
  always @ (*) begin
    pushPtr_valueNext = (pushPtr_value + _zz_5_);
    if(pushPtr_willClear)begin
      pushPtr_valueNext = (4'b0000);
    end
  end

  always @ (*) begin
    popPtr_willIncrement = 1'b0;
    if(popping)begin
      popPtr_willIncrement = 1'b1;
    end
  end

  assign popPtr_willOverflowIfInc = (popPtr_value == (4'b1111));
  assign popPtr_willOverflow = (popPtr_willOverflowIfInc && popPtr_willIncrement);
  always @ (*) begin
    popPtr_valueNext = (popPtr_value + _zz_7_);
    if(popPtr_willClear)begin
      popPtr_valueNext = (4'b0000);
    end
  end

  assign ptrMatch = (pushPtr_value == popPtr_value);
  assign pushing = (io_push_valid && io_push_ready);
  assign popping = (io_pop_valid && io_pop_ready);
  assign empty = (ptrMatch && (! risingOccupancy));
  assign full = (ptrMatch && risingOccupancy);
  assign io_push_ready = (! full);
  assign io_pop_valid = ((! empty) && (! (_zz_2_ && (! full))));
  assign io_pop_payload = _zz_3_;
  assign ptrDif = (pushPtr_value - popPtr_value);
  assign io_occupancy = {(risingOccupancy && ptrMatch),ptrDif};
  assign io_availability = {((! risingOccupancy) && ptrMatch),_zz_8_};
  always @ (posedge io_mainClk or posedge resetCtrl_systemReset) begin
    if (resetCtrl_systemReset) begin
      pushPtr_value <= (4'b0000);
      popPtr_value <= (4'b0000);
      risingOccupancy <= 1'b0;
      _zz_2_ <= 1'b0;
    end else begin
      pushPtr_value <= pushPtr_valueNext;
      popPtr_value <= popPtr_valueNext;
      _zz_2_ <= (popPtr_valueNext == pushPtr_value);
      if((pushing != popping))begin
        risingOccupancy <= pushing;
      end
      if(io_flush)begin
        risingOccupancy <= 1'b0;
      end
    end
  end

endmodule


//StreamFifo_1_ remplaced by StreamFifo

module Prescaler (
      input   io_clear,
      input  [15:0] io_limit,
      output  io_overflow,
      input   io_mainClk,
      input   resetCtrl_systemReset);
  reg [15:0] counter;
  assign io_overflow = (counter == io_limit);
  always @ (posedge io_mainClk) begin
    counter <= (counter + (16'b0000000000000001));
    if((io_clear || io_overflow))begin
      counter <= (16'b0000000000000000);
    end
  end

endmodule

module Timer (
      input   io_tick,
      input   io_clear,
      input  [15:0] io_limit,
      output  io_full,
      output [15:0] io_value,
      input   io_mainClk,
      input   resetCtrl_systemReset);
  wire [0:0] _zz_1_;
  wire [15:0] _zz_2_;
  reg [15:0] counter;
  wire  limitHit;
  reg  inhibitFull;
  assign _zz_1_ = (! limitHit);
  assign _zz_2_ = {15'd0, _zz_1_};
  assign limitHit = (counter == io_limit);
  assign io_full = ((limitHit && io_tick) && (! inhibitFull));
  assign io_value = counter;
  always @ (posedge io_mainClk or posedge resetCtrl_systemReset) begin
    if (resetCtrl_systemReset) begin
      inhibitFull <= 1'b0;
    end else begin
      if(io_tick)begin
        inhibitFull <= limitHit;
      end
      if(io_clear)begin
        inhibitFull <= 1'b0;
      end
    end
  end

  always @ (posedge io_mainClk) begin
    if(io_tick)begin
      counter <= (counter + _zz_2_);
    end
    if(io_clear)begin
      counter <= (16'b0000000000000000);
    end
  end

endmodule


//Timer_1_ remplaced by Timer

module InterruptCtrl (
      input  [1:0] io_inputs,
      input  [1:0] io_clears,
      input  [1:0] io_masks,
      output [1:0] io_pendings,
      input   io_mainClk,
      input   resetCtrl_systemReset);
  reg [1:0] pendings;
  assign io_pendings = (pendings & io_masks);
  always @ (posedge io_mainClk or posedge resetCtrl_systemReset) begin
    if (resetCtrl_systemReset) begin
      pendings <= (2'b00);
    end else begin
      pendings <= ((pendings & (~ io_clears)) | io_inputs);
    end
  end

endmodule

module BufferCC_2_ (
      input   io_dataIn,
      output  io_dataOut,
      input   io_mainClk);
  reg  buffers_0;
  reg  buffers_1;
  assign io_dataOut = buffers_1;
  always @ (posedge io_mainClk) begin
    buffers_0 <= io_dataIn;
    buffers_1 <= buffers_0;
  end

endmodule

module MuraxMasterArbiter (
      input   io_iBus_cmd_valid,
      output reg  io_iBus_cmd_ready,
      input  [31:0] io_iBus_cmd_payload_pc,
      output  io_iBus_rsp_valid,
      output  io_iBus_rsp_payload_error,
      output [31:0] io_iBus_rsp_payload_inst,
      input   io_dBus_cmd_valid,
      output reg  io_dBus_cmd_ready,
      input   io_dBus_cmd_payload_wr,
      input  [31:0] io_dBus_cmd_payload_address,
      input  [31:0] io_dBus_cmd_payload_data,
      input  [1:0] io_dBus_cmd_payload_size,
      output  io_dBus_rsp_ready,
      output  io_dBus_rsp_error,
      output [31:0] io_dBus_rsp_data,
      output reg  io_masterBus_cmd_valid,
      input   io_masterBus_cmd_ready,
      output  io_masterBus_cmd_payload_wr,
      output [31:0] io_masterBus_cmd_payload_address,
      output [31:0] io_masterBus_cmd_payload_data,
      output [3:0] io_masterBus_cmd_payload_mask,
      input   io_masterBus_rsp_valid,
      input  [31:0] io_masterBus_rsp_payload_data,
      input   io_mainClk,
      input   resetCtrl_systemReset);
  reg [3:0] _zz_1_;
  reg  rspPending;
  reg  rspTarget;
  always @ (*) begin
    io_masterBus_cmd_valid = (io_iBus_cmd_valid || io_dBus_cmd_valid);
    io_iBus_cmd_ready = (io_masterBus_cmd_ready && (! io_dBus_cmd_valid));
    io_dBus_cmd_ready = io_masterBus_cmd_ready;
    if((rspPending && (! io_masterBus_rsp_valid)))begin
      io_iBus_cmd_ready = 1'b0;
      io_dBus_cmd_ready = 1'b0;
      io_masterBus_cmd_valid = 1'b0;
    end
  end

  assign io_masterBus_cmd_payload_wr = (io_dBus_cmd_valid && io_dBus_cmd_payload_wr);
  assign io_masterBus_cmd_payload_address = (io_dBus_cmd_valid ? io_dBus_cmd_payload_address : io_iBus_cmd_payload_pc);
  assign io_masterBus_cmd_payload_data = io_dBus_cmd_payload_data;
  always @ (*) begin
    case(io_dBus_cmd_payload_size)
      2'b00 : begin
        _zz_1_ = (4'b0001);
      end
      2'b01 : begin
        _zz_1_ = (4'b0011);
      end
      default : begin
        _zz_1_ = (4'b1111);
      end
    endcase
  end

  assign io_masterBus_cmd_payload_mask = (_zz_1_ <<< io_dBus_cmd_payload_address[1 : 0]);
  assign io_iBus_rsp_valid = (io_masterBus_rsp_valid && (! rspTarget));
  assign io_iBus_rsp_payload_inst = io_masterBus_rsp_payload_data;
  assign io_iBus_rsp_payload_error = 1'b0;
  assign io_dBus_rsp_ready = (io_masterBus_rsp_valid && rspTarget);
  assign io_dBus_rsp_data = io_masterBus_rsp_payload_data;
  assign io_dBus_rsp_error = 1'b0;
  always @ (posedge io_mainClk or posedge resetCtrl_systemReset) begin
    if (resetCtrl_systemReset) begin
      rspPending <= 1'b0;
      rspTarget <= 1'b0;
    end else begin
      if(io_masterBus_rsp_valid)begin
        rspPending <= 1'b0;
      end
      if(((io_masterBus_cmd_valid && io_masterBus_cmd_ready) && (! io_masterBus_cmd_payload_wr)))begin
        rspTarget <= io_dBus_cmd_valid;
        rspPending <= 1'b1;
      end
    end
  end

endmodule

module VexRiscv (
      output  iBus_cmd_valid,
      input   iBus_cmd_ready,
      output [31:0] iBus_cmd_payload_pc,
      input   iBus_rsp_valid,
      input   iBus_rsp_payload_error,
      input  [31:0] iBus_rsp_payload_inst,
      input   timerInterrupt,
      input   externalInterrupt,
      input   debug_bus_cmd_valid,
      output reg  debug_bus_cmd_ready,
      input   debug_bus_cmd_payload_wr,
      input  [7:0] debug_bus_cmd_payload_address,
      input  [31:0] debug_bus_cmd_payload_data,
      output reg [31:0] debug_bus_rsp_data,
      output  debug_resetOut,
      output  dBus_cmd_valid,
      input   dBus_cmd_ready,
      output  dBus_cmd_payload_wr,
      output [31:0] dBus_cmd_payload_address,
      output [31:0] dBus_cmd_payload_data,
      output [1:0] dBus_cmd_payload_size,
      input   dBus_rsp_ready,
      input   dBus_rsp_error,
      input  [31:0] dBus_rsp_data,
      input   io_mainClk,
      input   resetCtrl_systemReset,
      input   resetCtrl_mainClkReset);
  wire  _zz_205_;
  wire  _zz_206_;
  reg [31:0] _zz_207_;
  reg [31:0] _zz_208_;
  reg [31:0] _zz_209_;
  reg [3:0] _zz_210_;
  reg [31:0] _zz_211_;
  wire  _zz_212_;
  wire  _zz_213_;
  wire  _zz_214_;
  wire [31:0] _zz_215_;
  wire [0:0] _zz_216_;
  wire  _zz_217_;
  wire  _zz_218_;
  wire  _zz_219_;
  wire  _zz_220_;
  wire  _zz_221_;
  wire  _zz_222_;
  wire  _zz_223_;
  wire  _zz_224_;
  wire  _zz_225_;
  wire [0:0] _zz_226_;
  wire  _zz_227_;
  wire [4:0] _zz_228_;
  wire [1:0] _zz_229_;
  wire [1:0] _zz_230_;
  wire [1:0] _zz_231_;
  wire  _zz_232_;
  wire [1:0] _zz_233_;
  wire [1:0] _zz_234_;
  wire [1:0] _zz_235_;
  wire [1:0] _zz_236_;
  wire [2:0] _zz_237_;
  wire [31:0] _zz_238_;
  wire [31:0] _zz_239_;
  wire [11:0] _zz_240_;
  wire [11:0] _zz_241_;
  wire [2:0] _zz_242_;
  wire [31:0] _zz_243_;
  wire [2:0] _zz_244_;
  wire [0:0] _zz_245_;
  wire [2:0] _zz_246_;
  wire [0:0] _zz_247_;
  wire [2:0] _zz_248_;
  wire [0:0] _zz_249_;
  wire [2:0] _zz_250_;
  wire [1:0] _zz_251_;
  wire [1:0] _zz_252_;
  wire [2:0] _zz_253_;
  wire [3:0] _zz_254_;
  wire [4:0] _zz_255_;
  wire [31:0] _zz_256_;
  wire [0:0] _zz_257_;
  wire [0:0] _zz_258_;
  wire [0:0] _zz_259_;
  wire [0:0] _zz_260_;
  wire [0:0] _zz_261_;
  wire [0:0] _zz_262_;
  wire [0:0] _zz_263_;
  wire [0:0] _zz_264_;
  wire [0:0] _zz_265_;
  wire [0:0] _zz_266_;
  wire [0:0] _zz_267_;
  wire [0:0] _zz_268_;
  wire [0:0] _zz_269_;
  wire [0:0] _zz_270_;
  wire [0:0] _zz_271_;
  wire [2:0] _zz_272_;
  wire [11:0] _zz_273_;
  wire [11:0] _zz_274_;
  wire [31:0] _zz_275_;
  wire [31:0] _zz_276_;
  wire [31:0] _zz_277_;
  wire [31:0] _zz_278_;
  wire [1:0] _zz_279_;
  wire [31:0] _zz_280_;
  wire [1:0] _zz_281_;
  wire [1:0] _zz_282_;
  wire [31:0] _zz_283_;
  wire [32:0] _zz_284_;
  wire [51:0] _zz_285_;
  wire [51:0] _zz_286_;
  wire [51:0] _zz_287_;
  wire [32:0] _zz_288_;
  wire [51:0] _zz_289_;
  wire [49:0] _zz_290_;
  wire [51:0] _zz_291_;
  wire [49:0] _zz_292_;
  wire [51:0] _zz_293_;
  wire [65:0] _zz_294_;
  wire [65:0] _zz_295_;
  wire [31:0] _zz_296_;
  wire [31:0] _zz_297_;
  wire [0:0] _zz_298_;
  wire [5:0] _zz_299_;
  wire [32:0] _zz_300_;
  wire [32:0] _zz_301_;
  wire [31:0] _zz_302_;
  wire [31:0] _zz_303_;
  wire [32:0] _zz_304_;
  wire [32:0] _zz_305_;
  wire [32:0] _zz_306_;
  wire [0:0] _zz_307_;
  wire [32:0] _zz_308_;
  wire [0:0] _zz_309_;
  wire [32:0] _zz_310_;
  wire [0:0] _zz_311_;
  wire [31:0] _zz_312_;
  wire [19:0] _zz_313_;
  wire [11:0] _zz_314_;
  wire [11:0] _zz_315_;
  wire [0:0] _zz_316_;
  wire [0:0] _zz_317_;
  wire [0:0] _zz_318_;
  wire [0:0] _zz_319_;
  wire [0:0] _zz_320_;
  wire [0:0] _zz_321_;
  wire [0:0] _zz_322_;
  wire  _zz_323_;
  wire  _zz_324_;
  wire [0:0] _zz_325_;
  wire  _zz_326_;
  wire  _zz_327_;
  wire [6:0] _zz_328_;
  wire [4:0] _zz_329_;
  wire  _zz_330_;
  wire [4:0] _zz_331_;
  wire [31:0] _zz_332_;
  wire [31:0] _zz_333_;
  wire [31:0] _zz_334_;
  wire  _zz_335_;
  wire [0:0] _zz_336_;
  wire [0:0] _zz_337_;
  wire  _zz_338_;
  wire [0:0] _zz_339_;
  wire [21:0] _zz_340_;
  wire [31:0] _zz_341_;
  wire [31:0] _zz_342_;
  wire [31:0] _zz_343_;
  wire [31:0] _zz_344_;
  wire  _zz_345_;
  wire [0:0] _zz_346_;
  wire [0:0] _zz_347_;
  wire [0:0] _zz_348_;
  wire [0:0] _zz_349_;
  wire  _zz_350_;
  wire [0:0] _zz_351_;
  wire [17:0] _zz_352_;
  wire [31:0] _zz_353_;
  wire [31:0] _zz_354_;
  wire [31:0] _zz_355_;
  wire  _zz_356_;
  wire [0:0] _zz_357_;
  wire [1:0] _zz_358_;
  wire  _zz_359_;
  wire [1:0] _zz_360_;
  wire [1:0] _zz_361_;
  wire  _zz_362_;
  wire [0:0] _zz_363_;
  wire [14:0] _zz_364_;
  wire [31:0] _zz_365_;
  wire [31:0] _zz_366_;
  wire [31:0] _zz_367_;
  wire [31:0] _zz_368_;
  wire [31:0] _zz_369_;
  wire [31:0] _zz_370_;
  wire [31:0] _zz_371_;
  wire  _zz_372_;
  wire [0:0] _zz_373_;
  wire [0:0] _zz_374_;
  wire [2:0] _zz_375_;
  wire [2:0] _zz_376_;
  wire  _zz_377_;
  wire [0:0] _zz_378_;
  wire [11:0] _zz_379_;
  wire [31:0] _zz_380_;
  wire [31:0] _zz_381_;
  wire  _zz_382_;
  wire [0:0] _zz_383_;
  wire [0:0] _zz_384_;
  wire [0:0] _zz_385_;
  wire [0:0] _zz_386_;
  wire [0:0] _zz_387_;
  wire [0:0] _zz_388_;
  wire  _zz_389_;
  wire [0:0] _zz_390_;
  wire [8:0] _zz_391_;
  wire [31:0] _zz_392_;
  wire [31:0] _zz_393_;
  wire  _zz_394_;
  wire  _zz_395_;
  wire [0:0] _zz_396_;
  wire [0:0] _zz_397_;
  wire  _zz_398_;
  wire [0:0] _zz_399_;
  wire [5:0] _zz_400_;
  wire [0:0] _zz_401_;
  wire [1:0] _zz_402_;
  wire [31:0] _zz_403_;
  wire [31:0] _zz_404_;
  wire  _zz_405_;
  wire [3:0] _zz_406_;
  wire [3:0] _zz_407_;
  wire  _zz_408_;
  wire [0:0] _zz_409_;
  wire [1:0] _zz_410_;
  wire [31:0] _zz_411_;
  wire [31:0] _zz_412_;
  wire [31:0] _zz_413_;
  wire [31:0] _zz_414_;
  wire [31:0] _zz_415_;
  wire [0:0] _zz_416_;
  wire [0:0] _zz_417_;
  wire  _zz_418_;
  wire [0:0] _zz_419_;
  wire [1:0] _zz_420_;
  wire [4:0] _zz_421_;
  wire [4:0] _zz_422_;
  wire [2:0] _zz_423_;
  wire [2:0] _zz_424_;
  wire [31:0] _zz_425_;
  wire [31:0] _zz_426_;
  wire  _zz_427_;
  wire [0:0] _zz_428_;
  wire [0:0] _zz_429_;
  wire [31:0] _zz_430_;
  wire [31:0] _zz_431_;
  wire [31:0] _zz_432_;
  wire [31:0] _zz_433_;
  wire [31:0] _zz_434_;
  wire [31:0] memory_MEMORY_READ_DATA;
  wire [31:0] decode_RS1;
  wire [33:0] memory_MUL_HH;
  wire [33:0] execute_MUL_HH;
  wire  decode_BYPASSABLE_EXECUTE_STAGE;
  wire [31:0] execute_BRANCH_CALC;
  wire [31:0] decode_SRC1;
  wire `EnvCtrlEnum_defaultEncoding_type memory_ENV_CTRL;
  wire `EnvCtrlEnum_defaultEncoding_type _zz_1_;
  wire `EnvCtrlEnum_defaultEncoding_type _zz_2_;
  wire `EnvCtrlEnum_defaultEncoding_type _zz_3_;
  wire `EnvCtrlEnum_defaultEncoding_type _zz_4_;
  wire `EnvCtrlEnum_defaultEncoding_type _zz_5_;
  wire `EnvCtrlEnum_defaultEncoding_type decode_ENV_CTRL;
  wire `EnvCtrlEnum_defaultEncoding_type _zz_6_;
  wire `EnvCtrlEnum_defaultEncoding_type _zz_7_;
  wire `EnvCtrlEnum_defaultEncoding_type _zz_8_;
  wire  decode_CSR_WRITE_OPCODE;
  wire `AluCtrlEnum_defaultEncoding_type decode_ALU_CTRL;
  wire `AluCtrlEnum_defaultEncoding_type _zz_9_;
  wire `AluCtrlEnum_defaultEncoding_type _zz_10_;
  wire `AluCtrlEnum_defaultEncoding_type _zz_11_;
  wire  decode_CSR_READ_OPCODE;
  wire  decode_IS_RS2_SIGNED;
  wire `AluBitwiseCtrlEnum_defaultEncoding_type decode_ALU_BITWISE_CTRL;
  wire `AluBitwiseCtrlEnum_defaultEncoding_type _zz_12_;
  wire `AluBitwiseCtrlEnum_defaultEncoding_type _zz_13_;
  wire `AluBitwiseCtrlEnum_defaultEncoding_type _zz_14_;
  wire [1:0] memory_MEMORY_ADDRESS_LOW;
  wire [1:0] execute_MEMORY_ADDRESS_LOW;
  wire [31:0] decode_RS2;
  wire [31:0] writeBack_FORMAL_PC_NEXT;
  wire [31:0] memory_FORMAL_PC_NEXT;
  wire [31:0] execute_FORMAL_PC_NEXT;
  wire [31:0] decode_FORMAL_PC_NEXT;
  wire  decode_IS_RS1_SIGNED;
  wire  decode_IS_DIV;
  wire  decode_IS_EBREAK;
  wire [33:0] execute_MUL_LH;
  wire [31:0] execute_MUL_LL;
  wire  execute_BYPASSABLE_MEMORY_STAGE;
  wire  decode_BYPASSABLE_MEMORY_STAGE;
  wire  memory_IS_MUL;
  wire  execute_IS_MUL;
  wire  decode_IS_MUL;
  wire  execute_BRANCH_DO;
  wire [31:0] memory_PC;
  wire [31:0] writeBack_REGFILE_WRITE_DATA;
  wire [31:0] execute_REGFILE_WRITE_DATA;
  wire [51:0] memory_MUL_LOW;
  wire  decode_MEMORY_ENABLE;
  wire  decode_SRC_LESS_UNSIGNED;
  wire `ShiftCtrlEnum_defaultEncoding_type decode_SHIFT_CTRL;
  wire `ShiftCtrlEnum_defaultEncoding_type _zz_15_;
  wire `ShiftCtrlEnum_defaultEncoding_type _zz_16_;
  wire `ShiftCtrlEnum_defaultEncoding_type _zz_17_;
  wire  decode_SRC_USE_SUB_LESS;
  wire [31:0] decode_SRC2;
  wire [33:0] execute_MUL_HL;
  wire `BranchCtrlEnum_defaultEncoding_type decode_BRANCH_CTRL;
  wire `BranchCtrlEnum_defaultEncoding_type _zz_18_;
  wire `BranchCtrlEnum_defaultEncoding_type _zz_19_;
  wire `BranchCtrlEnum_defaultEncoding_type _zz_20_;
  wire  execute_IS_EBREAK;
  wire [31:0] memory_BRANCH_CALC;
  wire  memory_BRANCH_DO;
  wire [31:0] _zz_21_;
  wire [31:0] execute_PC;
  wire `BranchCtrlEnum_defaultEncoding_type execute_BRANCH_CTRL;
  wire `BranchCtrlEnum_defaultEncoding_type _zz_22_;
  wire  _zz_23_;
  wire  execute_IS_RS1_SIGNED;
  wire [31:0] execute_RS1;
  wire  execute_IS_DIV;
  wire  execute_IS_RS2_SIGNED;
  reg [31:0] _zz_24_;
  wire  memory_IS_DIV;
  wire  writeBack_IS_MUL;
  wire [33:0] writeBack_MUL_HH;
  wire [51:0] writeBack_MUL_LOW;
  wire [33:0] memory_MUL_HL;
  wire [33:0] memory_MUL_LH;
  wire [31:0] memory_MUL_LL;
  wire [51:0] _zz_25_;
  wire [33:0] _zz_26_;
  wire [33:0] _zz_27_;
  wire [33:0] _zz_28_;
  wire [31:0] _zz_29_;
  wire  decode_RS2_USE;
  wire  decode_RS1_USE;
  wire  execute_REGFILE_WRITE_VALID;
  wire  execute_BYPASSABLE_EXECUTE_STAGE;
  wire  memory_REGFILE_WRITE_VALID;
  wire  memory_BYPASSABLE_MEMORY_STAGE;
  wire  writeBack_REGFILE_WRITE_VALID;
  wire `ShiftCtrlEnum_defaultEncoding_type execute_SHIFT_CTRL;
  wire `ShiftCtrlEnum_defaultEncoding_type _zz_30_;
  wire  _zz_31_;
  wire [31:0] _zz_32_;
  wire [31:0] _zz_33_;
  wire  execute_SRC_LESS_UNSIGNED;
  wire  execute_SRC_USE_SUB_LESS;
  wire [31:0] _zz_34_;
  wire [31:0] _zz_35_;
  wire `Src2CtrlEnum_defaultEncoding_type decode_SRC2_CTRL;
  wire `Src2CtrlEnum_defaultEncoding_type _zz_36_;
  wire [31:0] _zz_37_;
  wire [31:0] _zz_38_;
  wire `Src1CtrlEnum_defaultEncoding_type decode_SRC1_CTRL;
  wire `Src1CtrlEnum_defaultEncoding_type _zz_39_;
  wire [31:0] _zz_40_;
  wire [31:0] execute_SRC_ADD_SUB;
  wire  execute_SRC_LESS;
  wire `AluCtrlEnum_defaultEncoding_type execute_ALU_CTRL;
  wire `AluCtrlEnum_defaultEncoding_type _zz_41_;
  wire [31:0] _zz_42_;
  wire [31:0] execute_SRC2;
  wire `AluBitwiseCtrlEnum_defaultEncoding_type execute_ALU_BITWISE_CTRL;
  wire `AluBitwiseCtrlEnum_defaultEncoding_type _zz_43_;
  wire [31:0] _zz_44_;
  wire  _zz_45_;
  reg  _zz_46_;
  wire [31:0] _zz_47_;
  wire [31:0] _zz_48_;
  wire [31:0] decode_INSTRUCTION_ANTICIPATED;
  reg  decode_REGFILE_WRITE_VALID;
  wire `BranchCtrlEnum_defaultEncoding_type _zz_49_;
  wire `EnvCtrlEnum_defaultEncoding_type _zz_50_;
  wire  _zz_51_;
  wire `AluCtrlEnum_defaultEncoding_type _zz_52_;
  wire  _zz_53_;
  wire  _zz_54_;
  wire  _zz_55_;
  wire `ShiftCtrlEnum_defaultEncoding_type _zz_56_;
  wire  _zz_57_;
  wire `Src2CtrlEnum_defaultEncoding_type _zz_58_;
  wire  _zz_59_;
  wire  _zz_60_;
  wire  _zz_61_;
  wire `Src1CtrlEnum_defaultEncoding_type _zz_62_;
  wire  _zz_63_;
  wire  _zz_64_;
  wire  _zz_65_;
  wire  _zz_66_;
  wire `AluBitwiseCtrlEnum_defaultEncoding_type _zz_67_;
  wire  _zz_68_;
  wire  _zz_69_;
  reg [31:0] _zz_70_;
  wire  execute_CSR_READ_OPCODE;
  wire  execute_CSR_WRITE_OPCODE;
  wire [31:0] memory_REGFILE_WRITE_DATA;
  wire [31:0] execute_SRC1;
  wire  execute_IS_CSR;
  wire  decode_IS_CSR;
  wire  _zz_71_;
  wire  _zz_72_;
  wire `EnvCtrlEnum_defaultEncoding_type execute_ENV_CTRL;
  wire `EnvCtrlEnum_defaultEncoding_type _zz_73_;
  wire `EnvCtrlEnum_defaultEncoding_type writeBack_ENV_CTRL;
  wire `EnvCtrlEnum_defaultEncoding_type _zz_74_;
  reg [31:0] _zz_75_;
  wire  writeBack_MEMORY_ENABLE;
  wire [1:0] writeBack_MEMORY_ADDRESS_LOW;
  wire [31:0] writeBack_MEMORY_READ_DATA;
  wire [31:0] memory_INSTRUCTION;
  wire  memory_MEMORY_ENABLE;
  wire [31:0] _zz_76_;
  wire [1:0] _zz_77_;
  wire [31:0] execute_RS2;
  wire [31:0] execute_SRC_ADD;
  wire [31:0] execute_INSTRUCTION;
  wire  execute_ALIGNEMENT_FAULT;
  wire  execute_MEMORY_ENABLE;
  reg [31:0] _zz_78_;
  wire [31:0] _zz_79_;
  wire  _zz_80_;
  wire [31:0] _zz_81_;
  wire [31:0] _zz_82_;
  wire [31:0] _zz_83_;
  wire  decode_IS_RVC;
  wire [31:0] writeBack_PC /* verilator public */ ;
  wire [31:0] writeBack_INSTRUCTION /* verilator public */ ;
  wire [31:0] decode_PC /* verilator public */ ;
  wire [31:0] decode_INSTRUCTION /* verilator public */ ;
  reg  decode_arbitration_haltItself /* verilator public */ ;
  reg  decode_arbitration_haltByOther;
  reg  decode_arbitration_removeIt;
  reg  decode_arbitration_flushAll /* verilator public */ ;
  wire  decode_arbitration_redoIt;
  reg  decode_arbitration_isValid /* verilator public */ ;
  wire  decode_arbitration_isStuck;
  wire  decode_arbitration_isStuckByOthers;
  wire  decode_arbitration_isFlushed;
  wire  decode_arbitration_isMoving;
  wire  decode_arbitration_isFiring;
  reg  execute_arbitration_haltItself;
  reg  execute_arbitration_haltByOther;
  reg  execute_arbitration_removeIt;
  reg  execute_arbitration_flushAll;
  wire  execute_arbitration_redoIt;
  reg  execute_arbitration_isValid;
  wire  execute_arbitration_isStuck;
  wire  execute_arbitration_isStuckByOthers;
  wire  execute_arbitration_isFlushed;
  wire  execute_arbitration_isMoving;
  wire  execute_arbitration_isFiring;
  reg  memory_arbitration_haltItself;
  reg  memory_arbitration_haltByOther;
  reg  memory_arbitration_removeIt;
  reg  memory_arbitration_flushAll;
  wire  memory_arbitration_redoIt;
  reg  memory_arbitration_isValid;
  wire  memory_arbitration_isStuck;
  wire  memory_arbitration_isStuckByOthers;
  wire  memory_arbitration_isFlushed;
  wire  memory_arbitration_isMoving;
  wire  memory_arbitration_isFiring;
  wire  writeBack_arbitration_haltItself;
  wire  writeBack_arbitration_haltByOther;
  reg  writeBack_arbitration_removeIt;
  wire  writeBack_arbitration_flushAll;
  wire  writeBack_arbitration_redoIt;
  reg  writeBack_arbitration_isValid /* verilator public */ ;
  wire  writeBack_arbitration_isStuck;
  wire  writeBack_arbitration_isStuckByOthers;
  wire  writeBack_arbitration_isFlushed;
  wire  writeBack_arbitration_isMoving;
  wire  writeBack_arbitration_isFiring /* verilator public */ ;
  reg  _zz_84_;
  reg  _zz_85_;
  reg  _zz_86_;
  reg  _zz_87_;
  reg [31:0] _zz_88_;
  reg  _zz_89_;
  reg [3:0] _zz_90_;
  wire  contextSwitching;
  reg [1:0] _zz_91_;
  wire  _zz_92_;
  reg  _zz_93_;
  reg  _zz_94_;
  wire  _zz_95_;
  wire [31:0] _zz_96_;
  reg  _zz_97_;
  reg  _zz_98_;
  wire  IBusSimplePlugin_jump_pcLoad_valid;
  wire [31:0] IBusSimplePlugin_jump_pcLoad_payload;
  wire [1:0] _zz_99_;
  wire  _zz_100_;
  wire  IBusSimplePlugin_fetchPc_preOutput_valid;
  wire  IBusSimplePlugin_fetchPc_preOutput_ready;
  wire [31:0] IBusSimplePlugin_fetchPc_preOutput_payload;
  wire  _zz_101_;
  wire  IBusSimplePlugin_fetchPc_output_valid;
  wire  IBusSimplePlugin_fetchPc_output_ready;
  wire [31:0] IBusSimplePlugin_fetchPc_output_payload;
  reg [31:0] IBusSimplePlugin_fetchPc_pcReg /* verilator public */ ;
  wire [31:0] IBusSimplePlugin_fetchPc_pcPlus4;
  reg  _zz_102_;
  reg [31:0] IBusSimplePlugin_decodePc_pcReg /* verilator public */ ;
  wire [31:0] IBusSimplePlugin_decodePc_pcPlus;
  reg  IBusSimplePlugin_decodePc_injectedDecode;
  wire  IBusSimplePlugin_iBusRsp_input_valid;
  wire  IBusSimplePlugin_iBusRsp_input_ready;
  wire [31:0] IBusSimplePlugin_iBusRsp_input_payload;
  wire  IBusSimplePlugin_iBusRsp_inputPipeline_0_valid;
  reg  IBusSimplePlugin_iBusRsp_inputPipeline_0_ready;
  wire [31:0] IBusSimplePlugin_iBusRsp_inputPipeline_0_payload;
  wire  _zz_103_;
  reg  _zz_104_;
  reg [31:0] _zz_105_;
  reg  IBusSimplePlugin_iBusRsp_readyForError;
  wire  IBusSimplePlugin_iBusRsp_output_valid;
  wire  IBusSimplePlugin_iBusRsp_output_ready;
  wire [31:0] IBusSimplePlugin_iBusRsp_output_payload_pc;
  wire  IBusSimplePlugin_iBusRsp_output_payload_rsp_error;
  wire [31:0] IBusSimplePlugin_iBusRsp_output_payload_rsp_inst;
  wire  IBusSimplePlugin_iBusRsp_output_payload_isRvc;
  wire  IBusSimplePlugin_decompressor_inputBeforeStage_valid;
  wire  IBusSimplePlugin_decompressor_inputBeforeStage_ready;
  wire [31:0] IBusSimplePlugin_decompressor_inputBeforeStage_payload_pc;
  wire  IBusSimplePlugin_decompressor_inputBeforeStage_payload_rsp_error;
  wire [31:0] IBusSimplePlugin_decompressor_inputBeforeStage_payload_rsp_inst;
  wire  IBusSimplePlugin_decompressor_inputBeforeStage_payload_isRvc;
  reg  IBusSimplePlugin_decompressor_bufferValid;
  reg [15:0] IBusSimplePlugin_decompressor_bufferData;
  wire [31:0] IBusSimplePlugin_decompressor_raw;
  wire  IBusSimplePlugin_decompressor_isRvc;
  wire [15:0] _zz_106_;
  reg [31:0] IBusSimplePlugin_decompressor_decompressed;
  wire [4:0] _zz_107_;
  wire [4:0] _zz_108_;
  wire [11:0] _zz_109_;
  wire  _zz_110_;
  reg [11:0] _zz_111_;
  wire  _zz_112_;
  reg [9:0] _zz_113_;
  wire [20:0] _zz_114_;
  wire  _zz_115_;
  reg [14:0] _zz_116_;
  wire  _zz_117_;
  reg [2:0] _zz_118_;
  wire  _zz_119_;
  reg [9:0] _zz_120_;
  wire [20:0] _zz_121_;
  wire  _zz_122_;
  reg [4:0] _zz_123_;
  wire [12:0] _zz_124_;
  wire [4:0] _zz_125_;
  wire [4:0] _zz_126_;
  wire [4:0] _zz_127_;
  wire  _zz_128_;
  reg [2:0] _zz_129_;
  reg [2:0] _zz_130_;
  wire  _zz_131_;
  reg [6:0] _zz_132_;
  wire  IBusSimplePlugin_injector_decodeInput_valid;
  wire  IBusSimplePlugin_injector_decodeInput_ready;
  wire [31:0] IBusSimplePlugin_injector_decodeInput_payload_pc;
  wire  IBusSimplePlugin_injector_decodeInput_payload_rsp_error;
  wire [31:0] IBusSimplePlugin_injector_decodeInput_payload_rsp_inst;
  wire  IBusSimplePlugin_injector_decodeInput_payload_isRvc;
  reg  _zz_133_;
  reg [31:0] _zz_134_;
  reg  _zz_135_;
  reg [31:0] _zz_136_;
  reg  _zz_137_;
  reg  _zz_138_;
  reg  _zz_139_;
  reg  _zz_140_;
  reg  _zz_141_;
  reg  IBusSimplePlugin_injector_decodeRemoved;
  reg [31:0] IBusSimplePlugin_injector_formal_rawInDecode;
  reg [2:0] IBusSimplePlugin_pendingCmd;
  wire [2:0] IBusSimplePlugin_pendingCmdNext;
  wire  _zz_142_;
  reg [2:0] IBusSimplePlugin_rsp_discardCounter;
  wire [31:0] IBusSimplePlugin_rsp_fetchRsp_pc;
  reg  IBusSimplePlugin_rsp_fetchRsp_rsp_error;
  wire [31:0] IBusSimplePlugin_rsp_fetchRsp_rsp_inst;
  wire  IBusSimplePlugin_rsp_fetchRsp_isRvc;
  wire  IBusSimplePlugin_rsp_issueDetected;
  wire  _zz_143_;
  wire  _zz_144_;
  wire  IBusSimplePlugin_rsp_join_valid;
  wire  IBusSimplePlugin_rsp_join_ready;
  wire [31:0] IBusSimplePlugin_rsp_join_payload_pc;
  wire  IBusSimplePlugin_rsp_join_payload_rsp_error;
  wire [31:0] IBusSimplePlugin_rsp_join_payload_rsp_inst;
  wire  IBusSimplePlugin_rsp_join_payload_isRvc;
  wire  _zz_145_;
  reg [31:0] _zz_146_;
  reg [3:0] _zz_147_;
  wire [3:0] execute_DBusSimplePlugin_formalMask;
  reg [31:0] writeBack_DBusSimplePlugin_rspShifted;
  wire  _zz_148_;
  reg [31:0] _zz_149_;
  wire  _zz_150_;
  reg [31:0] _zz_151_;
  reg [31:0] writeBack_DBusSimplePlugin_rspFormated;
  reg [1:0] CsrPlugin_misa_base;
  reg [25:0] CsrPlugin_misa_extensions;
  reg [31:0] CsrPlugin_mtvec;
  reg [31:0] CsrPlugin_mepc;
  reg  CsrPlugin_mstatus_MIE;
  reg  CsrPlugin_mstatus_MPIE;
  reg [1:0] CsrPlugin_mstatus_MPP;
  reg  CsrPlugin_mip_MEIP;
  reg  CsrPlugin_mip_MTIP;
  reg  CsrPlugin_mip_MSIP;
  reg  CsrPlugin_mie_MEIE;
  reg  CsrPlugin_mie_MTIE;
  reg  CsrPlugin_mie_MSIE;
  reg [31:0] CsrPlugin_mscratch;
  reg  CsrPlugin_mcause_interrupt;
  reg [3:0] CsrPlugin_mcause_exceptionCode;
  reg [31:0] CsrPlugin_mbadaddr;
  reg [63:0] CsrPlugin_mcycle = 64'b0000000000000000000000000000000000000000000000000000000000000000;
  reg [63:0] CsrPlugin_minstret = 64'b0000000000000000000000000000000000000000000000000000000000000000;
  wire  CsrPlugin_exceptionPortCtrl_exceptionValids_decode;
  reg  CsrPlugin_exceptionPortCtrl_exceptionValids_execute;
  reg  CsrPlugin_exceptionPortCtrl_exceptionValids_memory;
  reg  CsrPlugin_exceptionPortCtrl_exceptionValids_writeBack;
  wire  CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_decode;
  reg  CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_execute;
  reg  CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_memory;
  reg  CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_writeBack;
  reg [3:0] CsrPlugin_exceptionPortCtrl_exceptionContext_code;
  reg [31:0] CsrPlugin_exceptionPortCtrl_exceptionContext_badAddr;
  wire  execute_exception_agregat_valid;
  wire [3:0] execute_exception_agregat_payload_code;
  wire [31:0] execute_exception_agregat_payload_badAddr;
  wire [1:0] _zz_152_;
  wire  _zz_153_;
  wire [0:0] _zz_154_;
  wire  CsrPlugin_interruptRequest;
  wire  CsrPlugin_interrupt;
  wire  CsrPlugin_exception;
  reg  CsrPlugin_writeBackWasWfi;
  reg  CsrPlugin_pipelineLiberator_done;
  wire [3:0] CsrPlugin_interruptCode /* verilator public */ ;
  wire  CsrPlugin_interruptJump /* verilator public */ ;
  reg  CsrPlugin_exception_regNext;
  reg  execute_CsrPlugin_illegalAccess;
  wire [31:0] execute_CsrPlugin_writeSrc;
  reg [31:0] execute_CsrPlugin_readData;
  reg  execute_CsrPlugin_readDataRegValid;
  reg [31:0] execute_CsrPlugin_writeData;
  wire  execute_CsrPlugin_writeInstruction;
  wire  execute_CsrPlugin_readInstruction;
  wire  execute_CsrPlugin_writeEnable;
  wire  execute_CsrPlugin_readEnable;
  wire [11:0] execute_CsrPlugin_csrAddress;
  wire [28:0] _zz_155_;
  wire  _zz_156_;
  wire  _zz_157_;
  wire  _zz_158_;
  wire  _zz_159_;
  wire  _zz_160_;
  wire  _zz_161_;
  wire  _zz_162_;
  wire  _zz_163_;
  wire  _zz_164_;
  wire `AluBitwiseCtrlEnum_defaultEncoding_type _zz_165_;
  wire `Src1CtrlEnum_defaultEncoding_type _zz_166_;
  wire `Src2CtrlEnum_defaultEncoding_type _zz_167_;
  wire `ShiftCtrlEnum_defaultEncoding_type _zz_168_;
  wire `AluCtrlEnum_defaultEncoding_type _zz_169_;
  wire `EnvCtrlEnum_defaultEncoding_type _zz_170_;
  wire `BranchCtrlEnum_defaultEncoding_type _zz_171_;
  wire [4:0] decode_RegFilePlugin_regFileReadAddress1;
  wire [4:0] decode_RegFilePlugin_regFileReadAddress2;
  wire [31:0] decode_RegFilePlugin_rs1Data;
  wire [31:0] decode_RegFilePlugin_rs2Data;
  reg  writeBack_RegFilePlugin_regFileWrite_valid /* verilator public */ ;
  wire [4:0] writeBack_RegFilePlugin_regFileWrite_payload_address /* verilator public */ ;
  wire [31:0] writeBack_RegFilePlugin_regFileWrite_payload_data /* verilator public */ ;
  reg  _zz_172_;
  reg [31:0] execute_IntAluPlugin_bitwise;
  reg [31:0] _zz_173_;
  reg [31:0] _zz_174_;
  wire  _zz_175_;
  reg [19:0] _zz_176_;
  wire  _zz_177_;
  reg [19:0] _zz_178_;
  reg [31:0] _zz_179_;
  wire [31:0] execute_SrcPlugin_addSub;
  wire  execute_SrcPlugin_less;
  reg  execute_LightShifterPlugin_isActive;
  wire  execute_LightShifterPlugin_isShift;
  reg [4:0] execute_LightShifterPlugin_amplitudeReg;
  wire [4:0] execute_LightShifterPlugin_amplitude;
  wire [31:0] execute_LightShifterPlugin_shiftInput;
  wire  execute_LightShifterPlugin_done;
  reg [31:0] _zz_180_;
  reg  _zz_181_;
  reg  _zz_182_;
  reg  _zz_183_;
  reg [4:0] _zz_184_;
  reg  execute_MulPlugin_aSigned;
  reg  execute_MulPlugin_bSigned;
  wire [31:0] execute_MulPlugin_a;
  wire [31:0] execute_MulPlugin_b;
  wire [15:0] execute_MulPlugin_aULow;
  wire [15:0] execute_MulPlugin_bULow;
  wire [16:0] execute_MulPlugin_aSLow;
  wire [16:0] execute_MulPlugin_bSLow;
  wire [16:0] execute_MulPlugin_aHigh;
  wire [16:0] execute_MulPlugin_bHigh;
  wire [65:0] writeBack_MulPlugin_result;
  reg [32:0] memory_DivPlugin_rs1;
  reg [31:0] memory_DivPlugin_rs2;
  reg [64:0] memory_DivPlugin_accumulator;
  reg  memory_DivPlugin_div_needRevert;
  reg  memory_DivPlugin_div_counter_willIncrement;
  reg  memory_DivPlugin_div_counter_willClear;
  reg [5:0] memory_DivPlugin_div_counter_valueNext;
  reg [5:0] memory_DivPlugin_div_counter_value;
  wire  memory_DivPlugin_div_willOverflowIfInc;
  wire  memory_DivPlugin_div_counter_willOverflow;
  reg [31:0] memory_DivPlugin_div_result;
  wire [31:0] _zz_185_;
  wire [32:0] _zz_186_;
  wire [32:0] _zz_187_;
  wire [31:0] _zz_188_;
  wire  _zz_189_;
  wire  _zz_190_;
  reg [32:0] _zz_191_;
  wire  execute_BranchPlugin_eq;
  wire [2:0] _zz_192_;
  reg  _zz_193_;
  reg  _zz_194_;
  wire [31:0] execute_BranchPlugin_branch_src1;
  wire  _zz_195_;
  reg [10:0] _zz_196_;
  wire  _zz_197_;
  reg [19:0] _zz_198_;
  wire  _zz_199_;
  reg [18:0] _zz_200_;
  reg [31:0] _zz_201_;
  wire [31:0] execute_BranchPlugin_branch_src2;
  wire [31:0] execute_BranchPlugin_branchAdder;
  reg  DebugPlugin_firstCycle;
  reg  DebugPlugin_secondCycle;
  reg  DebugPlugin_resetIt;
  reg  DebugPlugin_haltIt;
  reg  DebugPlugin_stepIt;
  reg  DebugPlugin_isPipActive;
  reg  DebugPlugin_isPipActive_regNext;
  wire  DebugPlugin_isPipBusy;
  reg  DebugPlugin_haltedByBreak;
  reg [31:0] DebugPlugin_busReadDataReg;
  reg  _zz_202_;
  reg  _zz_203_;
  reg  DebugPlugin_resetIt_regNext;
  reg `BranchCtrlEnum_defaultEncoding_type decode_to_execute_BRANCH_CTRL;
  reg [33:0] execute_to_memory_MUL_HL;
  reg  decode_to_execute_IS_CSR;
  reg [31:0] decode_to_execute_SRC2;
  reg  decode_to_execute_SRC_USE_SUB_LESS;
  reg `ShiftCtrlEnum_defaultEncoding_type decode_to_execute_SHIFT_CTRL;
  reg  decode_to_execute_SRC_LESS_UNSIGNED;
  reg  decode_to_execute_MEMORY_ENABLE;
  reg  execute_to_memory_MEMORY_ENABLE;
  reg  memory_to_writeBack_MEMORY_ENABLE;
  reg [51:0] memory_to_writeBack_MUL_LOW;
  reg [31:0] execute_to_memory_REGFILE_WRITE_DATA;
  reg [31:0] memory_to_writeBack_REGFILE_WRITE_DATA;
  reg [31:0] decode_to_execute_PC;
  reg [31:0] execute_to_memory_PC;
  reg [31:0] memory_to_writeBack_PC;
  reg  execute_to_memory_BRANCH_DO;
  reg  decode_to_execute_IS_MUL;
  reg  execute_to_memory_IS_MUL;
  reg  memory_to_writeBack_IS_MUL;
  reg  decode_to_execute_BYPASSABLE_MEMORY_STAGE;
  reg  execute_to_memory_BYPASSABLE_MEMORY_STAGE;
  reg [31:0] execute_to_memory_MUL_LL;
  reg [33:0] execute_to_memory_MUL_LH;
  reg  decode_to_execute_IS_EBREAK;
  reg  decode_to_execute_IS_DIV;
  reg  execute_to_memory_IS_DIV;
  reg  decode_to_execute_IS_RS1_SIGNED;
  reg [31:0] decode_to_execute_FORMAL_PC_NEXT;
  reg [31:0] execute_to_memory_FORMAL_PC_NEXT;
  reg [31:0] memory_to_writeBack_FORMAL_PC_NEXT;
  reg [31:0] decode_to_execute_RS2;
  reg [1:0] execute_to_memory_MEMORY_ADDRESS_LOW;
  reg [1:0] memory_to_writeBack_MEMORY_ADDRESS_LOW;
  reg `AluBitwiseCtrlEnum_defaultEncoding_type decode_to_execute_ALU_BITWISE_CTRL;
  reg  decode_to_execute_IS_RS2_SIGNED;
  reg  decode_to_execute_CSR_READ_OPCODE;
  reg `AluCtrlEnum_defaultEncoding_type decode_to_execute_ALU_CTRL;
  reg  decode_to_execute_CSR_WRITE_OPCODE;
  reg `EnvCtrlEnum_defaultEncoding_type decode_to_execute_ENV_CTRL;
  reg `EnvCtrlEnum_defaultEncoding_type execute_to_memory_ENV_CTRL;
  reg `EnvCtrlEnum_defaultEncoding_type memory_to_writeBack_ENV_CTRL;
  reg [31:0] decode_to_execute_SRC1;
  reg [31:0] execute_to_memory_BRANCH_CALC;
  reg  decode_to_execute_REGFILE_WRITE_VALID;
  reg  execute_to_memory_REGFILE_WRITE_VALID;
  reg  memory_to_writeBack_REGFILE_WRITE_VALID;
  reg  decode_to_execute_BYPASSABLE_EXECUTE_STAGE;
  reg [33:0] execute_to_memory_MUL_HH;
  reg [33:0] memory_to_writeBack_MUL_HH;
  reg [31:0] decode_to_execute_INSTRUCTION;
  reg [31:0] execute_to_memory_INSTRUCTION;
  reg [31:0] memory_to_writeBack_INSTRUCTION;
  reg [31:0] decode_to_execute_RS1;
  reg [31:0] memory_to_writeBack_MEMORY_READ_DATA;
  reg [2:0] _zz_204_;
  reg [31:0] RegFilePlugin_regFile [0:31] /* verilator public */ ;
  assign _zz_217_ = (memory_arbitration_isValid && memory_IS_DIV);
  assign _zz_218_ = (! memory_DivPlugin_div_willOverflowIfInc);
  assign _zz_219_ = (CsrPlugin_exception || CsrPlugin_interruptJump);
  assign _zz_220_ = (execute_arbitration_isValid && (execute_ENV_CTRL == `EnvCtrlEnum_defaultEncoding_MRET));
  assign _zz_221_ = (memory_arbitration_isValid || writeBack_arbitration_isValid);
  assign _zz_222_ = ((execute_arbitration_isValid && execute_LightShifterPlugin_isShift) && (execute_SRC2[4 : 0] != (5'b00000)));
  assign _zz_223_ = (! execute_arbitration_isStuckByOthers);
  assign _zz_224_ = (DebugPlugin_stepIt && _zz_86_);
  assign _zz_225_ = (! memory_arbitration_isStuck);
  assign _zz_226_ = debug_bus_cmd_payload_address[2 : 2];
  assign _zz_227_ = (IBusSimplePlugin_iBusRsp_output_valid && IBusSimplePlugin_iBusRsp_output_ready);
  assign _zz_228_ = {_zz_106_[1 : 0],_zz_106_[15 : 13]};
  assign _zz_229_ = _zz_106_[6 : 5];
  assign _zz_230_ = _zz_106_[11 : 10];
  assign _zz_231_ = writeBack_INSTRUCTION[13 : 12];
  assign _zz_232_ = execute_INSTRUCTION[13];
  assign _zz_233_ = execute_INSTRUCTION[13 : 12];
  assign _zz_234_ = writeBack_INSTRUCTION[13 : 12];
  assign _zz_235_ = (_zz_99_ & (~ _zz_236_));
  assign _zz_236_ = (_zz_99_ - (2'b01));
  assign _zz_237_ = (decode_IS_RVC ? (3'b010) : (3'b100));
  assign _zz_238_ = {29'd0, _zz_237_};
  assign _zz_239_ = {{_zz_116_,_zz_106_[6 : 2]},(12'b000000000000)};
  assign _zz_240_ = {{{(4'b0000),_zz_106_[8 : 7]},_zz_106_[12 : 9]},(2'b00)};
  assign _zz_241_ = {{{(4'b0000),_zz_106_[8 : 7]},_zz_106_[12 : 9]},(2'b00)};
  assign _zz_242_ = (decode_IS_RVC ? (3'b010) : (3'b100));
  assign _zz_243_ = {29'd0, _zz_242_};
  assign _zz_244_ = (IBusSimplePlugin_pendingCmd + _zz_246_);
  assign _zz_245_ = (iBus_cmd_valid && iBus_cmd_ready);
  assign _zz_246_ = {2'd0, _zz_245_};
  assign _zz_247_ = iBus_rsp_valid;
  assign _zz_248_ = {2'd0, _zz_247_};
  assign _zz_249_ = (iBus_rsp_valid && (IBusSimplePlugin_rsp_discardCounter != (3'b000)));
  assign _zz_250_ = {2'd0, _zz_249_};
  assign _zz_251_ = (_zz_152_ & (~ _zz_252_));
  assign _zz_252_ = (_zz_152_ - (2'b01));
  assign _zz_253_ = ((CsrPlugin_mip_MSIP && CsrPlugin_mie_MSIE) ? (3'b011) : (3'b111));
  assign _zz_254_ = {1'd0, _zz_253_};
  assign _zz_255_ = execute_INSTRUCTION[19 : 15];
  assign _zz_256_ = {27'd0, _zz_255_};
  assign _zz_257_ = _zz_155_[0 : 0];
  assign _zz_258_ = _zz_155_[1 : 1];
  assign _zz_259_ = _zz_155_[4 : 4];
  assign _zz_260_ = _zz_155_[5 : 5];
  assign _zz_261_ = _zz_155_[6 : 6];
  assign _zz_262_ = _zz_155_[7 : 7];
  assign _zz_263_ = _zz_155_[10 : 10];
  assign _zz_264_ = _zz_155_[11 : 11];
  assign _zz_265_ = _zz_155_[12 : 12];
  assign _zz_266_ = _zz_155_[15 : 15];
  assign _zz_267_ = _zz_155_[18 : 18];
  assign _zz_268_ = _zz_155_[19 : 19];
  assign _zz_269_ = _zz_155_[20 : 20];
  assign _zz_270_ = _zz_155_[23 : 23];
  assign _zz_271_ = execute_SRC_LESS;
  assign _zz_272_ = (decode_IS_RVC ? (3'b010) : (3'b100));
  assign _zz_273_ = decode_INSTRUCTION[31 : 20];
  assign _zz_274_ = {decode_INSTRUCTION[31 : 25],decode_INSTRUCTION[11 : 7]};
  assign _zz_275_ = ($signed(_zz_276_) + $signed(_zz_280_));
  assign _zz_276_ = ($signed(_zz_277_) + $signed(_zz_278_));
  assign _zz_277_ = execute_SRC1;
  assign _zz_278_ = (execute_SRC_USE_SUB_LESS ? (~ execute_SRC2) : execute_SRC2);
  assign _zz_279_ = (execute_SRC_USE_SUB_LESS ? _zz_281_ : _zz_282_);
  assign _zz_280_ = {{30{_zz_279_[1]}}, _zz_279_};
  assign _zz_281_ = (2'b01);
  assign _zz_282_ = (2'b00);
  assign _zz_283_ = (_zz_284_ >>> 1);
  assign _zz_284_ = {((execute_SHIFT_CTRL == `ShiftCtrlEnum_defaultEncoding_SRA_1) && execute_LightShifterPlugin_shiftInput[31]),execute_LightShifterPlugin_shiftInput};
  assign _zz_285_ = ($signed(_zz_286_) + $signed(_zz_291_));
  assign _zz_286_ = ($signed(_zz_287_) + $signed(_zz_289_));
  assign _zz_287_ = (52'b0000000000000000000000000000000000000000000000000000);
  assign _zz_288_ = {1'b0,memory_MUL_LL};
  assign _zz_289_ = {{19{_zz_288_[32]}}, _zz_288_};
  assign _zz_290_ = ({16'd0,memory_MUL_LH} <<< 16);
  assign _zz_291_ = {{2{_zz_290_[49]}}, _zz_290_};
  assign _zz_292_ = ({16'd0,memory_MUL_HL} <<< 16);
  assign _zz_293_ = {{2{_zz_292_[49]}}, _zz_292_};
  assign _zz_294_ = {{14{writeBack_MUL_LOW[51]}}, writeBack_MUL_LOW};
  assign _zz_295_ = ({32'd0,writeBack_MUL_HH} <<< 32);
  assign _zz_296_ = writeBack_MUL_LOW[31 : 0];
  assign _zz_297_ = writeBack_MulPlugin_result[63 : 32];
  assign _zz_298_ = memory_DivPlugin_div_counter_willIncrement;
  assign _zz_299_ = {5'd0, _zz_298_};
  assign _zz_300_ = {1'd0, memory_DivPlugin_rs2};
  assign _zz_301_ = {_zz_185_,(! _zz_187_[32])};
  assign _zz_302_ = _zz_187_[31:0];
  assign _zz_303_ = _zz_186_[31:0];
  assign _zz_304_ = _zz_305_;
  assign _zz_305_ = _zz_306_;
  assign _zz_306_ = ({1'b0,(memory_DivPlugin_div_needRevert ? (~ _zz_188_) : _zz_188_)} + _zz_308_);
  assign _zz_307_ = memory_DivPlugin_div_needRevert;
  assign _zz_308_ = {32'd0, _zz_307_};
  assign _zz_309_ = _zz_190_;
  assign _zz_310_ = {32'd0, _zz_309_};
  assign _zz_311_ = _zz_189_;
  assign _zz_312_ = {31'd0, _zz_311_};
  assign _zz_313_ = {{{execute_INSTRUCTION[31],execute_INSTRUCTION[19 : 12]},execute_INSTRUCTION[20]},execute_INSTRUCTION[30 : 21]};
  assign _zz_314_ = execute_INSTRUCTION[31 : 20];
  assign _zz_315_ = {{{execute_INSTRUCTION[31],execute_INSTRUCTION[7]},execute_INSTRUCTION[30 : 25]},execute_INSTRUCTION[11 : 8]};
  assign _zz_316_ = execute_CsrPlugin_writeData[7 : 7];
  assign _zz_317_ = execute_CsrPlugin_writeData[3 : 3];
  assign _zz_318_ = execute_CsrPlugin_writeData[3 : 3];
  assign _zz_319_ = execute_CsrPlugin_writeData[11 : 11];
  assign _zz_320_ = execute_CsrPlugin_writeData[7 : 7];
  assign _zz_321_ = execute_CsrPlugin_writeData[3 : 3];
  assign _zz_322_ = execute_CsrPlugin_writeData[31 : 31];
  assign _zz_323_ = 1'b1;
  assign _zz_324_ = 1'b1;
  assign _zz_325_ = _zz_100_;
  assign _zz_326_ = (_zz_106_[11 : 10] == (2'b01));
  assign _zz_327_ = ((_zz_106_[11 : 10] == (2'b11)) && (_zz_106_[6 : 5] == (2'b00)));
  assign _zz_328_ = (7'b0000000);
  assign _zz_329_ = _zz_106_[6 : 2];
  assign _zz_330_ = _zz_106_[12];
  assign _zz_331_ = _zz_106_[11 : 7];
  assign _zz_332_ = (32'b00000000000000000000000001011000);
  assign _zz_333_ = (decode_INSTRUCTION & (32'b00100000000100000011000001010000));
  assign _zz_334_ = (32'b00000000000000000000000001010000);
  assign _zz_335_ = ((decode_INSTRUCTION & (32'b00010000000000000011000001010000)) == (32'b00010000000000000000000001010000));
  assign _zz_336_ = ((decode_INSTRUCTION & (32'b00110000000000000011000001010000)) == (32'b00010000000000000000000001010000));
  assign _zz_337_ = (1'b0);
  assign _zz_338_ = ({(_zz_341_ == _zz_342_),(_zz_343_ == _zz_344_)} != (2'b00));
  assign _zz_339_ = ({_zz_345_,{_zz_346_,_zz_347_}} != (3'b000));
  assign _zz_340_ = {(_zz_164_ != (1'b0)),{(_zz_348_ != _zz_349_),{_zz_350_,{_zz_351_,_zz_352_}}}};
  assign _zz_341_ = (decode_INSTRUCTION & (32'b00000000000000000010000000010000));
  assign _zz_342_ = (32'b00000000000000000010000000000000);
  assign _zz_343_ = (decode_INSTRUCTION & (32'b00000000000000000101000000000000));
  assign _zz_344_ = (32'b00000000000000000001000000000000);
  assign _zz_345_ = ((decode_INSTRUCTION & (32'b00000000000000000100000000000100)) == (32'b00000000000000000100000000000000));
  assign _zz_346_ = ((decode_INSTRUCTION & _zz_353_) == (32'b00000000000000000000000000100100));
  assign _zz_347_ = ((decode_INSTRUCTION & _zz_354_) == (32'b00000000000000000001000000000000));
  assign _zz_348_ = ((decode_INSTRUCTION & _zz_355_) == (32'b00000010000000000000000000110000));
  assign _zz_349_ = (1'b0);
  assign _zz_350_ = ({_zz_356_,{_zz_357_,_zz_358_}} != (4'b0000));
  assign _zz_351_ = (_zz_359_ != (1'b0));
  assign _zz_352_ = {(_zz_360_ != _zz_361_),{_zz_362_,{_zz_363_,_zz_364_}}};
  assign _zz_353_ = (32'b00000000000000000000000001100100);
  assign _zz_354_ = (32'b00000000000000000011000000000100);
  assign _zz_355_ = (32'b00000010000000000100000001110100);
  assign _zz_356_ = ((decode_INSTRUCTION & (32'b00000000000000000000000001000100)) == (32'b00000000000000000000000000000000));
  assign _zz_357_ = ((decode_INSTRUCTION & _zz_365_) == (32'b00000000000000000000000000000000));
  assign _zz_358_ = {_zz_164_,(_zz_366_ == _zz_367_)};
  assign _zz_359_ = ((decode_INSTRUCTION & (32'b00000010000000000100000001100100)) == (32'b00000010000000000100000000100000));
  assign _zz_360_ = {(_zz_368_ == _zz_369_),(_zz_370_ == _zz_371_)};
  assign _zz_361_ = (2'b00);
  assign _zz_362_ = ({_zz_372_,{_zz_373_,_zz_374_}} != (3'b000));
  assign _zz_363_ = (_zz_162_ != (1'b0));
  assign _zz_364_ = {(_zz_375_ != _zz_376_),{_zz_377_,{_zz_378_,_zz_379_}}};
  assign _zz_365_ = (32'b00000000000000000000000000011000);
  assign _zz_366_ = (decode_INSTRUCTION & (32'b00000000000000000101000000000100));
  assign _zz_367_ = (32'b00000000000000000001000000000000);
  assign _zz_368_ = (decode_INSTRUCTION & (32'b00000000000000000111000000110100));
  assign _zz_369_ = (32'b00000000000000000101000000010000);
  assign _zz_370_ = (decode_INSTRUCTION & (32'b00000010000000000111000001100100));
  assign _zz_371_ = (32'b00000000000000000101000000100000);
  assign _zz_372_ = ((decode_INSTRUCTION & (32'b01000000000000000011000001010100)) == (32'b01000000000000000001000000010000));
  assign _zz_373_ = ((decode_INSTRUCTION & _zz_380_) == (32'b00000000000000000001000000010000));
  assign _zz_374_ = ((decode_INSTRUCTION & _zz_381_) == (32'b00000000000000000001000000010000));
  assign _zz_375_ = {_zz_158_,{_zz_163_,_zz_382_}};
  assign _zz_376_ = (3'b000);
  assign _zz_377_ = ({_zz_158_,{_zz_383_,_zz_384_}} != (3'b000));
  assign _zz_378_ = ({_zz_385_,_zz_386_} != (2'b00));
  assign _zz_379_ = {(_zz_387_ != _zz_388_),{_zz_389_,{_zz_390_,_zz_391_}}};
  assign _zz_380_ = (32'b00000000000000000111000000110100);
  assign _zz_381_ = (32'b00000010000000000111000001010100);
  assign _zz_382_ = ((decode_INSTRUCTION & (32'b00000000000000000000000001110000)) == (32'b00000000000000000000000000100000));
  assign _zz_383_ = _zz_160_;
  assign _zz_384_ = _zz_163_;
  assign _zz_385_ = ((decode_INSTRUCTION & _zz_392_) == (32'b00000000000000000000000000100000));
  assign _zz_386_ = ((decode_INSTRUCTION & _zz_393_) == (32'b00000000000000000000000000100000));
  assign _zz_387_ = _zz_162_;
  assign _zz_388_ = (1'b0);
  assign _zz_389_ = ({_zz_394_,_zz_395_} != (2'b00));
  assign _zz_390_ = (_zz_161_ != (1'b0));
  assign _zz_391_ = {(_zz_396_ != _zz_397_),{_zz_398_,{_zz_399_,_zz_400_}}};
  assign _zz_392_ = (32'b00000000000000000000000000110100);
  assign _zz_393_ = (32'b00000000000000000000000001100100);
  assign _zz_394_ = ((decode_INSTRUCTION & (32'b00000000000000000001000001010000)) == (32'b00000000000000000001000001010000));
  assign _zz_395_ = ((decode_INSTRUCTION & (32'b00000000000000000010000001010000)) == (32'b00000000000000000010000001010000));
  assign _zz_396_ = ((decode_INSTRUCTION & (32'b00000000000000000000000001000100)) == (32'b00000000000000000000000000000100));
  assign _zz_397_ = (1'b0);
  assign _zz_398_ = ({_zz_158_,{_zz_160_,{_zz_401_,_zz_402_}}} != (5'b00000));
  assign _zz_399_ = ((_zz_403_ == _zz_404_) != (1'b0));
  assign _zz_400_ = {(_zz_405_ != (1'b0)),{(_zz_406_ != _zz_407_),{_zz_408_,{_zz_409_,_zz_410_}}}};
  assign _zz_401_ = ((decode_INSTRUCTION & _zz_411_) == (32'b00000000000000000001000000010000));
  assign _zz_402_ = {(_zz_412_ == _zz_413_),(_zz_414_ == _zz_415_)};
  assign _zz_403_ = (decode_INSTRUCTION & (32'b00010000000100000011000001010000));
  assign _zz_404_ = (32'b00000000000100000000000001010000);
  assign _zz_405_ = ((decode_INSTRUCTION & (32'b00000000000000000000000001010000)) == (32'b00000000000000000000000000000000));
  assign _zz_406_ = {_zz_159_,{_zz_158_,{_zz_416_,_zz_417_}}};
  assign _zz_407_ = (4'b0000);
  assign _zz_408_ = ({_zz_418_,_zz_158_} != (2'b00));
  assign _zz_409_ = ({_zz_419_,_zz_420_} != (3'b000));
  assign _zz_410_ = {(_zz_421_ != _zz_422_),(_zz_423_ != _zz_424_)};
  assign _zz_411_ = (32'b00000000000000000001000000010000);
  assign _zz_412_ = (decode_INSTRUCTION & (32'b00000000000000000010000000010000));
  assign _zz_413_ = (32'b00000000000000000010000000010000);
  assign _zz_414_ = (decode_INSTRUCTION & (32'b00000000000000000000000001010000));
  assign _zz_415_ = (32'b00000000000000000000000000010000);
  assign _zz_416_ = _zz_157_;
  assign _zz_417_ = _zz_156_;
  assign _zz_418_ = ((decode_INSTRUCTION & (32'b00000000000000000001000000000000)) == (32'b00000000000000000001000000000000));
  assign _zz_419_ = _zz_158_;
  assign _zz_420_ = {((decode_INSTRUCTION & _zz_425_) == (32'b00000000000000000001000000000000)),((decode_INSTRUCTION & _zz_426_) == (32'b00000000000000000010000000000000))};
  assign _zz_421_ = {_zz_159_,{_zz_158_,{_zz_427_,{_zz_428_,_zz_429_}}}};
  assign _zz_422_ = (5'b00000);
  assign _zz_423_ = {((decode_INSTRUCTION & _zz_430_) == (32'b01000000000000000000000000110000)),{(_zz_431_ == _zz_432_),(_zz_433_ == _zz_434_)}};
  assign _zz_424_ = (3'b000);
  assign _zz_425_ = (32'b00000000000000000011000000000000);
  assign _zz_426_ = (32'b00000000000000000011000000000000);
  assign _zz_427_ = ((decode_INSTRUCTION & (32'b00000000000000000100000000100000)) == (32'b00000000000000000100000000100000));
  assign _zz_428_ = _zz_157_;
  assign _zz_429_ = _zz_156_;
  assign _zz_430_ = (32'b01000000000000000000000000110000);
  assign _zz_431_ = (decode_INSTRUCTION & (32'b00000000000000000010000000010100));
  assign _zz_432_ = (32'b00000000000000000010000000010000);
  assign _zz_433_ = (decode_INSTRUCTION & (32'b00000000000000000000000001010100));
  assign _zz_434_ = (32'b00000000000000000000000001000000);
  always @ (posedge io_mainClk) begin
    if(_zz_46_) begin
      RegFilePlugin_regFile[writeBack_RegFilePlugin_regFileWrite_payload_address] <= writeBack_RegFilePlugin_regFileWrite_payload_data;
    end
  end

  always @ (posedge io_mainClk) begin
    if(_zz_323_) begin
      _zz_207_ <= RegFilePlugin_regFile[decode_RegFilePlugin_regFileReadAddress1];
    end
  end

  always @ (posedge io_mainClk) begin
    if(_zz_324_) begin
      _zz_208_ <= RegFilePlugin_regFile[decode_RegFilePlugin_regFileReadAddress2];
    end
  end

  StreamFifoLowLatency IBusSimplePlugin_rsp_rspBuffer ( 
    .io_push_valid(_zz_205_),
    .io_push_ready(_zz_212_),
    .io_push_payload_error(iBus_rsp_payload_error),
    .io_push_payload_inst(iBus_rsp_payload_inst),
    .io_pop_valid(_zz_213_),
    .io_pop_ready(_zz_144_),
    .io_pop_payload_error(_zz_214_),
    .io_pop_payload_inst(_zz_215_),
    .io_flush(_zz_206_),
    .io_occupancy(_zz_216_),
    .io_mainClk(io_mainClk),
    .resetCtrl_systemReset(resetCtrl_systemReset) 
  );
  always @(*) begin
    case(_zz_325_)
      1'b0 : begin
        _zz_209_ = _zz_88_;
      end
      default : begin
        _zz_209_ = _zz_96_;
      end
    endcase
  end

  always @(*) begin
    case(_zz_154_)
      1'b0 : begin
        _zz_210_ = _zz_90_;
        _zz_211_ = (32'bxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx);
      end
      default : begin
        _zz_210_ = (4'b0010);
        _zz_211_ = (32'bxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx);
      end
    endcase
  end

  assign memory_MEMORY_READ_DATA = _zz_76_;
  assign decode_RS1 = _zz_48_;
  assign memory_MUL_HH = execute_to_memory_MUL_HH;
  assign execute_MUL_HH = _zz_26_;
  assign decode_BYPASSABLE_EXECUTE_STAGE = _zz_66_;
  assign execute_BRANCH_CALC = _zz_21_;
  assign decode_SRC1 = _zz_40_;
  assign memory_ENV_CTRL = _zz_1_;
  assign _zz_2_ = _zz_3_;
  assign _zz_4_ = _zz_5_;
  assign decode_ENV_CTRL = _zz_6_;
  assign _zz_7_ = _zz_8_;
  assign decode_CSR_WRITE_OPCODE = _zz_72_;
  assign decode_ALU_CTRL = _zz_9_;
  assign _zz_10_ = _zz_11_;
  assign decode_CSR_READ_OPCODE = _zz_71_;
  assign decode_IS_RS2_SIGNED = _zz_57_;
  assign decode_ALU_BITWISE_CTRL = _zz_12_;
  assign _zz_13_ = _zz_14_;
  assign memory_MEMORY_ADDRESS_LOW = execute_to_memory_MEMORY_ADDRESS_LOW;
  assign execute_MEMORY_ADDRESS_LOW = _zz_77_;
  assign decode_RS2 = _zz_47_;
  assign writeBack_FORMAL_PC_NEXT = memory_to_writeBack_FORMAL_PC_NEXT;
  assign memory_FORMAL_PC_NEXT = execute_to_memory_FORMAL_PC_NEXT;
  assign execute_FORMAL_PC_NEXT = decode_to_execute_FORMAL_PC_NEXT;
  assign decode_FORMAL_PC_NEXT = _zz_79_;
  assign decode_IS_RS1_SIGNED = _zz_60_;
  assign decode_IS_DIV = _zz_55_;
  assign decode_IS_EBREAK = _zz_64_;
  assign execute_MUL_LH = _zz_28_;
  assign execute_MUL_LL = _zz_29_;
  assign execute_BYPASSABLE_MEMORY_STAGE = decode_to_execute_BYPASSABLE_MEMORY_STAGE;
  assign decode_BYPASSABLE_MEMORY_STAGE = _zz_68_;
  assign memory_IS_MUL = execute_to_memory_IS_MUL;
  assign execute_IS_MUL = decode_to_execute_IS_MUL;
  assign decode_IS_MUL = _zz_53_;
  assign execute_BRANCH_DO = _zz_23_;
  assign memory_PC = execute_to_memory_PC;
  assign writeBack_REGFILE_WRITE_DATA = memory_to_writeBack_REGFILE_WRITE_DATA;
  assign execute_REGFILE_WRITE_DATA = _zz_42_;
  assign memory_MUL_LOW = _zz_25_;
  assign decode_MEMORY_ENABLE = _zz_65_;
  assign decode_SRC_LESS_UNSIGNED = _zz_51_;
  assign decode_SHIFT_CTRL = _zz_15_;
  assign _zz_16_ = _zz_17_;
  assign decode_SRC_USE_SUB_LESS = _zz_69_;
  assign decode_SRC2 = _zz_37_;
  assign execute_MUL_HL = _zz_27_;
  assign decode_BRANCH_CTRL = _zz_18_;
  assign _zz_19_ = _zz_20_;
  assign execute_IS_EBREAK = decode_to_execute_IS_EBREAK;
  assign memory_BRANCH_CALC = execute_to_memory_BRANCH_CALC;
  assign memory_BRANCH_DO = execute_to_memory_BRANCH_DO;
  assign execute_PC = decode_to_execute_PC;
  assign execute_BRANCH_CTRL = _zz_22_;
  assign execute_IS_RS1_SIGNED = decode_to_execute_IS_RS1_SIGNED;
  assign execute_RS1 = decode_to_execute_RS1;
  assign execute_IS_DIV = decode_to_execute_IS_DIV;
  assign execute_IS_RS2_SIGNED = decode_to_execute_IS_RS2_SIGNED;
  always @ (*) begin
    _zz_24_ = memory_REGFILE_WRITE_DATA;
    memory_arbitration_haltItself = 1'b0;
    if((((memory_arbitration_isValid && memory_MEMORY_ENABLE) && (! memory_INSTRUCTION[5])) && (! dBus_rsp_ready)))begin
      memory_arbitration_haltItself = 1'b1;
    end
    memory_DivPlugin_div_counter_willIncrement = 1'b0;
    if(_zz_217_)begin
      if(_zz_218_)begin
        memory_arbitration_haltItself = 1'b1;
        memory_DivPlugin_div_counter_willIncrement = 1'b1;
      end
      _zz_24_ = memory_DivPlugin_div_result;
    end
  end

  assign memory_IS_DIV = execute_to_memory_IS_DIV;
  assign writeBack_IS_MUL = memory_to_writeBack_IS_MUL;
  assign writeBack_MUL_HH = memory_to_writeBack_MUL_HH;
  assign writeBack_MUL_LOW = memory_to_writeBack_MUL_LOW;
  assign memory_MUL_HL = execute_to_memory_MUL_HL;
  assign memory_MUL_LH = execute_to_memory_MUL_LH;
  assign memory_MUL_LL = execute_to_memory_MUL_LL;
  assign decode_RS2_USE = _zz_59_;
  assign decode_RS1_USE = _zz_54_;
  assign execute_REGFILE_WRITE_VALID = decode_to_execute_REGFILE_WRITE_VALID;
  assign execute_BYPASSABLE_EXECUTE_STAGE = decode_to_execute_BYPASSABLE_EXECUTE_STAGE;
  assign memory_REGFILE_WRITE_VALID = execute_to_memory_REGFILE_WRITE_VALID;
  assign memory_BYPASSABLE_MEMORY_STAGE = execute_to_memory_BYPASSABLE_MEMORY_STAGE;
  assign writeBack_REGFILE_WRITE_VALID = memory_to_writeBack_REGFILE_WRITE_VALID;
  assign execute_SHIFT_CTRL = _zz_30_;
  assign execute_SRC_LESS_UNSIGNED = decode_to_execute_SRC_LESS_UNSIGNED;
  assign execute_SRC_USE_SUB_LESS = decode_to_execute_SRC_USE_SUB_LESS;
  assign _zz_34_ = decode_PC;
  assign _zz_35_ = decode_RS2;
  assign decode_SRC2_CTRL = _zz_36_;
  assign _zz_38_ = decode_RS1;
  assign decode_SRC1_CTRL = _zz_39_;
  assign execute_SRC_ADD_SUB = _zz_33_;
  assign execute_SRC_LESS = _zz_31_;
  assign execute_ALU_CTRL = _zz_41_;
  assign execute_SRC2 = decode_to_execute_SRC2;
  assign execute_ALU_BITWISE_CTRL = _zz_43_;
  assign _zz_44_ = writeBack_INSTRUCTION;
  assign _zz_45_ = writeBack_REGFILE_WRITE_VALID;
  always @ (*) begin
    _zz_46_ = 1'b0;
    if(writeBack_RegFilePlugin_regFileWrite_valid)begin
      _zz_46_ = 1'b1;
    end
  end

  assign decode_INSTRUCTION_ANTICIPATED = _zz_83_;
  always @ (*) begin
    decode_REGFILE_WRITE_VALID = _zz_63_;
    if((decode_INSTRUCTION[11 : 7] == (5'b00000)))begin
      decode_REGFILE_WRITE_VALID = 1'b0;
    end
  end

  always @ (*) begin
    _zz_70_ = execute_REGFILE_WRITE_DATA;
    decode_arbitration_flushAll = 1'b0;
    execute_arbitration_haltItself = 1'b0;
    memory_arbitration_flushAll = 1'b0;
    _zz_84_ = 1'b0;
    _zz_85_ = 1'b0;
    _zz_87_ = 1'b0;
    _zz_88_ = (32'bxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx);
    if((((execute_arbitration_isValid && execute_MEMORY_ENABLE) && (! dBus_cmd_ready)) && (! execute_ALIGNEMENT_FAULT)))begin
      execute_arbitration_haltItself = 1'b1;
    end
    if(_zz_219_)begin
      _zz_87_ = 1'b1;
      _zz_88_ = CsrPlugin_mtvec;
      memory_arbitration_flushAll = 1'b1;
    end
    if(_zz_220_)begin
      if(_zz_221_)begin
        execute_arbitration_haltItself = 1'b1;
      end else begin
        _zz_87_ = 1'b1;
        _zz_88_ = CsrPlugin_mepc;
        decode_arbitration_flushAll = 1'b1;
      end
    end
    if((execute_arbitration_isValid && (execute_ENV_CTRL == `EnvCtrlEnum_defaultEncoding_WFI)))begin
      if((! CsrPlugin_interrupt))begin
        execute_arbitration_haltItself = 1'b1;
      end
    end
    if((execute_CsrPlugin_writeInstruction && (! execute_CsrPlugin_readDataRegValid)))begin
      execute_arbitration_haltItself = 1'b1;
    end
    if((execute_arbitration_isValid && execute_IS_CSR))begin
      _zz_70_ = execute_CsrPlugin_readData;
    end
    if(_zz_222_)begin
      _zz_70_ = _zz_180_;
      if(_zz_223_)begin
        if(! execute_LightShifterPlugin_done) begin
          execute_arbitration_haltItself = 1'b1;
        end
      end
    end
    if(execute_IS_EBREAK)begin
      if(execute_arbitration_isValid)begin
        _zz_85_ = 1'b1;
        _zz_84_ = 1'b1;
        decode_arbitration_flushAll = 1'b1;
      end
    end
    if(DebugPlugin_haltIt)begin
      _zz_84_ = 1'b1;
    end
    if(_zz_224_)begin
      _zz_84_ = 1'b1;
    end
  end

  assign execute_CSR_READ_OPCODE = decode_to_execute_CSR_READ_OPCODE;
  assign execute_CSR_WRITE_OPCODE = decode_to_execute_CSR_WRITE_OPCODE;
  assign memory_REGFILE_WRITE_DATA = execute_to_memory_REGFILE_WRITE_DATA;
  assign execute_SRC1 = decode_to_execute_SRC1;
  assign execute_IS_CSR = decode_to_execute_IS_CSR;
  assign decode_IS_CSR = _zz_61_;
  assign execute_ENV_CTRL = _zz_73_;
  assign writeBack_ENV_CTRL = _zz_74_;
  always @ (*) begin
    _zz_75_ = writeBack_REGFILE_WRITE_DATA;
    if((writeBack_arbitration_isValid && writeBack_MEMORY_ENABLE))begin
      _zz_75_ = writeBack_DBusSimplePlugin_rspFormated;
    end
    if((writeBack_arbitration_isValid && writeBack_IS_MUL))begin
      case(_zz_234_)
        2'b00 : begin
          _zz_75_ = _zz_296_;
        end
        default : begin
          _zz_75_ = _zz_297_;
        end
      endcase
    end
  end

  assign writeBack_MEMORY_ENABLE = memory_to_writeBack_MEMORY_ENABLE;
  assign writeBack_MEMORY_ADDRESS_LOW = memory_to_writeBack_MEMORY_ADDRESS_LOW;
  assign writeBack_MEMORY_READ_DATA = memory_to_writeBack_MEMORY_READ_DATA;
  assign memory_INSTRUCTION = execute_to_memory_INSTRUCTION;
  assign memory_MEMORY_ENABLE = execute_to_memory_MEMORY_ENABLE;
  assign execute_RS2 = decode_to_execute_RS2;
  assign execute_SRC_ADD = _zz_32_;
  assign execute_INSTRUCTION = decode_to_execute_INSTRUCTION;
  assign execute_ALIGNEMENT_FAULT = 1'b0;
  assign execute_MEMORY_ENABLE = decode_to_execute_MEMORY_ENABLE;
  always @ (*) begin
    _zz_78_ = memory_FORMAL_PC_NEXT;
    if(_zz_95_)begin
      _zz_78_ = _zz_96_;
    end
  end

  assign decode_IS_RVC = _zz_80_;
  assign writeBack_PC = memory_to_writeBack_PC;
  assign writeBack_INSTRUCTION = memory_to_writeBack_INSTRUCTION;
  assign decode_PC = _zz_82_;
  assign decode_INSTRUCTION = _zz_81_;
  always @ (*) begin
    decode_arbitration_haltItself = 1'b0;
    decode_arbitration_isValid = (IBusSimplePlugin_injector_decodeInput_valid && (! IBusSimplePlugin_injector_decodeRemoved));
    if(((decode_arbitration_isValid && decode_IS_CSR) && (execute_arbitration_isValid || memory_arbitration_isValid)))begin
      decode_arbitration_haltItself = 1'b1;
    end
    if((decode_arbitration_isValid && (_zz_181_ || _zz_182_)))begin
      decode_arbitration_haltItself = 1'b1;
    end
    _zz_98_ = 1'b0;
    case(_zz_204_)
      3'b000 : begin
      end
      3'b001 : begin
      end
      3'b010 : begin
        decode_arbitration_isValid = 1'b1;
        decode_arbitration_haltItself = 1'b1;
      end
      3'b011 : begin
        decode_arbitration_isValid = 1'b1;
      end
      3'b100 : begin
        _zz_98_ = 1'b1;
      end
      default : begin
      end
    endcase
  end

  always @ (*) begin
    decode_arbitration_haltByOther = 1'b0;
    if(CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_execute)begin
      decode_arbitration_haltByOther = 1'b1;
    end
    if((CsrPlugin_interrupt && decode_arbitration_isValid))begin
      decode_arbitration_haltByOther = 1'b1;
    end
  end

  always @ (*) begin
    decode_arbitration_removeIt = 1'b0;
    if(_zz_203_)begin
      decode_arbitration_removeIt = 1'b1;
    end
    if(decode_arbitration_isFlushed)begin
      decode_arbitration_removeIt = 1'b1;
    end
  end

  assign decode_arbitration_redoIt = 1'b0;
  always @ (*) begin
    execute_arbitration_haltByOther = 1'b0;
    if(CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_memory)begin
      execute_arbitration_haltByOther = 1'b1;
    end
  end

  always @ (*) begin
    execute_arbitration_removeIt = 1'b0;
    CsrPlugin_exceptionPortCtrl_exceptionValids_execute = CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_execute;
    if(execute_exception_agregat_valid)begin
      execute_arbitration_removeIt = 1'b1;
      CsrPlugin_exceptionPortCtrl_exceptionValids_execute = 1'b1;
    end
    if(execute_arbitration_isFlushed)begin
      CsrPlugin_exceptionPortCtrl_exceptionValids_execute = 1'b0;
    end
    if(execute_arbitration_isFlushed)begin
      execute_arbitration_removeIt = 1'b1;
    end
  end

  always @ (*) begin
    execute_arbitration_flushAll = 1'b0;
    if(_zz_95_)begin
      execute_arbitration_flushAll = 1'b1;
    end
  end

  assign execute_arbitration_redoIt = 1'b0;
  always @ (*) begin
    memory_arbitration_haltByOther = 1'b0;
    if(CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_writeBack)begin
      memory_arbitration_haltByOther = 1'b1;
    end
  end

  always @ (*) begin
    memory_arbitration_removeIt = 1'b0;
    if(memory_arbitration_isFlushed)begin
      memory_arbitration_removeIt = 1'b1;
    end
  end

  assign memory_arbitration_redoIt = 1'b0;
  assign writeBack_arbitration_haltItself = 1'b0;
  assign writeBack_arbitration_haltByOther = 1'b0;
  always @ (*) begin
    writeBack_arbitration_removeIt = 1'b0;
    if(writeBack_arbitration_isFlushed)begin
      writeBack_arbitration_removeIt = 1'b1;
    end
  end

  assign writeBack_arbitration_flushAll = 1'b0;
  assign writeBack_arbitration_redoIt = 1'b0;
  always @ (*) begin
    _zz_86_ = 1'b0;
    if(IBusSimplePlugin_iBusRsp_inputPipeline_0_valid)begin
      _zz_86_ = 1'b1;
    end
    if((IBusSimplePlugin_decompressor_bufferValid && (IBusSimplePlugin_decompressor_bufferData[1 : 0] != (2'b11))))begin
      _zz_86_ = 1'b1;
    end
    if(IBusSimplePlugin_injector_decodeInput_valid)begin
      _zz_86_ = 1'b1;
    end
  end

  always @ (*) begin
    _zz_89_ = 1'b0;
    _zz_90_ = (4'bxxxx);
    if((execute_arbitration_isValid && (execute_ENV_CTRL == `EnvCtrlEnum_defaultEncoding_ECALL)))begin
      _zz_89_ = 1'b1;
      _zz_90_ = (4'b1011);
    end
  end

  always @ (*) begin
    _zz_93_ = 1'b1;
    if((DebugPlugin_haltIt || DebugPlugin_stepIt))begin
      _zz_93_ = 1'b0;
    end
  end

  always @ (*) begin
    _zz_94_ = 1'b1;
    if(DebugPlugin_haltIt)begin
      _zz_94_ = 1'b0;
    end
  end

  assign IBusSimplePlugin_jump_pcLoad_valid = (_zz_87_ || _zz_95_);
  assign _zz_99_ = {_zz_95_,_zz_87_};
  assign _zz_100_ = _zz_235_[1];
  assign IBusSimplePlugin_jump_pcLoad_payload = _zz_209_;
  assign _zz_101_ = (! _zz_84_);
  assign IBusSimplePlugin_fetchPc_output_valid = (IBusSimplePlugin_fetchPc_preOutput_valid && _zz_101_);
  assign IBusSimplePlugin_fetchPc_preOutput_ready = (IBusSimplePlugin_fetchPc_output_ready && _zz_101_);
  assign IBusSimplePlugin_fetchPc_output_payload = IBusSimplePlugin_fetchPc_preOutput_payload;
  assign IBusSimplePlugin_fetchPc_pcPlus4 = (IBusSimplePlugin_fetchPc_pcReg + (32'b00000000000000000000000000000100));
  assign IBusSimplePlugin_fetchPc_preOutput_valid = _zz_102_;
  assign IBusSimplePlugin_fetchPc_preOutput_payload = IBusSimplePlugin_fetchPc_pcReg;
  assign IBusSimplePlugin_decodePc_pcPlus = (IBusSimplePlugin_decodePc_pcReg + _zz_238_);
  always @ (*) begin
    IBusSimplePlugin_decodePc_injectedDecode = 1'b0;
    if((_zz_204_ != (3'b000)))begin
      IBusSimplePlugin_decodePc_injectedDecode = 1'b1;
    end
  end

  assign IBusSimplePlugin_iBusRsp_input_ready = ((1'b0 && (! _zz_103_)) || IBusSimplePlugin_iBusRsp_inputPipeline_0_ready);
  assign _zz_103_ = _zz_104_;
  assign IBusSimplePlugin_iBusRsp_inputPipeline_0_valid = _zz_103_;
  assign IBusSimplePlugin_iBusRsp_inputPipeline_0_payload = _zz_105_;
  always @ (*) begin
    IBusSimplePlugin_iBusRsp_readyForError = 1'b1;
    if((IBusSimplePlugin_decompressor_bufferValid && IBusSimplePlugin_decompressor_isRvc))begin
      IBusSimplePlugin_iBusRsp_readyForError = 1'b0;
    end
    if(IBusSimplePlugin_injector_decodeInput_valid)begin
      IBusSimplePlugin_iBusRsp_readyForError = 1'b0;
    end
  end

  assign IBusSimplePlugin_decompressor_raw = (IBusSimplePlugin_decompressor_bufferValid ? {IBusSimplePlugin_iBusRsp_output_payload_rsp_inst[15 : 0],IBusSimplePlugin_decompressor_bufferData} : {IBusSimplePlugin_iBusRsp_output_payload_rsp_inst[31 : 16],(IBusSimplePlugin_iBusRsp_output_payload_pc[1] ? IBusSimplePlugin_iBusRsp_output_payload_rsp_inst[31 : 16] : IBusSimplePlugin_iBusRsp_output_payload_rsp_inst[15 : 0])});
  assign IBusSimplePlugin_decompressor_isRvc = (IBusSimplePlugin_decompressor_raw[1 : 0] != (2'b11));
  assign _zz_106_ = IBusSimplePlugin_decompressor_raw[15 : 0];
  always @ (*) begin
    IBusSimplePlugin_decompressor_decompressed = (32'bxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx);
    case(_zz_228_)
      5'b00000 : begin
        IBusSimplePlugin_decompressor_decompressed = {{{{{{{{{(2'b00),_zz_106_[10 : 7]},_zz_106_[12 : 11]},_zz_106_[5]},_zz_106_[6]},(2'b00)},(5'b00010)},(3'b000)},_zz_108_},(7'b0010011)};
      end
      5'b00010 : begin
        IBusSimplePlugin_decompressor_decompressed = {{{{_zz_109_,_zz_107_},(3'b010)},_zz_108_},(7'b0000011)};
      end
      5'b00110 : begin
        IBusSimplePlugin_decompressor_decompressed = {{{{{_zz_109_[11 : 5],_zz_108_},_zz_107_},(3'b010)},_zz_109_[4 : 0]},(7'b0100011)};
      end
      5'b01000 : begin
        IBusSimplePlugin_decompressor_decompressed = {{{{_zz_111_,_zz_106_[11 : 7]},(3'b000)},_zz_106_[11 : 7]},(7'b0010011)};
      end
      5'b01001 : begin
        IBusSimplePlugin_decompressor_decompressed = {{{{{_zz_114_[20],_zz_114_[10 : 1]},_zz_114_[11]},_zz_114_[19 : 12]},_zz_126_},(7'b1101111)};
      end
      5'b01010 : begin
        IBusSimplePlugin_decompressor_decompressed = {{{{_zz_111_,(5'b00000)},(3'b000)},_zz_106_[11 : 7]},(7'b0010011)};
      end
      5'b01011 : begin
        IBusSimplePlugin_decompressor_decompressed = ((_zz_106_[11 : 7] == (5'b00010)) ? {{{{{{{{{_zz_118_,_zz_106_[4 : 3]},_zz_106_[5]},_zz_106_[2]},_zz_106_[6]},(4'b0000)},_zz_106_[11 : 7]},(3'b000)},_zz_106_[11 : 7]},(7'b0010011)} : {{_zz_239_[31 : 12],_zz_106_[11 : 7]},(7'b0110111)});
      end
      5'b01100 : begin
        IBusSimplePlugin_decompressor_decompressed = {{{{{((_zz_106_[11 : 10] == (2'b10)) ? _zz_132_ : {{(1'b0),(_zz_326_ || _zz_327_)},(5'b00000)}),(((! _zz_106_[11]) || _zz_128_) ? _zz_106_[6 : 2] : _zz_108_)},_zz_107_},_zz_130_},_zz_107_},(_zz_128_ ? (7'b0010011) : (7'b0110011))};
      end
      5'b01101 : begin
        IBusSimplePlugin_decompressor_decompressed = {{{{{_zz_121_[20],_zz_121_[10 : 1]},_zz_121_[11]},_zz_121_[19 : 12]},_zz_125_},(7'b1101111)};
      end
      5'b01110 : begin
        IBusSimplePlugin_decompressor_decompressed = {{{{{{{_zz_124_[12],_zz_124_[10 : 5]},_zz_125_},_zz_107_},(3'b000)},_zz_124_[4 : 1]},_zz_124_[11]},(7'b1100011)};
      end
      5'b01111 : begin
        IBusSimplePlugin_decompressor_decompressed = {{{{{{{_zz_124_[12],_zz_124_[10 : 5]},_zz_125_},_zz_107_},(3'b001)},_zz_124_[4 : 1]},_zz_124_[11]},(7'b1100011)};
      end
      5'b10000 : begin
        IBusSimplePlugin_decompressor_decompressed = {{{{{(7'b0000000),_zz_106_[6 : 2]},_zz_106_[11 : 7]},(3'b001)},_zz_106_[11 : 7]},(7'b0010011)};
      end
      5'b10010 : begin
        IBusSimplePlugin_decompressor_decompressed = {{{{{{{{(4'b0000),_zz_106_[3 : 2]},_zz_106_[12]},_zz_106_[6 : 4]},(2'b00)},_zz_127_},(3'b010)},_zz_106_[11 : 7]},(7'b0000011)};
      end
      5'b10100 : begin
        IBusSimplePlugin_decompressor_decompressed = ((_zz_106_[12 : 2] == (11'b10000000000)) ? (32'b00000000000100000000000001110011) : ((_zz_106_[6 : 2] == (5'b00000)) ? {{{{(12'b000000000000),_zz_106_[11 : 7]},(3'b000)},(_zz_106_[12] ? _zz_126_ : _zz_125_)},(7'b1100111)} : {{{{{_zz_328_,_zz_329_},(_zz_330_ ? _zz_331_ : _zz_125_)},(3'b000)},_zz_106_[11 : 7]},(7'b0110011)}));
      end
      5'b10110 : begin
        IBusSimplePlugin_decompressor_decompressed = {{{{{_zz_240_[11 : 5],_zz_106_[6 : 2]},_zz_127_},(3'b010)},_zz_241_[4 : 0]},(7'b0100011)};
      end
      default : begin
      end
    endcase
  end

  assign _zz_107_ = {(2'b01),_zz_106_[9 : 7]};
  assign _zz_108_ = {(2'b01),_zz_106_[4 : 2]};
  assign _zz_109_ = {{{{(5'b00000),_zz_106_[5]},_zz_106_[12 : 10]},_zz_106_[6]},(2'b00)};
  assign _zz_110_ = _zz_106_[12];
  always @ (*) begin
    _zz_111_[11] = _zz_110_;
    _zz_111_[10] = _zz_110_;
    _zz_111_[9] = _zz_110_;
    _zz_111_[8] = _zz_110_;
    _zz_111_[7] = _zz_110_;
    _zz_111_[6] = _zz_110_;
    _zz_111_[5] = _zz_110_;
    _zz_111_[4 : 0] = _zz_106_[6 : 2];
  end

  assign _zz_112_ = _zz_106_[12];
  always @ (*) begin
    _zz_113_[9] = _zz_112_;
    _zz_113_[8] = _zz_112_;
    _zz_113_[7] = _zz_112_;
    _zz_113_[6] = _zz_112_;
    _zz_113_[5] = _zz_112_;
    _zz_113_[4] = _zz_112_;
    _zz_113_[3] = _zz_112_;
    _zz_113_[2] = _zz_112_;
    _zz_113_[1] = _zz_112_;
    _zz_113_[0] = _zz_112_;
  end

  assign _zz_114_ = {{{{{{{{_zz_113_,_zz_106_[8]},_zz_106_[10 : 9]},_zz_106_[6]},_zz_106_[7]},_zz_106_[2]},_zz_106_[11]},_zz_106_[5 : 3]},(1'b0)};
  assign _zz_115_ = _zz_106_[12];
  always @ (*) begin
    _zz_116_[14] = _zz_115_;
    _zz_116_[13] = _zz_115_;
    _zz_116_[12] = _zz_115_;
    _zz_116_[11] = _zz_115_;
    _zz_116_[10] = _zz_115_;
    _zz_116_[9] = _zz_115_;
    _zz_116_[8] = _zz_115_;
    _zz_116_[7] = _zz_115_;
    _zz_116_[6] = _zz_115_;
    _zz_116_[5] = _zz_115_;
    _zz_116_[4] = _zz_115_;
    _zz_116_[3] = _zz_115_;
    _zz_116_[2] = _zz_115_;
    _zz_116_[1] = _zz_115_;
    _zz_116_[0] = _zz_115_;
  end

  assign _zz_117_ = _zz_106_[12];
  always @ (*) begin
    _zz_118_[2] = _zz_117_;
    _zz_118_[1] = _zz_117_;
    _zz_118_[0] = _zz_117_;
  end

  assign _zz_119_ = _zz_106_[12];
  always @ (*) begin
    _zz_120_[9] = _zz_119_;
    _zz_120_[8] = _zz_119_;
    _zz_120_[7] = _zz_119_;
    _zz_120_[6] = _zz_119_;
    _zz_120_[5] = _zz_119_;
    _zz_120_[4] = _zz_119_;
    _zz_120_[3] = _zz_119_;
    _zz_120_[2] = _zz_119_;
    _zz_120_[1] = _zz_119_;
    _zz_120_[0] = _zz_119_;
  end

  assign _zz_121_ = {{{{{{{{_zz_120_,_zz_106_[8]},_zz_106_[10 : 9]},_zz_106_[6]},_zz_106_[7]},_zz_106_[2]},_zz_106_[11]},_zz_106_[5 : 3]},(1'b0)};
  assign _zz_122_ = _zz_106_[12];
  always @ (*) begin
    _zz_123_[4] = _zz_122_;
    _zz_123_[3] = _zz_122_;
    _zz_123_[2] = _zz_122_;
    _zz_123_[1] = _zz_122_;
    _zz_123_[0] = _zz_122_;
  end

  assign _zz_124_ = {{{{{_zz_123_,_zz_106_[6 : 5]},_zz_106_[2]},_zz_106_[11 : 10]},_zz_106_[4 : 3]},(1'b0)};
  assign _zz_125_ = (5'b00000);
  assign _zz_126_ = (5'b00001);
  assign _zz_127_ = (5'b00010);
  assign _zz_128_ = (_zz_106_[11 : 10] != (2'b11));
  always @ (*) begin
    case(_zz_229_)
      2'b00 : begin
        _zz_129_ = (3'b000);
      end
      2'b01 : begin
        _zz_129_ = (3'b100);
      end
      2'b10 : begin
        _zz_129_ = (3'b110);
      end
      default : begin
        _zz_129_ = (3'b111);
      end
    endcase
  end

  always @ (*) begin
    case(_zz_230_)
      2'b00 : begin
        _zz_130_ = (3'b101);
      end
      2'b01 : begin
        _zz_130_ = (3'b101);
      end
      2'b10 : begin
        _zz_130_ = (3'b111);
      end
      default : begin
        _zz_130_ = _zz_129_;
      end
    endcase
  end

  assign _zz_131_ = _zz_106_[12];
  always @ (*) begin
    _zz_132_[6] = _zz_131_;
    _zz_132_[5] = _zz_131_;
    _zz_132_[4] = _zz_131_;
    _zz_132_[3] = _zz_131_;
    _zz_132_[2] = _zz_131_;
    _zz_132_[1] = _zz_131_;
    _zz_132_[0] = _zz_131_;
  end

  assign IBusSimplePlugin_decompressor_inputBeforeStage_valid = (IBusSimplePlugin_decompressor_isRvc ? (IBusSimplePlugin_decompressor_bufferValid || IBusSimplePlugin_iBusRsp_output_valid) : (IBusSimplePlugin_iBusRsp_output_valid && (IBusSimplePlugin_decompressor_bufferValid || (! IBusSimplePlugin_iBusRsp_output_payload_pc[1]))));
  assign IBusSimplePlugin_decompressor_inputBeforeStage_payload_pc = IBusSimplePlugin_iBusRsp_output_payload_pc;
  assign IBusSimplePlugin_decompressor_inputBeforeStage_payload_isRvc = IBusSimplePlugin_decompressor_isRvc;
  assign IBusSimplePlugin_decompressor_inputBeforeStage_payload_rsp_inst = (IBusSimplePlugin_decompressor_isRvc ? IBusSimplePlugin_decompressor_decompressed : IBusSimplePlugin_decompressor_raw);
  assign IBusSimplePlugin_iBusRsp_output_ready = ((! IBusSimplePlugin_decompressor_inputBeforeStage_valid) || (! (((! IBusSimplePlugin_decompressor_inputBeforeStage_ready) || ((IBusSimplePlugin_decompressor_isRvc && (! IBusSimplePlugin_iBusRsp_output_payload_pc[1])) && (IBusSimplePlugin_iBusRsp_output_payload_rsp_inst[17 : 16] != (2'b11)))) || (((! IBusSimplePlugin_decompressor_isRvc) && IBusSimplePlugin_decompressor_bufferValid) && (IBusSimplePlugin_iBusRsp_output_payload_rsp_inst[17 : 16] != (2'b11))))));
  assign IBusSimplePlugin_decompressor_inputBeforeStage_ready = ((1'b0 && (! IBusSimplePlugin_injector_decodeInput_valid)) || IBusSimplePlugin_injector_decodeInput_ready);
  assign IBusSimplePlugin_injector_decodeInput_valid = _zz_133_;
  assign IBusSimplePlugin_injector_decodeInput_payload_pc = _zz_134_;
  assign IBusSimplePlugin_injector_decodeInput_payload_rsp_error = _zz_135_;
  assign IBusSimplePlugin_injector_decodeInput_payload_rsp_inst = _zz_136_;
  assign IBusSimplePlugin_injector_decodeInput_payload_isRvc = _zz_137_;
  assign _zz_83_ = (decode_arbitration_isStuck ? decode_INSTRUCTION : IBusSimplePlugin_decompressor_inputBeforeStage_payload_rsp_inst);
  assign IBusSimplePlugin_injector_decodeInput_ready = (! decode_arbitration_isStuck);
  assign _zz_82_ = IBusSimplePlugin_decodePc_pcReg;
  assign _zz_81_ = IBusSimplePlugin_injector_decodeInput_payload_rsp_inst;
  assign _zz_80_ = IBusSimplePlugin_injector_decodeInput_payload_isRvc;
  assign _zz_79_ = (decode_PC + _zz_243_);
  assign IBusSimplePlugin_pendingCmdNext = (_zz_244_ - _zz_248_);
  assign _zz_142_ = (iBus_cmd_valid && iBus_cmd_ready);
  assign IBusSimplePlugin_fetchPc_output_ready = (IBusSimplePlugin_iBusRsp_input_ready && _zz_142_);
  assign IBusSimplePlugin_iBusRsp_input_valid = (IBusSimplePlugin_fetchPc_output_valid && _zz_142_);
  assign IBusSimplePlugin_iBusRsp_input_payload = IBusSimplePlugin_fetchPc_output_payload;
  assign iBus_cmd_valid = ((IBusSimplePlugin_fetchPc_output_valid && IBusSimplePlugin_iBusRsp_input_ready) && (IBusSimplePlugin_pendingCmd != (3'b111)));
  assign iBus_cmd_payload_pc = {IBusSimplePlugin_fetchPc_output_payload[31 : 2],(2'b00)};
  assign _zz_205_ = (iBus_rsp_valid && (! (IBusSimplePlugin_rsp_discardCounter != (3'b000))));
  assign _zz_206_ = (IBusSimplePlugin_jump_pcLoad_valid || _zz_85_);
  assign IBusSimplePlugin_rsp_fetchRsp_pc = IBusSimplePlugin_iBusRsp_inputPipeline_0_payload;
  always @ (*) begin
    IBusSimplePlugin_rsp_fetchRsp_rsp_error = _zz_214_;
    if((! _zz_213_))begin
      IBusSimplePlugin_rsp_fetchRsp_rsp_error = 1'b0;
    end
  end

  assign IBusSimplePlugin_rsp_fetchRsp_rsp_inst = _zz_215_;
  assign IBusSimplePlugin_rsp_issueDetected = 1'b0;
  assign _zz_144_ = (_zz_143_ && IBusSimplePlugin_rsp_join_ready);
  assign _zz_143_ = (IBusSimplePlugin_iBusRsp_inputPipeline_0_valid && _zz_213_);
  always @ (*) begin
    IBusSimplePlugin_iBusRsp_inputPipeline_0_ready = _zz_144_;
    if((! IBusSimplePlugin_iBusRsp_inputPipeline_0_valid))begin
      IBusSimplePlugin_iBusRsp_inputPipeline_0_ready = 1'b1;
    end
  end

  assign IBusSimplePlugin_rsp_join_valid = _zz_143_;
  assign IBusSimplePlugin_rsp_join_payload_pc = IBusSimplePlugin_rsp_fetchRsp_pc;
  assign IBusSimplePlugin_rsp_join_payload_rsp_error = IBusSimplePlugin_rsp_fetchRsp_rsp_error;
  assign IBusSimplePlugin_rsp_join_payload_rsp_inst = IBusSimplePlugin_rsp_fetchRsp_rsp_inst;
  assign IBusSimplePlugin_rsp_join_payload_isRvc = IBusSimplePlugin_rsp_fetchRsp_isRvc;
  assign _zz_145_ = (! IBusSimplePlugin_rsp_issueDetected);
  assign IBusSimplePlugin_rsp_join_ready = (IBusSimplePlugin_iBusRsp_output_ready && _zz_145_);
  assign IBusSimplePlugin_iBusRsp_output_valid = (IBusSimplePlugin_rsp_join_valid && _zz_145_);
  assign IBusSimplePlugin_iBusRsp_output_payload_pc = IBusSimplePlugin_rsp_join_payload_pc;
  assign IBusSimplePlugin_iBusRsp_output_payload_rsp_error = IBusSimplePlugin_rsp_join_payload_rsp_error;
  assign IBusSimplePlugin_iBusRsp_output_payload_rsp_inst = IBusSimplePlugin_rsp_join_payload_rsp_inst;
  assign IBusSimplePlugin_iBusRsp_output_payload_isRvc = IBusSimplePlugin_rsp_join_payload_isRvc;
  assign dBus_cmd_valid = ((((execute_arbitration_isValid && execute_MEMORY_ENABLE) && (! execute_arbitration_isStuckByOthers)) && (! execute_arbitration_removeIt)) && (! execute_ALIGNEMENT_FAULT));
  assign dBus_cmd_payload_wr = execute_INSTRUCTION[5];
  assign dBus_cmd_payload_address = execute_SRC_ADD;
  assign dBus_cmd_payload_size = execute_INSTRUCTION[13 : 12];
  always @ (*) begin
    case(dBus_cmd_payload_size)
      2'b00 : begin
        _zz_146_ = {{{execute_RS2[7 : 0],execute_RS2[7 : 0]},execute_RS2[7 : 0]},execute_RS2[7 : 0]};
      end
      2'b01 : begin
        _zz_146_ = {execute_RS2[15 : 0],execute_RS2[15 : 0]};
      end
      default : begin
        _zz_146_ = execute_RS2[31 : 0];
      end
    endcase
  end

  assign dBus_cmd_payload_data = _zz_146_;
  assign _zz_77_ = dBus_cmd_payload_address[1 : 0];
  always @ (*) begin
    case(dBus_cmd_payload_size)
      2'b00 : begin
        _zz_147_ = (4'b0001);
      end
      2'b01 : begin
        _zz_147_ = (4'b0011);
      end
      default : begin
        _zz_147_ = (4'b1111);
      end
    endcase
  end

  assign execute_DBusSimplePlugin_formalMask = (_zz_147_ <<< dBus_cmd_payload_address[1 : 0]);
  assign _zz_76_ = dBus_rsp_data;
  always @ (*) begin
    writeBack_DBusSimplePlugin_rspShifted = writeBack_MEMORY_READ_DATA;
    case(writeBack_MEMORY_ADDRESS_LOW)
      2'b01 : begin
        writeBack_DBusSimplePlugin_rspShifted[7 : 0] = writeBack_MEMORY_READ_DATA[15 : 8];
      end
      2'b10 : begin
        writeBack_DBusSimplePlugin_rspShifted[15 : 0] = writeBack_MEMORY_READ_DATA[31 : 16];
      end
      2'b11 : begin
        writeBack_DBusSimplePlugin_rspShifted[7 : 0] = writeBack_MEMORY_READ_DATA[31 : 24];
      end
      default : begin
      end
    endcase
  end

  assign _zz_148_ = (writeBack_DBusSimplePlugin_rspShifted[7] && (! writeBack_INSTRUCTION[14]));
  always @ (*) begin
    _zz_149_[31] = _zz_148_;
    _zz_149_[30] = _zz_148_;
    _zz_149_[29] = _zz_148_;
    _zz_149_[28] = _zz_148_;
    _zz_149_[27] = _zz_148_;
    _zz_149_[26] = _zz_148_;
    _zz_149_[25] = _zz_148_;
    _zz_149_[24] = _zz_148_;
    _zz_149_[23] = _zz_148_;
    _zz_149_[22] = _zz_148_;
    _zz_149_[21] = _zz_148_;
    _zz_149_[20] = _zz_148_;
    _zz_149_[19] = _zz_148_;
    _zz_149_[18] = _zz_148_;
    _zz_149_[17] = _zz_148_;
    _zz_149_[16] = _zz_148_;
    _zz_149_[15] = _zz_148_;
    _zz_149_[14] = _zz_148_;
    _zz_149_[13] = _zz_148_;
    _zz_149_[12] = _zz_148_;
    _zz_149_[11] = _zz_148_;
    _zz_149_[10] = _zz_148_;
    _zz_149_[9] = _zz_148_;
    _zz_149_[8] = _zz_148_;
    _zz_149_[7 : 0] = writeBack_DBusSimplePlugin_rspShifted[7 : 0];
  end

  assign _zz_150_ = (writeBack_DBusSimplePlugin_rspShifted[15] && (! writeBack_INSTRUCTION[14]));
  always @ (*) begin
    _zz_151_[31] = _zz_150_;
    _zz_151_[30] = _zz_150_;
    _zz_151_[29] = _zz_150_;
    _zz_151_[28] = _zz_150_;
    _zz_151_[27] = _zz_150_;
    _zz_151_[26] = _zz_150_;
    _zz_151_[25] = _zz_150_;
    _zz_151_[24] = _zz_150_;
    _zz_151_[23] = _zz_150_;
    _zz_151_[22] = _zz_150_;
    _zz_151_[21] = _zz_150_;
    _zz_151_[20] = _zz_150_;
    _zz_151_[19] = _zz_150_;
    _zz_151_[18] = _zz_150_;
    _zz_151_[17] = _zz_150_;
    _zz_151_[16] = _zz_150_;
    _zz_151_[15 : 0] = writeBack_DBusSimplePlugin_rspShifted[15 : 0];
  end

  always @ (*) begin
    case(_zz_231_)
      2'b00 : begin
        writeBack_DBusSimplePlugin_rspFormated = _zz_149_;
      end
      2'b01 : begin
        writeBack_DBusSimplePlugin_rspFormated = _zz_151_;
      end
      default : begin
        writeBack_DBusSimplePlugin_rspFormated = writeBack_DBusSimplePlugin_rspShifted;
      end
    endcase
  end

  assign CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_decode = 1'b0;
  assign execute_exception_agregat_valid = (_zz_89_ || _zz_92_);
  assign _zz_152_ = {_zz_92_,_zz_89_};
  assign _zz_153_ = _zz_251_[1];
  assign _zz_154_ = _zz_153_;
  assign execute_exception_agregat_payload_code = _zz_210_;
  assign execute_exception_agregat_payload_badAddr = _zz_211_;
  assign CsrPlugin_exceptionPortCtrl_exceptionValids_decode = CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_decode;
  always @ (*) begin
    CsrPlugin_exceptionPortCtrl_exceptionValids_memory = CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_memory;
    if(memory_arbitration_isFlushed)begin
      CsrPlugin_exceptionPortCtrl_exceptionValids_memory = 1'b0;
    end
  end

  always @ (*) begin
    CsrPlugin_exceptionPortCtrl_exceptionValids_writeBack = CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_writeBack;
    if(writeBack_arbitration_isFlushed)begin
      CsrPlugin_exceptionPortCtrl_exceptionValids_writeBack = 1'b0;
    end
  end

  assign CsrPlugin_interruptRequest = ((((CsrPlugin_mip_MSIP && CsrPlugin_mie_MSIE) || (CsrPlugin_mip_MEIP && CsrPlugin_mie_MEIE)) || (CsrPlugin_mip_MTIP && CsrPlugin_mie_MTIE)) && CsrPlugin_mstatus_MIE);
  assign CsrPlugin_interrupt = (CsrPlugin_interruptRequest && _zz_93_);
  assign CsrPlugin_exception = (CsrPlugin_exceptionPortCtrl_exceptionValids_writeBack && _zz_94_);
  always @ (*) begin
    CsrPlugin_pipelineLiberator_done = ((! ((execute_arbitration_isValid || memory_arbitration_isValid) || writeBack_arbitration_isValid)) && _zz_141_);
    if(((CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_execute || CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_memory) || CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_writeBack))begin
      CsrPlugin_pipelineLiberator_done = 1'b0;
    end
  end

  assign CsrPlugin_interruptCode = ((CsrPlugin_mip_MEIP && CsrPlugin_mie_MEIE) ? (4'b1011) : _zz_254_);
  assign CsrPlugin_interruptJump = (CsrPlugin_interrupt && CsrPlugin_pipelineLiberator_done);
  assign contextSwitching = _zz_87_;
  assign _zz_72_ = (! (((decode_INSTRUCTION[14 : 13] == (2'b01)) && (decode_INSTRUCTION[19 : 15] == (5'b00000))) || ((decode_INSTRUCTION[14 : 13] == (2'b11)) && (decode_INSTRUCTION[19 : 15] == (5'b00000)))));
  assign _zz_71_ = (decode_INSTRUCTION[13 : 7] != (7'b0100000));
  always @ (*) begin
    execute_CsrPlugin_illegalAccess = (execute_arbitration_isValid && execute_IS_CSR);
    execute_CsrPlugin_readData = (32'b00000000000000000000000000000000);
    case(execute_CsrPlugin_csrAddress)
      12'b001100000000 : begin
        execute_CsrPlugin_illegalAccess = 1'b0;
        execute_CsrPlugin_readData[12 : 11] = CsrPlugin_mstatus_MPP;
        execute_CsrPlugin_readData[7 : 7] = CsrPlugin_mstatus_MPIE;
        execute_CsrPlugin_readData[3 : 3] = CsrPlugin_mstatus_MIE;
      end
      12'b111100010001 : begin
        if(execute_CSR_READ_OPCODE)begin
          execute_CsrPlugin_illegalAccess = 1'b0;
        end
        execute_CsrPlugin_readData[3 : 0] = (4'b1011);
      end
      12'b111100010100 : begin
        if(execute_CSR_READ_OPCODE)begin
          execute_CsrPlugin_illegalAccess = 1'b0;
        end
      end
      12'b001101000001 : begin
        execute_CsrPlugin_illegalAccess = 1'b0;
        execute_CsrPlugin_readData[31 : 0] = CsrPlugin_mepc;
      end
      12'b101100000000 : begin
        execute_CsrPlugin_illegalAccess = 1'b0;
        execute_CsrPlugin_readData[31 : 0] = CsrPlugin_mcycle[31 : 0];
      end
      12'b101110000000 : begin
        execute_CsrPlugin_illegalAccess = 1'b0;
        execute_CsrPlugin_readData[31 : 0] = CsrPlugin_mcycle[63 : 32];
      end
      12'b001101000100 : begin
        execute_CsrPlugin_illegalAccess = 1'b0;
        execute_CsrPlugin_readData[11 : 11] = CsrPlugin_mip_MEIP;
        execute_CsrPlugin_readData[7 : 7] = CsrPlugin_mip_MTIP;
        execute_CsrPlugin_readData[3 : 3] = CsrPlugin_mip_MSIP;
      end
      12'b001100000101 : begin
        execute_CsrPlugin_illegalAccess = 1'b0;
        execute_CsrPlugin_readData[31 : 0] = CsrPlugin_mtvec;
      end
      12'b101100000010 : begin
        execute_CsrPlugin_illegalAccess = 1'b0;
        execute_CsrPlugin_readData[31 : 0] = CsrPlugin_minstret[31 : 0];
      end
      12'b111100010011 : begin
        if(execute_CSR_READ_OPCODE)begin
          execute_CsrPlugin_illegalAccess = 1'b0;
        end
        execute_CsrPlugin_readData[5 : 0] = (6'b100001);
      end
      12'b001101000011 : begin
        execute_CsrPlugin_illegalAccess = 1'b0;
        execute_CsrPlugin_readData[31 : 0] = CsrPlugin_mbadaddr;
      end
      12'b110000000000 : begin
        if(execute_CSR_READ_OPCODE)begin
          execute_CsrPlugin_illegalAccess = 1'b0;
        end
        execute_CsrPlugin_readData[31 : 0] = CsrPlugin_mcycle[31 : 0];
      end
      12'b001100000001 : begin
        execute_CsrPlugin_illegalAccess = 1'b0;
        execute_CsrPlugin_readData[31 : 30] = CsrPlugin_misa_base;
        execute_CsrPlugin_readData[25 : 0] = CsrPlugin_misa_extensions;
      end
      12'b001101000000 : begin
        execute_CsrPlugin_illegalAccess = 1'b0;
        execute_CsrPlugin_readData[31 : 0] = CsrPlugin_mscratch;
      end
      12'b111100010010 : begin
        if(execute_CSR_READ_OPCODE)begin
          execute_CsrPlugin_illegalAccess = 1'b0;
        end
        execute_CsrPlugin_readData[4 : 0] = (5'b10110);
      end
      12'b001100000100 : begin
        execute_CsrPlugin_illegalAccess = 1'b0;
        execute_CsrPlugin_readData[11 : 11] = CsrPlugin_mie_MEIE;
        execute_CsrPlugin_readData[7 : 7] = CsrPlugin_mie_MTIE;
        execute_CsrPlugin_readData[3 : 3] = CsrPlugin_mie_MSIE;
      end
      12'b101110000010 : begin
        execute_CsrPlugin_illegalAccess = 1'b0;
        execute_CsrPlugin_readData[31 : 0] = CsrPlugin_minstret[63 : 32];
      end
      12'b001101000010 : begin
        execute_CsrPlugin_illegalAccess = 1'b0;
        execute_CsrPlugin_readData[31 : 31] = CsrPlugin_mcause_interrupt;
        execute_CsrPlugin_readData[3 : 0] = CsrPlugin_mcause_exceptionCode;
      end
      default : begin
      end
    endcase
    if((_zz_91_ < execute_CsrPlugin_csrAddress[9 : 8]))begin
      execute_CsrPlugin_illegalAccess = 1'b1;
    end
  end

  assign _zz_92_ = (execute_CsrPlugin_illegalAccess || ((execute_arbitration_isValid && (_zz_91_ == (2'b00))) && ((execute_ENV_CTRL == `EnvCtrlEnum_defaultEncoding_EBREAK) || (execute_ENV_CTRL == `EnvCtrlEnum_defaultEncoding_MRET))));
  assign execute_CsrPlugin_writeSrc = (execute_INSTRUCTION[14] ? _zz_256_ : execute_SRC1);
  always @ (*) begin
    case(_zz_232_)
      1'b0 : begin
        execute_CsrPlugin_writeData = execute_CsrPlugin_writeSrc;
      end
      default : begin
        execute_CsrPlugin_writeData = (execute_INSTRUCTION[12] ? (memory_REGFILE_WRITE_DATA & (~ execute_CsrPlugin_writeSrc)) : (memory_REGFILE_WRITE_DATA | execute_CsrPlugin_writeSrc));
      end
    endcase
  end

  assign execute_CsrPlugin_writeInstruction = ((execute_arbitration_isValid && execute_IS_CSR) && execute_CSR_WRITE_OPCODE);
  assign execute_CsrPlugin_readInstruction = ((execute_arbitration_isValid && execute_IS_CSR) && execute_CSR_READ_OPCODE);
  assign execute_CsrPlugin_writeEnable = (execute_CsrPlugin_writeInstruction && execute_CsrPlugin_readDataRegValid);
  assign execute_CsrPlugin_readEnable = (execute_CsrPlugin_readInstruction && (! execute_CsrPlugin_readDataRegValid));
  assign execute_CsrPlugin_csrAddress = execute_INSTRUCTION[31 : 20];
  assign _zz_156_ = ((decode_INSTRUCTION & (32'b00000010000000000000000000100000)) == (32'b00000000000000000000000000100000));
  assign _zz_157_ = ((decode_INSTRUCTION & (32'b00000000000000000000000000110000)) == (32'b00000000000000000000000000010000));
  assign _zz_158_ = ((decode_INSTRUCTION & (32'b00000000000000000000000000000100)) == (32'b00000000000000000000000000000100));
  assign _zz_159_ = ((decode_INSTRUCTION & (32'b00000000000000000000000001000000)) == (32'b00000000000000000000000001000000));
  assign _zz_160_ = ((decode_INSTRUCTION & (32'b00000000000000000000000000100000)) == (32'b00000000000000000000000000000000));
  assign _zz_161_ = ((decode_INSTRUCTION & (32'b00000000000000000000000000010100)) == (32'b00000000000000000000000000000100));
  assign _zz_162_ = ((decode_INSTRUCTION & (32'b00000000000000000001000000000000)) == (32'b00000000000000000000000000000000));
  assign _zz_163_ = ((decode_INSTRUCTION & (32'b00000000000000000000000001010000)) == (32'b00000000000000000000000001010000));
  assign _zz_164_ = ((decode_INSTRUCTION & (32'b00000000000000000110000000000100)) == (32'b00000000000000000010000000000000));
  assign _zz_155_ = {(_zz_161_ != (1'b0)),{(((decode_INSTRUCTION & _zz_332_) == (32'b00000000000000000000000001000000)) != (1'b0)),{((_zz_333_ == _zz_334_) != (1'b0)),{(_zz_335_ != (1'b0)),{(_zz_336_ != _zz_337_),{_zz_338_,{_zz_339_,_zz_340_}}}}}}};
  assign _zz_69_ = _zz_257_[0];
  assign _zz_68_ = _zz_258_[0];
  assign _zz_165_ = _zz_155_[3 : 2];
  assign _zz_67_ = _zz_165_;
  assign _zz_66_ = _zz_259_[0];
  assign _zz_65_ = _zz_260_[0];
  assign _zz_64_ = _zz_261_[0];
  assign _zz_63_ = _zz_262_[0];
  assign _zz_166_ = _zz_155_[9 : 8];
  assign _zz_62_ = _zz_166_;
  assign _zz_61_ = _zz_263_[0];
  assign _zz_60_ = _zz_264_[0];
  assign _zz_59_ = _zz_265_[0];
  assign _zz_167_ = _zz_155_[14 : 13];
  assign _zz_58_ = _zz_167_;
  assign _zz_57_ = _zz_266_[0];
  assign _zz_168_ = _zz_155_[17 : 16];
  assign _zz_56_ = _zz_168_;
  assign _zz_55_ = _zz_267_[0];
  assign _zz_54_ = _zz_268_[0];
  assign _zz_53_ = _zz_269_[0];
  assign _zz_169_ = _zz_155_[22 : 21];
  assign _zz_52_ = _zz_169_;
  assign _zz_51_ = _zz_270_[0];
  assign _zz_170_ = _zz_155_[26 : 24];
  assign _zz_50_ = _zz_170_;
  assign _zz_171_ = _zz_155_[28 : 27];
  assign _zz_49_ = _zz_171_;
  assign decode_RegFilePlugin_regFileReadAddress1 = decode_INSTRUCTION_ANTICIPATED[19 : 15];
  assign decode_RegFilePlugin_regFileReadAddress2 = decode_INSTRUCTION_ANTICIPATED[24 : 20];
  assign decode_RegFilePlugin_rs1Data = _zz_207_;
  assign decode_RegFilePlugin_rs2Data = _zz_208_;
  assign _zz_48_ = decode_RegFilePlugin_rs1Data;
  assign _zz_47_ = decode_RegFilePlugin_rs2Data;
  always @ (*) begin
    writeBack_RegFilePlugin_regFileWrite_valid = (_zz_45_ && writeBack_arbitration_isFiring);
    if(_zz_172_)begin
      writeBack_RegFilePlugin_regFileWrite_valid = 1'b1;
    end
  end

  assign writeBack_RegFilePlugin_regFileWrite_payload_address = _zz_44_[11 : 7];
  assign writeBack_RegFilePlugin_regFileWrite_payload_data = _zz_75_;
  always @ (*) begin
    case(execute_ALU_BITWISE_CTRL)
      `AluBitwiseCtrlEnum_defaultEncoding_AND_1 : begin
        execute_IntAluPlugin_bitwise = (execute_SRC1 & execute_SRC2);
      end
      `AluBitwiseCtrlEnum_defaultEncoding_OR_1 : begin
        execute_IntAluPlugin_bitwise = (execute_SRC1 | execute_SRC2);
      end
      `AluBitwiseCtrlEnum_defaultEncoding_XOR_1 : begin
        execute_IntAluPlugin_bitwise = (execute_SRC1 ^ execute_SRC2);
      end
      default : begin
        execute_IntAluPlugin_bitwise = execute_SRC1;
      end
    endcase
  end

  always @ (*) begin
    case(execute_ALU_CTRL)
      `AluCtrlEnum_defaultEncoding_BITWISE : begin
        _zz_173_ = execute_IntAluPlugin_bitwise;
      end
      `AluCtrlEnum_defaultEncoding_SLT_SLTU : begin
        _zz_173_ = {31'd0, _zz_271_};
      end
      default : begin
        _zz_173_ = execute_SRC_ADD_SUB;
      end
    endcase
  end

  assign _zz_42_ = _zz_173_;
  always @ (*) begin
    case(decode_SRC1_CTRL)
      `Src1CtrlEnum_defaultEncoding_RS : begin
        _zz_174_ = _zz_38_;
      end
      `Src1CtrlEnum_defaultEncoding_PC_INCREMENT : begin
        _zz_174_ = {29'd0, _zz_272_};
      end
      default : begin
        _zz_174_ = {decode_INSTRUCTION[31 : 12],(12'b000000000000)};
      end
    endcase
  end

  assign _zz_40_ = _zz_174_;
  assign _zz_175_ = _zz_273_[11];
  always @ (*) begin
    _zz_176_[19] = _zz_175_;
    _zz_176_[18] = _zz_175_;
    _zz_176_[17] = _zz_175_;
    _zz_176_[16] = _zz_175_;
    _zz_176_[15] = _zz_175_;
    _zz_176_[14] = _zz_175_;
    _zz_176_[13] = _zz_175_;
    _zz_176_[12] = _zz_175_;
    _zz_176_[11] = _zz_175_;
    _zz_176_[10] = _zz_175_;
    _zz_176_[9] = _zz_175_;
    _zz_176_[8] = _zz_175_;
    _zz_176_[7] = _zz_175_;
    _zz_176_[6] = _zz_175_;
    _zz_176_[5] = _zz_175_;
    _zz_176_[4] = _zz_175_;
    _zz_176_[3] = _zz_175_;
    _zz_176_[2] = _zz_175_;
    _zz_176_[1] = _zz_175_;
    _zz_176_[0] = _zz_175_;
  end

  assign _zz_177_ = _zz_274_[11];
  always @ (*) begin
    _zz_178_[19] = _zz_177_;
    _zz_178_[18] = _zz_177_;
    _zz_178_[17] = _zz_177_;
    _zz_178_[16] = _zz_177_;
    _zz_178_[15] = _zz_177_;
    _zz_178_[14] = _zz_177_;
    _zz_178_[13] = _zz_177_;
    _zz_178_[12] = _zz_177_;
    _zz_178_[11] = _zz_177_;
    _zz_178_[10] = _zz_177_;
    _zz_178_[9] = _zz_177_;
    _zz_178_[8] = _zz_177_;
    _zz_178_[7] = _zz_177_;
    _zz_178_[6] = _zz_177_;
    _zz_178_[5] = _zz_177_;
    _zz_178_[4] = _zz_177_;
    _zz_178_[3] = _zz_177_;
    _zz_178_[2] = _zz_177_;
    _zz_178_[1] = _zz_177_;
    _zz_178_[0] = _zz_177_;
  end

  always @ (*) begin
    case(decode_SRC2_CTRL)
      `Src2CtrlEnum_defaultEncoding_RS : begin
        _zz_179_ = _zz_35_;
      end
      `Src2CtrlEnum_defaultEncoding_IMI : begin
        _zz_179_ = {_zz_176_,decode_INSTRUCTION[31 : 20]};
      end
      `Src2CtrlEnum_defaultEncoding_IMS : begin
        _zz_179_ = {_zz_178_,{decode_INSTRUCTION[31 : 25],decode_INSTRUCTION[11 : 7]}};
      end
      default : begin
        _zz_179_ = _zz_34_;
      end
    endcase
  end

  assign _zz_37_ = _zz_179_;
  assign execute_SrcPlugin_addSub = _zz_275_;
  assign execute_SrcPlugin_less = ((execute_SRC1[31] == execute_SRC2[31]) ? execute_SrcPlugin_addSub[31] : (execute_SRC_LESS_UNSIGNED ? execute_SRC2[31] : execute_SRC1[31]));
  assign _zz_33_ = execute_SrcPlugin_addSub;
  assign _zz_32_ = execute_SrcPlugin_addSub;
  assign _zz_31_ = execute_SrcPlugin_less;
  assign execute_LightShifterPlugin_isShift = (execute_SHIFT_CTRL != `ShiftCtrlEnum_defaultEncoding_DISABLE_1);
  assign execute_LightShifterPlugin_amplitude = (execute_LightShifterPlugin_isActive ? execute_LightShifterPlugin_amplitudeReg : execute_SRC2[4 : 0]);
  assign execute_LightShifterPlugin_shiftInput = (execute_LightShifterPlugin_isActive ? memory_REGFILE_WRITE_DATA : execute_SRC1);
  assign execute_LightShifterPlugin_done = (execute_LightShifterPlugin_amplitude[4 : 1] == (4'b0000));
  always @ (*) begin
    case(execute_SHIFT_CTRL)
      `ShiftCtrlEnum_defaultEncoding_SLL_1 : begin
        _zz_180_ = (execute_LightShifterPlugin_shiftInput <<< 1);
      end
      default : begin
        _zz_180_ = _zz_283_;
      end
    endcase
  end

  always @ (*) begin
    _zz_181_ = 1'b0;
    _zz_182_ = 1'b0;
    if(_zz_183_)begin
      if((_zz_184_ == decode_INSTRUCTION[19 : 15]))begin
        _zz_181_ = 1'b1;
      end
      if((_zz_184_ == decode_INSTRUCTION[24 : 20]))begin
        _zz_182_ = 1'b1;
      end
    end
    if((writeBack_arbitration_isValid && writeBack_REGFILE_WRITE_VALID))begin
      if((1'b1 || (! 1'b1)))begin
        if((writeBack_INSTRUCTION[11 : 7] == decode_INSTRUCTION[19 : 15]))begin
          _zz_181_ = 1'b1;
        end
        if((writeBack_INSTRUCTION[11 : 7] == decode_INSTRUCTION[24 : 20]))begin
          _zz_182_ = 1'b1;
        end
      end
    end
    if((memory_arbitration_isValid && memory_REGFILE_WRITE_VALID))begin
      if((1'b1 || (! memory_BYPASSABLE_MEMORY_STAGE)))begin
        if((memory_INSTRUCTION[11 : 7] == decode_INSTRUCTION[19 : 15]))begin
          _zz_181_ = 1'b1;
        end
        if((memory_INSTRUCTION[11 : 7] == decode_INSTRUCTION[24 : 20]))begin
          _zz_182_ = 1'b1;
        end
      end
    end
    if((execute_arbitration_isValid && execute_REGFILE_WRITE_VALID))begin
      if((1'b1 || (! execute_BYPASSABLE_EXECUTE_STAGE)))begin
        if((execute_INSTRUCTION[11 : 7] == decode_INSTRUCTION[19 : 15]))begin
          _zz_181_ = 1'b1;
        end
        if((execute_INSTRUCTION[11 : 7] == decode_INSTRUCTION[24 : 20]))begin
          _zz_182_ = 1'b1;
        end
      end
    end
    if((! decode_RS1_USE))begin
      _zz_181_ = 1'b0;
    end
    if((! decode_RS2_USE))begin
      _zz_182_ = 1'b0;
    end
  end

  assign execute_MulPlugin_a = execute_SRC1;
  assign execute_MulPlugin_b = execute_SRC2;
  always @ (*) begin
    case(_zz_233_)
      2'b01 : begin
        execute_MulPlugin_aSigned = 1'b1;
        execute_MulPlugin_bSigned = 1'b1;
      end
      2'b10 : begin
        execute_MulPlugin_aSigned = 1'b1;
        execute_MulPlugin_bSigned = 1'b0;
      end
      default : begin
        execute_MulPlugin_aSigned = 1'b0;
        execute_MulPlugin_bSigned = 1'b0;
      end
    endcase
  end

  assign execute_MulPlugin_aULow = execute_MulPlugin_a[15 : 0];
  assign execute_MulPlugin_bULow = execute_MulPlugin_b[15 : 0];
  assign execute_MulPlugin_aSLow = {1'b0,execute_MulPlugin_a[15 : 0]};
  assign execute_MulPlugin_bSLow = {1'b0,execute_MulPlugin_b[15 : 0]};
  assign execute_MulPlugin_aHigh = {(execute_MulPlugin_aSigned && execute_MulPlugin_a[31]),execute_MulPlugin_a[31 : 16]};
  assign execute_MulPlugin_bHigh = {(execute_MulPlugin_bSigned && execute_MulPlugin_b[31]),execute_MulPlugin_b[31 : 16]};
  assign _zz_29_ = (execute_MulPlugin_aULow * execute_MulPlugin_bULow);
  assign _zz_28_ = ($signed(execute_MulPlugin_aSLow) * $signed(execute_MulPlugin_bHigh));
  assign _zz_27_ = ($signed(execute_MulPlugin_aHigh) * $signed(execute_MulPlugin_bSLow));
  assign _zz_26_ = ($signed(execute_MulPlugin_aHigh) * $signed(execute_MulPlugin_bHigh));
  assign _zz_25_ = ($signed(_zz_285_) + $signed(_zz_293_));
  assign writeBack_MulPlugin_result = ($signed(_zz_294_) + $signed(_zz_295_));
  always @ (*) begin
    memory_DivPlugin_div_counter_willClear = 1'b0;
    if(_zz_225_)begin
      memory_DivPlugin_div_counter_willClear = 1'b1;
    end
  end

  assign memory_DivPlugin_div_willOverflowIfInc = (memory_DivPlugin_div_counter_value == (6'b100001));
  assign memory_DivPlugin_div_counter_willOverflow = (memory_DivPlugin_div_willOverflowIfInc && memory_DivPlugin_div_counter_willIncrement);
  always @ (*) begin
    if(memory_DivPlugin_div_counter_willOverflow)begin
      memory_DivPlugin_div_counter_valueNext = (6'b000000);
    end else begin
      memory_DivPlugin_div_counter_valueNext = (memory_DivPlugin_div_counter_value + _zz_299_);
    end
    if(memory_DivPlugin_div_counter_willClear)begin
      memory_DivPlugin_div_counter_valueNext = (6'b000000);
    end
  end

  assign _zz_185_ = memory_DivPlugin_rs1[31 : 0];
  assign _zz_186_ = {memory_DivPlugin_accumulator[31 : 0],_zz_185_[31]};
  assign _zz_187_ = (_zz_186_ - _zz_300_);
  assign _zz_188_ = (memory_INSTRUCTION[13] ? memory_DivPlugin_accumulator[31 : 0] : memory_DivPlugin_rs1[31 : 0]);
  assign _zz_189_ = (execute_RS2[31] && execute_IS_RS2_SIGNED);
  assign _zz_190_ = (1'b0 || ((execute_IS_DIV && execute_RS1[31]) && execute_IS_RS1_SIGNED));
  always @ (*) begin
    _zz_191_[32] = (execute_IS_RS1_SIGNED && execute_RS1[31]);
    _zz_191_[31 : 0] = execute_RS1;
  end

  assign execute_BranchPlugin_eq = (execute_SRC1 == execute_SRC2);
  assign _zz_192_ = execute_INSTRUCTION[14 : 12];
  always @ (*) begin
    if((_zz_192_ == (3'b000))) begin
        _zz_193_ = execute_BranchPlugin_eq;
    end else if((_zz_192_ == (3'b001))) begin
        _zz_193_ = (! execute_BranchPlugin_eq);
    end else if((((_zz_192_ & (3'b101)) == (3'b101)))) begin
        _zz_193_ = (! execute_SRC_LESS);
    end else begin
        _zz_193_ = execute_SRC_LESS;
    end
  end

  always @ (*) begin
    case(execute_BRANCH_CTRL)
      `BranchCtrlEnum_defaultEncoding_INC : begin
        _zz_194_ = 1'b0;
      end
      `BranchCtrlEnum_defaultEncoding_JAL : begin
        _zz_194_ = 1'b1;
      end
      `BranchCtrlEnum_defaultEncoding_JALR : begin
        _zz_194_ = 1'b1;
      end
      default : begin
        _zz_194_ = _zz_193_;
      end
    endcase
  end

  assign _zz_23_ = _zz_194_;
  assign execute_BranchPlugin_branch_src1 = ((execute_BRANCH_CTRL == `BranchCtrlEnum_defaultEncoding_JALR) ? execute_RS1 : execute_PC);
  assign _zz_195_ = _zz_313_[19];
  always @ (*) begin
    _zz_196_[10] = _zz_195_;
    _zz_196_[9] = _zz_195_;
    _zz_196_[8] = _zz_195_;
    _zz_196_[7] = _zz_195_;
    _zz_196_[6] = _zz_195_;
    _zz_196_[5] = _zz_195_;
    _zz_196_[4] = _zz_195_;
    _zz_196_[3] = _zz_195_;
    _zz_196_[2] = _zz_195_;
    _zz_196_[1] = _zz_195_;
    _zz_196_[0] = _zz_195_;
  end

  assign _zz_197_ = _zz_314_[11];
  always @ (*) begin
    _zz_198_[19] = _zz_197_;
    _zz_198_[18] = _zz_197_;
    _zz_198_[17] = _zz_197_;
    _zz_198_[16] = _zz_197_;
    _zz_198_[15] = _zz_197_;
    _zz_198_[14] = _zz_197_;
    _zz_198_[13] = _zz_197_;
    _zz_198_[12] = _zz_197_;
    _zz_198_[11] = _zz_197_;
    _zz_198_[10] = _zz_197_;
    _zz_198_[9] = _zz_197_;
    _zz_198_[8] = _zz_197_;
    _zz_198_[7] = _zz_197_;
    _zz_198_[6] = _zz_197_;
    _zz_198_[5] = _zz_197_;
    _zz_198_[4] = _zz_197_;
    _zz_198_[3] = _zz_197_;
    _zz_198_[2] = _zz_197_;
    _zz_198_[1] = _zz_197_;
    _zz_198_[0] = _zz_197_;
  end

  assign _zz_199_ = _zz_315_[11];
  always @ (*) begin
    _zz_200_[18] = _zz_199_;
    _zz_200_[17] = _zz_199_;
    _zz_200_[16] = _zz_199_;
    _zz_200_[15] = _zz_199_;
    _zz_200_[14] = _zz_199_;
    _zz_200_[13] = _zz_199_;
    _zz_200_[12] = _zz_199_;
    _zz_200_[11] = _zz_199_;
    _zz_200_[10] = _zz_199_;
    _zz_200_[9] = _zz_199_;
    _zz_200_[8] = _zz_199_;
    _zz_200_[7] = _zz_199_;
    _zz_200_[6] = _zz_199_;
    _zz_200_[5] = _zz_199_;
    _zz_200_[4] = _zz_199_;
    _zz_200_[3] = _zz_199_;
    _zz_200_[2] = _zz_199_;
    _zz_200_[1] = _zz_199_;
    _zz_200_[0] = _zz_199_;
  end

  always @ (*) begin
    case(execute_BRANCH_CTRL)
      `BranchCtrlEnum_defaultEncoding_JAL : begin
        _zz_201_ = {{_zz_196_,{{{execute_INSTRUCTION[31],execute_INSTRUCTION[19 : 12]},execute_INSTRUCTION[20]},execute_INSTRUCTION[30 : 21]}},1'b0};
      end
      `BranchCtrlEnum_defaultEncoding_JALR : begin
        _zz_201_ = {_zz_198_,execute_INSTRUCTION[31 : 20]};
      end
      default : begin
        _zz_201_ = {{_zz_200_,{{{execute_INSTRUCTION[31],execute_INSTRUCTION[7]},execute_INSTRUCTION[30 : 25]},execute_INSTRUCTION[11 : 8]}},1'b0};
      end
    endcase
  end

  assign execute_BranchPlugin_branch_src2 = _zz_201_;
  assign execute_BranchPlugin_branchAdder = (execute_BranchPlugin_branch_src1 + execute_BranchPlugin_branch_src2);
  assign _zz_21_ = {execute_BranchPlugin_branchAdder[31 : 1],((execute_BRANCH_CTRL == `BranchCtrlEnum_defaultEncoding_JALR) ? 1'b0 : execute_BranchPlugin_branchAdder[0])};
  assign _zz_95_ = (memory_arbitration_isFiring && memory_BRANCH_DO);
  assign _zz_96_ = memory_BRANCH_CALC;
  assign DebugPlugin_isPipBusy = (DebugPlugin_isPipActive || DebugPlugin_isPipActive_regNext);
  always @ (*) begin
    debug_bus_cmd_ready = 1'b1;
    _zz_97_ = 1'b0;
    if(debug_bus_cmd_valid)begin
      case(_zz_226_)
        1'b0 : begin
        end
        default : begin
          if(debug_bus_cmd_payload_wr)begin
            _zz_97_ = 1'b1;
            debug_bus_cmd_ready = _zz_98_;
          end
        end
      endcase
    end
  end

  always @ (*) begin
    debug_bus_rsp_data = DebugPlugin_busReadDataReg;
    if((! _zz_202_))begin
      debug_bus_rsp_data[0] = DebugPlugin_resetIt;
      debug_bus_rsp_data[1] = DebugPlugin_haltIt;
      debug_bus_rsp_data[2] = DebugPlugin_isPipBusy;
      debug_bus_rsp_data[3] = DebugPlugin_haltedByBreak;
      debug_bus_rsp_data[4] = DebugPlugin_stepIt;
    end
  end

  assign debug_resetOut = DebugPlugin_resetIt_regNext;
  assign _zz_20_ = decode_BRANCH_CTRL;
  assign _zz_18_ = _zz_49_;
  assign _zz_22_ = decode_to_execute_BRANCH_CTRL;
  assign _zz_17_ = decode_SHIFT_CTRL;
  assign _zz_15_ = _zz_56_;
  assign _zz_30_ = decode_to_execute_SHIFT_CTRL;
  assign _zz_36_ = _zz_58_;
  assign _zz_14_ = decode_ALU_BITWISE_CTRL;
  assign _zz_12_ = _zz_67_;
  assign _zz_43_ = decode_to_execute_ALU_BITWISE_CTRL;
  assign _zz_39_ = _zz_62_;
  assign _zz_11_ = decode_ALU_CTRL;
  assign _zz_9_ = _zz_52_;
  assign _zz_41_ = decode_to_execute_ALU_CTRL;
  assign _zz_8_ = decode_ENV_CTRL;
  assign _zz_5_ = execute_ENV_CTRL;
  assign _zz_3_ = memory_ENV_CTRL;
  assign _zz_6_ = _zz_50_;
  assign _zz_73_ = decode_to_execute_ENV_CTRL;
  assign _zz_1_ = execute_to_memory_ENV_CTRL;
  assign _zz_74_ = memory_to_writeBack_ENV_CTRL;
  assign decode_arbitration_isFlushed = (((decode_arbitration_flushAll || execute_arbitration_flushAll) || memory_arbitration_flushAll) || writeBack_arbitration_flushAll);
  assign execute_arbitration_isFlushed = ((execute_arbitration_flushAll || memory_arbitration_flushAll) || writeBack_arbitration_flushAll);
  assign memory_arbitration_isFlushed = (memory_arbitration_flushAll || writeBack_arbitration_flushAll);
  assign writeBack_arbitration_isFlushed = writeBack_arbitration_flushAll;
  assign decode_arbitration_isStuckByOthers = (decode_arbitration_haltByOther || (((1'b0 || execute_arbitration_isStuck) || memory_arbitration_isStuck) || writeBack_arbitration_isStuck));
  assign decode_arbitration_isStuck = (decode_arbitration_haltItself || decode_arbitration_isStuckByOthers);
  assign decode_arbitration_isMoving = ((! decode_arbitration_isStuck) && (! decode_arbitration_removeIt));
  assign decode_arbitration_isFiring = ((decode_arbitration_isValid && (! decode_arbitration_isStuck)) && (! decode_arbitration_removeIt));
  assign execute_arbitration_isStuckByOthers = (execute_arbitration_haltByOther || ((1'b0 || memory_arbitration_isStuck) || writeBack_arbitration_isStuck));
  assign execute_arbitration_isStuck = (execute_arbitration_haltItself || execute_arbitration_isStuckByOthers);
  assign execute_arbitration_isMoving = ((! execute_arbitration_isStuck) && (! execute_arbitration_removeIt));
  assign execute_arbitration_isFiring = ((execute_arbitration_isValid && (! execute_arbitration_isStuck)) && (! execute_arbitration_removeIt));
  assign memory_arbitration_isStuckByOthers = (memory_arbitration_haltByOther || (1'b0 || writeBack_arbitration_isStuck));
  assign memory_arbitration_isStuck = (memory_arbitration_haltItself || memory_arbitration_isStuckByOthers);
  assign memory_arbitration_isMoving = ((! memory_arbitration_isStuck) && (! memory_arbitration_removeIt));
  assign memory_arbitration_isFiring = ((memory_arbitration_isValid && (! memory_arbitration_isStuck)) && (! memory_arbitration_removeIt));
  assign writeBack_arbitration_isStuckByOthers = (writeBack_arbitration_haltByOther || 1'b0);
  assign writeBack_arbitration_isStuck = (writeBack_arbitration_haltItself || writeBack_arbitration_isStuckByOthers);
  assign writeBack_arbitration_isMoving = ((! writeBack_arbitration_isStuck) && (! writeBack_arbitration_removeIt));
  assign writeBack_arbitration_isFiring = ((writeBack_arbitration_isValid && (! writeBack_arbitration_isStuck)) && (! writeBack_arbitration_removeIt));
  always @ (posedge io_mainClk or posedge resetCtrl_systemReset) begin
    if (resetCtrl_systemReset) begin
      _zz_91_ <= (2'b11);
      IBusSimplePlugin_fetchPc_pcReg <= (32'b10000000000000000000000000000000);
      _zz_102_ <= 1'b0;
      IBusSimplePlugin_decodePc_pcReg <= (32'b10000000000000000000000000000000);
      _zz_104_ <= 1'b0;
      IBusSimplePlugin_decompressor_bufferValid <= 1'b0;
      _zz_133_ <= 1'b0;
      _zz_138_ <= 1'b0;
      _zz_139_ <= 1'b0;
      _zz_140_ <= 1'b0;
      _zz_141_ <= 1'b0;
      IBusSimplePlugin_injector_decodeRemoved <= 1'b0;
      IBusSimplePlugin_pendingCmd <= (3'b000);
      IBusSimplePlugin_rsp_discardCounter <= (3'b000);
      CsrPlugin_misa_base <= (2'b01);
      CsrPlugin_misa_extensions <= (26'b00000000000000000001000010);
      CsrPlugin_mtvec <= (32'b10000000000000000000000000100000);
      CsrPlugin_mstatus_MIE <= 1'b0;
      CsrPlugin_mstatus_MPIE <= 1'b0;
      CsrPlugin_mstatus_MPP <= (2'b11);
      CsrPlugin_mip_MEIP <= 1'b0;
      CsrPlugin_mip_MTIP <= 1'b0;
      CsrPlugin_mip_MSIP <= 1'b0;
      CsrPlugin_mie_MEIE <= 1'b0;
      CsrPlugin_mie_MTIE <= 1'b0;
      CsrPlugin_mie_MSIE <= 1'b0;
      CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_execute <= 1'b0;
      CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_memory <= 1'b0;
      CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_writeBack <= 1'b0;
      CsrPlugin_writeBackWasWfi <= 1'b0;
      _zz_172_ <= 1'b1;
      execute_LightShifterPlugin_isActive <= 1'b0;
      _zz_183_ <= 1'b0;
      memory_DivPlugin_div_counter_value <= (6'b000000);
      execute_arbitration_isValid <= 1'b0;
      memory_arbitration_isValid <= 1'b0;
      writeBack_arbitration_isValid <= 1'b0;
      _zz_204_ <= (3'b000);
      memory_to_writeBack_REGFILE_WRITE_DATA <= (32'b00000000000000000000000000000000);
      memory_to_writeBack_INSTRUCTION <= (32'b00000000000000000000000000000000);
    end else begin
      if((IBusSimplePlugin_fetchPc_preOutput_valid && IBusSimplePlugin_fetchPc_preOutput_ready))begin
        IBusSimplePlugin_fetchPc_pcReg <= IBusSimplePlugin_fetchPc_pcPlus4;
      end
      if((IBusSimplePlugin_fetchPc_preOutput_valid && IBusSimplePlugin_fetchPc_preOutput_ready))begin
        IBusSimplePlugin_fetchPc_pcReg[1 : 0] <= (2'b00);
      end
      _zz_102_ <= 1'b1;
      if(IBusSimplePlugin_jump_pcLoad_valid)begin
        IBusSimplePlugin_fetchPc_pcReg <= IBusSimplePlugin_jump_pcLoad_payload;
      end
      if((decode_arbitration_isFiring && (! IBusSimplePlugin_decodePc_injectedDecode)))begin
        IBusSimplePlugin_decodePc_pcReg <= IBusSimplePlugin_decodePc_pcPlus;
      end
      if(IBusSimplePlugin_jump_pcLoad_valid)begin
        IBusSimplePlugin_decodePc_pcReg <= IBusSimplePlugin_jump_pcLoad_payload;
      end
      if(IBusSimplePlugin_iBusRsp_input_ready)begin
        _zz_104_ <= IBusSimplePlugin_iBusRsp_input_valid;
      end
      if((IBusSimplePlugin_jump_pcLoad_valid || _zz_85_))begin
        _zz_104_ <= 1'b0;
      end
      if((IBusSimplePlugin_decompressor_inputBeforeStage_valid && IBusSimplePlugin_decompressor_inputBeforeStage_ready))begin
        IBusSimplePlugin_decompressor_bufferValid <= 1'b0;
      end
      if(_zz_227_)begin
        IBusSimplePlugin_decompressor_bufferValid <= ((! (((! IBusSimplePlugin_decompressor_isRvc) && (! IBusSimplePlugin_iBusRsp_output_payload_pc[1])) && (! IBusSimplePlugin_decompressor_bufferValid))) && (! ((IBusSimplePlugin_decompressor_isRvc && IBusSimplePlugin_iBusRsp_output_payload_pc[1]) && IBusSimplePlugin_decompressor_inputBeforeStage_ready)));
      end
      if((IBusSimplePlugin_jump_pcLoad_valid || _zz_85_))begin
        IBusSimplePlugin_decompressor_bufferValid <= 1'b0;
      end
      if(IBusSimplePlugin_decompressor_inputBeforeStage_ready)begin
        _zz_133_ <= IBusSimplePlugin_decompressor_inputBeforeStage_valid;
      end
      if((IBusSimplePlugin_jump_pcLoad_valid || _zz_85_))begin
        _zz_133_ <= 1'b0;
      end
      if((! 1'b0))begin
        _zz_138_ <= 1'b1;
      end
      if((IBusSimplePlugin_jump_pcLoad_valid || _zz_85_))begin
        _zz_138_ <= 1'b0;
      end
      if((! execute_arbitration_isStuck))begin
        _zz_139_ <= _zz_138_;
      end
      if((IBusSimplePlugin_jump_pcLoad_valid || _zz_85_))begin
        _zz_139_ <= 1'b0;
      end
      if((! memory_arbitration_isStuck))begin
        _zz_140_ <= _zz_139_;
      end
      if((IBusSimplePlugin_jump_pcLoad_valid || _zz_85_))begin
        _zz_140_ <= 1'b0;
      end
      if((! writeBack_arbitration_isStuck))begin
        _zz_141_ <= _zz_140_;
      end
      if((IBusSimplePlugin_jump_pcLoad_valid || _zz_85_))begin
        _zz_141_ <= 1'b0;
      end
      if(decode_arbitration_removeIt)begin
        IBusSimplePlugin_injector_decodeRemoved <= 1'b1;
      end
      if((IBusSimplePlugin_jump_pcLoad_valid || _zz_85_))begin
        IBusSimplePlugin_injector_decodeRemoved <= 1'b0;
      end
      IBusSimplePlugin_pendingCmd <= IBusSimplePlugin_pendingCmdNext;
      IBusSimplePlugin_rsp_discardCounter <= (IBusSimplePlugin_rsp_discardCounter - _zz_250_);
      if((IBusSimplePlugin_jump_pcLoad_valid || _zz_85_))begin
        IBusSimplePlugin_rsp_discardCounter <= IBusSimplePlugin_pendingCmdNext;
      end
      CsrPlugin_mip_MEIP <= externalInterrupt;
      CsrPlugin_mip_MTIP <= timerInterrupt;
      if((! execute_arbitration_isStuck))begin
        CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_execute <= 1'b0;
      end else begin
        CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_execute <= CsrPlugin_exceptionPortCtrl_exceptionValids_execute;
      end
      if((! memory_arbitration_isStuck))begin
        CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_memory <= (CsrPlugin_exceptionPortCtrl_exceptionValids_execute && (! execute_arbitration_isStuck));
      end else begin
        CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_memory <= CsrPlugin_exceptionPortCtrl_exceptionValids_memory;
      end
      if((! writeBack_arbitration_isStuck))begin
        CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_writeBack <= (CsrPlugin_exceptionPortCtrl_exceptionValids_memory && (! memory_arbitration_isStuck));
      end else begin
        CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_writeBack <= CsrPlugin_exceptionPortCtrl_exceptionValids_writeBack;
      end
      CsrPlugin_writeBackWasWfi <= (writeBack_arbitration_isFiring && (writeBack_ENV_CTRL == `EnvCtrlEnum_defaultEncoding_WFI));
      if(_zz_219_)begin
        CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_writeBack <= 1'b0;
        CsrPlugin_mstatus_MIE <= 1'b0;
        CsrPlugin_mstatus_MPIE <= CsrPlugin_mstatus_MIE;
        CsrPlugin_mstatus_MPP <= _zz_91_;
      end
      if(_zz_220_)begin
        if(! _zz_221_) begin
          CsrPlugin_mstatus_MIE <= CsrPlugin_mstatus_MPIE;
          _zz_91_ <= CsrPlugin_mstatus_MPP;
        end
      end
      _zz_172_ <= 1'b0;
      if(_zz_222_)begin
        if(_zz_223_)begin
          execute_LightShifterPlugin_isActive <= 1'b1;
          if(execute_LightShifterPlugin_done)begin
            execute_LightShifterPlugin_isActive <= 1'b0;
          end
        end
      end
      if(execute_arbitration_removeIt)begin
        execute_LightShifterPlugin_isActive <= 1'b0;
      end
      _zz_183_ <= (_zz_45_ && writeBack_arbitration_isFiring);
      memory_DivPlugin_div_counter_value <= memory_DivPlugin_div_counter_valueNext;
      if((! writeBack_arbitration_isStuck))begin
        memory_to_writeBack_REGFILE_WRITE_DATA <= _zz_24_;
      end
      if((! writeBack_arbitration_isStuck))begin
        memory_to_writeBack_INSTRUCTION <= memory_INSTRUCTION;
      end
      if(((! execute_arbitration_isStuck) || execute_arbitration_removeIt))begin
        execute_arbitration_isValid <= 1'b0;
      end
      if(((! decode_arbitration_isStuck) && (! decode_arbitration_removeIt)))begin
        execute_arbitration_isValid <= decode_arbitration_isValid;
      end
      if(((! memory_arbitration_isStuck) || memory_arbitration_removeIt))begin
        memory_arbitration_isValid <= 1'b0;
      end
      if(((! execute_arbitration_isStuck) && (! execute_arbitration_removeIt)))begin
        memory_arbitration_isValid <= execute_arbitration_isValid;
      end
      if(((! writeBack_arbitration_isStuck) || writeBack_arbitration_removeIt))begin
        writeBack_arbitration_isValid <= 1'b0;
      end
      if(((! memory_arbitration_isStuck) && (! memory_arbitration_removeIt)))begin
        writeBack_arbitration_isValid <= memory_arbitration_isValid;
      end
      case(_zz_204_)
        3'b000 : begin
          if(_zz_97_)begin
            _zz_204_ <= (3'b001);
          end
        end
        3'b001 : begin
          _zz_204_ <= (3'b010);
        end
        3'b010 : begin
          _zz_204_ <= (3'b011);
        end
        3'b011 : begin
          if((! decode_arbitration_isStuck))begin
            _zz_204_ <= (3'b100);
          end
        end
        3'b100 : begin
          _zz_204_ <= (3'b000);
        end
        default : begin
        end
      endcase
      case(execute_CsrPlugin_csrAddress)
        12'b001100000000 : begin
          if(execute_CsrPlugin_writeEnable)begin
            CsrPlugin_mstatus_MPP <= execute_CsrPlugin_writeData[12 : 11];
            CsrPlugin_mstatus_MPIE <= _zz_316_[0];
            CsrPlugin_mstatus_MIE <= _zz_317_[0];
          end
        end
        12'b111100010001 : begin
        end
        12'b111100010100 : begin
        end
        12'b001101000001 : begin
        end
        12'b101100000000 : begin
        end
        12'b101110000000 : begin
        end
        12'b001101000100 : begin
          if(execute_CsrPlugin_writeEnable)begin
            CsrPlugin_mip_MSIP <= _zz_318_[0];
          end
        end
        12'b001100000101 : begin
          if(execute_CsrPlugin_writeEnable)begin
            CsrPlugin_mtvec <= execute_CsrPlugin_writeData[31 : 0];
          end
        end
        12'b101100000010 : begin
        end
        12'b111100010011 : begin
        end
        12'b001101000011 : begin
        end
        12'b110000000000 : begin
        end
        12'b001100000001 : begin
          if(execute_CsrPlugin_writeEnable)begin
            CsrPlugin_misa_base <= execute_CsrPlugin_writeData[31 : 30];
            CsrPlugin_misa_extensions <= execute_CsrPlugin_writeData[25 : 0];
          end
        end
        12'b001101000000 : begin
        end
        12'b111100010010 : begin
        end
        12'b001100000100 : begin
          if(execute_CsrPlugin_writeEnable)begin
            CsrPlugin_mie_MEIE <= _zz_319_[0];
            CsrPlugin_mie_MTIE <= _zz_320_[0];
            CsrPlugin_mie_MSIE <= _zz_321_[0];
          end
        end
        12'b101110000010 : begin
        end
        12'b001101000010 : begin
        end
        default : begin
        end
      endcase
    end
  end

  always @ (posedge io_mainClk) begin
    if(IBusSimplePlugin_iBusRsp_input_ready)begin
      _zz_105_ <= IBusSimplePlugin_iBusRsp_input_payload;
    end
    if(_zz_227_)begin
      IBusSimplePlugin_decompressor_bufferData <= IBusSimplePlugin_iBusRsp_output_payload_rsp_inst[31 : 16];
    end
    if(IBusSimplePlugin_decompressor_inputBeforeStage_ready)begin
      _zz_134_ <= IBusSimplePlugin_decompressor_inputBeforeStage_payload_pc;
      _zz_135_ <= IBusSimplePlugin_decompressor_inputBeforeStage_payload_rsp_error;
      _zz_136_ <= IBusSimplePlugin_decompressor_inputBeforeStage_payload_rsp_inst;
      _zz_137_ <= IBusSimplePlugin_decompressor_inputBeforeStage_payload_isRvc;
    end
    if(IBusSimplePlugin_injector_decodeInput_ready)begin
      IBusSimplePlugin_injector_formal_rawInDecode <= IBusSimplePlugin_decompressor_raw;
    end
`ifndef SYNTHESIS
    if(!(! (((dBus_rsp_ready && memory_MEMORY_ENABLE) && memory_arbitration_isValid) && memory_arbitration_isStuck))) begin
      $display("ERROR DBusSimplePlugin doesn't allow memory stage stall when read happend");
    end
`endif
`ifndef SYNTHESIS
    if(!(! (((writeBack_arbitration_isValid && writeBack_MEMORY_ENABLE) && (! writeBack_INSTRUCTION[5])) && writeBack_arbitration_isStuck))) begin
      $display("ERROR DBusSimplePlugin doesn't allow writeback stage stall when read happend");
    end
`endif
    CsrPlugin_mcycle <= (CsrPlugin_mcycle + (64'b0000000000000000000000000000000000000000000000000000000000000001));
    if(writeBack_arbitration_isFiring)begin
      CsrPlugin_minstret <= (CsrPlugin_minstret + (64'b0000000000000000000000000000000000000000000000000000000000000001));
    end
    if(execute_exception_agregat_valid)begin
      if((! ((1'b0 || CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_memory) || CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_writeBack)))begin
        CsrPlugin_exceptionPortCtrl_exceptionContext_code <= execute_exception_agregat_payload_code;
        CsrPlugin_exceptionPortCtrl_exceptionContext_badAddr <= execute_exception_agregat_payload_badAddr;
      end
    end
    if(_zz_219_)begin
      CsrPlugin_mepc <= writeBack_PC;
      CsrPlugin_mcause_interrupt <= CsrPlugin_interruptJump;
      CsrPlugin_mcause_exceptionCode <= CsrPlugin_interruptCode;
    end
    CsrPlugin_exception_regNext <= CsrPlugin_exception;
    if(CsrPlugin_exception_regNext)begin
      CsrPlugin_mbadaddr <= CsrPlugin_exceptionPortCtrl_exceptionContext_badAddr;
      CsrPlugin_mcause_exceptionCode <= CsrPlugin_exceptionPortCtrl_exceptionContext_code;
    end
    if(execute_arbitration_isValid)begin
      execute_CsrPlugin_readDataRegValid <= 1'b1;
    end
    if((! execute_arbitration_isStuck))begin
      execute_CsrPlugin_readDataRegValid <= 1'b0;
    end
    if(_zz_222_)begin
      if(_zz_223_)begin
        execute_LightShifterPlugin_amplitudeReg <= (execute_LightShifterPlugin_amplitude - (5'b00001));
      end
    end
    _zz_184_ <= _zz_44_[11 : 7];
    if(_zz_217_)begin
      if(_zz_218_)begin
        memory_DivPlugin_rs1[31 : 0] <= _zz_301_[31:0];
        memory_DivPlugin_accumulator[31 : 0] <= ((! _zz_187_[32]) ? _zz_302_ : _zz_303_);
        if((memory_DivPlugin_div_counter_value == (6'b100000)))begin
          memory_DivPlugin_div_result <= _zz_304_[31:0];
        end
      end
    end
    if(_zz_225_)begin
      memory_DivPlugin_accumulator <= (65'b00000000000000000000000000000000000000000000000000000000000000000);
      memory_DivPlugin_rs1 <= ((_zz_190_ ? (~ _zz_191_) : _zz_191_) + _zz_310_);
      memory_DivPlugin_rs2 <= ((_zz_189_ ? (~ execute_RS2) : execute_RS2) + _zz_312_);
      memory_DivPlugin_div_needRevert <= (_zz_190_ ^ (_zz_189_ && (! execute_INSTRUCTION[13])));
    end
    if((! execute_arbitration_isStuck))begin
      decode_to_execute_BRANCH_CTRL <= _zz_19_;
    end
    if((! memory_arbitration_isStuck))begin
      execute_to_memory_MUL_HL <= execute_MUL_HL;
    end
    if((! execute_arbitration_isStuck))begin
      decode_to_execute_IS_CSR <= decode_IS_CSR;
    end
    if((! execute_arbitration_isStuck))begin
      decode_to_execute_SRC2 <= decode_SRC2;
    end
    if((! execute_arbitration_isStuck))begin
      decode_to_execute_SRC_USE_SUB_LESS <= decode_SRC_USE_SUB_LESS;
    end
    if((! execute_arbitration_isStuck))begin
      decode_to_execute_SHIFT_CTRL <= _zz_16_;
    end
    if((! execute_arbitration_isStuck))begin
      decode_to_execute_SRC_LESS_UNSIGNED <= decode_SRC_LESS_UNSIGNED;
    end
    if((! execute_arbitration_isStuck))begin
      decode_to_execute_MEMORY_ENABLE <= decode_MEMORY_ENABLE;
    end
    if((! memory_arbitration_isStuck))begin
      execute_to_memory_MEMORY_ENABLE <= execute_MEMORY_ENABLE;
    end
    if((! writeBack_arbitration_isStuck))begin
      memory_to_writeBack_MEMORY_ENABLE <= memory_MEMORY_ENABLE;
    end
    if((! writeBack_arbitration_isStuck))begin
      memory_to_writeBack_MUL_LOW <= memory_MUL_LOW;
    end
    if((! memory_arbitration_isStuck))begin
      execute_to_memory_REGFILE_WRITE_DATA <= _zz_70_;
    end
    if((! execute_arbitration_isStuck))begin
      decode_to_execute_PC <= _zz_34_;
    end
    if((! memory_arbitration_isStuck))begin
      execute_to_memory_PC <= execute_PC;
    end
    if((! writeBack_arbitration_isStuck))begin
      memory_to_writeBack_PC <= memory_PC;
    end
    if((! memory_arbitration_isStuck))begin
      execute_to_memory_BRANCH_DO <= execute_BRANCH_DO;
    end
    if((! execute_arbitration_isStuck))begin
      decode_to_execute_IS_MUL <= decode_IS_MUL;
    end
    if((! memory_arbitration_isStuck))begin
      execute_to_memory_IS_MUL <= execute_IS_MUL;
    end
    if((! writeBack_arbitration_isStuck))begin
      memory_to_writeBack_IS_MUL <= memory_IS_MUL;
    end
    if((! execute_arbitration_isStuck))begin
      decode_to_execute_BYPASSABLE_MEMORY_STAGE <= decode_BYPASSABLE_MEMORY_STAGE;
    end
    if((! memory_arbitration_isStuck))begin
      execute_to_memory_BYPASSABLE_MEMORY_STAGE <= execute_BYPASSABLE_MEMORY_STAGE;
    end
    if((! memory_arbitration_isStuck))begin
      execute_to_memory_MUL_LL <= execute_MUL_LL;
    end
    if((! memory_arbitration_isStuck))begin
      execute_to_memory_MUL_LH <= execute_MUL_LH;
    end
    if((! execute_arbitration_isStuck))begin
      decode_to_execute_IS_EBREAK <= decode_IS_EBREAK;
    end
    if((! execute_arbitration_isStuck))begin
      decode_to_execute_IS_DIV <= decode_IS_DIV;
    end
    if((! memory_arbitration_isStuck))begin
      execute_to_memory_IS_DIV <= execute_IS_DIV;
    end
    if((! execute_arbitration_isStuck))begin
      decode_to_execute_IS_RS1_SIGNED <= decode_IS_RS1_SIGNED;
    end
    if((! execute_arbitration_isStuck))begin
      decode_to_execute_FORMAL_PC_NEXT <= decode_FORMAL_PC_NEXT;
    end
    if((! memory_arbitration_isStuck))begin
      execute_to_memory_FORMAL_PC_NEXT <= execute_FORMAL_PC_NEXT;
    end
    if((! writeBack_arbitration_isStuck))begin
      memory_to_writeBack_FORMAL_PC_NEXT <= _zz_78_;
    end
    if((! execute_arbitration_isStuck))begin
      decode_to_execute_RS2 <= _zz_35_;
    end
    if((! memory_arbitration_isStuck))begin
      execute_to_memory_MEMORY_ADDRESS_LOW <= execute_MEMORY_ADDRESS_LOW;
    end
    if((! writeBack_arbitration_isStuck))begin
      memory_to_writeBack_MEMORY_ADDRESS_LOW <= memory_MEMORY_ADDRESS_LOW;
    end
    if((! execute_arbitration_isStuck))begin
      decode_to_execute_ALU_BITWISE_CTRL <= _zz_13_;
    end
    if((! execute_arbitration_isStuck))begin
      decode_to_execute_IS_RS2_SIGNED <= decode_IS_RS2_SIGNED;
    end
    if((! execute_arbitration_isStuck))begin
      decode_to_execute_CSR_READ_OPCODE <= decode_CSR_READ_OPCODE;
    end
    if((! execute_arbitration_isStuck))begin
      decode_to_execute_ALU_CTRL <= _zz_10_;
    end
    if((! execute_arbitration_isStuck))begin
      decode_to_execute_CSR_WRITE_OPCODE <= decode_CSR_WRITE_OPCODE;
    end
    if((! execute_arbitration_isStuck))begin
      decode_to_execute_ENV_CTRL <= _zz_7_;
    end
    if((! memory_arbitration_isStuck))begin
      execute_to_memory_ENV_CTRL <= _zz_4_;
    end
    if((! writeBack_arbitration_isStuck))begin
      memory_to_writeBack_ENV_CTRL <= _zz_2_;
    end
    if((! execute_arbitration_isStuck))begin
      decode_to_execute_SRC1 <= decode_SRC1;
    end
    if((! memory_arbitration_isStuck))begin
      execute_to_memory_BRANCH_CALC <= execute_BRANCH_CALC;
    end
    if((! execute_arbitration_isStuck))begin
      decode_to_execute_REGFILE_WRITE_VALID <= decode_REGFILE_WRITE_VALID;
    end
    if((! memory_arbitration_isStuck))begin
      execute_to_memory_REGFILE_WRITE_VALID <= execute_REGFILE_WRITE_VALID;
    end
    if((! writeBack_arbitration_isStuck))begin
      memory_to_writeBack_REGFILE_WRITE_VALID <= memory_REGFILE_WRITE_VALID;
    end
    if((! execute_arbitration_isStuck))begin
      decode_to_execute_BYPASSABLE_EXECUTE_STAGE <= decode_BYPASSABLE_EXECUTE_STAGE;
    end
    if((! memory_arbitration_isStuck))begin
      execute_to_memory_MUL_HH <= execute_MUL_HH;
    end
    if((! writeBack_arbitration_isStuck))begin
      memory_to_writeBack_MUL_HH <= memory_MUL_HH;
    end
    if((! execute_arbitration_isStuck))begin
      decode_to_execute_INSTRUCTION <= decode_INSTRUCTION;
    end
    if((! memory_arbitration_isStuck))begin
      execute_to_memory_INSTRUCTION <= execute_INSTRUCTION;
    end
    if((! execute_arbitration_isStuck))begin
      decode_to_execute_RS1 <= _zz_38_;
    end
    if((! writeBack_arbitration_isStuck))begin
      memory_to_writeBack_MEMORY_READ_DATA <= memory_MEMORY_READ_DATA;
    end
    if((((! IBusSimplePlugin_iBusRsp_output_ready) && (IBusSimplePlugin_decompressor_inputBeforeStage_valid && IBusSimplePlugin_decompressor_inputBeforeStage_ready)) && (! (IBusSimplePlugin_jump_pcLoad_valid || _zz_85_))))begin
      _zz_105_[1] <= 1'b1;
    end
    if((_zz_204_ != (3'b000)))begin
      _zz_136_ <= debug_bus_cmd_payload_data;
    end
    case(execute_CsrPlugin_csrAddress)
      12'b001100000000 : begin
      end
      12'b111100010001 : begin
      end
      12'b111100010100 : begin
      end
      12'b001101000001 : begin
        if(execute_CsrPlugin_writeEnable)begin
          CsrPlugin_mepc <= execute_CsrPlugin_writeData[31 : 0];
        end
      end
      12'b101100000000 : begin
        if(execute_CsrPlugin_writeEnable)begin
          CsrPlugin_mcycle[31 : 0] <= execute_CsrPlugin_writeData[31 : 0];
        end
      end
      12'b101110000000 : begin
        if(execute_CsrPlugin_writeEnable)begin
          CsrPlugin_mcycle[63 : 32] <= execute_CsrPlugin_writeData[31 : 0];
        end
      end
      12'b001101000100 : begin
      end
      12'b001100000101 : begin
      end
      12'b101100000010 : begin
        if(execute_CsrPlugin_writeEnable)begin
          CsrPlugin_minstret[31 : 0] <= execute_CsrPlugin_writeData[31 : 0];
        end
      end
      12'b111100010011 : begin
      end
      12'b001101000011 : begin
        if(execute_CsrPlugin_writeEnable)begin
          CsrPlugin_mbadaddr <= execute_CsrPlugin_writeData[31 : 0];
        end
      end
      12'b110000000000 : begin
      end
      12'b001100000001 : begin
      end
      12'b001101000000 : begin
        if(execute_CsrPlugin_writeEnable)begin
          CsrPlugin_mscratch <= execute_CsrPlugin_writeData[31 : 0];
        end
      end
      12'b111100010010 : begin
      end
      12'b001100000100 : begin
      end
      12'b101110000010 : begin
        if(execute_CsrPlugin_writeEnable)begin
          CsrPlugin_minstret[63 : 32] <= execute_CsrPlugin_writeData[31 : 0];
        end
      end
      12'b001101000010 : begin
        if(execute_CsrPlugin_writeEnable)begin
          CsrPlugin_mcause_interrupt <= _zz_322_[0];
          CsrPlugin_mcause_exceptionCode <= execute_CsrPlugin_writeData[3 : 0];
        end
      end
      default : begin
      end
    endcase
  end

  always @ (posedge io_mainClk) begin
    DebugPlugin_firstCycle <= 1'b0;
    if(debug_bus_cmd_ready)begin
      DebugPlugin_firstCycle <= 1'b1;
    end
    DebugPlugin_secondCycle <= DebugPlugin_firstCycle;
    DebugPlugin_isPipActive <= (((decode_arbitration_isValid || execute_arbitration_isValid) || memory_arbitration_isValid) || writeBack_arbitration_isValid);
    DebugPlugin_isPipActive_regNext <= DebugPlugin_isPipActive;
    if(writeBack_arbitration_isValid)begin
      DebugPlugin_busReadDataReg <= _zz_75_;
    end
    _zz_202_ <= debug_bus_cmd_payload_address[2];
    DebugPlugin_resetIt_regNext <= DebugPlugin_resetIt;
  end

  always @ (posedge io_mainClk or posedge resetCtrl_mainClkReset) begin
    if (resetCtrl_mainClkReset) begin
      DebugPlugin_resetIt <= 1'b0;
      DebugPlugin_haltIt <= 1'b0;
      DebugPlugin_stepIt <= 1'b0;
      DebugPlugin_haltedByBreak <= 1'b0;
      _zz_203_ <= 1'b0;
    end else begin
      if(debug_bus_cmd_valid)begin
        case(_zz_226_)
          1'b0 : begin
            if(debug_bus_cmd_payload_wr)begin
              DebugPlugin_stepIt <= debug_bus_cmd_payload_data[4];
              if(debug_bus_cmd_payload_data[16])begin
                DebugPlugin_resetIt <= 1'b1;
              end
              if(debug_bus_cmd_payload_data[24])begin
                DebugPlugin_resetIt <= 1'b0;
              end
              if(debug_bus_cmd_payload_data[17])begin
                DebugPlugin_haltIt <= 1'b1;
              end
              if(debug_bus_cmd_payload_data[25])begin
                DebugPlugin_haltIt <= 1'b0;
              end
              if(debug_bus_cmd_payload_data[25])begin
                DebugPlugin_haltedByBreak <= 1'b0;
              end
            end
          end
          default : begin
          end
        endcase
      end
      if(execute_IS_EBREAK)begin
        if(execute_arbitration_isFiring)begin
          DebugPlugin_haltIt <= 1'b1;
          DebugPlugin_haltedByBreak <= 1'b1;
        end
      end
      if(_zz_224_)begin
        if(decode_arbitration_isValid)begin
          DebugPlugin_haltIt <= 1'b1;
        end
      end
      if((DebugPlugin_stepIt && ({writeBack_arbitration_redoIt,{memory_arbitration_redoIt,{execute_arbitration_redoIt,decode_arbitration_redoIt}}} != (4'b0000))))begin
        DebugPlugin_haltIt <= 1'b0;
      end
      _zz_203_ <= (DebugPlugin_stepIt && decode_arbitration_isFiring);
    end
  end

endmodule

module JtagBridge (
      input   io_jtag_tms,
      input   io_jtag_tdi,
      output reg  io_jtag_tdo,
      input   io_jtag_tck,
      output  io_remote_cmd_valid,
      input   io_remote_cmd_ready,
      output  io_remote_cmd_payload_last,
      output [0:0] io_remote_cmd_payload_fragment,
      input   io_remote_rsp_valid,
      output  io_remote_rsp_ready,
      input   io_remote_rsp_payload_error,
      input  [31:0] io_remote_rsp_payload_data,
      input   io_mainClk,
      input   resetCtrl_mainClkReset);
  wire  _zz_2_;
  wire  _zz_3_;
  wire [0:0] _zz_4_;
  wire  _zz_5_;
  wire  _zz_6_;
  wire [3:0] _zz_7_;
  wire [3:0] _zz_8_;
  wire [3:0] _zz_9_;
  wire  system_cmd_valid;
  wire  system_cmd_payload_last;
  wire [0:0] system_cmd_payload_fragment;
  reg  system_rsp_valid;
  reg  system_rsp_payload_error;
  reg [31:0] system_rsp_payload_data;
  wire `JtagState_defaultEncoding_type jtag_tap_fsm_stateNext;
  reg `JtagState_defaultEncoding_type jtag_tap_fsm_state = `JtagState_defaultEncoding_RESET;
  reg `JtagState_defaultEncoding_type _zz_1_;
  reg [3:0] jtag_tap_instruction;
  reg [3:0] jtag_tap_instructionShift;
  reg  jtag_tap_bypass;
  wire [0:0] jtag_idcodeArea_instructionId;
  wire  jtag_idcodeArea_instructionHit;
  reg [31:0] jtag_idcodeArea_shifter;
  wire [1:0] jtag_writeArea_instructionId;
  wire  jtag_writeArea_instructionHit;
  reg  jtag_writeArea_source_valid;
  wire  jtag_writeArea_source_payload_last;
  wire [0:0] jtag_writeArea_source_payload_fragment;
  wire [1:0] jtag_readArea_instructionId;
  wire  jtag_readArea_instructionHit;
  reg [33:0] jtag_readArea_shifter;
  assign _zz_5_ = (jtag_tap_fsm_state == `JtagState_defaultEncoding_DR_SHIFT);
  assign _zz_6_ = (jtag_tap_fsm_state == `JtagState_defaultEncoding_DR_SHIFT);
  assign _zz_7_ = {3'd0, jtag_idcodeArea_instructionId};
  assign _zz_8_ = {2'd0, jtag_writeArea_instructionId};
  assign _zz_9_ = {2'd0, jtag_readArea_instructionId};
  FlowCCByToggle flowCCByToggle_1_ ( 
    .io_input_valid(jtag_writeArea_source_valid),
    .io_input_payload_last(jtag_writeArea_source_payload_last),
    .io_input_payload_fragment(jtag_writeArea_source_payload_fragment),
    .io_output_valid(_zz_2_),
    .io_output_payload_last(_zz_3_),
    .io_output_payload_fragment(_zz_4_),
    .io_jtag_tck(io_jtag_tck),
    .io_mainClk(io_mainClk),
    .resetCtrl_mainClkReset(resetCtrl_mainClkReset) 
  );
  assign io_remote_cmd_valid = system_cmd_valid;
  assign io_remote_cmd_payload_last = system_cmd_payload_last;
  assign io_remote_cmd_payload_fragment = system_cmd_payload_fragment;
  assign io_remote_rsp_ready = 1'b1;
  always @ (*) begin
    case(jtag_tap_fsm_state)
      `JtagState_defaultEncoding_IDLE : begin
        _zz_1_ = (io_jtag_tms ? `JtagState_defaultEncoding_DR_SELECT : `JtagState_defaultEncoding_IDLE);
      end
      `JtagState_defaultEncoding_IR_SELECT : begin
        _zz_1_ = (io_jtag_tms ? `JtagState_defaultEncoding_RESET : `JtagState_defaultEncoding_IR_CAPTURE);
      end
      `JtagState_defaultEncoding_IR_CAPTURE : begin
        _zz_1_ = (io_jtag_tms ? `JtagState_defaultEncoding_IR_EXIT1 : `JtagState_defaultEncoding_IR_SHIFT);
      end
      `JtagState_defaultEncoding_IR_SHIFT : begin
        _zz_1_ = (io_jtag_tms ? `JtagState_defaultEncoding_IR_EXIT1 : `JtagState_defaultEncoding_IR_SHIFT);
      end
      `JtagState_defaultEncoding_IR_EXIT1 : begin
        _zz_1_ = (io_jtag_tms ? `JtagState_defaultEncoding_IR_UPDATE : `JtagState_defaultEncoding_IR_PAUSE);
      end
      `JtagState_defaultEncoding_IR_PAUSE : begin
        _zz_1_ = (io_jtag_tms ? `JtagState_defaultEncoding_IR_EXIT2 : `JtagState_defaultEncoding_IR_PAUSE);
      end
      `JtagState_defaultEncoding_IR_EXIT2 : begin
        _zz_1_ = (io_jtag_tms ? `JtagState_defaultEncoding_IR_UPDATE : `JtagState_defaultEncoding_IR_SHIFT);
      end
      `JtagState_defaultEncoding_IR_UPDATE : begin
        _zz_1_ = (io_jtag_tms ? `JtagState_defaultEncoding_DR_SELECT : `JtagState_defaultEncoding_IDLE);
      end
      `JtagState_defaultEncoding_DR_SELECT : begin
        _zz_1_ = (io_jtag_tms ? `JtagState_defaultEncoding_IR_SELECT : `JtagState_defaultEncoding_DR_CAPTURE);
      end
      `JtagState_defaultEncoding_DR_CAPTURE : begin
        _zz_1_ = (io_jtag_tms ? `JtagState_defaultEncoding_DR_EXIT1 : `JtagState_defaultEncoding_DR_SHIFT);
      end
      `JtagState_defaultEncoding_DR_SHIFT : begin
        _zz_1_ = (io_jtag_tms ? `JtagState_defaultEncoding_DR_EXIT1 : `JtagState_defaultEncoding_DR_SHIFT);
      end
      `JtagState_defaultEncoding_DR_EXIT1 : begin
        _zz_1_ = (io_jtag_tms ? `JtagState_defaultEncoding_DR_UPDATE : `JtagState_defaultEncoding_DR_PAUSE);
      end
      `JtagState_defaultEncoding_DR_PAUSE : begin
        _zz_1_ = (io_jtag_tms ? `JtagState_defaultEncoding_DR_EXIT2 : `JtagState_defaultEncoding_DR_PAUSE);
      end
      `JtagState_defaultEncoding_DR_EXIT2 : begin
        _zz_1_ = (io_jtag_tms ? `JtagState_defaultEncoding_DR_UPDATE : `JtagState_defaultEncoding_DR_SHIFT);
      end
      `JtagState_defaultEncoding_DR_UPDATE : begin
        _zz_1_ = (io_jtag_tms ? `JtagState_defaultEncoding_DR_SELECT : `JtagState_defaultEncoding_IDLE);
      end
      default : begin
        _zz_1_ = (io_jtag_tms ? `JtagState_defaultEncoding_RESET : `JtagState_defaultEncoding_IDLE);
      end
    endcase
  end

  assign jtag_tap_fsm_stateNext = _zz_1_;
  always @ (*) begin
    io_jtag_tdo = jtag_tap_bypass;
    case(jtag_tap_fsm_state)
      `JtagState_defaultEncoding_IR_CAPTURE : begin
      end
      `JtagState_defaultEncoding_IR_SHIFT : begin
        io_jtag_tdo = jtag_tap_instructionShift[0];
      end
      `JtagState_defaultEncoding_IR_UPDATE : begin
      end
      `JtagState_defaultEncoding_DR_SHIFT : begin
      end
      default : begin
      end
    endcase
    if(jtag_idcodeArea_instructionHit)begin
      if(_zz_5_)begin
        io_jtag_tdo = jtag_idcodeArea_shifter[0];
      end
    end
    if(jtag_readArea_instructionHit)begin
      if(_zz_6_)begin
        io_jtag_tdo = jtag_readArea_shifter[0];
      end
    end
  end

  assign jtag_idcodeArea_instructionId = (1'b1);
  assign jtag_idcodeArea_instructionHit = (jtag_tap_instruction == _zz_7_);
  assign jtag_writeArea_instructionId = (2'b10);
  assign jtag_writeArea_instructionHit = (jtag_tap_instruction == _zz_8_);
  always @ (*) begin
    jtag_writeArea_source_valid = 1'b0;
    if(jtag_writeArea_instructionHit)begin
      if((jtag_tap_fsm_state == `JtagState_defaultEncoding_DR_SHIFT))begin
        jtag_writeArea_source_valid = 1'b1;
      end
    end
  end

  assign jtag_writeArea_source_payload_last = io_jtag_tms;
  assign jtag_writeArea_source_payload_fragment[0] = io_jtag_tdi;
  assign system_cmd_valid = _zz_2_;
  assign system_cmd_payload_last = _zz_3_;
  assign system_cmd_payload_fragment = _zz_4_;
  assign jtag_readArea_instructionId = (2'b11);
  assign jtag_readArea_instructionHit = (jtag_tap_instruction == _zz_9_);
  always @ (posedge io_mainClk) begin
    if(io_remote_cmd_valid)begin
      system_rsp_valid <= 1'b0;
    end
    if((io_remote_rsp_valid && io_remote_rsp_ready))begin
      system_rsp_valid <= 1'b1;
      system_rsp_payload_error <= io_remote_rsp_payload_error;
      system_rsp_payload_data <= io_remote_rsp_payload_data;
    end
  end

  always @ (posedge io_jtag_tck) begin
    jtag_tap_fsm_state <= jtag_tap_fsm_stateNext;
    case(jtag_tap_fsm_state)
      `JtagState_defaultEncoding_IR_CAPTURE : begin
        jtag_tap_instructionShift <= jtag_tap_instruction;
      end
      `JtagState_defaultEncoding_IR_SHIFT : begin
        jtag_tap_instructionShift <= ({io_jtag_tdi,jtag_tap_instructionShift} >>> 1);
      end
      `JtagState_defaultEncoding_IR_UPDATE : begin
        jtag_tap_instruction <= jtag_tap_instructionShift;
      end
      `JtagState_defaultEncoding_DR_SHIFT : begin
        jtag_tap_bypass <= io_jtag_tdi;
      end
      default : begin
      end
    endcase
    if(jtag_idcodeArea_instructionHit)begin
      if(_zz_5_)begin
        jtag_idcodeArea_shifter <= ({io_jtag_tdi,jtag_idcodeArea_shifter} >>> 1);
      end
    end
    if((jtag_tap_fsm_state == `JtagState_defaultEncoding_RESET))begin
      jtag_idcodeArea_shifter <= (32'b00010000000000000001111111111111);
      jtag_tap_instruction <= {3'd0, jtag_idcodeArea_instructionId};
    end
    if(jtag_readArea_instructionHit)begin
      if((jtag_tap_fsm_state == `JtagState_defaultEncoding_DR_CAPTURE))begin
        jtag_readArea_shifter <= {{system_rsp_payload_data,system_rsp_payload_error},system_rsp_valid};
      end
      if(_zz_6_)begin
        jtag_readArea_shifter <= ({io_jtag_tdi,jtag_readArea_shifter} >>> 1);
      end
    end
  end

endmodule

module SystemDebugger (
      input   io_remote_cmd_valid,
      output  io_remote_cmd_ready,
      input   io_remote_cmd_payload_last,
      input  [0:0] io_remote_cmd_payload_fragment,
      output  io_remote_rsp_valid,
      input   io_remote_rsp_ready,
      output  io_remote_rsp_payload_error,
      output [31:0] io_remote_rsp_payload_data,
      output  io_mem_cmd_valid,
      input   io_mem_cmd_ready,
      output [31:0] io_mem_cmd_payload_address,
      output [31:0] io_mem_cmd_payload_data,
      output  io_mem_cmd_payload_wr,
      output [1:0] io_mem_cmd_payload_size,
      input   io_mem_rsp_valid,
      input  [31:0] io_mem_rsp_payload,
      input   io_mainClk,
      input   resetCtrl_mainClkReset);
  wire  _zz_2_;
  wire [0:0] _zz_3_;
  reg [66:0] dispatcher_dataShifter;
  reg  dispatcher_dataLoaded;
  reg [7:0] dispatcher_headerShifter;
  wire [7:0] dispatcher_header;
  reg  dispatcher_headerLoaded;
  reg [2:0] dispatcher_counter;
  wire [66:0] _zz_1_;
  assign _zz_2_ = (dispatcher_headerLoaded == 1'b0);
  assign _zz_3_ = _zz_1_[64 : 64];
  assign dispatcher_header = dispatcher_headerShifter[7 : 0];
  assign io_remote_cmd_ready = (! dispatcher_dataLoaded);
  assign _zz_1_ = dispatcher_dataShifter[66 : 0];
  assign io_mem_cmd_payload_address = _zz_1_[31 : 0];
  assign io_mem_cmd_payload_data = _zz_1_[63 : 32];
  assign io_mem_cmd_payload_wr = _zz_3_[0];
  assign io_mem_cmd_payload_size = _zz_1_[66 : 65];
  assign io_mem_cmd_valid = (dispatcher_dataLoaded && (dispatcher_header == (8'b00000000)));
  assign io_remote_rsp_valid = io_mem_rsp_valid;
  assign io_remote_rsp_payload_error = 1'b0;
  assign io_remote_rsp_payload_data = io_mem_rsp_payload;
  always @ (posedge io_mainClk or posedge resetCtrl_mainClkReset) begin
    if (resetCtrl_mainClkReset) begin
      dispatcher_dataLoaded <= 1'b0;
      dispatcher_headerLoaded <= 1'b0;
      dispatcher_counter <= (3'b000);
    end else begin
      if(io_remote_cmd_valid)begin
        if(_zz_2_)begin
          dispatcher_counter <= (dispatcher_counter + (3'b001));
          if((dispatcher_counter == (3'b111)))begin
            dispatcher_headerLoaded <= 1'b1;
          end
        end
        if(io_remote_cmd_payload_last)begin
          dispatcher_headerLoaded <= 1'b1;
          dispatcher_dataLoaded <= 1'b1;
          dispatcher_counter <= (3'b000);
        end
      end
      if((io_mem_cmd_valid && io_mem_cmd_ready))begin
        dispatcher_headerLoaded <= 1'b0;
        dispatcher_dataLoaded <= 1'b0;
      end
    end
  end

  always @ (posedge io_mainClk) begin
    if(io_remote_cmd_valid)begin
      if(_zz_2_)begin
        dispatcher_headerShifter <= ({io_remote_cmd_payload_fragment,dispatcher_headerShifter} >>> 1);
      end else begin
        dispatcher_dataShifter <= ({io_remote_cmd_payload_fragment,dispatcher_dataShifter} >>> 1);
      end
    end
  end

endmodule

module MuraxSimpleBusRam (
      input   io_bus_cmd_valid,
      output  io_bus_cmd_ready,
      input   io_bus_cmd_payload_wr,
      input  [31:0] io_bus_cmd_payload_address,
      input  [31:0] io_bus_cmd_payload_data,
      input  [3:0] io_bus_cmd_payload_mask,
      output  io_bus_rsp_valid,
      output [31:0] io_bus_rsp_0_data,
      input   io_mainClk,
      input   resetCtrl_systemReset);
  reg [31:0] _zz_4_;
  wire [15:0] _zz_5_;
  reg  _zz_1_;
  wire [29:0] _zz_2_;
  wire [31:0] _zz_3_;
  reg [7:0] ram_symbol0 [0:49151];
  reg [7:0] ram_symbol1 [0:49151];
  reg [7:0] ram_symbol2 [0:49151];
  reg [7:0] ram_symbol3 [0:49151];
  reg [7:0] _zz_6_;
  reg [7:0] _zz_7_;
  reg [7:0] _zz_8_;
  reg [7:0] _zz_9_;
  assign _zz_5_ = _zz_2_[15:0];
  initial begin
    $readmemb("Murax.v_toplevel_system_ram_ram_symbol0.bin",ram_symbol0);
    $readmemb("Murax.v_toplevel_system_ram_ram_symbol1.bin",ram_symbol1);
    $readmemb("Murax.v_toplevel_system_ram_ram_symbol2.bin",ram_symbol2);
    $readmemb("Murax.v_toplevel_system_ram_ram_symbol3.bin",ram_symbol3);
  end
  always @ (*) begin
    _zz_4_ = {_zz_9_, _zz_8_, _zz_7_, _zz_6_};
  end
  always @ (posedge io_mainClk) begin
    if(io_bus_cmd_payload_mask[0] && io_bus_cmd_valid && io_bus_cmd_payload_wr ) begin
      ram_symbol0[_zz_5_] <= _zz_3_[7 : 0];
    end
    if(io_bus_cmd_payload_mask[1] && io_bus_cmd_valid && io_bus_cmd_payload_wr ) begin
      ram_symbol1[_zz_5_] <= _zz_3_[15 : 8];
    end
    if(io_bus_cmd_payload_mask[2] && io_bus_cmd_valid && io_bus_cmd_payload_wr ) begin
      ram_symbol2[_zz_5_] <= _zz_3_[23 : 16];
    end
    if(io_bus_cmd_payload_mask[3] && io_bus_cmd_valid && io_bus_cmd_payload_wr ) begin
      ram_symbol3[_zz_5_] <= _zz_3_[31 : 24];
    end
    if(io_bus_cmd_valid) begin
      _zz_6_ <= ram_symbol0[_zz_5_];
      _zz_7_ <= ram_symbol1[_zz_5_];
      _zz_8_ <= ram_symbol2[_zz_5_];
      _zz_9_ <= ram_symbol3[_zz_5_];
    end
  end

  assign io_bus_rsp_valid = _zz_1_;
  assign _zz_2_ = (io_bus_cmd_payload_address >>> 2);
  assign _zz_3_ = io_bus_cmd_payload_data;
  assign io_bus_rsp_0_data = _zz_4_;
  assign io_bus_cmd_ready = 1'b1;
  always @ (posedge io_mainClk or posedge resetCtrl_systemReset) begin
    if (resetCtrl_systemReset) begin
      _zz_1_ <= 1'b0;
    end else begin
      _zz_1_ <= ((io_bus_cmd_valid && io_bus_cmd_ready) && (! io_bus_cmd_payload_wr));
    end
  end

endmodule

module MuraxSimpleBusToApbBridge (
      input   io_simpleBus_cmd_valid,
      output  io_simpleBus_cmd_ready,
      input   io_simpleBus_cmd_payload_wr,
      input  [31:0] io_simpleBus_cmd_payload_address,
      input  [31:0] io_simpleBus_cmd_payload_data,
      input  [3:0] io_simpleBus_cmd_payload_mask,
      output  io_simpleBus_rsp_valid,
      output [31:0] io_simpleBus_rsp_1_data,
      output [19:0] io_apb_PADDR,
      output [0:0] io_apb_PSEL,
      output  io_apb_PENABLE,
      input   io_apb_PREADY,
      output  io_apb_PWRITE,
      output [31:0] io_apb_PWDATA,
      input  [31:0] io_apb_PRDATA,
      input   io_apb_PSLVERROR,
      input   io_mainClk,
      input   resetCtrl_systemReset);
  wire  _zz_8_;
  wire  _zz_9_;
  wire  simpleBusStage_cmd_valid;
  reg  simpleBusStage_cmd_ready;
  wire  simpleBusStage_cmd_payload_wr;
  wire [31:0] simpleBusStage_cmd_payload_address;
  wire [31:0] simpleBusStage_cmd_payload_data;
  wire [3:0] simpleBusStage_cmd_payload_mask;
  reg  simpleBusStage_rsp_valid;
  wire [31:0] simpleBusStage_rsp_payload_data;
  wire  _zz_1_;
  reg  _zz_2_;
  reg  _zz_3_;
  reg  _zz_4_;
  reg [31:0] _zz_5_;
  reg [31:0] _zz_6_;
  reg [3:0] _zz_7_;
  reg  simpleBusStage_rsp_regNext_valid;
  reg [31:0] simpleBusStage_rsp_regNext_payload_data;
  reg  state;
  assign _zz_8_ = (! state);
  assign _zz_9_ = (! _zz_2_);
  assign io_simpleBus_cmd_ready = _zz_3_;
  assign simpleBusStage_cmd_valid = _zz_2_;
  assign _zz_1_ = simpleBusStage_cmd_ready;
  assign simpleBusStage_cmd_payload_wr = _zz_4_;
  assign simpleBusStage_cmd_payload_address = _zz_5_;
  assign simpleBusStage_cmd_payload_data = _zz_6_;
  assign simpleBusStage_cmd_payload_mask = _zz_7_;
  assign io_simpleBus_rsp_valid = simpleBusStage_rsp_regNext_valid;
  assign io_simpleBus_rsp_1_data = simpleBusStage_rsp_regNext_payload_data;
  always @ (*) begin
    simpleBusStage_cmd_ready = 1'b0;
    simpleBusStage_rsp_valid = 1'b0;
    if(! _zz_8_) begin
      if(io_apb_PREADY)begin
        simpleBusStage_rsp_valid = (! simpleBusStage_cmd_payload_wr);
        simpleBusStage_cmd_ready = 1'b1;
      end
    end
  end

  assign io_apb_PSEL[0] = simpleBusStage_cmd_valid;
  assign io_apb_PENABLE = state;
  assign io_apb_PWRITE = simpleBusStage_cmd_payload_wr;
  assign io_apb_PADDR = simpleBusStage_cmd_payload_address[19:0];
  assign io_apb_PWDATA = simpleBusStage_cmd_payload_data;
  assign simpleBusStage_rsp_payload_data = io_apb_PRDATA;
  always @ (posedge io_mainClk or posedge resetCtrl_systemReset) begin
    if (resetCtrl_systemReset) begin
      _zz_2_ <= 1'b0;
      _zz_3_ <= 1'b1;
      simpleBusStage_rsp_regNext_valid <= 1'b0;
      state <= 1'b0;
    end else begin
      if(_zz_9_)begin
        _zz_2_ <= io_simpleBus_cmd_valid;
        _zz_3_ <= (! io_simpleBus_cmd_valid);
      end else begin
        _zz_2_ <= (! _zz_1_);
        _zz_3_ <= _zz_1_;
      end
      simpleBusStage_rsp_regNext_valid <= simpleBusStage_rsp_valid;
      if(_zz_8_)begin
        state <= simpleBusStage_cmd_valid;
      end else begin
        if(io_apb_PREADY)begin
          state <= 1'b0;
        end
      end
    end
  end

  always @ (posedge io_mainClk) begin
    if(_zz_9_)begin
      _zz_4_ <= io_simpleBus_cmd_payload_wr;
      _zz_5_ <= io_simpleBus_cmd_payload_address;
      _zz_6_ <= io_simpleBus_cmd_payload_data;
      _zz_7_ <= io_simpleBus_cmd_payload_mask;
    end
    simpleBusStage_rsp_regNext_payload_data <= simpleBusStage_rsp_payload_data;
  end

endmodule

module Apb3Gpio (
      input  [3:0] io_apb_PADDR,
      input  [0:0] io_apb_PSEL,
      input   io_apb_PENABLE,
      output  io_apb_PREADY,
      input   io_apb_PWRITE,
      input  [31:0] io_apb_PWDATA,
      output reg [31:0] io_apb_PRDATA,
      output  io_apb_PSLVERROR,
      input  [31:0] io_gpio_read,
      output [31:0] io_gpio_write,
      output [31:0] io_gpio_writeEnable,
      input   io_mainClk,
      input   resetCtrl_systemReset);
  wire  ctrl_askWrite;
  wire  ctrl_askRead;
  wire  ctrl_doWrite;
  wire  ctrl_doRead;
  reg [31:0] _zz_1_;
  reg [31:0] _zz_2_;
  assign io_apb_PREADY = 1'b1;
  always @ (*) begin
    io_apb_PRDATA = (32'b00000000000000000000000000000000);
    case(io_apb_PADDR)
      4'b0000 : begin
        io_apb_PRDATA[31 : 0] = io_gpio_read;
      end
      4'b0100 : begin
        io_apb_PRDATA[31 : 0] = _zz_1_;
      end
      4'b1000 : begin
        io_apb_PRDATA[31 : 0] = _zz_2_;
      end
      default : begin
      end
    endcase
  end

  assign io_apb_PSLVERROR = 1'b0;
  assign ctrl_askWrite = ((io_apb_PSEL[0] && io_apb_PENABLE) && io_apb_PWRITE);
  assign ctrl_askRead = ((io_apb_PSEL[0] && io_apb_PENABLE) && (! io_apb_PWRITE));
  assign ctrl_doWrite = (((io_apb_PSEL[0] && io_apb_PENABLE) && io_apb_PREADY) && io_apb_PWRITE);
  assign ctrl_doRead = (((io_apb_PSEL[0] && io_apb_PENABLE) && io_apb_PREADY) && (! io_apb_PWRITE));
  assign io_gpio_write = _zz_1_;
  assign io_gpio_writeEnable = _zz_2_;
  always @ (posedge io_mainClk or posedge resetCtrl_systemReset) begin
    if (resetCtrl_systemReset) begin
      _zz_2_ <= (32'b00000000000000000000000000000000);
    end else begin
      case(io_apb_PADDR)
        4'b0000 : begin
        end
        4'b0100 : begin
        end
        4'b1000 : begin
          if(ctrl_doWrite)begin
            _zz_2_ <= io_apb_PWDATA[31 : 0];
          end
        end
        default : begin
        end
      endcase
    end
  end

  always @ (posedge io_mainClk) begin
    case(io_apb_PADDR)
      4'b0000 : begin
      end
      4'b0100 : begin
        if(ctrl_doWrite)begin
          _zz_1_ <= io_apb_PWDATA[31 : 0];
        end
      end
      4'b1000 : begin
      end
      default : begin
      end
    endcase
  end

endmodule

module Apb3UartCtrl (
      input  [3:0] io_apb_PADDR,
      input  [0:0] io_apb_PSEL,
      input   io_apb_PENABLE,
      output  io_apb_PREADY,
      input   io_apb_PWRITE,
      input  [31:0] io_apb_PWDATA,
      output reg [31:0] io_apb_PRDATA,
      output  io_uart_txd,
      input   io_uart_rxd,
      output  io_interrupt,
      input   io_mainClk,
      input   resetCtrl_systemReset);
  wire  _zz_3_;
  reg  _zz_4_;
  wire  _zz_5_;
  wire  _zz_6_;
  wire  _zz_7_;
  wire [7:0] _zz_8_;
  wire  _zz_9_;
  wire  _zz_10_;
  wire  _zz_11_;
  wire [7:0] _zz_12_;
  wire [4:0] _zz_13_;
  wire [4:0] _zz_14_;
  wire  _zz_15_;
  wire  _zz_16_;
  wire [7:0] _zz_17_;
  wire [4:0] _zz_18_;
  wire [4:0] _zz_19_;
  wire [0:0] _zz_20_;
  wire [0:0] _zz_21_;
  wire [4:0] _zz_22_;
  wire  busCtrl_askWrite;
  wire  busCtrl_askRead;
  wire  busCtrl_doWrite;
  wire  busCtrl_doRead;
  wire [2:0] bridge_uartConfigReg_frame_dataLength;
  wire `UartStopType_defaultEncoding_type bridge_uartConfigReg_frame_stop;
  wire `UartParityType_defaultEncoding_type bridge_uartConfigReg_frame_parity;
  reg [19:0] bridge_uartConfigReg_clockDivider;
  reg  _zz_1_;
  wire  bridge_write_streamUnbuffered_valid;
  wire  bridge_write_streamUnbuffered_ready;
  wire [7:0] bridge_write_streamUnbuffered_payload;
  reg  bridge_interruptCtrl_writeIntEnable;
  reg  bridge_interruptCtrl_readIntEnable;
  wire  bridge_interruptCtrl_readInt;
  wire  bridge_interruptCtrl_writeInt;
  wire  bridge_interruptCtrl_interrupt;
  wire [7:0] _zz_2_;
  function [19:0] zz_bridge_uartConfigReg_clockDivider(input dummy);
    begin
      zz_bridge_uartConfigReg_clockDivider = (20'b00000000000000000000);
      zz_bridge_uartConfigReg_clockDivider = (20'b00000000000001010101);
    end
  endfunction
  wire [19:0] _zz_23_;
  assign _zz_20_ = io_apb_PWDATA[0 : 0];
  assign _zz_21_ = io_apb_PWDATA[1 : 1];
  assign _zz_22_ = ((5'b10000) - _zz_13_);
  UartCtrl uartCtrl_1_ ( 
    .io_config_frame_dataLength(bridge_uartConfigReg_frame_dataLength),
    .io_config_frame_stop(bridge_uartConfigReg_frame_stop),
    .io_config_frame_parity(bridge_uartConfigReg_frame_parity),
    .io_config_clockDivider(bridge_uartConfigReg_clockDivider),
    .io_write_valid(_zz_11_),
    .io_write_ready(_zz_6_),
    .io_write_payload(_zz_12_),
    .io_read_valid(_zz_7_),
    .io_read_payload(_zz_8_),
    .io_uart_txd(_zz_9_),
    .io_uart_rxd(io_uart_rxd),
    .io_mainClk(io_mainClk),
    .resetCtrl_systemReset(resetCtrl_systemReset) 
  );
  StreamFifo streamFifo_2_ ( 
    .io_push_valid(bridge_write_streamUnbuffered_valid),
    .io_push_ready(_zz_10_),
    .io_push_payload(bridge_write_streamUnbuffered_payload),
    .io_pop_valid(_zz_11_),
    .io_pop_ready(_zz_6_),
    .io_pop_payload(_zz_12_),
    .io_flush(_zz_3_),
    .io_occupancy(_zz_13_),
    .io_availability(_zz_14_),
    .io_mainClk(io_mainClk),
    .resetCtrl_systemReset(resetCtrl_systemReset) 
  );
  StreamFifo streamFifo_3_ ( 
    .io_push_valid(_zz_7_),
    .io_push_ready(_zz_15_),
    .io_push_payload(_zz_8_),
    .io_pop_valid(_zz_16_),
    .io_pop_ready(_zz_4_),
    .io_pop_payload(_zz_17_),
    .io_flush(_zz_5_),
    .io_occupancy(_zz_18_),
    .io_availability(_zz_19_),
    .io_mainClk(io_mainClk),
    .resetCtrl_systemReset(resetCtrl_systemReset) 
  );
  assign io_uart_txd = _zz_9_;
  assign io_apb_PREADY = 1'b1;
  always @ (*) begin
    io_apb_PRDATA = (32'b00000000000000000000000000000000);
    _zz_1_ = 1'b0;
    _zz_4_ = 1'b0;
    case(io_apb_PADDR)
      4'b0000 : begin
        if(busCtrl_doWrite)begin
          _zz_1_ = 1'b1;
        end
        if(busCtrl_doRead)begin
          _zz_4_ = 1'b1;
        end
        io_apb_PRDATA[16 : 16] = _zz_16_;
        io_apb_PRDATA[7 : 0] = _zz_17_;
      end
      4'b0100 : begin
        io_apb_PRDATA[20 : 16] = _zz_22_;
        io_apb_PRDATA[28 : 24] = _zz_18_;
        io_apb_PRDATA[0 : 0] = bridge_interruptCtrl_writeIntEnable;
        io_apb_PRDATA[1 : 1] = bridge_interruptCtrl_readIntEnable;
        io_apb_PRDATA[8 : 8] = bridge_interruptCtrl_writeInt;
        io_apb_PRDATA[9 : 9] = bridge_interruptCtrl_readInt;
      end
      default : begin
      end
    endcase
  end

  assign busCtrl_askWrite = ((io_apb_PSEL[0] && io_apb_PENABLE) && io_apb_PWRITE);
  assign busCtrl_askRead = ((io_apb_PSEL[0] && io_apb_PENABLE) && (! io_apb_PWRITE));
  assign busCtrl_doWrite = (((io_apb_PSEL[0] && io_apb_PENABLE) && io_apb_PREADY) && io_apb_PWRITE);
  assign busCtrl_doRead = (((io_apb_PSEL[0] && io_apb_PENABLE) && io_apb_PREADY) && (! io_apb_PWRITE));
  assign _zz_23_ = zz_bridge_uartConfigReg_clockDivider(1'b0);
  always @ (*) bridge_uartConfigReg_clockDivider = _zz_23_;
  assign bridge_uartConfigReg_frame_dataLength = (3'b111);
  assign bridge_uartConfigReg_frame_parity = `UartParityType_defaultEncoding_NONE;
  assign bridge_uartConfigReg_frame_stop = `UartStopType_defaultEncoding_ONE;
  assign bridge_write_streamUnbuffered_valid = _zz_1_;
  assign bridge_write_streamUnbuffered_payload = _zz_2_;
  assign bridge_write_streamUnbuffered_ready = _zz_10_;
  assign bridge_interruptCtrl_readInt = (bridge_interruptCtrl_readIntEnable && _zz_16_);
  assign bridge_interruptCtrl_writeInt = (bridge_interruptCtrl_writeIntEnable && (! _zz_11_));
  assign bridge_interruptCtrl_interrupt = (bridge_interruptCtrl_readInt || bridge_interruptCtrl_writeInt);
  assign io_interrupt = bridge_interruptCtrl_interrupt;
  assign _zz_2_ = io_apb_PWDATA[7 : 0];
  assign _zz_3_ = 1'b0;
  assign _zz_5_ = 1'b0;
  always @ (posedge io_mainClk or posedge resetCtrl_systemReset) begin
    if (resetCtrl_systemReset) begin
      bridge_interruptCtrl_writeIntEnable <= 1'b0;
      bridge_interruptCtrl_readIntEnable <= 1'b0;
    end else begin
      case(io_apb_PADDR)
        4'b0000 : begin
        end
        4'b0100 : begin
          if(busCtrl_doWrite)begin
            bridge_interruptCtrl_writeIntEnable <= _zz_20_[0];
            bridge_interruptCtrl_readIntEnable <= _zz_21_[0];
          end
        end
        default : begin
        end
      endcase
    end
  end

endmodule

module MuraxApb3Timer (
      input  [7:0] io_apb_PADDR,
      input  [0:0] io_apb_PSEL,
      input   io_apb_PENABLE,
      output  io_apb_PREADY,
      input   io_apb_PWRITE,
      input  [31:0] io_apb_PWDATA,
      output reg [31:0] io_apb_PRDATA,
      output  io_apb_PSLVERROR,
      output  io_interrupt,
      input   io_mainClk,
      input   resetCtrl_systemReset);
  wire  _zz_10_;
  wire  _zz_11_;
  wire  _zz_12_;
  wire  _zz_13_;
  reg [1:0] _zz_14_;
  reg [1:0] _zz_15_;
  wire  _zz_16_;
  wire  _zz_17_;
  wire [15:0] _zz_18_;
  wire  _zz_19_;
  wire [15:0] _zz_20_;
  wire [1:0] _zz_21_;
  wire  busCtrl_askWrite;
  wire  busCtrl_askRead;
  wire  busCtrl_doWrite;
  wire  busCtrl_doRead;
  reg [15:0] _zz_1_;
  reg  _zz_2_;
  reg [1:0] timerABridge_ticksEnable;
  reg [0:0] timerABridge_clearsEnable;
  reg  timerABridge_busClearing;
  reg [15:0] _zz_3_;
  reg  _zz_4_;
  reg  _zz_5_;
  reg [1:0] timerBBridge_ticksEnable;
  reg [0:0] timerBBridge_clearsEnable;
  reg  timerBBridge_busClearing;
  reg [15:0] _zz_6_;
  reg  _zz_7_;
  reg  _zz_8_;
  reg [1:0] _zz_9_;
  Prescaler prescaler_1_ ( 
    .io_clear(_zz_2_),
    .io_limit(_zz_1_),
    .io_overflow(_zz_16_),
    .io_mainClk(io_mainClk),
    .resetCtrl_systemReset(resetCtrl_systemReset) 
  );
  Timer timerA ( 
    .io_tick(_zz_10_),
    .io_clear(_zz_11_),
    .io_limit(_zz_3_),
    .io_full(_zz_17_),
    .io_value(_zz_18_),
    .io_mainClk(io_mainClk),
    .resetCtrl_systemReset(resetCtrl_systemReset) 
  );
  Timer timerB ( 
    .io_tick(_zz_12_),
    .io_clear(_zz_13_),
    .io_limit(_zz_6_),
    .io_full(_zz_19_),
    .io_value(_zz_20_),
    .io_mainClk(io_mainClk),
    .resetCtrl_systemReset(resetCtrl_systemReset) 
  );
  InterruptCtrl interruptCtrl_1_ ( 
    .io_inputs(_zz_14_),
    .io_clears(_zz_15_),
    .io_masks(_zz_9_),
    .io_pendings(_zz_21_),
    .io_mainClk(io_mainClk),
    .resetCtrl_systemReset(resetCtrl_systemReset) 
  );
  assign io_apb_PREADY = 1'b1;
  always @ (*) begin
    io_apb_PRDATA = (32'b00000000000000000000000000000000);
    _zz_2_ = 1'b0;
    _zz_4_ = 1'b0;
    _zz_5_ = 1'b0;
    _zz_7_ = 1'b0;
    _zz_8_ = 1'b0;
    _zz_15_ = (2'b00);
    case(io_apb_PADDR)
      8'b00000000 : begin
        if(busCtrl_doWrite)begin
          _zz_2_ = 1'b1;
        end
        io_apb_PRDATA[15 : 0] = _zz_1_;
      end
      8'b01000000 : begin
        io_apb_PRDATA[1 : 0] = timerABridge_ticksEnable;
        io_apb_PRDATA[16 : 16] = timerABridge_clearsEnable;
      end
      8'b01000100 : begin
        if(busCtrl_doWrite)begin
          _zz_4_ = 1'b1;
        end
        io_apb_PRDATA[15 : 0] = _zz_3_;
      end
      8'b01001000 : begin
        if(busCtrl_doWrite)begin
          _zz_5_ = 1'b1;
        end
        io_apb_PRDATA[15 : 0] = _zz_18_;
      end
      8'b01010000 : begin
        io_apb_PRDATA[1 : 0] = timerBBridge_ticksEnable;
        io_apb_PRDATA[16 : 16] = timerBBridge_clearsEnable;
      end
      8'b01010100 : begin
        if(busCtrl_doWrite)begin
          _zz_7_ = 1'b1;
        end
        io_apb_PRDATA[15 : 0] = _zz_6_;
      end
      8'b01011000 : begin
        if(busCtrl_doWrite)begin
          _zz_8_ = 1'b1;
        end
        io_apb_PRDATA[15 : 0] = _zz_20_;
      end
      8'b00010000 : begin
        if(busCtrl_doWrite)begin
          _zz_15_ = io_apb_PWDATA[1 : 0];
        end
        io_apb_PRDATA[1 : 0] = _zz_21_;
      end
      8'b00010100 : begin
        io_apb_PRDATA[1 : 0] = _zz_9_;
      end
      default : begin
      end
    endcase
  end

  assign io_apb_PSLVERROR = 1'b0;
  assign busCtrl_askWrite = ((io_apb_PSEL[0] && io_apb_PENABLE) && io_apb_PWRITE);
  assign busCtrl_askRead = ((io_apb_PSEL[0] && io_apb_PENABLE) && (! io_apb_PWRITE));
  assign busCtrl_doWrite = (((io_apb_PSEL[0] && io_apb_PENABLE) && io_apb_PREADY) && io_apb_PWRITE);
  assign busCtrl_doRead = (((io_apb_PSEL[0] && io_apb_PENABLE) && io_apb_PREADY) && (! io_apb_PWRITE));
  always @ (*) begin
    timerABridge_busClearing = 1'b0;
    if(_zz_4_)begin
      timerABridge_busClearing = 1'b1;
    end
    if(_zz_5_)begin
      timerABridge_busClearing = 1'b1;
    end
  end

  assign _zz_11_ = (((timerABridge_clearsEnable & _zz_17_) != (1'b0)) || timerABridge_busClearing);
  assign _zz_10_ = ((timerABridge_ticksEnable & {_zz_16_,1'b1}) != (2'b00));
  always @ (*) begin
    timerBBridge_busClearing = 1'b0;
    if(_zz_7_)begin
      timerBBridge_busClearing = 1'b1;
    end
    if(_zz_8_)begin
      timerBBridge_busClearing = 1'b1;
    end
  end

  assign _zz_13_ = (((timerBBridge_clearsEnable & _zz_19_) != (1'b0)) || timerBBridge_busClearing);
  assign _zz_12_ = ((timerBBridge_ticksEnable & {_zz_16_,1'b1}) != (2'b00));
  always @ (*) begin
    _zz_14_[0] = _zz_17_;
    _zz_14_[1] = _zz_19_;
  end

  assign io_interrupt = (_zz_21_ != (2'b00));
  always @ (posedge io_mainClk or posedge resetCtrl_systemReset) begin
    if (resetCtrl_systemReset) begin
      timerABridge_ticksEnable <= (2'b00);
      timerABridge_clearsEnable <= (1'b0);
      timerBBridge_ticksEnable <= (2'b00);
      timerBBridge_clearsEnable <= (1'b0);
      _zz_9_ <= (2'b00);
    end else begin
      case(io_apb_PADDR)
        8'b00000000 : begin
        end
        8'b01000000 : begin
          if(busCtrl_doWrite)begin
            timerABridge_ticksEnable <= io_apb_PWDATA[1 : 0];
            timerABridge_clearsEnable <= io_apb_PWDATA[16 : 16];
          end
        end
        8'b01000100 : begin
        end
        8'b01001000 : begin
        end
        8'b01010000 : begin
          if(busCtrl_doWrite)begin
            timerBBridge_ticksEnable <= io_apb_PWDATA[1 : 0];
            timerBBridge_clearsEnable <= io_apb_PWDATA[16 : 16];
          end
        end
        8'b01010100 : begin
        end
        8'b01011000 : begin
        end
        8'b00010000 : begin
        end
        8'b00010100 : begin
          if(busCtrl_doWrite)begin
            _zz_9_ <= io_apb_PWDATA[1 : 0];
          end
        end
        default : begin
        end
      endcase
    end
  end

  always @ (posedge io_mainClk) begin
    case(io_apb_PADDR)
      8'b00000000 : begin
        if(busCtrl_doWrite)begin
          _zz_1_ <= io_apb_PWDATA[15 : 0];
        end
      end
      8'b01000000 : begin
      end
      8'b01000100 : begin
        if(busCtrl_doWrite)begin
          _zz_3_ <= io_apb_PWDATA[15 : 0];
        end
      end
      8'b01001000 : begin
      end
      8'b01010000 : begin
      end
      8'b01010100 : begin
        if(busCtrl_doWrite)begin
          _zz_6_ <= io_apb_PWDATA[15 : 0];
        end
      end
      8'b01011000 : begin
      end
      8'b00010000 : begin
      end
      8'b00010100 : begin
      end
      default : begin
      end
    endcase
  end

endmodule

module Apb3Decoder (
      input  [19:0] io_input_PADDR,
      input  [0:0] io_input_PSEL,
      input   io_input_PENABLE,
      output reg  io_input_PREADY,
      input   io_input_PWRITE,
      input  [31:0] io_input_PWDATA,
      output [31:0] io_input_PRDATA,
      output reg  io_input_PSLVERROR,
      output [19:0] io_output_PADDR,
      output reg [2:0] io_output_PSEL,
      output  io_output_PENABLE,
      input   io_output_PREADY,
      output  io_output_PWRITE,
      output [31:0] io_output_PWDATA,
      input  [31:0] io_output_PRDATA,
      input   io_output_PSLVERROR);
  wire [19:0] _zz_1_;
  wire [19:0] _zz_2_;
  wire [19:0] _zz_3_;
  assign _zz_1_ = (20'b11111111000000000000);
  assign _zz_2_ = (20'b11111111000000000000);
  assign _zz_3_ = (20'b11111111000000000000);
  assign io_output_PADDR = io_input_PADDR;
  assign io_output_PENABLE = io_input_PENABLE;
  assign io_output_PWRITE = io_input_PWRITE;
  assign io_output_PWDATA = io_input_PWDATA;
  always @ (*) begin
    io_output_PSEL[0] = (((io_input_PADDR & _zz_1_) == (20'b00000000000000000000)) && io_input_PSEL[0]);
    io_output_PSEL[1] = (((io_input_PADDR & _zz_2_) == (20'b00010000000000000000)) && io_input_PSEL[0]);
    io_output_PSEL[2] = (((io_input_PADDR & _zz_3_) == (20'b00100000000000000000)) && io_input_PSEL[0]);
  end

  always @ (*) begin
    io_input_PREADY = io_output_PREADY;
    io_input_PSLVERROR = io_output_PSLVERROR;
    if((io_input_PSEL[0] && (io_output_PSEL == (3'b000))))begin
      io_input_PREADY = 1'b1;
      io_input_PSLVERROR = 1'b1;
    end
  end

  assign io_input_PRDATA = io_output_PRDATA;
endmodule

module Apb3Router (
      input  [19:0] io_input_PADDR,
      input  [2:0] io_input_PSEL,
      input   io_input_PENABLE,
      output  io_input_PREADY,
      input   io_input_PWRITE,
      input  [31:0] io_input_PWDATA,
      output [31:0] io_input_PRDATA,
      output  io_input_PSLVERROR,
      output [19:0] io_outputs_0_PADDR,
      output [0:0] io_outputs_0_PSEL,
      output  io_outputs_0_PENABLE,
      input   io_outputs_0_PREADY,
      output  io_outputs_0_PWRITE,
      output [31:0] io_outputs_0_PWDATA,
      input  [31:0] io_outputs_0_PRDATA,
      input   io_outputs_0_PSLVERROR,
      output [19:0] io_outputs_1_PADDR,
      output [0:0] io_outputs_1_PSEL,
      output  io_outputs_1_PENABLE,
      input   io_outputs_1_PREADY,
      output  io_outputs_1_PWRITE,
      output [31:0] io_outputs_1_PWDATA,
      input  [31:0] io_outputs_1_PRDATA,
      input   io_outputs_1_PSLVERROR,
      output [19:0] io_outputs_2_PADDR,
      output [0:0] io_outputs_2_PSEL,
      output  io_outputs_2_PENABLE,
      input   io_outputs_2_PREADY,
      output  io_outputs_2_PWRITE,
      output [31:0] io_outputs_2_PWDATA,
      input  [31:0] io_outputs_2_PRDATA,
      input   io_outputs_2_PSLVERROR,
      input   io_mainClk,
      input   resetCtrl_systemReset);
  reg  _zz_3_;
  reg [31:0] _zz_4_;
  reg  _zz_5_;
  wire  _zz_1_;
  wire  _zz_2_;
  reg [1:0] selIndex;
  always @(*) begin
    case(selIndex)
      2'b00 : begin
        _zz_3_ = io_outputs_0_PREADY;
        _zz_4_ = io_outputs_0_PRDATA;
        _zz_5_ = io_outputs_0_PSLVERROR;
      end
      2'b01 : begin
        _zz_3_ = io_outputs_1_PREADY;
        _zz_4_ = io_outputs_1_PRDATA;
        _zz_5_ = io_outputs_1_PSLVERROR;
      end
      default : begin
        _zz_3_ = io_outputs_2_PREADY;
        _zz_4_ = io_outputs_2_PRDATA;
        _zz_5_ = io_outputs_2_PSLVERROR;
      end
    endcase
  end

  assign io_outputs_0_PADDR = io_input_PADDR;
  assign io_outputs_0_PENABLE = io_input_PENABLE;
  assign io_outputs_0_PSEL[0] = io_input_PSEL[0];
  assign io_outputs_0_PWRITE = io_input_PWRITE;
  assign io_outputs_0_PWDATA = io_input_PWDATA;
  assign io_outputs_1_PADDR = io_input_PADDR;
  assign io_outputs_1_PENABLE = io_input_PENABLE;
  assign io_outputs_1_PSEL[0] = io_input_PSEL[1];
  assign io_outputs_1_PWRITE = io_input_PWRITE;
  assign io_outputs_1_PWDATA = io_input_PWDATA;
  assign io_outputs_2_PADDR = io_input_PADDR;
  assign io_outputs_2_PENABLE = io_input_PENABLE;
  assign io_outputs_2_PSEL[0] = io_input_PSEL[2];
  assign io_outputs_2_PWRITE = io_input_PWRITE;
  assign io_outputs_2_PWDATA = io_input_PWDATA;
  assign _zz_1_ = io_input_PSEL[1];
  assign _zz_2_ = io_input_PSEL[2];
  assign io_input_PREADY = _zz_3_;
  assign io_input_PRDATA = _zz_4_;
  assign io_input_PSLVERROR = _zz_5_;
  always @ (posedge io_mainClk) begin
    selIndex <= {_zz_2_,_zz_1_};
  end

endmodule

module Murax (
      input   io_asyncReset,
      input   io_mainClk,
      input   io_jtag_tms,
      input   io_jtag_tdi,
      output  io_jtag_tdo,
      input   io_jtag_tck,
      input  [31:0] io_gpioA_read,
      output [31:0] io_gpioA_write,
      output [31:0] io_gpioA_writeEnable,
      output  io_uart_txd,
      input   io_uart_rxd);
  wire [7:0] _zz_10_;
  reg  _zz_11_;
  reg  _zz_12_;
  wire [3:0] _zz_13_;
  wire [3:0] _zz_14_;
  wire [7:0] _zz_15_;
  wire  _zz_16_;
  reg [31:0] _zz_17_;
  wire  _zz_18_;
  wire  _zz_19_;
  wire  _zz_20_;
  wire  _zz_21_;
  wire [31:0] _zz_22_;
  wire  _zz_23_;
  wire  _zz_24_;
  wire  _zz_25_;
  wire [31:0] _zz_26_;
  wire  _zz_27_;
  wire  _zz_28_;
  wire [31:0] _zz_29_;
  wire [31:0] _zz_30_;
  wire [3:0] _zz_31_;
  wire  _zz_32_;
  wire [31:0] _zz_33_;
  wire  _zz_34_;
  wire [31:0] _zz_35_;
  wire  _zz_36_;
  wire  _zz_37_;
  wire  _zz_38_;
  wire [31:0] _zz_39_;
  wire [31:0] _zz_40_;
  wire [1:0] _zz_41_;
  wire  _zz_42_;
  wire  _zz_43_;
  wire  _zz_44_;
  wire [0:0] _zz_45_;
  wire  _zz_46_;
  wire  _zz_47_;
  wire  _zz_48_;
  wire  _zz_49_;
  wire [31:0] _zz_50_;
  wire  _zz_51_;
  wire [31:0] _zz_52_;
  wire [31:0] _zz_53_;
  wire  _zz_54_;
  wire [1:0] _zz_55_;
  wire  _zz_56_;
  wire  _zz_57_;
  wire [31:0] _zz_58_;
  wire  _zz_59_;
  wire  _zz_60_;
  wire [31:0] _zz_61_;
  wire [19:0] _zz_62_;
  wire [0:0] _zz_63_;
  wire  _zz_64_;
  wire  _zz_65_;
  wire [31:0] _zz_66_;
  wire  _zz_67_;
  wire [31:0] _zz_68_;
  wire  _zz_69_;
  wire [31:0] _zz_70_;
  wire [31:0] _zz_71_;
  wire  _zz_72_;
  wire [31:0] _zz_73_;
  wire  _zz_74_;
  wire  _zz_75_;
  wire  _zz_76_;
  wire [31:0] _zz_77_;
  wire  _zz_78_;
  wire  _zz_79_;
  wire  _zz_80_;
  wire [31:0] _zz_81_;
  wire  _zz_82_;
  wire [19:0] _zz_83_;
  wire [2:0] _zz_84_;
  wire  _zz_85_;
  wire  _zz_86_;
  wire [31:0] _zz_87_;
  wire  _zz_88_;
  wire [31:0] _zz_89_;
  wire  _zz_90_;
  wire [19:0] _zz_91_;
  wire [0:0] _zz_92_;
  wire  _zz_93_;
  wire  _zz_94_;
  wire [31:0] _zz_95_;
  wire [19:0] _zz_96_;
  wire [0:0] _zz_97_;
  wire  _zz_98_;
  wire  _zz_99_;
  wire [31:0] _zz_100_;
  wire [19:0] _zz_101_;
  wire [0:0] _zz_102_;
  wire  _zz_103_;
  wire  _zz_104_;
  wire [31:0] _zz_105_;
  wire  _zz_106_;
  wire  _zz_107_;
  wire [31:0] _zz_108_;
  reg  resetCtrl_mainClkResetUnbuffered;
  reg [5:0] resetCtrl_systemClkResetCounter = (6'b000000);
  wire [5:0] _zz_1_;
  reg  resetCtrl_mainClkReset;
  reg  resetCtrl_systemReset;
  reg  system_timerInterrupt;
  reg  system_externalInterrupt;
  wire  _zz_2_;
  reg  _zz_3_;
  reg  _zz_4_;
  reg  _zz_5_;
  reg [31:0] _zz_6_;
  reg [31:0] _zz_7_;
  reg [1:0] _zz_8_;
  reg  debug_resetOut_regNext;
  reg  _zz_9_;
  wire  system_mainBusDecoder_logic_masterPipelined_cmd_valid;
  reg  system_mainBusDecoder_logic_masterPipelined_cmd_ready;
  wire  system_mainBusDecoder_logic_masterPipelined_cmd_payload_wr;
  wire [31:0] system_mainBusDecoder_logic_masterPipelined_cmd_payload_address;
  wire [31:0] system_mainBusDecoder_logic_masterPipelined_cmd_payload_data;
  wire [3:0] system_mainBusDecoder_logic_masterPipelined_cmd_payload_mask;
  wire  system_mainBusDecoder_logic_masterPipelined_rsp_valid;
  wire [31:0] system_mainBusDecoder_logic_masterPipelined_rsp_payload_data;
  wire  system_mainBusDecoder_logic_hits_0;
  wire  system_mainBusDecoder_logic_hits_1;
  wire  system_mainBusDecoder_logic_noHit;
  reg  system_mainBusDecoder_logic_rspPending;
  reg  system_mainBusDecoder_logic_rspNoHit;
  reg [0:0] system_mainBusDecoder_logic_rspSourceId;
  assign _zz_106_ = (resetCtrl_systemClkResetCounter != _zz_1_);
  assign _zz_107_ = (! _zz_3_);
  assign _zz_108_ = (32'b11111111111100000000000000000000);
  BufferCC_2_ bufferCC_3_ ( 
    .io_dataIn(io_asyncReset),
    .io_dataOut(_zz_18_),
    .io_mainClk(io_mainClk) 
  );
  MuraxMasterArbiter system_mainBusArbiter ( 
    .io_iBus_cmd_valid(_zz_32_),
    .io_iBus_cmd_ready(_zz_19_),
    .io_iBus_cmd_payload_pc(_zz_33_),
    .io_iBus_rsp_valid(_zz_20_),
    .io_iBus_rsp_payload_error(_zz_21_),
    .io_iBus_rsp_payload_inst(_zz_22_),
    .io_dBus_cmd_valid(_zz_3_),
    .io_dBus_cmd_ready(_zz_23_),
    .io_dBus_cmd_payload_wr(_zz_5_),
    .io_dBus_cmd_payload_address(_zz_6_),
    .io_dBus_cmd_payload_data(_zz_7_),
    .io_dBus_cmd_payload_size(_zz_8_),
    .io_dBus_rsp_ready(_zz_24_),
    .io_dBus_rsp_error(_zz_25_),
    .io_dBus_rsp_data(_zz_26_),
    .io_masterBus_cmd_valid(_zz_27_),
    .io_masterBus_cmd_ready(system_mainBusDecoder_logic_masterPipelined_cmd_ready),
    .io_masterBus_cmd_payload_wr(_zz_28_),
    .io_masterBus_cmd_payload_address(_zz_29_),
    .io_masterBus_cmd_payload_data(_zz_30_),
    .io_masterBus_cmd_payload_mask(_zz_31_),
    .io_masterBus_rsp_valid(system_mainBusDecoder_logic_masterPipelined_rsp_valid),
    .io_masterBus_rsp_payload_data(system_mainBusDecoder_logic_masterPipelined_rsp_payload_data),
    .io_mainClk(io_mainClk),
    .resetCtrl_systemReset(resetCtrl_systemReset) 
  );
  VexRiscv system_cpu ( 
    .iBus_cmd_valid(_zz_32_),
    .iBus_cmd_ready(_zz_19_),
    .iBus_cmd_payload_pc(_zz_33_),
    .iBus_rsp_valid(_zz_20_),
    .iBus_rsp_payload_error(_zz_21_),
    .iBus_rsp_payload_inst(_zz_22_),
    .timerInterrupt(system_timerInterrupt),
    .externalInterrupt(system_externalInterrupt),
    .debug_bus_cmd_valid(_zz_51_),
    .debug_bus_cmd_ready(_zz_34_),
    .debug_bus_cmd_payload_wr(_zz_54_),
    .debug_bus_cmd_payload_address(_zz_10_),
    .debug_bus_cmd_payload_data(_zz_53_),
    .debug_bus_rsp_data(_zz_35_),
    .debug_resetOut(_zz_36_),
    .dBus_cmd_valid(_zz_37_),
    .dBus_cmd_ready(_zz_4_),
    .dBus_cmd_payload_wr(_zz_38_),
    .dBus_cmd_payload_address(_zz_39_),
    .dBus_cmd_payload_data(_zz_40_),
    .dBus_cmd_payload_size(_zz_41_),
    .dBus_rsp_ready(_zz_24_),
    .dBus_rsp_error(_zz_25_),
    .dBus_rsp_data(_zz_26_),
    .io_mainClk(io_mainClk),
    .resetCtrl_systemReset(resetCtrl_systemReset),
    .resetCtrl_mainClkReset(resetCtrl_mainClkReset) 
  );
  JtagBridge jtagBridge_1_ ( 
    .io_jtag_tms(io_jtag_tms),
    .io_jtag_tdi(io_jtag_tdi),
    .io_jtag_tdo(_zz_42_),
    .io_jtag_tck(io_jtag_tck),
    .io_remote_cmd_valid(_zz_43_),
    .io_remote_cmd_ready(_zz_47_),
    .io_remote_cmd_payload_last(_zz_44_),
    .io_remote_cmd_payload_fragment(_zz_45_),
    .io_remote_rsp_valid(_zz_48_),
    .io_remote_rsp_ready(_zz_46_),
    .io_remote_rsp_payload_error(_zz_49_),
    .io_remote_rsp_payload_data(_zz_50_),
    .io_mainClk(io_mainClk),
    .resetCtrl_mainClkReset(resetCtrl_mainClkReset) 
  );
  SystemDebugger systemDebugger_1_ ( 
    .io_remote_cmd_valid(_zz_43_),
    .io_remote_cmd_ready(_zz_47_),
    .io_remote_cmd_payload_last(_zz_44_),
    .io_remote_cmd_payload_fragment(_zz_45_),
    .io_remote_rsp_valid(_zz_48_),
    .io_remote_rsp_ready(_zz_46_),
    .io_remote_rsp_payload_error(_zz_49_),
    .io_remote_rsp_payload_data(_zz_50_),
    .io_mem_cmd_valid(_zz_51_),
    .io_mem_cmd_ready(_zz_34_),
    .io_mem_cmd_payload_address(_zz_52_),
    .io_mem_cmd_payload_data(_zz_53_),
    .io_mem_cmd_payload_wr(_zz_54_),
    .io_mem_cmd_payload_size(_zz_55_),
    .io_mem_rsp_valid(_zz_9_),
    .io_mem_rsp_payload(_zz_35_),
    .io_mainClk(io_mainClk),
    .resetCtrl_mainClkReset(resetCtrl_mainClkReset) 
  );
  MuraxSimpleBusRam system_ram ( 
    .io_bus_cmd_valid(_zz_11_),
    .io_bus_cmd_ready(_zz_56_),
    .io_bus_cmd_payload_wr(system_mainBusDecoder_logic_masterPipelined_cmd_payload_wr),
    .io_bus_cmd_payload_address(system_mainBusDecoder_logic_masterPipelined_cmd_payload_address),
    .io_bus_cmd_payload_data(system_mainBusDecoder_logic_masterPipelined_cmd_payload_data),
    .io_bus_cmd_payload_mask(system_mainBusDecoder_logic_masterPipelined_cmd_payload_mask),
    .io_bus_rsp_valid(_zz_57_),
    .io_bus_rsp_0_data(_zz_58_),
    .io_mainClk(io_mainClk),
    .resetCtrl_systemReset(resetCtrl_systemReset) 
  );
  MuraxSimpleBusToApbBridge system_apbBridge ( 
    .io_simpleBus_cmd_valid(_zz_12_),
    .io_simpleBus_cmd_ready(_zz_59_),
    .io_simpleBus_cmd_payload_wr(system_mainBusDecoder_logic_masterPipelined_cmd_payload_wr),
    .io_simpleBus_cmd_payload_address(system_mainBusDecoder_logic_masterPipelined_cmd_payload_address),
    .io_simpleBus_cmd_payload_data(system_mainBusDecoder_logic_masterPipelined_cmd_payload_data),
    .io_simpleBus_cmd_payload_mask(system_mainBusDecoder_logic_masterPipelined_cmd_payload_mask),
    .io_simpleBus_rsp_valid(_zz_60_),
    .io_simpleBus_rsp_1_data(_zz_61_),
    .io_apb_PADDR(_zz_62_),
    .io_apb_PSEL(_zz_63_),
    .io_apb_PENABLE(_zz_64_),
    .io_apb_PREADY(_zz_80_),
    .io_apb_PWRITE(_zz_65_),
    .io_apb_PWDATA(_zz_66_),
    .io_apb_PRDATA(_zz_81_),
    .io_apb_PSLVERROR(_zz_82_),
    .io_mainClk(io_mainClk),
    .resetCtrl_systemReset(resetCtrl_systemReset) 
  );
  Apb3Gpio system_gpioACtrl ( 
    .io_apb_PADDR(_zz_13_),
    .io_apb_PSEL(_zz_92_),
    .io_apb_PENABLE(_zz_93_),
    .io_apb_PREADY(_zz_67_),
    .io_apb_PWRITE(_zz_94_),
    .io_apb_PWDATA(_zz_95_),
    .io_apb_PRDATA(_zz_68_),
    .io_apb_PSLVERROR(_zz_69_),
    .io_gpio_read(io_gpioA_read),
    .io_gpio_write(_zz_70_),
    .io_gpio_writeEnable(_zz_71_),
    .io_mainClk(io_mainClk),
    .resetCtrl_systemReset(resetCtrl_systemReset) 
  );
  Apb3UartCtrl system_uartCtrl ( 
    .io_apb_PADDR(_zz_14_),
    .io_apb_PSEL(_zz_97_),
    .io_apb_PENABLE(_zz_98_),
    .io_apb_PREADY(_zz_72_),
    .io_apb_PWRITE(_zz_99_),
    .io_apb_PWDATA(_zz_100_),
    .io_apb_PRDATA(_zz_73_),
    .io_uart_txd(_zz_74_),
    .io_uart_rxd(io_uart_rxd),
    .io_interrupt(_zz_75_),
    .io_mainClk(io_mainClk),
    .resetCtrl_systemReset(resetCtrl_systemReset) 
  );
  MuraxApb3Timer system_timer ( 
    .io_apb_PADDR(_zz_15_),
    .io_apb_PSEL(_zz_102_),
    .io_apb_PENABLE(_zz_103_),
    .io_apb_PREADY(_zz_76_),
    .io_apb_PWRITE(_zz_104_),
    .io_apb_PWDATA(_zz_105_),
    .io_apb_PRDATA(_zz_77_),
    .io_apb_PSLVERROR(_zz_78_),
    .io_interrupt(_zz_79_),
    .io_mainClk(io_mainClk),
    .resetCtrl_systemReset(resetCtrl_systemReset) 
  );
  Apb3Decoder io_apb_decoder ( 
    .io_input_PADDR(_zz_62_),
    .io_input_PSEL(_zz_63_),
    .io_input_PENABLE(_zz_64_),
    .io_input_PREADY(_zz_80_),
    .io_input_PWRITE(_zz_65_),
    .io_input_PWDATA(_zz_66_),
    .io_input_PRDATA(_zz_81_),
    .io_input_PSLVERROR(_zz_82_),
    .io_output_PADDR(_zz_83_),
    .io_output_PSEL(_zz_84_),
    .io_output_PENABLE(_zz_85_),
    .io_output_PREADY(_zz_88_),
    .io_output_PWRITE(_zz_86_),
    .io_output_PWDATA(_zz_87_),
    .io_output_PRDATA(_zz_89_),
    .io_output_PSLVERROR(_zz_90_) 
  );
  Apb3Router apb3Router_1_ ( 
    .io_input_PADDR(_zz_83_),
    .io_input_PSEL(_zz_84_),
    .io_input_PENABLE(_zz_85_),
    .io_input_PREADY(_zz_88_),
    .io_input_PWRITE(_zz_86_),
    .io_input_PWDATA(_zz_87_),
    .io_input_PRDATA(_zz_89_),
    .io_input_PSLVERROR(_zz_90_),
    .io_outputs_0_PADDR(_zz_91_),
    .io_outputs_0_PSEL(_zz_92_),
    .io_outputs_0_PENABLE(_zz_93_),
    .io_outputs_0_PREADY(_zz_67_),
    .io_outputs_0_PWRITE(_zz_94_),
    .io_outputs_0_PWDATA(_zz_95_),
    .io_outputs_0_PRDATA(_zz_68_),
    .io_outputs_0_PSLVERROR(_zz_69_),
    .io_outputs_1_PADDR(_zz_96_),
    .io_outputs_1_PSEL(_zz_97_),
    .io_outputs_1_PENABLE(_zz_98_),
    .io_outputs_1_PREADY(_zz_72_),
    .io_outputs_1_PWRITE(_zz_99_),
    .io_outputs_1_PWDATA(_zz_100_),
    .io_outputs_1_PRDATA(_zz_73_),
    .io_outputs_1_PSLVERROR(_zz_16_),
    .io_outputs_2_PADDR(_zz_101_),
    .io_outputs_2_PSEL(_zz_102_),
    .io_outputs_2_PENABLE(_zz_103_),
    .io_outputs_2_PREADY(_zz_76_),
    .io_outputs_2_PWRITE(_zz_104_),
    .io_outputs_2_PWDATA(_zz_105_),
    .io_outputs_2_PRDATA(_zz_77_),
    .io_outputs_2_PSLVERROR(_zz_78_),
    .io_mainClk(io_mainClk),
    .resetCtrl_systemReset(resetCtrl_systemReset) 
  );
  always @(*) begin
    case(system_mainBusDecoder_logic_rspSourceId)
      1'b0 : begin
        _zz_17_ = _zz_58_;
      end
      default : begin
        _zz_17_ = _zz_61_;
      end
    endcase
  end

  always @ (*) begin
    resetCtrl_mainClkResetUnbuffered = 1'b0;
    if(_zz_106_)begin
      resetCtrl_mainClkResetUnbuffered = 1'b1;
    end
  end

  assign _zz_1_[5 : 0] = (6'b111111);
  always @ (*) begin
    system_timerInterrupt = 1'b0;
    if(_zz_79_)begin
      system_timerInterrupt = 1'b1;
    end
  end

  always @ (*) begin
    system_externalInterrupt = 1'b0;
    if(_zz_75_)begin
      system_externalInterrupt = 1'b1;
    end
  end

  assign _zz_2_ = _zz_23_;
  assign _zz_10_ = _zz_52_[7:0];
  assign io_jtag_tdo = _zz_42_;
  assign io_gpioA_write = _zz_70_;
  assign io_gpioA_writeEnable = _zz_71_;
  assign io_uart_txd = _zz_74_;
  assign _zz_13_ = _zz_91_[3:0];
  assign _zz_14_ = _zz_96_[3:0];
  assign _zz_16_ = 1'b0;
  assign _zz_15_ = _zz_101_[7:0];
  assign system_mainBusDecoder_logic_masterPipelined_cmd_valid = _zz_27_;
  assign system_mainBusDecoder_logic_masterPipelined_cmd_payload_wr = _zz_28_;
  assign system_mainBusDecoder_logic_masterPipelined_cmd_payload_address = _zz_29_;
  assign system_mainBusDecoder_logic_masterPipelined_cmd_payload_data = _zz_30_;
  assign system_mainBusDecoder_logic_masterPipelined_cmd_payload_mask = _zz_31_;
  assign system_mainBusDecoder_logic_hits_0 = (((32'b10000000000000000000000000000000) <= system_mainBusDecoder_logic_masterPipelined_cmd_payload_address) && (system_mainBusDecoder_logic_masterPipelined_cmd_payload_address < (32'b10000000000000110000000000000000)));
  always @ (*) begin
    _zz_11_ = (system_mainBusDecoder_logic_masterPipelined_cmd_valid && system_mainBusDecoder_logic_hits_0);
    _zz_12_ = (system_mainBusDecoder_logic_masterPipelined_cmd_valid && system_mainBusDecoder_logic_hits_1);
    system_mainBusDecoder_logic_masterPipelined_cmd_ready = (((system_mainBusDecoder_logic_hits_0 && _zz_56_) || (system_mainBusDecoder_logic_hits_1 && _zz_59_)) || system_mainBusDecoder_logic_noHit);
    if((system_mainBusDecoder_logic_rspPending && (! system_mainBusDecoder_logic_masterPipelined_rsp_valid)))begin
      system_mainBusDecoder_logic_masterPipelined_cmd_ready = 1'b0;
      _zz_11_ = 1'b0;
      _zz_12_ = 1'b0;
    end
  end

  assign system_mainBusDecoder_logic_hits_1 = ((system_mainBusDecoder_logic_masterPipelined_cmd_payload_address & _zz_108_) == (32'b11110000000000000000000000000000));
  assign system_mainBusDecoder_logic_noHit = (! (system_mainBusDecoder_logic_hits_0 || system_mainBusDecoder_logic_hits_1));
  assign system_mainBusDecoder_logic_masterPipelined_rsp_valid = ((_zz_57_ || _zz_60_) || (system_mainBusDecoder_logic_rspPending && system_mainBusDecoder_logic_rspNoHit));
  assign system_mainBusDecoder_logic_masterPipelined_rsp_payload_data = _zz_17_;
  always @ (posedge io_mainClk) begin
    if(_zz_106_)begin
      resetCtrl_systemClkResetCounter <= (resetCtrl_systemClkResetCounter + (6'b000001));
    end
    if(_zz_18_)begin
      resetCtrl_systemClkResetCounter <= (6'b000000);
    end
  end

  always @ (posedge io_mainClk) begin
    resetCtrl_mainClkReset <= resetCtrl_mainClkResetUnbuffered;
    resetCtrl_systemReset <= resetCtrl_mainClkResetUnbuffered;
    if(debug_resetOut_regNext)begin
      resetCtrl_systemReset <= 1'b1;
    end
  end

  always @ (posedge io_mainClk or posedge resetCtrl_systemReset) begin
    if (resetCtrl_systemReset) begin
      _zz_3_ <= 1'b0;
      _zz_4_ <= 1'b1;
      system_mainBusDecoder_logic_rspPending <= 1'b0;
      system_mainBusDecoder_logic_rspNoHit <= 1'b0;
    end else begin
      if(_zz_107_)begin
        _zz_3_ <= _zz_37_;
        _zz_4_ <= (! _zz_37_);
      end else begin
        _zz_3_ <= (! _zz_2_);
        _zz_4_ <= _zz_2_;
      end
      if(system_mainBusDecoder_logic_masterPipelined_rsp_valid)begin
        system_mainBusDecoder_logic_rspPending <= 1'b0;
      end
      if(((system_mainBusDecoder_logic_masterPipelined_cmd_valid && system_mainBusDecoder_logic_masterPipelined_cmd_ready) && (! system_mainBusDecoder_logic_masterPipelined_cmd_payload_wr)))begin
        system_mainBusDecoder_logic_rspPending <= 1'b1;
      end
      system_mainBusDecoder_logic_rspNoHit <= 1'b0;
      if(system_mainBusDecoder_logic_noHit)begin
        system_mainBusDecoder_logic_rspNoHit <= 1'b1;
      end
    end
  end

  always @ (posedge io_mainClk) begin
    if(_zz_107_)begin
      _zz_5_ <= _zz_38_;
      _zz_6_ <= _zz_39_;
      _zz_7_ <= _zz_40_;
      _zz_8_ <= _zz_41_;
    end
    if((system_mainBusDecoder_logic_masterPipelined_cmd_valid && system_mainBusDecoder_logic_masterPipelined_cmd_ready))begin
      system_mainBusDecoder_logic_rspSourceId <= system_mainBusDecoder_logic_hits_1;
    end
  end

  always @ (posedge io_mainClk) begin
    debug_resetOut_regNext <= _zz_36_;
  end

  always @ (posedge io_mainClk or posedge resetCtrl_mainClkReset) begin
    if (resetCtrl_mainClkReset) begin
      _zz_9_ <= 1'b0;
    end else begin
      _zz_9_ <= (_zz_51_ && _zz_34_);
    end
  end

endmodule

