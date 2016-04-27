module adv_dbg_if 
    #(
        parameter NB_CORES       = 4,
        parameter AXI_ADDR_WIDTH = 32,
        parameter AXI_DATA_WIDTH = 64,
        parameter AXI_USER_WIDTH = 6,
        parameter AXI_ID_WIDTH   = 3
    ) (
       input  logic                    tms_pad_i, 
       input  logic                    tck_pad_i, 
       input  logic                    trstn_pad_i, 
       input  logic                    tdi_pad_i, 
       output logic                    tdo_pad_o, 
       output logic                    tdo_padoe_o,

       input  logic                    test_mode_i,

        // CPU signals
        input  logic [NB_CORES-1:0]        cpu_clk_i,
        output logic [NB_CORES-1:0] [15:0] cpu_addr_o, 
        input  logic [NB_CORES-1:0] [31:0] cpu_data_i, 
        output logic [NB_CORES-1:0] [31:0] cpu_data_o,
        input  logic [NB_CORES-1:0]        cpu_bp_i,
        output logic [NB_CORES-1:0]        cpu_stall_o,
        output logic [NB_CORES-1:0]        cpu_stb_o,
        output logic [NB_CORES-1:0]        cpu_we_o,
        input  logic [NB_CORES-1:0]        cpu_ack_i,
        output logic [NB_CORES-1:0]        cpu_rst_o,
		
		// AXI4 MASTER
		//***************************************
		input  logic                        axi_aclk,
		input  logic                        axi_aresetn,
		// WRITE ADDRESS CHANNEL
		output logic                        axi_master_aw_valid,
		output logic [AXI_ADDR_WIDTH-1:0]   axi_master_aw_addr,
		output logic [2:0]                  axi_master_aw_prot,
		output logic [3:0]                  axi_master_aw_region,
		output logic [7:0]                  axi_master_aw_len,
		output logic [2:0]                  axi_master_aw_size,
		output logic [1:0]                  axi_master_aw_burst,
		output logic                        axi_master_aw_lock,
		output logic [3:0]                  axi_master_aw_cache,
		output logic [3:0]                  axi_master_aw_qos,
		output logic [AXI_ID_WIDTH-1:0]     axi_master_aw_id,
		output logic [AXI_USER_WIDTH-1:0]   axi_master_aw_user,
		input  logic                        axi_master_aw_ready,
    
		// READ ADDRESS CHANNEL
		output logic                        axi_master_ar_valid,
		output logic [AXI_ADDR_WIDTH-1:0]   axi_master_ar_addr,
		output logic [2:0]                  axi_master_ar_prot,
		output logic [3:0]                  axi_master_ar_region,
		output logic [7:0]                  axi_master_ar_len,
		output logic [2:0]                  axi_master_ar_size,
		output logic [1:0]                  axi_master_ar_burst,
		output logic                        axi_master_ar_lock,
		output logic [3:0]                  axi_master_ar_cache,
		output logic [3:0]                  axi_master_ar_qos,
		output logic [AXI_ID_WIDTH-1:0]     axi_master_ar_id,
		output logic [AXI_USER_WIDTH-1:0]   axi_master_ar_user,
		input  logic                        axi_master_ar_ready,
    
		// WRITE DATA CHANNEL
		output logic                        axi_master_w_valid,
		output logic [AXI_DATA_WIDTH-1:0]   axi_master_w_data,
		output logic [AXI_DATA_WIDTH/8-1:0] axi_master_w_strb,
		output logic [AXI_USER_WIDTH-1:0]   axi_master_w_user,
		output logic                        axi_master_w_last,
		input  logic                        axi_master_w_ready,
    
		// READ DATA CHANNEL
		input  logic                        axi_master_r_valid,
		input  logic [AXI_DATA_WIDTH-1:0]   axi_master_r_data,
		input  logic [1:0]                  axi_master_r_resp,
		input  logic                        axi_master_r_last,
		input  logic [AXI_ID_WIDTH-1:0]     axi_master_r_id,
		input  logic [AXI_USER_WIDTH-1:0]   axi_master_r_user,
		output logic                        axi_master_r_ready,
                                            
		// WRITE RESPONSE CHANNEL           
		input  logic                        axi_master_b_valid,
		input  logic [1:0]                  axi_master_b_resp,
		input  logic [AXI_ID_WIDTH-1:0]     axi_master_b_id,
		input  logic [AXI_USER_WIDTH-1:0]   axi_master_b_user,
		output logic                        axi_master_b_ready
    );

    logic       s_test_logic_reset;
    logic       s_run_test_idle;
    logic       s_shift_dr;
    logic       s_pause_dr;
    logic       s_update_dr;
    logic       s_capture_dr;
    logic       s_extest_select;
    logic       s_sample_preload_select;
    logic       s_mbist_select;
    logic       s_debug_select;
    logic       s_tdi;
    logic       s_debug_tdo;

    adbg_tap_top cluster_tap_i (
                // JTAG pads
                .tms_pad_i(tms_pad_i), 
                .tck_pad_i(tck_pad_i), 
                .trstn_pad_i(trstn_pad_i), 
                .tdi_pad_i(tdi_pad_i), 
                .tdo_pad_o(tdo_pad_o), 
                .tdo_padoe_o(tdo_padoe_o),

                .test_mode_i(test_mode_i),

                // TAP states
				.test_logic_reset_o(s_test_logic_reset),
				.run_test_idle_o(s_run_test_idle),
                .shift_dr_o(s_shift_dr),
                .pause_dr_o(s_pause_dr), 
                .update_dr_o(s_update_dr),
                .capture_dr_o(s_capture_dr),
                
                // Select signals for boundary scan or mbist
                .extest_select_o(s_extest_select), 
                .sample_preload_select_o(s_sample_preload_select),
                .mbist_select_o(s_mbist_select),
                .debug_select_o(s_debug_select),
                
                // TDO signal that is connected to TDI of sub-modules.
                .tdi_o(s_tdi), 
                
                // TDI signals from sub-modules
                .debug_tdo_i(s_debug_tdo),    // from debug module
                .bs_chain_tdo_i(1'b0), // from Boundary Scan Chain
                .mbist_tdo_i(1'b0)     // from Mbist Chain
              );

// Top module
adbg_top #(
        .NB_CORES(NB_CORES),
        .AXI_ADDR_WIDTH(AXI_ADDR_WIDTH),
        .AXI_DATA_WIDTH(AXI_DATA_WIDTH),
        .AXI_USER_WIDTH(AXI_USER_WIDTH),
        .AXI_ID_WIDTH(AXI_ID_WIDTH)
    ) dbg_module_i (

                // JTAG signals
                .tck_i(tck_pad_i),
                .tdi_i(s_tdi),
                .tdo_o(s_debug_tdo),
                .trstn_i(trstn_pad_i),

                // TAP states
                .shift_dr_i(s_shift_dr),
                .pause_dr_i(s_pause_dr),
                .update_dr_i(s_update_dr),
                .capture_dr_i(s_capture_dr),

                // Instructions
                .debug_select_i(s_debug_select),

                // CPU signals
                .cpu_addr_o(cpu_addr_o), 
                .cpu_data_i(cpu_data_i),
                .cpu_data_o(cpu_data_o),
                .cpu_bp_i(cpu_bp_i),
                .cpu_stall_o(cpu_stall_o),
                .cpu_stb_o(cpu_stb_o),
                .cpu_we_o(cpu_we_o),
                .cpu_ack_i(cpu_ack_i),
                .cpu_rst_o(cpu_rst_o),

        .axi_aclk(axi_aclk),
        .axi_aresetn(axi_aresetn),

        .axi_master_aw_valid(axi_master_aw_valid),
        .axi_master_aw_addr(axi_master_aw_addr),
        .axi_master_aw_prot(axi_master_aw_prot),
        .axi_master_aw_region(axi_master_aw_region),
        .axi_master_aw_len(axi_master_aw_len),
        .axi_master_aw_size(axi_master_aw_size),
        .axi_master_aw_burst(axi_master_aw_burst),
        .axi_master_aw_lock(axi_master_aw_lock),
        .axi_master_aw_cache(axi_master_aw_cache),
        .axi_master_aw_qos(axi_master_aw_qos),
        .axi_master_aw_id(axi_master_aw_id),
        .axi_master_aw_user(axi_master_aw_user),
        .axi_master_aw_ready(axi_master_aw_ready),

        .axi_master_ar_valid(axi_master_ar_valid),
        .axi_master_ar_addr(axi_master_ar_addr),
        .axi_master_ar_prot(axi_master_ar_prot),
        .axi_master_ar_region(axi_master_ar_region),
        .axi_master_ar_len(axi_master_ar_len),
        .axi_master_ar_size(axi_master_ar_size),
        .axi_master_ar_burst(axi_master_ar_burst),
        .axi_master_ar_lock(axi_master_ar_lock),
        .axi_master_ar_cache(axi_master_ar_cache),
        .axi_master_ar_qos(axi_master_ar_qos),
        .axi_master_ar_id(axi_master_ar_id),
        .axi_master_ar_user(axi_master_ar_user),
        .axi_master_ar_ready(axi_master_ar_ready),

        .axi_master_w_valid(axi_master_w_valid),
        .axi_master_w_data(axi_master_w_data),
        .axi_master_w_strb(axi_master_w_strb),
        .axi_master_w_user(axi_master_w_user),
        .axi_master_w_last(axi_master_w_last),
        .axi_master_w_ready(axi_master_w_ready),

        .axi_master_r_valid(axi_master_r_valid),
        .axi_master_r_data(axi_master_r_data),
        .axi_master_r_resp(axi_master_r_resp),
        .axi_master_r_last(axi_master_r_last),
        .axi_master_r_id(axi_master_r_id),
        .axi_master_r_user(axi_master_r_user),
        .axi_master_r_ready(axi_master_r_ready),

        .axi_master_b_valid(axi_master_b_valid),
        .axi_master_b_resp(axi_master_b_resp),
        .axi_master_b_id(axi_master_b_id),
        .axi_master_b_user(axi_master_b_user),
        .axi_master_b_ready(axi_master_b_ready)
              );

endmodule

