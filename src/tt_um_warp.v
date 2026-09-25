/*
 * Copyright (c) 2026 Kanishk Sama
 * SPDX-License-Identifier: Apache-2.0
 *
 * WARP top level. Phase 0 placeholder: the template's adder, renamed.
 * Replaced by the shell + fabric in phase 2 (docs/design/ARCHITECTURE.md).
 */

`default_nettype none

module tt_um_warp (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  assign uo_out  = ui_in + uio_in;
  assign uio_out = 0;
  assign uio_oe  = 0;

  wire _unused = &{ena, clk, rst_n, 1'b0};

endmodule
