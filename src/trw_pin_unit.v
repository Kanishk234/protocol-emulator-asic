// Pin unit (ARCHITECTURE.md §7, §14 P-rules): a timed TX half fed by the unit's fabric consumer port and
// an RX half that loads the unit's fabric producer register. The port and the producer belong to the
// fabric (§4); the configuration block is trw_pin_cfg.v.
//
// FULL = 1 is U0-U1, FULL = 0 is U2-U5 (D-040). Milestone A implements the lean feature set for both;
// PULSE, carrier and BITSYNC (FULL only) come in milestone B, so for now FULL only changes which
// configuration bits exist (trw_pin_cfg.v).
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
    wire lvl, oe, echo, rxset, smp, late_set;
    wire [4:0] rxset_n;
    trw_pin_tx #(.FRAC (FRAC)) u_tx (
        .clk (clk), .rst_n (rst_n), .restart (restart), .live (live),
        .txmode (txmode), .order (order), .idle (idle), .tx_lentok (tx_lentok), .tx_preload (tx_preload),
        .stretch (stretch), .tx_edge (tx_edge), .period (period), .presc (presc), .nbits (nbits),
        .a_in (a_in), .b_rise (b_rise), .b_fall (b_fall), .sel (sel), .sel_fall (sel_fall),
        .tx_avail (tx_avail), .tx_tag (tx_tag), .tx_data (tx_data), .tx_take (tx_take),
        .lvl (lvl), .oe (oe), .echo (echo),
        .rxset (rxset), .rxset_n (rxset_n), .smp (smp), .late_set (late_set)
    );

    // ------------------------------------------------------------------ RX half
    wire ovr_set;
    trw_pin_rx #(.FRAC (FRAC)) u_rx (
        .clk (clk), .rst_n (rst_n), .restart (restart), .live (live),
        .rxmode (rxmode), .order (order), .idle (idle), .autorearm (autorearm), .rx_echo (rx_echo),
        .rx_edge (rx_edge), .ev_pin (ev_pin), .ev_edge (ev_edge), .ev_qual (ev_qual), .ev_reset (ev_reset),
        .period (period), .sampleofs (sampleofs), .presc (presc), .nbits (nbits),
        .rx_nbits (rx_nbits), .rx_nbits2 (rx_nbits2),
        .a_in (a_in), .a_prev (a_prev), .b_in (b_in), .b_prev (b_prev), .c_in (c_in), .c_prev (c_prev),
        .sel (sel),
        .echo (echo), .rxset (rxset), .rxset_n (rxset_n), .smp (smp),
        .rx_free (rx_free), .rx_load (rx_load), .rx_tag (rx_tag), .rx_data (rx_data), .ovr_set (ovr_set)
    );

    // ------------------------------------------------------------------ pins out (§7.1, P15, P29)
    // C_OE gates the output enable one clock after the synchronised change of pin C (sel_q).
    // OD: 1 releases (OE = 0), 0 drives low. Pin N is the push-pull complement of pin A with pin A's
    // output enable before OD (P-G2).
    wire en = oe && (!c_oe || sel_q);
    assign a_out = od ? 1'b0 : lvl;
    assign a_oe  = od ? (en && !lvl) : en;
    assign n_out = !lvl;
    assign n_oe  = en;

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
    wire _unused = &{1'b0, cfg};
endmodule
