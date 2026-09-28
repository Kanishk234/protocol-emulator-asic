// Pin unit, BITSYNC engine (ARCHITECTURE.md §14 P20-P29, D-023, D-025-D-027): one bit clock recovered from the
// line, shared by TX and RX. Full units only (U0-U1, D-040). Active while TXMODE and RXMODE are both `bitsync`;
// it then owns the unit's token takes, pin A and the producer loads.
//
// Built so far (docs/reports/PIN_UNIT_RTL.md §9):
//   B2a: the bit clock (P20), bus idle, frame start with hard sync (P21), resync limited to SJW (P22).
//   B2b: RX bit stuffing and stuff errors (P23), the RX CRC, RX words and `FRAME n` with its verdict (P24);
//        the RX commands `FRAME` and `SETN` rx are taken at once (P25).
//   B2c: the TX queue (P25): DATA words, `SYNC` (our frame start, or joining another node's, P21), `LINE`
//        [2] stuffing, [6] TX CRC reset, [3] TX CRC append; `WAIT` [1]; TX stuffing; pin A; the own-edge
//        rules (no resync on an edge to the level we drive, no idle while we drive a bit).
// Next (B3, P26-P29): readback (`LINE` [1:0]), errors, flags, `JAM` (taken at once and ignored until then),
// listen-only, NRZI, SE0 (`LINE` [4], ignored until then), OE auto.
//
// Timing contract (clock n is the cycle that edge n ends; `a_in` in clock n is the pad of clock n-2, P1):
//   - Time is kept in 1/256 clocks with one timer: `tb` is the distance from the start of this clock to the
//     next bit boundary (it drops by 256 each clock), so the time since the bit start is e = PERIOD - tb. A
//     boundary falls on this clock's edge when tb < 256; the sample is taken in the clock that contains
//     bit start + SAMPLEOFS, once per bit (`smp_done`) (the P4/P5 convention: an event at time t acts in
//     clock / on edge floor(t)).
//   - A frame start in clock c sets the bit start to the start of clock c: the next boundary is PERIOD after
//     it and the sample SAMPLEOFS after it (P21).
//   - A resync in clock c: before this bit's sample the bit start moves later by min(e, SJW); after it the bit
//     ends earlier by min(tb, SJW) (P22). Either is one signed correction of `tb`.
//   - A sample in clock n is one line bit. With stuffing on, a bit due as a stuff bit is removed (an equal bit
//     is a stuff error); every other bit is a destuffed frame bit: it enters the CRC (after CRC_SKIP) and the
//     word. A token it produces (DATA word, verdict EVENT/ERR, stuff error ERR) is loaded at edge n if the
//     producer is free, else it is dropped and `ovr_set` rises (§4.5). At most one per sample.
//   - A token taken in clock n (tx_take) acts at edge n. A TX token is taken only with no bits queued, so a
//     `LINE` acts when taken: every data bit before it is already sent (and in the TX CRC); a stuff bit due
//     after them is already decided (`ts_p`) and goes out first.
//   - A boundary on edge n drives the next bit from edge n (`tx_lvl` in clock n+1): a due stuff bit, else the
//     next queued bit, else the line is released. Our frame opens on that edge (P-G32); a join drives our first
//     bit from the edge of the frame-start clock.
// Readings where the text leaves a choice are marked P-G<n> (PIN_UNIT_RTL.md §9).
`default_nettype none
`include "trw_defs.vh"
`include "trw_assert.vh"

module trw_pin_bs (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        restart,
    input  wire        live,
    input  wire        active,       // TXMODE and RXMODE are bitsync (and this is a full unit)
    // configuration (static while running)
    input  wire        idle,         // the recessive level
    input  wire        order,
    input  wire        tx_lentok,
    input  wire [23:0] period,       // 16.8 clocks
    input  wire [23:0] sampleofs,    // 16.8 clocks after the bit start
    input  wire [23:0] sjw,          // 16.8 clocks, 0 = hard sync only
    input  wire [4:0]  idle_bits,
    input  wire        resync_both,
    input  wire [3:0]  nbits,        // NBITS - 1
    input  wire [4:0]  rx_nbits,     // 0 = NBITS
    input  wire [3:0]  stuff_n,      // 0 = no stuffing
    input  wire [1:0]  stuff_lvl,    // 0 any level, 2 only runs of 0, 3 only runs of 1
    input  wire [4:0]  crc_width,    // 0 = no CRC
    input  wire [4:0]  crc_skip,
    input  wire [15:0] crc_poly,
    input  wire [15:0] crc_init,
    input  wire [15:0] crc_res,
    input  wire [15:0] crc_xor,
    // sensed pin (S, else A), this clock and the previous one
    input  wire        a_in,
    input  wire        a_prev,
    // consumer port head
    input  wire        tx_avail,
    input  wire [1:0]  tx_tag,
    input  wire [15:0] tx_data,
    output wire        tx_take,
    output wire        late_set,
    // producer register
    input  wire        rx_free,
    output wire        rx_load,
    output wire [1:0]  rx_tag,
    output wire [15:0] rx_data,
    output wire        ovr_set,
    // pin A
    output wire        tx_lvl,
    // state, for debug
    output reg         bus_idle,
    output reg         in_frame,
    output wire        bnd,          // a bit boundary at this clock's edge
    output wire        smp           // a sample in this clock
);
    // ------------------------------------------------------------------ edges on the sensed pin
    wire dom_edge = (a_prev == idle) && (a_in != idle);        // recessive to dominant
    wire any_edge = (a_prev != a_in);

    // ------------------------------------------------------------------ TX state (declared for the rules below)
    reg         drv;           // a bit of ours is on the line (P20, P22)
    reg         tlv;           // its level

    // ------------------------------------------------------------------ bit clock
    reg  [24:0] tb;            // 1/256 clocks to the next boundary, from this clock's start
    reg         smp_done;      // this bit's sample has been taken
    reg         rs_done;       // one resync per bit (P22)
    reg  [4:0]  icnt;          // consecutive recessive samples

    wire f_start = active && bus_idle && dom_edge;              // P21 (at idle: another node's first bit)
    wire hsync   = f_start;                                     // it hard-syncs the bit clock
    // P22/D-025: never resync on an edge to the level this unit is driving itself
    wire own_lvl = drv && (a_in == tlv);
    wire rs_edge = active && !f_start && !rs_done && !own_lvl && (resync_both ? any_edge : dom_edge);

    // Timing: the sensed pin can come straight from a uo pad (P7), so every sum below uses registered state
    // only; the edge terms (hsync, rs_do) just select among the results. Without a hard sync the bit start
    // is as registered (tb, smp_done); with one it is the start of this clock (tb1 = PERIOD, no resync, the
    // sample not yet taken: the sample time is SAMPLEOFS).
    wire [24:0] per  = {1'b0, period};
    wire [24:0] sof  = {1'b0, sampleofs};
    wire [24:0] sj   = {1'b0, sjw};
    wire        done = !hsync && smp_done;
    // P22: e = time since the bit start; before the sample move later by min(e, SJW), after it end earlier
    wire [24:0] e    = per - tb;
    wire [24:0] d    = !smp_done ? ((e < sj) ? e : sj) : ((tb < sj) ? tb : sj);
    wire        rs_do = rs_edge && (d != 25'd0);
    wire [24:0] tb_r = !smp_done ? tb + d : tb - d;             // the boundary after a resync
    wire [24:0] sp   = sof - per;                               // sample time - boundary time
    wire [24:0] x_n  = sp + tb;                                 // the sample time, from this clock's start
    wire [24:0] x_r  = sp + tb_r;                               // the same after a resync
    wire        s_n  = x_n[24] || (x_n < 25'd256);              // at or before the end of this clock
    wire        s_r  = x_r[24] || (x_r < 25'd256);
    wire        s_h  = sof < 25'd256;
    wire [24:0] tb1  = hsync ? per : rs_do ? tb_r : tb;

    assign bnd = active && (hsync ? (per < 25'd256) : rs_do ? (tb_r < 25'd256) : (tb < 25'd256));
    assign smp = active && (hsync ? s_h : (!smp_done && (rs_do ? s_r : s_n)));

    // ------------------------------------------------------------------ tokens (P25)
    wire [3:0]  op      = tx_data[15:12];
    wire [11:0] arg     = tx_data[11:0];
    wire        t_ctrl  = (tx_tag == `TRW_TAG_CTRL);
    wire        c_frame = t_ctrl && (op == `TRW_CMD_FRAME);
    wire        c_rxs   = t_ctrl && (op == `TRW_CMD_SETN) && arg[5];
    wire        c_jam   = t_ctrl && (op == `TRW_CMD_JAM);
    wire        rx_cmd  = c_frame || c_rxs || c_jam;             // taken at once, even behind TX data
    reg  [4:0]  qn;            // bits queued
    reg         wt_p;          // WAIT [1]: no TX token until the next sample point
    // P-G31: the next token may be taken in the clock of that sample point
    wire        tx_ok   = (qn == 5'd0) && (!wt_p || smp);
    assign tx_take = live && active && tx_avail && (rx_cmd || tx_ok);
    wire        tk      = tx_take && !rx_cmd;                    // a TX token (other ops: taken and ignored)
    wire        k_data  = tk && (tx_tag == `TRW_TAG_DATA);
    wire        k_sync  = tk && t_ctrl && (op == `TRW_CMD_SYNC);
    wire        k_line  = tk && t_ctrl && (op == `TRW_CMD_LINE);
    wire        k_wait  = tk && t_ctrl && (op == `TRW_CMD_WAIT) && arg[1];

    // ------------------------------------------------------------------ RX frame: stuffing, CRC, words
    reg  [15:0] w;             // the word so far (right-aligned as it will be emitted)
    reg  [4:0]  wn;            // bits in it
    reg  [4:0]  wlen_o;        // SETN rx override of the word length (0 = none)
    reg         rl;            // stuffing: level of the current run
    reg  [3:0]  rc;            // stuffing: its length (saturates at 15)
    reg         stuff_on;      // RX stuffing active (from the frame start until after FRAME's n)
    reg         words_on;      // word framing active (stops at a stuff error or FRAME's verdict)
    reg  [10:0] lcnt;          // line bits in this frame
    reg  [10:0] dcnt;          // destuffed bits in this frame
    reg  [15:0] crc;
    reg         fr_v;          // FRAME n applies to this frame
    reg  [10:0] fr_n;
    reg         fnx_v;         // FRAME n for the next frame ([11])
    reg  [10:0] fnx_n;
    reg         post;          // after FRAME's n: one stuff bit may still be due (P24)

    wire        bit_in   = a_in;
    wire        rec      = (bit_in == idle);
    // P20: IDLE_BITS recessive samples make the bus idle; in a frame that ends it without a verdict, and
    // never while this unit is driving a bit
    wire [4:0]  icnt_r    = (icnt == 5'd31) ? icnt : icnt + 5'd1;   // the count if this sample is recessive
    wire [4:0]  icnt1     = rec ? icnt_r : 5'd0;
    wire        goes_idle = smp && rec && (icnt_r >= idle_bits) && (idle_bits != 5'd0) && !drv;
    wire        fbit     = smp && in_frame && !goes_idle;        // P-G29: the idle-making sample is no frame bit

    // P23: a stuff bit is due after STUFF_N equal line bits (of STUFF_LVL, if set)
    wire        lvl_ok   = !stuff_lvl[1] || (rl == stuff_lvl[0]);
    wire        s_due    = (stuff_n != 4'd0) && (rc == stuff_n) && lvl_ok && (stuff_on || post);
    wire        s_err    = fbit && s_due && (bit_in == rl);
    wire        s_bit    = fbit && s_due && (bit_in != rl);
    wire        open_fr  = words_on || stuff_on;              // destuffed bits count until FRAME's n
    wire        dbit     = fbit && !s_due && open_fr;
    wire [3:0]  rc1      = (bit_in == rl) ? ((rc == 4'hf) ? rc : rc + 4'd1) : 4'd1;

    // CRC (P24, P25): MSB-first LFSR of CRC_WIDTH bits; RX after the first CRC_SKIP destuffed bits
    wire [4:0]  cw       = (crc_width > 5'd16) ? 5'd16 : crc_width;
    wire [15:0] cmask    = (cw == 5'd0) ? 16'd0 : (16'hffff >> (5'd16 - cw));
    wire [3:0]  ctop     = (cw == 5'd0) ? 4'd0 : (cw[3:0] - 4'd1);
    wire [15:0] cres     = crc_res & cmask;
    wire [15:0] cr0      = ({crc[14:0], 1'b0} ^ ( crc[ctop] ? crc_poly : 16'd0)) & cmask;
    wire [15:0] cr1      = ({crc[14:0], 1'b0} ^ (!crc[ctop] ? crc_poly : 16'd0)) & cmask;
    wire [15:0] crc1     = bit_in ? cr1 : cr0;                   // the register after this bit
    wire        c_in     = dbit && (dcnt >= {6'd0, crc_skip}) && (cw != 5'd0);

    // words
    wire [4:0]  wlen_c   = (rx_nbits == 5'd0) ? {1'b0, nbits} + 5'd1 : (rx_nbits > 5'd16) ? 5'd16 : rx_nbits;
    wire [4:0]  wlen     = (wlen_o != 5'd0) ? wlen_o : wlen_c;
    wire [4:0]  wn1      = wn + 5'd1;
    wire [15:0] w1       = order ? {w[14:0], bit_in} : (w | ({15'd0, bit_in} << wn));
    wire [10:0] dcnt1    = dcnt + 11'd1;
    wire        at_n     = dbit && fr_v && (dcnt1 == fr_n);    // this bit is FRAME's n-th
    // the comparisons use registered state; the bit and c_in only select (timing, as the bit clock)
    wire        crc_ok   = c_in ? (bit_in ? (cr1 == cres) : (cr0 == cres)) : (crc == cres);
    // P24/P-G30: at bit n the verdict carries the word (partial or complete) instead of a DATA word
    wire        v_tok    = at_n && words_on;
    wire        w_tok    = dbit && words_on && !at_n && (wn1 == wlen);
    wire        err_tok  = s_err && (words_on || post);         // P23/P-G27: ERR 0x1nnn; P24: also the stuff bit after n

    // ------------------------------------------------------------------ TX queue (P25)
    reg  [15:0] q;             // queued bits, the next one in q[15]
    reg         q_crc;         // they are TX CRC bits (not fed back into the TX CRC)
    reg         sync_p;        // SYNC: the queued bits start a new frame at bus idle (P21)
    reg         ts_on;         // LINE [2]: TX stuffing
    reg         ts_p;          // a stuff bit is due at the next bit start
    reg         trl;           // TX run: level of the last bit sent
    reg  [3:0]  trc;           // and its length (stuff bits included, saturates at 15)
    reg  [15:0] tcrc;          // TX CRC register

    wire        q_any    = (qn != 5'd0);
    // P21: another node's frame starts while ours waits for idle and our first bit is dominant: join it
    wire        jn       = f_start && sync_p && q_any && !ts_p && (q[15] != idle);
    wire        go       = bnd && (ts_p || (q_any && (!sync_p || bus_idle)));
    wire        deq      = go || jn;                            // a bit of ours starts on this edge
    wire        nlv      = ts_p ? !trl : q[15];
    // P-G32: our frame opens at the bit start of a SYNC frame's first bit, or of a dominant bit sent at bus idle
    wire        o_start  = go && !ts_p && bus_idle && (sync_p || (nlv != idle));
    wire        new_run  = o_start || jn;
    wire        sync_ev  = ((o_start && sync_p) || jn) && live;   // EVENT 0x9001: our SYNC frame started
    wire        q_dbit   = deq && !ts_p;                        // a queued bit (data or CRC) leaves the queue
    wire [3:0]  trc1     = (new_run || (nlv != trl)) ? 4'd1 : ((trc == 4'hf) ? trc : trc + 4'd1);
    wire        tlvl_ok  = !stuff_lvl[1] || (nlv == stuff_lvl[0]);
    wire        ts_due   = ts_on && (stuff_n != 4'd0) && (trc1 == stuff_n) && tlvl_ok;
    wire        tcfb     = tcrc[ctop] ^ nlv;
    wire [15:0] tcrc1    = (({tcrc[14:0], 1'b0}) ^ (tcfb ? crc_poly : 16'd0)) & cmask;

    // loading the queue: a DATA word (NBITS or length-in-token, ORDER) or the TX CRC (LINE [3], MSB first)
    wire [4:0]  nb       = (tx_lentok ? {1'b0, tx_data[15:12]} : {1'b0, nbits}) + 5'd1;
    wire [15:0] pay      = tx_lentok ? {4'h0, tx_data[11:0]} : tx_data;
    wire [15:0] crc_src  = arg[6] ? (crc_init & cmask) : tcrc;  // [6] acts before [3]
    wire        k_crc    = k_line && arg[3];
    reg  [15:0] pay_r;                                          // LSB first: bit 0 goes out first
    integer i;
    always @(*)
        for (i = 0; i < 16; i = i + 1)
            pay_r[15 - i] = pay[i];
    wire [15:0] ld_src   = k_crc ? ((crc_src ^ crc_xor) & cmask) : (order ? pay : pay_r);
    wire [4:0]  ld_sh    = k_crc ? (5'd16 - cw) : (order ? (5'd16 - nb) : 5'd0);
    wire [15:0] ld_q     = ld_src << ld_sh;

    assign tx_lvl = drv ? tlv : idle;                           // no bit: released (recessive)

    // ------------------------------------------------------------------ producer
    assign rx_tag  = err_tok ? `TRW_TAG_ERR : v_tok ? (crc_ok ? `TRW_TAG_EVENT : `TRW_TAG_ERR) :
                     w_tok   ? `TRW_TAG_DATA : `TRW_TAG_EVENT;
    assign rx_data = err_tok ? {4'h1, 1'b0, lcnt} :
                     v_tok   ? {4'h0, w1[11:0]} : w_tok ? w1 : 16'h9001;
    wire   want    = live && (err_tok || v_tok || w_tok || sync_ev);
    assign rx_load = want && rx_free;
    assign ovr_set = want && !rx_free;

    // FRAME without [11] is LATE with no frame in progress, word framing stopped, or the count at/after n
    wire f_now   = tx_take && c_frame && !arg[11];
    assign late_set = f_now && (!in_frame || !words_on || (dcnt >= arg[10:0]));

`ifdef TRW_ASSERT_ON
    // the start event never shares a clock with a frame token (a frame starts only with no frame in progress)
    wire ev_clash = sync_ev && (err_tok || v_tok || w_tok);
    wire q_clash  = (k_data || k_crc) && q_dbit;
    `TRW_ASSERT(!ev_clash, "BITSYNC: the frame-start EVENT collides with a frame token")
    `TRW_ASSERT(!q_clash, "BITSYNC: a load of the TX queue while a queued bit leaves it")
`endif

    always @(posedge clk) begin
        if (!rst_n || restart || !active) begin
            tb <= per;  smp_done <= 1'b0;  rs_done <= 1'b0;  icnt <= 5'd0;
            bus_idle <= 1'b0;  in_frame <= 1'b0;  w <= 16'd0;  wn <= 5'd0;  wlen_o <= 5'd0;
            rl <= 1'b0;  rc <= 4'd0;  stuff_on <= 1'b0;  words_on <= 1'b0;  lcnt <= 11'd0;  dcnt <= 11'd0;
            crc <= 16'd0;  fr_v <= 1'b0;  fr_n <= 11'd0;  fnx_v <= 1'b0;  fnx_n <= 11'd0;  post <= 1'b0;
            q <= 16'd0;  qn <= 5'd0;  q_crc <= 1'b0;  sync_p <= 1'b0;  wt_p <= 1'b0;  ts_on <= 1'b0;
            ts_p <= 1'b0;  trl <= 1'b0;  trc <= 4'd0;  tcrc <= 16'd0;  drv <= 1'b0;  tlv <= 1'b0;
        end else begin
            tb       <= (bnd ? tb1 + per : tb1) - 25'd256;
            smp_done <= bnd ? 1'b0 : (done || smp);
            if (bnd)
                rs_done <= 1'b0;
            else if (rs_do)
                rs_done <= 1'b1;
            if (smp)
                icnt <= icnt1;

            // ---------------------------------------------------------- TX
            if (deq) begin                                     // a bit of ours from this edge
                drv  <= 1'b1;
                tlv  <= nlv;
                trl  <= nlv;
                trc  <= trc1;
                ts_p <= ts_due;
            end else if (bnd) begin                            // nothing to send: release the line
                drv  <= 1'b0;
                tlv  <= idle;
            end
            if (new_run)
                sync_p <= 1'b0;
            if (q_dbit) begin
                q  <= {q[14:0], 1'b0};
                qn <= qn - 5'd1;
                if (!q_crc)
                    tcrc <= tcrc1;                             // P25: data bits only
            end
            if (k_data) begin
                q <= ld_q;  qn <= nb;  q_crc <= 1'b0;
            end
            if (k_sync) begin
                sync_p <= 1'b1;
                tcrc   <= crc_init & cmask;
            end
            if (k_line) begin
                ts_on <= arg[2];
                if (arg[6])
                    tcrc <= crc_init & cmask;
                if (arg[3]) begin
                    q <= ld_q;  qn <= cw;  q_crc <= 1'b1;
                end
            end
            if (k_wait)
                wt_p <= 1'b1;
            else if (smp)
                wt_p <= 1'b0;

            // ---------------------------------------------------------- RX commands
            if (tx_take && c_rxs) begin                        // SETN rx: word length, framing restarts
                wlen_o <= ((arg[4:0] == 5'd0) || (arg[4:0] > 5'd16)) ? 5'd16 : arg[4:0];
            end
            if (tx_take && c_frame) begin
                if (arg[11]) begin
                    fnx_v <= 1'b1;
                    fnx_n <= arg[10:0];
                end else if (!late_set) begin
                    fr_v <= 1'b1;
                    fr_n <= arg[10:0];
                end
            end

            // ---------------------------------------------------------- RX frame
            if (f_start || o_start) begin                      // P21: a frame opens; its first bit follows
                bus_idle <= 1'b0;
                in_frame <= 1'b1;
                w <= 16'd0;  wn <= 5'd0;
                rl <= !idle;  rc <= 4'd0;                      // the first bit starts the run
                stuff_on <= 1'b1;  words_on <= 1'b1;  post <= 1'b0;
                lcnt <= 11'd0;  dcnt <= 11'd0;  crc <= crc_init & cmask;
                fr_v <= fnx_v;  fr_n <= fnx_n;  fnx_v <= 1'b0;
            end else if (goes_idle) begin                      // P20: no verdict, the partial word is dropped
                bus_idle <= 1'b1;
                in_frame <= 1'b0;
                w <= 16'd0;  wn <= 5'd0;
                stuff_on <= 1'b0;  words_on <= 1'b0;  post <= 1'b0;  fr_v <= 1'b0;
            end else if (fbit) begin
                lcnt <= lcnt + 11'd1;
                if (stuff_on || post) begin
                    rl <= bit_in;
                    rc <= s_bit ? 4'd1 : rc1;
                end
                if (s_err) begin                               // P23: framing stops for the frame
                    words_on <= 1'b0;
                    stuff_on <= 1'b0;
                    post     <= 1'b0;
                end else if (s_bit) begin
                    post <= 1'b0;                              // the stuff bit after n has been checked
                end else if (dbit) begin
                    dcnt <= dcnt1;
                    if (c_in)
                        crc <= crc1;
                    if (at_n) begin                            // P24: verdict; stuffing stops (one more may be due)
                        words_on <= 1'b0;
                        stuff_on <= 1'b0;
                        post     <= 1'b1;
                        fr_v     <= 1'b0;
                        w <= 16'd0;  wn <= 5'd0;
                    end else if (words_on) begin
                        if (wn1 == wlen) begin
                            w <= 16'd0;  wn <= 5'd0;
                        end else begin
                            w <= w1;  wn <= wn1;
                        end
                    end
                end else begin
                    post <= 1'b0;                              // after n: no stuff bit was due
                end
            end
            if (tx_take && c_rxs) begin                        // SETN rx restarts the framing (applies at once)
                w <= 16'd0;
                wn <= 5'd0;
            end
        end
    end
endmodule
