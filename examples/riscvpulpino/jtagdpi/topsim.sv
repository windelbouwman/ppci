
module topsim
(
 input logic clk,
 input logic rst_n,
 input logic clk_sel_i,
 input logic testmode_i,
 input logic fetch_enable_i,
 input logic spi_clk_i,
 input logic spi_cs_i
 );

   logic     tms;
   logic     tck;
   logic     trstn;
   logic     tdi;
   logic     tdo;
   
   
   
   jtag_dpi
    #(
      .TIMEOUT_COUNT ( 6'd10 )
    )
    i_jtag
    (
      .clk_i    ( clk   ),
      .enable_i ( rst_n ),

      .tms_o    ( tms     ),
      .tck_o    ( tck     ),
      .trst_o   ( trstn   ),
      .tdi_o    ( tdi     ),
      .tdo_i    ( tdo     )
     );
  

  pulpino_top top_i
  (
    .clk               ( clk        ),
    .rst_n             ( rst_n      ),

    .clk_sel_i         ( clk_sel_i         ),
    .testmode_i        ( testmode_i         ),
    .fetch_enable_i    ( fetch_enable_i ),

    .spi_clk_i         ( spi_clk_i      ),
    .spi_cs_i          ( spi_cs_i      ),
    .spi_mode_o        (      ),
    .spi_sdo0_o        (      ),
    .spi_sdo1_o        (      ),
    .spi_sdo2_o        (      ),
    .spi_sdo3_o        (      ),
    .spi_sdi0_i        (      ),
    .spi_sdi1_i        (      ),
    .spi_sdi2_i        (      ),
    .spi_sdi3_i        (      ),

    .spi_master_clk_o  (              ),
    .spi_master_csn0_o (              ),
    .spi_master_csn1_o (              ),
    .spi_master_csn2_o (              ),
    .spi_master_csn3_o (              ),
    .spi_master_mode_o (              ),
    .spi_master_sdo0_o (              ),
    .spi_master_sdo1_o (              ),
    .spi_master_sdo2_o (              ),
    .spi_master_sdo3_o (              ),
    .spi_master_sdi0_i (              ),
    .spi_master_sdi1_i (              ),
    .spi_master_sdi2_i (              ),
    .spi_master_sdi3_i (              ),

    .scl_pad_i         (              ),
    .scl_pad_o         (              ),
    .scl_padoen_o      (              ),
    .sda_pad_i         (              ),
    .sda_pad_o         (              ),
    .sda_padoen_o      (              ),


    .uart_tx           (       ),
    .uart_rx           (       ),
    .uart_rts          (       ),
    .uart_dtr          (       ),
    .uart_cts          ( 1'b0         ),
    .uart_dsr          ( 1'b0         ),

    .gpio_in           (              ),
    .gpio_out          (              ),
    .gpio_dir          (              ),
    .gpio_padcfg       (              ),

    .tck_i             (tck      ),
    .trstn_i           (trstn      ),
    .tms_i             (tms      ),
    .tdi_i             (tdi      ),
    .tdo_o             (tdo      )
  );


endmodule
