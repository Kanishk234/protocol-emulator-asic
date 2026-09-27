/*
 * Copyright (c) 2026 Kanishk Sama
 * SPDX-License-Identifier: Apache-2.0
 *
 * WARP top level (docs/design/ARCHITECTURE.md): the fabric macro behind the shell.
 *
 * Pins (ARCHITECTURE.md §1):
 *   ui[0]      HOST_CS_N   host SPI chip select (active low)
 *   ui[1]      HOST_SCK    host SPI clock, <= clk/8
 *   ui[2]      HOST_MOSI   host -> chip
 *   ui[3..7]   FAB_IN0..4  fabric inputs, synchronized
 *   uo[0]      HOST_MISO   chip -> host (0 while CS_N is high)
 *   uo[1]      HOST_IRQ
 *   uo[2..7]   FAB_OUT0..5 fabric outputs, registered, parked unless RUNNING
 *   uio[0..7]  FAB_IO0..7  fabric bidirectional pins, registered out/oe, parked unless RUNNING
 *
 * Current fabric: the 16-LUT phase 1 macro `warp_tiny` (D-018), which has fewer IO BELs than the
 * contract: FAB_IN0..3 -> east X2Y2 A..D (FAB_IN4 unconnected), FAB_OUT0..3 <- east X2Y1 A..D
 * (FAB_OUT4..5 = 0), FAB_IO0..7 <-> west X0Y1/X0Y2 A..D, and no host channel BELs (the shell's
 * channel ports are tied off). The G0/G1 fabric replaces it with the full mapping.
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
    // ---- shell
    wire        host_miso, host_irq;
    wire [31:0] cfg_word;
    wire        cfg_strobe, cfg_restart;
    wire        running, user_reset;
    wire [7:0]  h_wdata;
    wire        h_wlast, h_wvalid, h_rready;

    wp_shell #(.ARCH_VERSION(16'h0001)) u_shell (
        .clk         (clk),
        .rst_n       (rst_n),
        .host_cs_n   (ui_in[0]),
        .host_sck    (ui_in[1]),
        .host_mosi   (ui_in[2]),
        .host_miso   (host_miso),
        .host_irq    (host_irq),
        .cfg_word    (cfg_word),
        .cfg_strobe  (cfg_strobe),
        .cfg_restart (cfg_restart),
        .running     (running),
        .user_reset  (user_reset),
        .h_wdata     (h_wdata),
        .h_wlast     (h_wlast),
        .h_wvalid    (h_wvalid),
        .h_wready    (1'b0),
        .h_rdata     (8'h00),
        .h_rvalid    (1'b0),
        .h_rready    (h_rready),
        .h_status    (8'h00),
        .h_attention (1'b0)
    );

    // ---- configuration path
    wire [127:0] frame_data;
    wire [59:0]  frame_strobe;
    wp_fabric_cfg #(.ROWS(4), .COLS(3), .FRAME_BITS(32), .MAX_FRAMES(20)) u_cfg (
        .clk          (clk),
        .rst_n        (rst_n),
        .word         (cfg_word),
        .word_strobe  (cfg_strobe),
        .restart      (cfg_restart),
        .frame_data   (frame_data),
        .frame_strobe (frame_strobe)
    );

    // ---- input cells: two-flop synchronizers (ARCHITECTURE.md §6)
    wire [4:0] fab_in;
    wire [7:0] io_in;
    wp_sync #(.WIDTH(13)) u_in_sync (
        .clk(clk), .rst_n(rst_n), .d({ui_in[7:3], uio_in}), .q({fab_in, io_in})
    );

    // ---- fabric
    wire [7:0] w_out, w_en;              // west IO tiles: fabric -> pad, output enable
    wire [3:0] e_out, e_out_en;          // east X2Y1 A..D: fabric outputs
    wire [3:0] e_in_nc, e_in_en_nc;      // east X2Y2 A..D: used as inputs only
    wire [1:0] s_out_nc, s_en_nc;        // south X1Y3 A/B: clock and reset in only
    reg        user_rst_n;
    always @(posedge clk) begin
        if (!rst_n) user_rst_n <= 1'b0;
        else        user_rst_n <= !user_reset;
    end

    warp_tiny u_fabric (
        .Tile_X0Y1_A_OUT_top(io_in[0]), .Tile_X0Y1_A_IN_top(w_out[0]), .Tile_X0Y1_A_EN_top(w_en[0]),
        .Tile_X0Y1_B_OUT_top(io_in[1]), .Tile_X0Y1_B_IN_top(w_out[1]), .Tile_X0Y1_B_EN_top(w_en[1]),
        .Tile_X0Y1_C_OUT_top(io_in[2]), .Tile_X0Y1_C_IN_top(w_out[2]), .Tile_X0Y1_C_EN_top(w_en[2]),
        .Tile_X0Y1_D_OUT_top(io_in[3]), .Tile_X0Y1_D_IN_top(w_out[3]), .Tile_X0Y1_D_EN_top(w_en[3]),
        .Tile_X0Y2_A_OUT_top(io_in[4]), .Tile_X0Y2_A_IN_top(w_out[4]), .Tile_X0Y2_A_EN_top(w_en[4]),
        .Tile_X0Y2_B_OUT_top(io_in[5]), .Tile_X0Y2_B_IN_top(w_out[5]), .Tile_X0Y2_B_EN_top(w_en[5]),
        .Tile_X0Y2_C_OUT_top(io_in[6]), .Tile_X0Y2_C_IN_top(w_out[6]), .Tile_X0Y2_C_EN_top(w_en[6]),
        .Tile_X0Y2_D_OUT_top(io_in[7]), .Tile_X0Y2_D_IN_top(w_out[7]), .Tile_X0Y2_D_EN_top(w_en[7]),
        .Tile_X2Y1_A_OUT_top(1'b0), .Tile_X2Y1_A_IN_top(e_out[0]), .Tile_X2Y1_A_EN_top(e_out_en[0]),
        .Tile_X2Y1_B_OUT_top(1'b0), .Tile_X2Y1_B_IN_top(e_out[1]), .Tile_X2Y1_B_EN_top(e_out_en[1]),
        .Tile_X2Y1_C_OUT_top(1'b0), .Tile_X2Y1_C_IN_top(e_out[2]), .Tile_X2Y1_C_EN_top(e_out_en[2]),
        .Tile_X2Y1_D_OUT_top(1'b0), .Tile_X2Y1_D_IN_top(e_out[3]), .Tile_X2Y1_D_EN_top(e_out_en[3]),
        .Tile_X2Y2_A_OUT_top(fab_in[0]), .Tile_X2Y2_A_IN_top(e_in_nc[0]), .Tile_X2Y2_A_EN_top(e_in_en_nc[0]),
        .Tile_X2Y2_B_OUT_top(fab_in[1]), .Tile_X2Y2_B_IN_top(e_in_nc[1]), .Tile_X2Y2_B_EN_top(e_in_en_nc[1]),
        .Tile_X2Y2_C_OUT_top(fab_in[2]), .Tile_X2Y2_C_IN_top(e_in_nc[2]), .Tile_X2Y2_C_EN_top(e_in_en_nc[2]),
        .Tile_X2Y2_D_OUT_top(fab_in[3]), .Tile_X2Y2_D_IN_top(e_in_nc[3]), .Tile_X2Y2_D_EN_top(e_in_en_nc[3]),
        .Tile_X0Y3_SYS_RESET_RESET_top(user_reset),
        .Tile_X1Y3_A_OUT_top(clk),        .Tile_X1Y3_A_IN_top(s_out_nc[0]), .Tile_X1Y3_A_EN_top(s_en_nc[0]),
        .Tile_X1Y3_B_OUT_top(user_rst_n), .Tile_X1Y3_B_IN_top(s_out_nc[1]), .Tile_X1Y3_B_EN_top(s_en_nc[1]),
        .FrameData   (frame_data),
        .FrameStrobe (frame_strobe)
    );

    // ---- output cells: registered, then the parking gate (ARCHITECTURE.md §4, §6; F1).
    // The gate sits after the registers so that outputs are 0 in the very cycle `running` drops.
    reg [5:0] out_q;
    reg [7:0] io_out_q, io_oe_q;
    always @(posedge clk) begin
        if (!rst_n) begin
            out_q    <= 6'd0;
            io_out_q <= 8'd0;
            io_oe_q  <= 8'd0;
        end else begin
            out_q    <= {2'b00, e_out};
            io_out_q <= w_out;
            io_oe_q  <= w_en;
        end
    end

    assign uo_out  = {out_q & {6{running}}, host_irq, host_miso};
    assign uio_out = io_out_q & {8{running}};
    assign uio_oe  = io_oe_q  & {8{running}};

`ifdef FORMAL
    // F1 (VERIFICATION.md): whatever the fabric drives, the pins it owns are parked unless RUNNING.
    // formal/f1_isolation.sby leaves the fabric macro's outputs unconstrained.
    always @(*) begin
        if (!running) begin
            assert (uo_out[7:2] == 6'd0);
            assert (uio_out == 8'd0);
            assert (uio_oe == 8'd0);
        end
    end
`endif

    wire _unused = &{ena, fab_in[4], e_out_en, e_in_nc, e_in_en_nc, s_out_nc, s_en_nc,
                     h_wdata, h_wlast, h_wvalid, h_rready, 1'b0};
endmodule
