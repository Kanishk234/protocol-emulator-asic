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
 * Fabric: G1 (arch/warp_g1, D-024, D-026): G0's 4 x 3 grid with one LUT4x8 slot (X2Y2) holding the
 * primitive tile PRIM2T2S (2 timers + 2 shift registers) = 88 LUT4+FF, macro `warp_g1`. Its 36 IO
 * cells are numbered below (cell_*[i]); each has a pad side into the fabric (cell_pad, the tile's
 * OUT_top) and two fabric outputs (cell_val = IN_top, cell_en = EN_top). The pin map for user
 * designs is arch/warp_g1/pins.csv (same as G0's); this file must match it (tools/compile tests check).
 *    0- 7  west X0Y1/X0Y2 A-D   FAB_IO0..7 (uio)
 *    8-11  west X0Y3 A-D        host channel H0-H3
 *   12-16  east X5Y1 A-D, X5Y2 A  FAB_IN0..4
 *   17-22  east X5Y2 B-D, X5Y3 A-C  FAB_OUT0..5
 *   23     east X5Y3 D          host channel H14
 *   24-27  north X1..X4 Y0 A    host channel H4-H7
 *   28-29  south X1Y4 A/B       clock, user reset
 *   30-35  south X2..X4 Y4 A/B  host channel H8-H13
 * Host channel (ARCHITECTURE §7.3): into the fabric H0-H7 h_wdata, H8 h_wlast, H9 h_wvalid,
 * H10 h_rready; out of the fabric (value wire) H0-H7 h_rdata, H8 h_rvalid, H9 h_wready,
 * H10 h_attention, and (enable wire) H0-H7 h_status.
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
    localparam integer ROWS = 5, COLS = 6;

    // ---- reset (BUGS #18): the rst_n pin is asynchronous to clk. Two flops make its assertion
    // and its release land on clock edges; every block is reset from rst_s_n (low from 2 clocks
    // after rst_n falls until 2 clocks after it rises). The configuration path (FABulous's
    // ConfigFSM, asynchronous reset) gets its own copy one flop later, rst_cfg_n, so no net is
    // used both as a synchronous and as an asynchronous reset. The synchronizer has no reset of
    // its own: it is the reset source.
    reg  [1:0] rst_sync;
    reg        rst_cfg_n;
    always @(posedge clk) begin
        rst_sync  <= {rst_sync[0], rst_n};
        rst_cfg_n <= rst_sync[1];
    end
    wire rst_s_n = rst_sync[1];

    // ---- IO cells of the fabric (numbering above)
    wire [35:0] cell_pad;             // into the fabric
    wire [35:0] cell_val, cell_en;    // out of the fabric
    // host channel cell of H0..H14
    function integer hcell(input integer h);
        begin
            if (h < 4)       hcell = 8 + h;
            else if (h < 8)  hcell = 24 + (h - 4);
            else if (h < 14) hcell = 30 + (h - 8);
            else             hcell = 23;
        end
    endfunction

    // ---- shell
    wire        host_miso, host_irq;
    wire [31:0] cfg_word;
    wire        cfg_strobe, cfg_restart;
    wire        running, user_reset;
    wire [7:0]  h_wdata, h_rdata, h_status;
    wire        h_wlast, h_wvalid, h_wready, h_rvalid, h_rready, h_attention;

    wp_shell #(.ARCH_VERSION(16'h0003)) u_shell (
        .clk         (clk),
        .rst_n       (rst_s_n),
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
        .h_wready    (h_wready),
        .h_rdata     (h_rdata),
        .h_rvalid    (h_rvalid),
        .h_rready    (h_rready),
        .h_status    (h_status),
        .h_attention (h_attention)
    );

    // ---- configuration path
    wire [32*ROWS-1:0] frame_data;
    wire [20*COLS-1:0] frame_strobe;
    wp_fabric_cfg #(.ROWS(ROWS), .COLS(COLS), .FRAME_BITS(32), .MAX_FRAMES(20)) u_cfg (
        .clk          (clk),
        .rst_n        (rst_cfg_n),
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
        .clk(clk), .rst_n(rst_s_n), .d({ui_in[7:3], uio_in}), .q({fab_in, io_in})
    );

    reg user_rst_n;
    always @(posedge clk) begin
        if (!rst_s_n) user_rst_n <= 1'b0;
        else          user_rst_n <= !user_reset;
    end

    // ---- pads into the fabric
    genvar g;
    generate
        for (g = 0; g < 8; g = g + 1) begin : g_io
            assign cell_pad[g] = io_in[g];
        end
        for (g = 0; g < 5; g = g + 1) begin : g_in
            assign cell_pad[12 + g] = fab_in[g];
        end
        for (g = 0; g < 6; g = g + 1) begin : g_out
            assign cell_pad[17 + g] = 1'b0;           // FAB_OUT cells: output only
        end
        for (g = 0; g < 8; g = g + 1) begin : g_hw
            assign cell_pad[hcell(g)]   = h_wdata[g];
            assign h_rdata[g]           = cell_val[hcell(g)];
            assign h_status[g]          = cell_en[hcell(g)];
        end
        for (g = 11; g < 15; g = g + 1) begin : g_hspare
            assign cell_pad[hcell(g)] = 1'b0;
        end
    endgenerate
    assign cell_pad[hcell(8)]  = h_wlast;
    assign cell_pad[hcell(9)]  = h_wvalid;
    assign cell_pad[hcell(10)] = h_rready;
    assign cell_pad[28]        = clk;
    assign cell_pad[29]        = user_rst_n;
    assign h_rvalid    = cell_val[hcell(8)];
    assign h_wready    = cell_val[hcell(9)];
    assign h_attention = cell_val[hcell(10)];

    // ---- fabric
    warp_g1 u_fabric (
        .Tile_X0Y1_A_OUT_top(cell_pad[0]), .Tile_X0Y1_A_IN_top(cell_val[0]), .Tile_X0Y1_A_EN_top(cell_en[0]),
        .Tile_X0Y1_B_OUT_top(cell_pad[1]), .Tile_X0Y1_B_IN_top(cell_val[1]), .Tile_X0Y1_B_EN_top(cell_en[1]),
        .Tile_X0Y1_C_OUT_top(cell_pad[2]), .Tile_X0Y1_C_IN_top(cell_val[2]), .Tile_X0Y1_C_EN_top(cell_en[2]),
        .Tile_X0Y1_D_OUT_top(cell_pad[3]), .Tile_X0Y1_D_IN_top(cell_val[3]), .Tile_X0Y1_D_EN_top(cell_en[3]),
        .Tile_X0Y2_A_OUT_top(cell_pad[4]), .Tile_X0Y2_A_IN_top(cell_val[4]), .Tile_X0Y2_A_EN_top(cell_en[4]),
        .Tile_X0Y2_B_OUT_top(cell_pad[5]), .Tile_X0Y2_B_IN_top(cell_val[5]), .Tile_X0Y2_B_EN_top(cell_en[5]),
        .Tile_X0Y2_C_OUT_top(cell_pad[6]), .Tile_X0Y2_C_IN_top(cell_val[6]), .Tile_X0Y2_C_EN_top(cell_en[6]),
        .Tile_X0Y2_D_OUT_top(cell_pad[7]), .Tile_X0Y2_D_IN_top(cell_val[7]), .Tile_X0Y2_D_EN_top(cell_en[7]),
        .Tile_X0Y3_A_OUT_top(cell_pad[8]), .Tile_X0Y3_A_IN_top(cell_val[8]), .Tile_X0Y3_A_EN_top(cell_en[8]),
        .Tile_X0Y3_B_OUT_top(cell_pad[9]), .Tile_X0Y3_B_IN_top(cell_val[9]), .Tile_X0Y3_B_EN_top(cell_en[9]),
        .Tile_X0Y3_C_OUT_top(cell_pad[10]), .Tile_X0Y3_C_IN_top(cell_val[10]), .Tile_X0Y3_C_EN_top(cell_en[10]),
        .Tile_X0Y3_D_OUT_top(cell_pad[11]), .Tile_X0Y3_D_IN_top(cell_val[11]), .Tile_X0Y3_D_EN_top(cell_en[11]),
        .Tile_X5Y1_A_OUT_top(cell_pad[12]), .Tile_X5Y1_A_IN_top(cell_val[12]), .Tile_X5Y1_A_EN_top(cell_en[12]),
        .Tile_X5Y1_B_OUT_top(cell_pad[13]), .Tile_X5Y1_B_IN_top(cell_val[13]), .Tile_X5Y1_B_EN_top(cell_en[13]),
        .Tile_X5Y1_C_OUT_top(cell_pad[14]), .Tile_X5Y1_C_IN_top(cell_val[14]), .Tile_X5Y1_C_EN_top(cell_en[14]),
        .Tile_X5Y1_D_OUT_top(cell_pad[15]), .Tile_X5Y1_D_IN_top(cell_val[15]), .Tile_X5Y1_D_EN_top(cell_en[15]),
        .Tile_X5Y2_A_OUT_top(cell_pad[16]), .Tile_X5Y2_A_IN_top(cell_val[16]), .Tile_X5Y2_A_EN_top(cell_en[16]),
        .Tile_X5Y2_B_OUT_top(cell_pad[17]), .Tile_X5Y2_B_IN_top(cell_val[17]), .Tile_X5Y2_B_EN_top(cell_en[17]),
        .Tile_X5Y2_C_OUT_top(cell_pad[18]), .Tile_X5Y2_C_IN_top(cell_val[18]), .Tile_X5Y2_C_EN_top(cell_en[18]),
        .Tile_X5Y2_D_OUT_top(cell_pad[19]), .Tile_X5Y2_D_IN_top(cell_val[19]), .Tile_X5Y2_D_EN_top(cell_en[19]),
        .Tile_X5Y3_A_OUT_top(cell_pad[20]), .Tile_X5Y3_A_IN_top(cell_val[20]), .Tile_X5Y3_A_EN_top(cell_en[20]),
        .Tile_X5Y3_B_OUT_top(cell_pad[21]), .Tile_X5Y3_B_IN_top(cell_val[21]), .Tile_X5Y3_B_EN_top(cell_en[21]),
        .Tile_X5Y3_C_OUT_top(cell_pad[22]), .Tile_X5Y3_C_IN_top(cell_val[22]), .Tile_X5Y3_C_EN_top(cell_en[22]),
        .Tile_X5Y3_D_OUT_top(cell_pad[23]), .Tile_X5Y3_D_IN_top(cell_val[23]), .Tile_X5Y3_D_EN_top(cell_en[23]),
        .Tile_X1Y0_A_OUT_top(cell_pad[24]), .Tile_X1Y0_A_IN_top(cell_val[24]), .Tile_X1Y0_A_EN_top(cell_en[24]),
        .Tile_X2Y0_A_OUT_top(cell_pad[25]), .Tile_X2Y0_A_IN_top(cell_val[25]), .Tile_X2Y0_A_EN_top(cell_en[25]),
        .Tile_X3Y0_A_OUT_top(cell_pad[26]), .Tile_X3Y0_A_IN_top(cell_val[26]), .Tile_X3Y0_A_EN_top(cell_en[26]),
        .Tile_X4Y0_A_OUT_top(cell_pad[27]), .Tile_X4Y0_A_IN_top(cell_val[27]), .Tile_X4Y0_A_EN_top(cell_en[27]),
        .Tile_X1Y4_A_OUT_top(cell_pad[28]), .Tile_X1Y4_A_IN_top(cell_val[28]), .Tile_X1Y4_A_EN_top(cell_en[28]),
        .Tile_X1Y4_B_OUT_top(cell_pad[29]), .Tile_X1Y4_B_IN_top(cell_val[29]), .Tile_X1Y4_B_EN_top(cell_en[29]),
        .Tile_X2Y4_A_OUT_top(cell_pad[30]), .Tile_X2Y4_A_IN_top(cell_val[30]), .Tile_X2Y4_A_EN_top(cell_en[30]),
        .Tile_X2Y4_B_OUT_top(cell_pad[31]), .Tile_X2Y4_B_IN_top(cell_val[31]), .Tile_X2Y4_B_EN_top(cell_en[31]),
        .Tile_X3Y4_A_OUT_top(cell_pad[32]), .Tile_X3Y4_A_IN_top(cell_val[32]), .Tile_X3Y4_A_EN_top(cell_en[32]),
        .Tile_X3Y4_B_OUT_top(cell_pad[33]), .Tile_X3Y4_B_IN_top(cell_val[33]), .Tile_X3Y4_B_EN_top(cell_en[33]),
        .Tile_X4Y4_A_OUT_top(cell_pad[34]), .Tile_X4Y4_A_IN_top(cell_val[34]), .Tile_X4Y4_A_EN_top(cell_en[34]),
        .Tile_X4Y4_B_OUT_top(cell_pad[35]), .Tile_X4Y4_B_IN_top(cell_val[35]), .Tile_X4Y4_B_EN_top(cell_en[35]),
        .Tile_X0Y4_SYS_RESET_RESET_top(user_reset),
        .FrameData   (frame_data),
        .FrameStrobe (frame_strobe)
    );

    // ---- output cells: registered, then the parking gate (ARCHITECTURE.md §4, §6; F1).
    // The gate sits after the registers so that outputs are 0 in the very cycle `running` drops.
    reg [5:0] out_q;
    reg [7:0] io_out_q, io_oe_q;
    always @(posedge clk) begin
        if (!rst_s_n) begin
            out_q    <= 6'd0;
            io_out_q <= 8'd0;
            io_oe_q  <= 8'd0;
        end else begin
            out_q    <= cell_val[22:17];
            io_out_q <= cell_val[7:0];
            io_oe_q  <= cell_en[7:0];
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

    // unused: FAB_OUT/FAB_IN cells' other wires, spare host-channel cells, clock/reset cells
    wire _unused = &{ena, cell_en[35:8], cell_val[35:23], cell_val[16:8], 1'b0};
endmodule
