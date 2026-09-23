/*
 * Copyright (c) 2026 Kanishk, Krithik
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

// TRIPWIRE top level.
// Phase 0 placeholder: an 8-bit counter on uo_out, advancing by one on every
// clock while ui_in[0] is high. It exists only to prove the CI flow end to end
// (test, gds, precheck, gl_test, viewer, docs). Replaced by the real design in phase 2.
//
// Timing contract: uo_out = count, updated on the rising clock edge;
// synchronous active-low reset clears it to 0.

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

  assign uo_out  = count;
  assign uio_out = 8'd0;
  assign uio_oe  = 8'd0;

  // List all unused inputs to prevent warnings
  wire _unused = &{ena, ui_in[7:1], uio_in, 1'b0};

endmodule
