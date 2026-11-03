/*
 * Copyright (c) 2026 Kanishk, Krithik
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

// Isolated physical-preservation probe. Counter supplies clocked load; relay is asynchronous.
module tt_um_tripwire (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  reg [7:0] count;

  always @(posedge clk) begin
    if (!rst_n)
      count <= 8'd0;
    else if (ui_in[0])
      count <= count + 8'd1;
  end

  (* keep = 1 *) wire trw_ap_node;
  wire relay;
  (* keep = 1 *) sg13cmos5l_buf_2 trw_ap_driver (.A(ui_in[1]), .X(trw_ap_node));
  (* keep = 1 *) sg13cmos5l_buf_2 trw_ap_sink (.A(trw_ap_node), .X(relay));
  (* keep = 1 *) sg13cmos5l_antennanp trw_ap_diode (.A(trw_ap_node));
  assign uo_out  = {count[7:1], relay};
  assign uio_out = 8'd0;
  assign uio_oe  = 8'd0;

  // List all unused inputs to prevent warnings
  wire _unused = &{ena, ui_in[7:2], uio_in, 1'b0};

endmodule
