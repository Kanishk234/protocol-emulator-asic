/*
 * Copyright (c) 2026 Kanishk Sama
 * SPDX-License-Identifier: Apache-2.0
 *
 * WARP top level, phase 1 spike (DECISIONS D-018): the 16-LUT fabric macro `warp_tiny`
 * behind a minimal shell. Replaced by the full shell (host interface, loader checks,
 * run control) in phase 2 (docs/design/ARCHITECTURE.md).
 *
 * Pins:
 *   ui[0]      RUN        1 = fabric outputs live; 0 = parked (uo fabric bits 0, all uio inputs)
 *   ui[1]      CFG_CLK    bit-bang configuration clock   (FABulous bitbang protocol)
 *   ui[2]      CFG_DATA   bit-bang configuration data
 *   ui[3..6]   fabric inputs  (east IO tile X2Y2, A..D)
 *   uo[0]      CFG_ACTIVE configuration session in progress
 *   uo[2..5]   fabric outputs (east IO tile X2Y1, A..D)
 *   uio[0..7]  fabric bidirectional pins (west IO tiles X0Y1 A..D, X0Y2 A..D)
 * The fabric's user clock comes in on IO tile X1Y3 A (= clk) and its user reset on X1Y3 B
 * (= rst_n, held low during a configuration session); SYS_RESET is held during a session too.
 */

`default_nettype none

module tt_um_warp (
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);
    // ---- run control: outputs parked unless RUN is high and no configuration is running
    reg  [1:0] run_s;
    wire       cfg_active;
    always @(posedge clk) begin
        if (!rst_n) run_s <= 2'b00;
        else        run_s <= {run_s[0], ui_in[0]};
    end
    wire run = run_s[1] && !cfg_active;

    // ---- configuration path
    wire [127:0] frame_data;
    wire [59:0]  frame_strobe;
    wp_fabric_cfg #(.ROWS(4), .COLS(3), .FRAME_BITS(32), .MAX_FRAMES(20)) u_cfg (
        .clk          (clk),
        .rst_n        (rst_n),
        .cfg_clk      (ui_in[1]),
        .cfg_data     (ui_in[2]),
        .active       (cfg_active),
        .frame_data   (frame_data),
        .frame_strobe (frame_strobe)
    );

    // ---- fabric
    wire [7:0] w_in  = uio_in;           // west IO tiles: pad -> fabric
    wire [7:0] w_out, w_en;              // fabric -> pad, output enable
    wire [3:0] e_out, e_out_en;          // east X2Y1 A..D: fabric outputs
    wire [3:0] e_in_nc, e_in_en_nc;      // east X2Y2 A..D: used as inputs only
    wire [1:0] s_out_nc, s_en_nc;        // south X1Y3 A/B: clock and reset in only
    wire       user_rst_n = rst_n && !cfg_active;

    warp_tiny u_fabric (
        .Tile_X0Y1_A_OUT_top(w_in[0]), .Tile_X0Y1_A_IN_top(w_out[0]), .Tile_X0Y1_A_EN_top(w_en[0]),
        .Tile_X0Y1_B_OUT_top(w_in[1]), .Tile_X0Y1_B_IN_top(w_out[1]), .Tile_X0Y1_B_EN_top(w_en[1]),
        .Tile_X0Y1_C_OUT_top(w_in[2]), .Tile_X0Y1_C_IN_top(w_out[2]), .Tile_X0Y1_C_EN_top(w_en[2]),
        .Tile_X0Y1_D_OUT_top(w_in[3]), .Tile_X0Y1_D_IN_top(w_out[3]), .Tile_X0Y1_D_EN_top(w_en[3]),
        .Tile_X0Y2_A_OUT_top(w_in[4]), .Tile_X0Y2_A_IN_top(w_out[4]), .Tile_X0Y2_A_EN_top(w_en[4]),
        .Tile_X0Y2_B_OUT_top(w_in[5]), .Tile_X0Y2_B_IN_top(w_out[5]), .Tile_X0Y2_B_EN_top(w_en[5]),
        .Tile_X0Y2_C_OUT_top(w_in[6]), .Tile_X0Y2_C_IN_top(w_out[6]), .Tile_X0Y2_C_EN_top(w_en[6]),
        .Tile_X0Y2_D_OUT_top(w_in[7]), .Tile_X0Y2_D_IN_top(w_out[7]), .Tile_X0Y2_D_EN_top(w_en[7]),
        .Tile_X2Y1_A_OUT_top(1'b0), .Tile_X2Y1_A_IN_top(e_out[0]), .Tile_X2Y1_A_EN_top(e_out_en[0]),
        .Tile_X2Y1_B_OUT_top(1'b0), .Tile_X2Y1_B_IN_top(e_out[1]), .Tile_X2Y1_B_EN_top(e_out_en[1]),
        .Tile_X2Y1_C_OUT_top(1'b0), .Tile_X2Y1_C_IN_top(e_out[2]), .Tile_X2Y1_C_EN_top(e_out_en[2]),
        .Tile_X2Y1_D_OUT_top(1'b0), .Tile_X2Y1_D_IN_top(e_out[3]), .Tile_X2Y1_D_EN_top(e_out_en[3]),
        .Tile_X2Y2_A_OUT_top(ui_in[3]), .Tile_X2Y2_A_IN_top(e_in_nc[0]), .Tile_X2Y2_A_EN_top(e_in_en_nc[0]),
        .Tile_X2Y2_B_OUT_top(ui_in[4]), .Tile_X2Y2_B_IN_top(e_in_nc[1]), .Tile_X2Y2_B_EN_top(e_in_en_nc[1]),
        .Tile_X2Y2_C_OUT_top(ui_in[5]), .Tile_X2Y2_C_IN_top(e_in_nc[2]), .Tile_X2Y2_C_EN_top(e_in_en_nc[2]),
        .Tile_X2Y2_D_OUT_top(ui_in[6]), .Tile_X2Y2_D_IN_top(e_in_nc[3]), .Tile_X2Y2_D_EN_top(e_in_en_nc[3]),
        .Tile_X0Y3_SYS_RESET_RESET_top(cfg_active),
        .Tile_X1Y3_A_OUT_top(clk),        .Tile_X1Y3_A_IN_top(s_out_nc[0]), .Tile_X1Y3_A_EN_top(s_en_nc[0]),
        .Tile_X1Y3_B_OUT_top(user_rst_n), .Tile_X1Y3_B_IN_top(s_out_nc[1]), .Tile_X1Y3_B_EN_top(s_en_nc[1]),
        .FrameData   (frame_data),
        .FrameStrobe (frame_strobe)
    );

    // ---- pins (parked unless running)
    assign uo_out  = {2'b00, e_out & {4{run}}, 1'b0, cfg_active};
    assign uio_out = w_out & {8{run}};
    assign uio_oe  = w_en  & {8{run}};

    wire _unused = &{ena, ui_in[7], e_out_en, e_in_nc, e_in_en_nc, s_out_nc, s_en_nc, 1'b0};
endmodule
