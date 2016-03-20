///////////////////////////////////////////////
//  _____            _     _                 //
// |  __ \          (_)   | |                //
// | |__) |___  __ _ _ ___| |_ ___ _ __ ___  //
// |  _  // _ \/ _` | / __| __/ _ \ '__/ __| //
// | | \ \  __/ (_| | \__ \ ||  __/ |  \__ \ //
// |_|  \_\___|\__, |_|___/\__\___|_|  |___/ //
//              __/ |                        //
//             |___/                         //
///////////////////////////////////////////////

// total number of address space reserved for the apb_event_unit
`define ADR_MAX_ADR				'd2 // number of bits needed to access all subunits

`define IRQ						2'b00
`define EVENT					2'b01
`define SLEEP					2'b10

// number of registers per (interrupt, event) service unit - 8 regs in total
`define REGS_MAX_IDX			'd3 // number of bits needed to access all registers
`define REGS_MAX_ADR				'd2

`define REG_ENABLE 				2'b00
`define REG_PENDING      		2'b01
`define REG_SET_PENDING			2'b10
`define REG_CLEAR_PENDING		2'b11

`define REGS_SLEEP_MAX_IDX		'd1

`define REG_SLEEP_CTRL        	2'b0
`define REG_SLEEP_STATUS		2'b1

`define SLEEP_ENABLE			1'b0
`define SLEEP_STATUS 			1'b0
