// Pin unit (ARCHITECTURE.md §7, §14 P-rules): a timed TX half fed by the unit's fabric consumer port and
// an RX half that loads the unit's fabric producer register. The port and the producer belong to the
// fabric (§4); the configuration block is trw_pin_cfg.v.
//
// FULL = 1 is U0-U1, FULL = 0 is U2-U5 (D-040). Both have the lean feature set (milestone A). FULL adds
// PULSE and the carrier in the TX half (milestone B1) and the BITSYNC engine trw_pin_bs.v (milestone B2/B3,
// in progress), which owns takes, pin A and loads while TXMODE and RXMODE are both `bitsync`.
//
// Timing contract:
//   - `cfg` is static while running (written while halted, §14 H1). `restart` (clock after a write to
//     the block) restarts every register of the unit, including the sticky flags (P-G15).
//   - `pads`: see trw_pin_io.v. Outputs `a_*` and `n_*` are registered (the level/OE registers of the
//     TX half) and gated combinationally by OD, C_OE (P15) and the registered "selected".
//   - `live` = 0 holds the unit off the fabric: it takes and loads nothing (P-G16).
//   - Token interface: see trw_pin_tx.v (take) and trw_pin_rx.v (load).
//   - `late` / `overrun` are sticky (P4, §4.5); `clr_*` clears them at the edge (a set in the same
//     clock wins).
`default_nettype none
`include "trw_defs.vh"
`include "trw_assert.vh"

module trw_pin_unit #(
    parameter FULL = 0,
    parameter FRAC = 8           // time fraction bits; 8 is the spec (16.8). FRAC < 8 is a measurement
                                 // variant only: it uses the top FRAC bits of the fraction fields
) (
    input  wire                    clk,
    input  wire                    rst_n,
    input  wire                    restart,
    input  wire                    live,
    input  wire [`TRW_PC_BITS-1:0] cfg,
    input  wire [23:0]             pads,
    // consumer port head (TX half)
    input  wire                    tx_avail,
    input  wire [1:0]              tx_tag,
    input  wire [15:0]             tx_data,
    output wire                    tx_take,
    // producer register (RX half)
    input  wire                    rx_free,
    output wire                    rx_load,
    output wire [1:0]              rx_tag,
    output wire [15:0]             rx_data,
    // pins A and N, to the pad owner mux
    output wire                    a_out,
    output wire                    a_oe,
    output wire                    n_out,
    output wire                    n_oe,
    // host-visible sticky flags
    output reg                     late,
    output reg                     overrun,
    input  wire                    clr_late,
    input  wire                    clr_overrun
);
    // ------------------------------------------------------------------ configuration fields (§7.2)
    wire [2:0]  txmode     = cfg[`TRW_PC_TXMODE_MSB:`TRW_PC_TXMODE_LSB];
    wire [1:0]  rxmode     = cfg[`TRW_PC_RXMODE_MSB:`TRW_PC_RXMODE_LSB];
    wire        order      = cfg[`TRW_PC_ORDER_LSB];
    wire        od         = cfg[`TRW_PC_OD_LSB];
    wire        idle       = cfg[`TRW_PC_IDLE_LSB];
    wire        autorearm  = cfg[`TRW_PC_AUTOREARM_LSB];
    wire        rx_echo    = cfg[`TRW_PC_RX_ECHO_LSB];
    wire        tx_lentok  = cfg[`TRW_PC_TX_LENTOK_LSB];
    wire        tx_preload = cfg[`TRW_PC_TX_PRELOAD_LSB];
    wire        stretch    = cfg[`TRW_PC_STRETCH_LSB];
    wire [4:0]  pin_a      = cfg[`TRW_PC_PIN_A_MSB:`TRW_PC_PIN_A_LSB];
    wire [4:0]  pin_b      = cfg[`TRW_PC_PIN_B_MSB:`TRW_PC_PIN_B_LSB];
    wire        rx_edge    = cfg[`TRW_PC_RX_EDGE_LSB];
    wire [1:0]  tx_edge    = cfg[`TRW_PC_TX_EDGE_MSB:`TRW_PC_TX_EDGE_LSB];
    wire [4:0]  pin_c      = cfg[`TRW_PC_PIN_C_MSB:`TRW_PC_PIN_C_LSB];
    wire        c_active   = cfg[`TRW_PC_C_ACTIVE_LSB];
    wire        c_oe       = cfg[`TRW_PC_C_OE_LSB];
    wire [4:0]  pin_s      = cfg[`TRW_PC_PIN_S_MSB:`TRW_PC_PIN_S_LSB];
    wire        ev_pin     = cfg[`TRW_PC_EV_PIN_LSB];
    wire [1:0]  ev_edge    = cfg[`TRW_PC_EV_EDGE_MSB:`TRW_PC_EV_EDGE_LSB];
    wire [1:0]  ev_qual    = cfg[`TRW_PC_EV_QUAL_MSB:`TRW_PC_EV_QUAL_LSB];
    wire        ev_reset   = cfg[`TRW_PC_EV_RESET_LSB];
    wire [23:0] period     = cfg[`TRW_PC_PERIOD_MSB:`TRW_PC_PERIOD_LSB];
    wire [7:0]  presc      = cfg[`TRW_PC_PRESC_MSB:`TRW_PC_PRESC_LSB];
    wire [23:0] sampleofs  = cfg[`TRW_PC_SAMPLEOFS_MSB:`TRW_PC_SAMPLEOFS_LSB];
    wire [3:0]  nbits      = cfg[`TRW_PC_NBITS_MSB:`TRW_PC_NBITS_LSB];
    wire [4:0]  rx_nbits   = cfg[`TRW_PC_RX_NBITS_MSB:`TRW_PC_RX_NBITS_LSB];
    wire [4:0]  rx_nbits2  = cfg[`TRW_PC_RX_NBITS2_MSB:`TRW_PC_RX_NBITS2_LSB];
    // PULSE and carrier (FULL units; on a lean unit these bits are not stored and read 0, D-040)
    wire [11:0] sym0_t1    = cfg[`TRW_PC_SYM0_T1_MSB:`TRW_PC_SYM0_T1_LSB];
    wire        sym0_first = cfg[`TRW_PC_SYM0_FIRST_LSB];
    wire [11:0] sym0_t2    = cfg[`TRW_PC_SYM0_T2_MSB:`TRW_PC_SYM0_T2_LSB];
    wire [11:0] sym1_t1    = cfg[`TRW_PC_SYM1_T1_MSB:`TRW_PC_SYM1_T1_LSB];
    wire        sym1_first = cfg[`TRW_PC_SYM1_FIRST_LSB];
    wire [11:0] sym1_t2    = cfg[`TRW_PC_SYM1_T2_MSB:`TRW_PC_SYM1_T2_LSB];
    wire [23:0] carrier    = cfg[`TRW_PC_CARRIER_MSB:`TRW_PC_CARRIER_LSB];
    // BITSYNC (FULL)
    wire [23:0] sjw        = cfg[`TRW_PC_SJW_MSB:`TRW_PC_SJW_LSB];
    wire [4:0]  idle_bits  = cfg[`TRW_PC_IDLE_BITS_MSB:`TRW_PC_IDLE_BITS_LSB];
    wire        resync     = cfg[`TRW_PC_RESYNC_LSB];
    wire [3:0]  stuff_n    = cfg[`TRW_PC_STUFF_N_MSB:`TRW_PC_STUFF_N_LSB];
    wire [1:0]  stuff_lvl  = cfg[`TRW_PC_STUFF_LVL_MSB:`TRW_PC_STUFF_LVL_LSB];
    wire [4:0]  crc_width  = cfg[`TRW_PC_CRC_WIDTH_MSB:`TRW_PC_CRC_WIDTH_LSB];
    wire [4:0]  crc_skip   = cfg[`TRW_PC_CRC_SKIP_MSB:`TRW_PC_CRC_SKIP_LSB];
    wire [15:0] crc_poly   = cfg[`TRW_PC_CRC_POLY_MSB:`TRW_PC_CRC_POLY_LSB];
    wire [15:0] crc_init   = cfg[`TRW_PC_CRC_INIT_MSB:`TRW_PC_CRC_INIT_LSB];
    wire [15:0] crc_res    = cfg[`TRW_PC_CRC_RES_MSB:`TRW_PC_CRC_RES_LSB];
    wire        bs_on      = (FULL != 0) && (txmode == `TRW_PCE_TXMODE_BITSYNC)
                                         && (rxmode == `TRW_PCE_RXMODE_BITSYNC);
    // PIN_N only matters to the pad owner mux (trw_pins.v), which reads it from the same block.

    // ------------------------------------------------------------------ pins in
    wire a_in, a_prev, b_in, b_prev, c_in, c_prev, sel, sel_q, sel_fall;
    trw_pin_io u_io (
        .clk (clk), .pads (pads), .pin_a (pin_a), .pin_s (pin_s), .pin_b (pin_b), .pin_c (pin_c),
        .idle (idle), .c_active (c_active),
        .a_in (a_in), .a_prev (a_prev), .b_in (b_in), .b_prev (b_prev), .c_in (c_in), .c_prev (c_prev),
        .sel (sel), .sel_q (sel_q), .sel_fall (sel_fall)
    );
    wire b_rise = b_in && !b_prev;
    wire b_fall = !b_in && b_prev;

    // ------------------------------------------------------------------ TX half
    wire lvl_t, oe, echo_t, rxset, smp, late_t, take_t;
    wire [4:0] rxset_n;
    trw_pin_tx #(.FULL (FULL), .FRAC (FRAC)) u_tx (
        .clk (clk), .rst_n (rst_n), .restart (restart), .live (live),
        .txmode (txmode), .order (order), .idle (idle), .tx_lentok (tx_lentok), .tx_preload (tx_preload),
        .stretch (stretch), .tx_edge (tx_edge), .period (period), .presc (presc), .nbits (nbits),
        .sym0_t1 (sym0_t1), .sym0_first (sym0_first), .sym0_t2 (sym0_t2),
        .sym1_t1 (sym1_t1), .sym1_first (sym1_first), .sym1_t2 (sym1_t2), .carrier (carrier),
        .a_in (a_in), .b_rise (b_rise), .b_fall (b_fall), .sel (sel), .sel_fall (sel_fall),
        .tx_avail (tx_avail && !bs_on), .tx_tag (tx_tag), .tx_data (tx_data), .tx_take (take_t),
        .lvl (lvl_t), .oe (oe), .echo (echo_t),
        .rxset (rxset), .rxset_n (rxset_n), .smp (smp), .late_set (late_t)
    );

    // B2a: pin A stays recessive (IDLE) in BITSYNC until the engine's TX queue exists (B2c)
    wire lvl  = bs_on ? idle : lvl_t;
    wire echo = bs_on ? 1'b0 : echo_t;

    // ------------------------------------------------------------------ RX half
    wire ovr_set, load_h, ovr_h;
    wire [1:0]  tag_h;
    wire [15:0] data_h;
    trw_pin_rx #(.FRAC (FRAC)) u_rx (
        .clk (clk), .rst_n (rst_n), .restart (restart), .live (live),
        .rxmode (rxmode), .order (order), .idle (idle), .autorearm (autorearm), .rx_echo (rx_echo),
        .rx_edge (rx_edge), .ev_pin (ev_pin), .ev_edge (ev_edge), .ev_qual (ev_qual), .ev_reset (ev_reset),
        .period (period), .sampleofs (sampleofs), .presc (presc), .nbits (nbits),
        .rx_nbits (rx_nbits), .rx_nbits2 (rx_nbits2),
        .a_in (a_in), .a_prev (a_prev), .b_in (b_in), .b_prev (b_prev), .c_in (c_in), .c_prev (c_prev),
        .sel (sel),
        .echo (echo), .rxset (rxset), .rxset_n (rxset_n), .smp (smp),
        .rx_free (rx_free), .rx_load (load_h), .rx_tag (tag_h), .rx_data (data_h), .ovr_set (ovr_h)
    );

    // ------------------------------------------------------------------ BITSYNC engine (FULL)
    // P-G28: the RX half's event generator keeps working in BITSYNC and wins a clock it loads in (EVENT
    // first, P19); the engine's token then counts as lost (OVERRUN).
    wire        load_b, ovr_b, bs_idle, bs_frame, bs_bnd, bs_smp, take_b, late_b;
    wire [1:0]  tag_b;
    wire [15:0] data_b;
    generate
        if (FULL != 0) begin : g_bs
            trw_pin_bs u_bs (
                .clk (clk), .rst_n (rst_n), .restart (restart), .live (live), .active (bs_on),
                .idle (idle), .order (order), .period (period), .sampleofs (sampleofs), .sjw (sjw),
                .idle_bits (idle_bits), .resync_both (resync), .nbits (nbits), .rx_nbits (rx_nbits),
                .stuff_n (stuff_n), .stuff_lvl (stuff_lvl), .crc_width (crc_width), .crc_skip (crc_skip),
                .crc_poly (crc_poly), .crc_init (crc_init), .crc_res (crc_res),
                .a_in (a_in), .a_prev (a_prev),
                .tx_avail (tx_avail && bs_on), .tx_tag (tx_tag), .tx_data (tx_data), .tx_take (take_b),
                .late_set (late_b),
                .rx_free (rx_free && !load_h), .rx_load (load_b), .rx_tag (tag_b), .rx_data (data_b),
                .ovr_set (ovr_b), .bus_idle (bs_idle), .in_frame (bs_frame), .bnd (bs_bnd), .smp (bs_smp)
            );
        end else begin : g_nobs
            assign load_b = 1'b0;  assign ovr_b = 1'b0;  assign tag_b = 2'd0;  assign data_b = 16'd0;
            assign bs_idle = 1'b0;  assign bs_frame = 1'b0;  assign bs_bnd = 1'b0;  assign bs_smp = 1'b0;
            assign take_b = 1'b0;  assign late_b = 1'b0;
            wire _unused_bs = &{1'b0, sjw, idle_bits, resync, stuff_n, stuff_lvl, crc_width, crc_skip,
                                crc_poly, crc_init, crc_res};
        end
    endgenerate
    assign rx_load = load_h || load_b;
    assign rx_tag  = load_h ? tag_h : tag_b;
    assign rx_data = load_h ? data_h : data_b;
    assign ovr_set = ovr_h || ovr_b;

    // In BITSYNC the engine takes (RX commands so far; its TX queue comes with B2c)
    assign tx_take  = bs_on ? take_b : take_t;
    wire   late_set = late_t || late_b;

    // ------------------------------------------------------------------ pins out (§7.1, P15, P29)
    // C_OE gates the output enable one clock after the synchronised change of pin C (sel_q).
    // OD: 1 releases (OE = 0), 0 drives low. Pin N is the push-pull complement of pin A with pin A's
    // output enable before OD (P-G2).
    wire en = oe && (!c_oe || sel_q);
    assign a_out = od ? 1'b0 : lvl;
    assign a_oe  = od ? (en && !lvl) : en;
    assign n_out = !lvl;
    assign n_oe  = en;

`ifdef TRW_ASSERT_ON
    wire od_drives_high = od && a_oe && a_out;
    wire load_not_free  = rx_load && !rx_free;
    `TRW_ASSERT(!od_drives_high, "an open-drain pin A drives high")
    `TRW_ASSERT(!load_not_free, "the RX half loads a producer that is not free (4.5)")
`endif

    // ------------------------------------------------------------------ sticky flags
    always @(posedge clk) begin
        if (!rst_n || restart) begin
            late    <= 1'b0;
            overrun <= 1'b0;
        end else begin
            late    <= late_set || (late && !clr_late);
            overrun <= ovr_set || (overrun && !clr_overrun);
        end
    end

    // Optional-feature fields (FULL) and unused block bits: used from milestone B on.
    /* verilator lint_off UNUSEDPARAM */
    localparam HAS_OPT = FULL;
    /* verilator lint_on UNUSEDPARAM */
    wire _unused = &{1'b0, cfg, bs_idle, bs_frame, bs_bnd, bs_smp};
endmodule
