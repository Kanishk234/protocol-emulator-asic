`default_nettype none
`timescale 1ns / 1ps

// Co-simulation (phase 4, VERIFICATION.md): the chip (tt_um_warp, with the fabric RTL; a user
// design is loaded as a real bitstream through the host pins) next to that design's source RTL
// (ref_uart: protocols/uart, the same parameters as the bitstream uart16). test_cosim.py drives
// both with the same stimulus and compares what they do. Module name `tb` so the fabric settle
// include (D-023) resolves its hierarchical names as in test/tb.v.
module tb ();
  initial begin
    $dumpfile("tb.fst");
    $dumpvars(0, tb);
    #1;
  end

  reg clk;
  reg rst_n;
  reg ena;
  reg [7:0] ui_in;
  reg [7:0] uio_in;
  wire [7:0] uo_out;
  wire [7:0] uio_out;
  wire [7:0] uio_oe;

  tt_um_warp user_project (
      .ui_in(ui_in), .uo_out(uo_out), .uio_in(uio_in), .uio_out(uio_out), .uio_oe(uio_oe),
      .ena(ena), .clk(clk), .rst_n(rst_n)
  );

  reg settle_routing = 1'b0;
  reg hold_x = 1'b0;
  `include "fabric_settle_rtl.vh"

  // the design's source RTL, same parameters as tools/compile/examples/uart16.yaml
  reg        ref_rst_n;
  reg        ref_rx;
  reg  [7:0] ref_h_wdata;
  reg        ref_h_wvalid;
  reg        ref_h_rready;
  wire       ref_tx, ref_tx_oe, ref_h_wready, ref_h_rvalid;
  wire [7:0] ref_h_rdata, ref_h_status;
  uart_top #(.DIV(16), .RUNTIME_DIV(0), .PRIMS(1)) ref_uart (
      .clk(clk), .rst_n(ref_rst_n), .rx_i(ref_rx), .tx_o(ref_tx), .tx_oe(ref_tx_oe),
      .h_wdata(ref_h_wdata), .h_wvalid(ref_h_wvalid), .h_wready(ref_h_wready),
      .h_rdata(ref_h_rdata), .h_rvalid(ref_h_rvalid), .h_rready(ref_h_rready),
      .h_status(ref_h_status), .cfg_div(16'd0), .cfg_we(1'b0)
  );
endmodule
