// Pin unit, TX half (ARCHITECTURE.md §7.3, §14 P3, P4, P6, P9, P11, P12, P14-P16, P18, P19): takes tokens
// from the unit's consumer port and drives pin A's level and output enable. Lean feature set: modes
// LEVEL, SHIFT (timed or linked to pin B) and CLKGEN; ops LEVEL, OE, CLK, GAP, SYNC, SETN, WAIT, SAMPLE.
//
// Timing contract:
//   - Clock n: `tx_take` = 1 takes the head token (the port applies it at edge n). It is combinational
//     from the head (`tx_avail`, `tx_tag`, `tx_data`) and this block's registers; nothing depends on the
//     producer (§14 F3).
//   - An action "at edge k" is computed in clock k and lands in `lvl`/`oe`/`echo` at edge k, so a token
//     taken in clock n changes the pad register at edge n+1 at the earliest (P3). `rxset`/`smp` are 1
//     in clock k, and the RX half applies them at edge k.
//
// The cursor (P4) is kept relative to the present, in ticks, so no multiplier is needed for
// `delay * PRESC`: E = now - floor(cursor) = eq * PRESC + er (0 <= er < PRESC) clocks, plus the cursor's
// fraction cf in 1/256 clocks. A delay of d ticks is `eq -= d`; the cursor is in the past or now when
// eq >= 0, and an action at the cursor is due at the next edge when E = -1. While a shift or clock burst
// runs, its own bit timer `bt` (16.9 clocks to the next boundary) gives the cursor instead (the burst
// ends at a boundary, so E there is -1 or 0).
//
// Choices the documents leave open are marked P-G<n> (docs/reports/PIN_UNIT_RTL.md §6).
`default_nettype none
`include "trw_defs.vh"

module trw_pin_tx #(
    parameter FRAC = 8           // fraction bits of time arithmetic (8 = the spec's 16.8; less = measurement only)
) (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        restart,     // a configuration write to this unit: restart (P-G15)
    input  wire        live,        // the chip is running: tokens may be taken (P-G16)
    // configuration (static while running)
    input  wire [2:0]  txmode,
    input  wire        order,
    input  wire        idle,
    input  wire        tx_lentok,
    input  wire        tx_preload,
    input  wire        stretch,
    input  wire [1:0]  tx_edge,
    input  wire [23:0] period,      // 16.8 clocks
    input  wire [7:0]  presc,       // clocks per tick - 1
    input  wire [3:0]  nbits,       // TX shift length - 1
    // pins
    input  wire        a_in,
    input  wire        b_rise,
    input  wire        b_fall,
    input  wire        sel,
    input  wire        sel_fall,
    // consumer port head
    input  wire        tx_avail,
    input  wire [1:0]  tx_tag,
    input  wire [15:0] tx_data,
    output wire        tx_take,
    // pin A (registered)
    output wire        lvl,
    output reg         oe,
    output reg         echo,        // pin A holds one of our shifted bits (P13 taint)
    // RX actions, this clock
    output reg         rxset,
    output reg  [4:0]  rxset_n,
    output reg         smp,
    output wire        late_set
);
    // ------------------------------------------------------------------ modes and the head token
    wire m_shift = (txmode == `TRW_PCE_TXMODE_SHIFT);
    wire m_clk   = (txmode == `TRW_PCE_TXMODE_CLKGEN);
    wire m_level = !m_shift && !m_clk;           // lean: the PULSE / BITSYNC codes act as LEVEL (D-040)
    wire linked  = m_shift && (tx_edge != `TRW_PCE_TX_EDGE_NONE);
    wire tshift  = m_shift && !linked;

    wire [3:0]  op  = tx_data[15:12];
    wire [11:0] arg = tx_data[11:0];
    wire t_data = (tx_tag == `TRW_TAG_DATA);
    wire t_ctrl = (tx_tag == `TRW_TAG_CTRL);
    wire t_ev   = (tx_tag == `TRW_TAG_EVENT);
    wire c_lvl  = t_ctrl && (op == `TRW_CMD_LEVEL);
    wire c_oe   = t_ctrl && (op == `TRW_CMD_OE);
    wire c_gap  = t_ctrl && (op == `TRW_CMD_GAP);
    wire c_sync = t_ctrl && (op == `TRW_CMD_SYNC);
    wire c_setn = t_ctrl && (op == `TRW_CMD_SETN);
    wire c_wait = t_ctrl && (op == `TRW_CMD_WAIT);
    wire c_smp  = t_ctrl && (op == `TRW_CMD_SAMPLE);
    wire c_clk  = t_ctrl && (op == `TRW_CMD_CLK);

    wire h_lvl   = c_lvl || (m_level && (t_data || t_ev));   // P12: DATA/EVENT drive data[0] in LEVEL
    wire h_rxs   = c_setn && arg[5];                          // P18
    wire h_setn  = c_setn && !arg[5];
    wire h_shift = t_data && tshift;
    wire h_lk    = t_data && linked;
    wire h_clk   = c_clk && m_clk && (arg[7:0] != 8'd0);     // P-G5: CLK outside CLKGEN, or n = 0, is ignored
    wire [11:0] h_d = (c_lvl || c_oe) ? {1'b0, arg[10:0]} : (c_gap || c_smp) ? arg : 12'd0;
    wire        h_v = (c_lvl || c_oe) ? arg[11] : tx_data[0];

    // ------------------------------------------------------------------ state
    localparam K_LVL = 3'd0, K_OE = 3'd1, K_RXS = 3'd2, K_SMP = 3'd3, K_START = 3'd4;

    reg  [15:0] eq;          // signed ticks (see above)
    reg  [7:0]  er;
    localparam BW = 17 + FRAC;                 // burst timer: 16 integer bits, FRAC + 1 fraction bits
    localparam [BW-1:0] BT_ONE = 1 << (FRAC + 1);
    wire [15+FRAC:0] per = period[23:8-FRAC];  // PERIOD, top FRAC bits of its fraction

    reg  [FRAC-1:0] cf;
    reg         e_own;       // a take during a burst's tail made eq/er authoritative again
    reg         pend_v;      // one timed action waiting for its time (P3 allows no more)
    reg  [2:0]  pend_k;
    reg  [4:0]  pend_a;
    reg         due_lvl_v, due_lvl, due_oe_v, due_oe;
    reg         p_act;       // a timed shift or clock burst is running
    reg  [BW-1:0] bt;        // 16.(FRAC+1) clocks from this clock to the next boundary
    reg  [4:0]  rem;         // bits still to drive (timed or linked shift)
    reg  [3:0]  bi;          // index of the next bit in sreg
    reg  [15:0] sreg;
    reg  [8:0]  cn;          // CLKGEN periods still to start
    reg         ph;          // CLKGEN: the next boundary drives ACTIVE
    reg         p_first;     // CLKGEN: the next boundary is the burst's first
    reg         p_sw;        // CLKGEN STRETCH: waiting for pin A to read IDLE
    reg         lk_ret;      // linked: return to IDLE on the next TX_EDGE
    reg         lk_pre;      // linked: preloaded bit 0 goes out at this clock's edge (P9)
    reg         w_v, w_rise; // WAIT (P16)
    reg         ntx_v;       // SETN tx override of NBITS
    reg  [3:0]  ntx;
    reg         lvx;         // pin A level XOR IDLE, so an idle unit shows IDLE whatever IDLE is

    assign lvl = lvx ^ idle;

    // ------------------------------------------------------------------ the running shift / burst
    wire [15:0] bt_i    = bt[BW-1:FRAC+1];
    wire        fire    = p_act && !p_sw && (bt_i == 16'd0);
    wire [BW-1:0] step  = m_clk ? {1'b0, per} : {per, 1'b0};  // CLKGEN: half periods (P11)
    wire [BW:0] bt_add  = {1'b0, bt} + {1'b0, step};
    wire [15:0] bt_add_i = bt_add[BW-1:FRAC+1];
    wire        a_idle  = (a_in == idle);

    wire s_tail  = tshift && p_act && (rem == 5'd0);                  // next boundary: return to IDLE
    wire s_lastb = tshift && fire && (rem == 5'd1);                   // drives the last bit now
    wire c_tail  = m_clk && p_act && !stretch && !p_sw && !ph && !p_first && (cn == 9'd0);
    wire c_lasta = m_clk && fire && ph && !stretch && (cn == 9'd1);   // the last ACTIVE half starts now
    wire c_swend = m_clk && p_act && p_sw && (cn == 9'd0) && a_idle;  // STRETCH: burst ends now
    wire tail    = s_tail || c_tail;
    wire lastb   = s_lastb || c_lasta;
    wire p_end   = (tail && fire) || c_swend;                          // the burst ends at this edge
    // P3: all pending pad actions at edges <= n+1
    wire tail_ok = (tail && (bt_i <= 16'd1)) || (lastb && (bt_add_i == 16'd1)) || c_swend;
    wire pe_m1   = (tail && (bt_i == 16'd1)) || (lastb && (bt_add_i == 16'd1));
    wire pe_fv   = lastb || c_swend;                                   // the end time is known now
    wire [FRAC-1:0] pe_f = c_swend ? {FRAC{1'b0}} : bt_add[FRAC:1];

    // ------------------------------------------------------------------ the cursor, this clock
    wire use_pe = p_act && !e_own;
    wire [15:0] q_eff = use_pe ? (pe_m1 ? 16'hffff : 16'h0000) : eq;
    wire [7:0]  r_eff = use_pe ? (pe_m1 ? presc : 8'h00) : er;
    wire [FRAC-1:0] cf_eff = pe_fv ? pe_f : cf;
    wire w_fire = w_v && (w_rise ? b_rise : b_fall);                   // P16: cursor := earliest
    wire [15:0] q_b  = w_fire ? 16'hffff : q_eff;
    wire [7:0]  r_b  = w_fire ? presc : r_eff;
    wire [FRAC-1:0] cf_b = w_fire ? {FRAC{1'b0}} : cf_eff;

    wire [16:0] q_sub = {q_b[15], q_b} - {5'd0, h_d};                   // cursor + d * PRESC
    wire        q_uf  = (q_sub[16:15] == 2'b10);                       // below -32768 ticks (P-G3)
    wire        late  = !q_sub[16];                                    // earlier than the earliest edge
    wire        at_m1 = (q_sub[15:0] == 16'hffff) && (r_b == presc);   // exactly the earliest edge

    // ------------------------------------------------------------------ take
    wire h_timed = h_lvl || c_oe || h_rxs || c_smp || h_shift || h_clk;
    wire h_cur   = h_timed || c_gap || c_sync;
    wire clk_run = m_clk && p_act && !p_end;
    wire h_ext   = h_clk && clk_run;                                   // P11: extends the burst
    wire [9:0] cn_sum = {1'b0, cn} + {2'b0, arg[7:0]};
    wire pend_go = pend_v && (eq == 16'hffff) && (er == presc);        // due at the next edge
    wire pend_ok = !pend_v || (pend_go && (pend_k != K_START));
    wire lk_ok   = !linked || ((rem == 5'd0) && !lk_pre);              // P6: all bits are out
    wire w_ok    = !w_v || w_fire;
    wire can     = h_ext ? !cn_sum[9]
                         : (pend_ok && w_ok && lk_ok && (!p_act || tail_ok) && !(h_cur && q_uf));
    assign tx_take = live && tx_avail && can;

    wire tk        = tx_take;
    wire tk_timed  = tk && h_timed && !h_ext;
    wire tk_now    = tk_timed && (late || at_m1);                      // acts at the next edge
    wire tk_late   = tk_timed && late;
    wire start_new = (h_shift || (h_clk && !h_ext));
    wire load_proc = (pend_go && (pend_k == K_START)) || (tk_now && start_new);
    wire [FRAC-1:0] p_frac = tk_late ? {FRAC{1'b0}} : cf_b;

    assign late_set = tk_late && (c_lvl || c_oe) && (arg[10:0] != 11'd0);   // P4

    // shift length and payload (P14, SETN)
    wire [3:0]  lenm1 = tx_lentok ? tx_data[15:12] : (ntx_v ? ntx : nbits);
    wire [15:0] pay   = tx_lentok ? {4'h0, tx_data[11:0]} : tx_data;
    wire [3:0]  bi_nx = order ? bi - 4'd1 : bi + 4'd1;
    wire        bit_o = sreg[bi];

    // ------------------------------------------------------------------ linked shift (P6, P9, P15)
    wire lk_edge  = linked && sel && ((tx_edge == `TRW_PCE_TX_EDGE_RISE) ? b_rise : b_fall);   // P-G9
    wire lk_abort = linked && sel_fall && ((rem != 5'd0) || lk_ret || lk_pre);
    wire lk_bit   = !lk_abort && (lk_pre || (lk_edge && (rem != 5'd0)));
    wire lk_idle  = lk_abort || (!lk_pre && lk_edge && (rem == 5'd0) && lk_ret);

    // ------------------------------------------------------------------ pad drive at this edge
    // Priority (a later token wins an edge): shifted bit / clock edge > LEVEL > return to IDLE.
    wire s_bit  = tshift && fire && (rem != 5'd0);
    wire s_end  = tshift && fire && (rem == 5'd0);
    wire k_hi   = m_clk && fire && (ph || p_first);                    // first IDLE, or ACTIVE
    wire k_rel  = m_clk && fire && !ph && !p_first;                    // release (IDLE)
    wire d_hi   = s_bit || lk_bit || k_hi;
    wire d_hi_v = (s_bit || lk_bit) ? bit_o : (ph ? !idle : idle);
    wire d_lo   = s_end || lk_idle || k_rel;
    wire [0:0] nlvx = d_hi ? (d_hi_v ^ idle) : due_lvl_v ? (due_lvl ^ idle) : d_lo ? 1'b0 : lvx;
    wire       necho = d_hi ? (s_bit || lk_bit) : (due_lvl_v || d_lo) ? 1'b0 : echo;

    // ------------------------------------------------------------------ next cursor
    reg [15:0] qn;
    reg [7:0]  rn;
    always @* begin
        qn = q_b;
        rn = r_b;
        if (tk && !h_ext) begin
            if (c_sync || tk_late) begin
                qn = 16'hffff;             // cursor := earliest
                rn = presc;
            end else if (c_gap || tk_timed) begin
                qn = q_sub[15:0];
            end
        end
    end
    wire        r_wrap = (rn == presc);
    wire [15:0] q_inc  = (r_wrap && (qn != 16'h7fff)) ? qn + 16'd1 : qn;
    wire [7:0]  r_inc  = r_wrap ? 8'h00 : rn + 8'd1;

    always @(posedge clk) begin
        if (!rst_n || restart) begin
            eq <= 16'h0000;  er <= 8'h00;  cf <= {FRAC{1'b0}};  e_own <= 1'b0;
            pend_v <= 1'b0;  pend_k <= K_LVL;  pend_a <= 5'd0;
            due_lvl_v <= 1'b0;  due_lvl <= 1'b0;  due_oe_v <= 1'b0;  due_oe <= 1'b0;
            rxset <= 1'b0;  rxset_n <= 5'd0;  smp <= 1'b0;
            p_act <= 1'b0;  bt <= {BW{1'b0}};  rem <= 5'd0;  bi <= 4'd0;  sreg <= 16'h0000;
            cn <= 9'd0;  ph <= 1'b0;  p_first <= 1'b0;  p_sw <= 1'b0;
            lk_ret <= 1'b0;  lk_pre <= 1'b0;  w_v <= 1'b0;  w_rise <= 1'b0;
            ntx_v <= 1'b0;  ntx <= 4'd0;
            lvx <= 1'b0;  oe <= 1'b1;  echo <= 1'b0;      // P-G1: output enabled after reset
        end else begin
            // cursor
            eq <= q_inc;
            er <= r_inc;
            cf <= ((tk && !h_ext && (c_sync || tk_late)) || w_fire) ? {FRAC{1'b0}} : cf_eff;
            if (load_proc)
                e_own <= 1'b0;
            else if (tk && !h_ext)
                e_own <= 1'b1;

            // pending action -> due at the next edge
            if (tk_timed && !tk_now) begin
                pend_v <= 1'b1;
                pend_k <= h_lvl ? K_LVL : c_oe ? K_OE : h_rxs ? K_RXS : c_smp ? K_SMP : K_START;
                pend_a <= (h_lvl || c_oe) ? {4'd0, h_v} : arg[4:0];
            end else if (pend_go) begin
                pend_v <= 1'b0;
            end
            due_lvl_v <= (pend_go && pend_k == K_LVL) || (tk_now && h_lvl);
            due_lvl   <= (tk_now && h_lvl) ? h_v : pend_a[0];
            due_oe_v  <= (pend_go && pend_k == K_OE) || (tk_now && c_oe);
            due_oe    <= (tk_now && c_oe) ? h_v : pend_a[0];
            rxset     <= (pend_go && pend_k == K_RXS) || (tk_now && h_rxs);
            rxset_n   <= (tk_now && h_rxs) ? arg[4:0] : pend_a;
            smp       <= (pend_go && pend_k == K_SMP) || (tk_now && c_smp);

            // pad registers
            lvx  <= nlvx;
            echo <= necho;
            if (due_oe_v)
                oe <= due_oe;

            // SETN tx (n = 0 or 17..31 means 16, P4)
            if (tk && h_setn) begin
                ntx_v <= 1'b1;
                ntx   <= ((arg[4:0] == 5'd0) || (arg[4:0] > 5'd16)) ? 4'd15 : arg[3:0] - 4'd1;
            end

            // WAIT
            if (tk && c_wait) begin
                w_v    <= 1'b1;
                w_rise <= arg[0];
            end else if (w_fire) begin
                w_v <= 1'b0;
            end

            // payload of a new shift (loaded at the take; it starts when due)
            if (tk && (h_shift || h_lk)) begin
                sreg <= pay;
                bi   <= order ? lenm1 : 4'd0;
            end else if (s_bit || lk_bit) begin
                bi <= bi_nx;
            end

            // bits to drive
            if (tk && (h_shift || h_lk))
                rem <= {1'b0, lenm1} + 5'd1;
            else if (lk_abort)
                rem <= 5'd0;
            else if (s_bit || lk_bit)
                rem <= rem - 5'd1;

            // linked return-to-IDLE and preload
            if (lk_abort) begin
                lk_ret <= 1'b0;
                lk_pre <= 1'b0;
            end else begin
                lk_pre <= tk && h_lk && tx_preload && (rem == 5'd0) && !lk_ret;
                if (lk_bit && (rem == 5'd1))
                    lk_ret <= 1'b1;
                else if (lk_idle || (lk_edge && !lk_pre && (rem != 5'd0)))
                    lk_ret <= 1'b0;
            end

            // CLKGEN period count
            if (tk && h_ext)
                cn <= cn_sum[8:0] - {8'd0, k_hi && ph};
            else if (tk && h_clk)
                cn <= {1'b0, arg[7:0]};
            else if (k_hi && ph)
                cn <= cn - 9'd1;

            // the running shift / burst
            if (load_proc) begin
                p_act   <= 1'b1;
                bt      <= {16'd0, p_frac, 1'b0};
                ph      <= 1'b0;
                p_first <= 1'b1;
                p_sw    <= 1'b0;
            end else if (p_act) begin
                if (p_end) begin
                    p_act <= 1'b0;
                    p_sw  <= 1'b0;
                end else if (p_sw) begin
                    // STRETCH (P11): the IDLE half starts in the first clock pin A reads IDLE
                    if (a_idle) begin
                        p_sw <= 1'b0;
                        ph   <= 1'b1;
                        bt   <= step - BT_ONE;
                    end
                end else if (fire) begin
                    bt <= bt_add[BW-1:0] - BT_ONE;
                    if (m_clk) begin
                        p_first <= 1'b0;
                        if (ph) begin
                            ph <= 1'b0;
                        end else if (!p_first && stretch) begin
                            p_sw <= 1'b1;
                        end else begin
                            ph <= 1'b1;
                        end
                    end
                end else begin
                    bt <= bt - BT_ONE;
                end
            end
        end
    end

    wire _unused = &{1'b0, pend_a[4:1], bt_add[BW], period};
endmodule
