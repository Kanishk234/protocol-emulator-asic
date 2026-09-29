// Pin unit, BITSYNC engine (ARCHITECTURE.md §14 P20-P29, D-023, D-025-D-027): one bit clock recovered from the
// line, shared by TX and RX. Full units only (U0-U1, D-040). Active while TXMODE and RXMODE are both `bitsync`;
// it then owns the unit's token takes, pin A (and pin N's SE0) and the producer loads.
//
// Built in stages (docs/reports/PIN_UNIT_RTL.md §9):
//   B2a: the bit clock (P20), bus idle, frame start with hard sync (P21), resync limited to SJW (P22).
//   B2b: RX bit stuffing and stuff errors (P23), the RX CRC, RX words and `FRAME n` with its verdict (P24);
//        the RX commands `FRAME` and `SETN` rx are taken at once (P25).
//   B2c: the TX queue (P25): DATA words, `SYNC` (our frame start, or joining another node's, P21), `LINE`
//        [2] stuffing, [6] TX CRC reset, [3] TX CRC append; `WAIT` [1]; TX stuffing; pin A; the own-edge
//        rules (no resync on an edge to the level we drive, no idle while we drive a bit).
//   B3:  readback (`LINE` [1:0]) with arbitration and bit errors (P26); DELIM = flag with the hold-back and
//        aborts (P27); `JAM`: responses, armed error flags, listen-only (P28); NRZI, SE0 (`LINE` [4]), DELIM =
//        se0, OE auto (P29); data[14] "our own frame" in the verdict (P24).
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
//   - A sample in clock n is one line bit (with NRZI, the data bit is 1 when the line equals the previous
//     sample's level). With stuffing on, a bit due as a stuff bit is removed (an equal bit is a stuff error, or
//     with DELIM = flag the sixth one of a flag); every other bit is a destuffed frame bit. With DELIM = flag a
//     destuffed bit is committed STUFF_N + 1 destuffed bits later (P27); otherwise at once. A committed bit
//     enters the CRC (after CRC_SKIP) and the word. A frame token (DATA word, verdict EVENT/ERR, stuff error,
//     abort) is loaded at edge n if the producer is free, else it is dropped and `ovr_set` rises (§4.5).
//   - Status EVENTs (our frame started 0x9001, readback 0x8000/0xA000/0xB000, refused 0xC001) wait in a
//     one-entry register while the producer is busy or a frame token takes the clock; a second one while it
//     is full is dropped with `ovr_set`.
//   - A token taken in clock n (tx_take) acts at edge n. A TX token is taken only with no bits, SE0 or J
//     queued, so a `LINE` acts when taken: every data bit before it is already sent (and in the TX CRC); a
//     stuff bit due after them is already decided (`ts_p`) and goes out first. The readback mode is latched
//     with each bit when it starts (a stuff bit gets the mode of the bit before it).
//   - A boundary on edge n drives the next bit from edge n (`tx_lvl` in clock n+1): a JAM bit, else a due
//     stuff bit, else the next queued bit, else SE0 / J, else the line is released. Our frame opens on that
//     edge (P-G32); a join drives our first bit from the edge of the frame-start clock.
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
    input  wire        nrzi,
    input  wire        oe_auto,
    input  wire [1:0]  delim,        // 0 none, 1 flag, 2 se0
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
    // sensed pin (S, else A), this clock and the previous one; pin B (DELIM = se0)
    input  wire        a_in,
    input  wire        a_prev,
    input  wire        b_in,
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
    // pin A (and pin N during SE0, P29)
    output wire        tx_lvl,
    output wire        tx_se0,
    output wire        tx_drv,       // a bit of ours is on the line (OE_AUTO)
    // state, for debug
    output reg         bus_idle,
    output reg         in_frame,
    output wire        bnd,          // a bit boundary at this clock's edge
    output wire        smp           // a sample in this clock
);
    // ------------------------------------------------------------------ edges on the sensed pin (line levels)
    wire dom_edge = (a_prev == idle) && (a_in != idle);        // recessive to dominant
    wire any_edge = (a_prev != a_in);

    // ------------------------------------------------------------------ TX state (declared for the rules below)
    reg         drv;           // a bit of ours is on the line (P20, P22)
    reg         tlv;           // its line level
    reg         own;           // the frame in progress is one this unit transmits (P24 data[14], P28, P29)
    reg         txoff;         // listen-only (P28)

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
    wire        rs_do = rs_edge && (sj != 25'd0) && (smp_done ? (tb != 25'd0) : (e != 25'd0));
    // Fold the min-and-add/subtract into the boundary value directly. Before the sample,
    // tb + min(per - tb, sjw) is either per or tb + sjw. After it,
    // tb - min(tb, sjw) is either zero or tb - sjw. This removes one 25-bit
    // arithmetic stage from the resync path without changing its saturation behavior.
    wire [24:0] tb_r = !smp_done ? ((e < sj) ? per : tb + sj) : ((tb < sj) ? 25'd0 : tb - sj);
    wire [24:0] sp   = sof - per;                               // sample time - boundary time
    wire [24:0] x_n  = sp + tb;                                 // the sample time, from this clock's start
    wire [24:0] x_r  = sp + tb_r;                               // the same after a resync
    wire        s_n  = x_n[24] || (x_n < 25'd256);              // at or before the end of this clock
    wire        s_r  = x_r[24] || (x_r < 25'd256);
    wire        s_h  = sof < 25'd256;
    wire [24:0] tb1  = hsync ? per : rs_do ? tb_r : tb;

    assign bnd = active && (hsync ? (per < 25'd256) : rs_do ? (tb_r < 25'd256) : (tb < 25'd256));
    assign smp = active && (hsync ? s_h : (!smp_done && (rs_do ? s_r : s_n)));

    // ------------------------------------------------------------------ tokens (P25, P28)
    wire [3:0]  op      = tx_data[15:12];
    wire [11:0] arg     = tx_data[11:0];
    wire        t_ctrl  = (tx_tag == `TRW_TAG_CTRL);
    wire        c_frame = t_ctrl && (op == `TRW_CMD_FRAME);
    wire        c_rxs   = t_ctrl && (op == `TRW_CMD_SETN) && arg[5];
    wire        c_jam   = t_ctrl && (op == `TRW_CMD_JAM);
    wire        rx_cmd  = c_frame || c_rxs || c_jam;             // taken at once, even behind TX data
    reg  [4:0]  qn;            // bits queued
    reg  [4:0]  sq;            // SE0 bits queued (after the queued bits, P29)
    reg         jq;            // the J (idle) bit after them
    reg         wt_p;          // WAIT [1]: no TX token until the next sample point
    reg         dsc;           // after a readback abort or in listen-only: DATA and LINE are discarded (P26)
    // P-G31: the next token may be taken in the clock of that sample point
    wire        tx_ok   = (qn == 5'd0) && (sq == 5'd0) && !jq && (!wt_p || smp);
    assign tx_take = live && active && tx_avail && (rx_cmd || tx_ok);
    wire        tk      = tx_take && !rx_cmd;                    // a TX token (other ops: taken and ignored)
    wire        k_sync  = tk && t_ctrl && (op == `TRW_CMD_SYNC);
    wire        k_wait  = tk && t_ctrl && (op == `TRW_CMD_WAIT) && arg[1];
    wire        k_data  = tk && (tx_tag == `TRW_TAG_DATA) && !dsc;
    wire        k_line  = tk && t_ctrl && (op == `TRW_CMD_LINE) && !dsc;
    // JAM (P28): [1] listen-only on (wins), [2] off; [4] with [0] disarms; [4] arms; else a response. P-G38:
    // [0] without [4] is ignored as a bit (the JAM is a response)
    wire        k_jam   = tx_take && c_jam;
    wire        jm_off  = k_jam && arg[1];
    wire        jm_on   = k_jam && !arg[1] && arg[2];
    wire        jm_ctl  = !arg[1] && !arg[2];
    wire        jm_dis  = k_jam && jm_ctl && arg[4] && arg[0];
    wire        jm_arm  = k_jam && jm_ctl && arg[4] && !arg[0];
    // P28: a response in a frame this unit transmits is dropped (P-G36: judged when taken); nothing in listen-only
    wire        jm_rsp  = k_jam && jm_ctl && !arg[4] && !own && !txoff;

    // ------------------------------------------------------------------ RX frame: stuffing, CRC, words
    reg  [15:0] w;             // the word so far (right-aligned as it will be emitted)
    reg  [4:0]  wn;            // bits in it
    reg  [4:0]  wlen_o;        // SETN rx override of the word length (0 = none)
    reg         rl;            // stuffing: level of the current run (data bits)
    reg  [3:0]  rc;            // stuffing: its length (saturates at 15)
    reg         stuff_on;      // RX stuffing active (from the frame start until after FRAME's n)
    reg         words_on;      // word framing active (stops at a stuff error, an abort or the verdict)
    reg  [10:0] lcnt;          // line bits in this frame
    reg  [10:0] dcnt;          // committed destuffed bits in this frame
    reg  [15:0] crc;
    reg         fr_v;          // FRAME n applies to this frame
    reg  [10:0] fr_n;
    reg         fnx_v;         // FRAME n for the next frame ([11])
    reg  [10:0] fnx_n;
    reg         post;          // after FRAME's n: one stuff bit may still be due (P24)
    reg         rxl;           // NRZI: the line level at the previous sample
    reg  [15:0] hb;            // DELIM = flag: destuffed bits held back, newest in hb[0] (P27)
    reg  [4:0]  hbn;           // how many (up to STUFF_N + 1)
    reg         f6;            // DELIM = flag: the last bit was the (STUFF_N + 1)th one of a run

    wire        dlf      = (delim == 2'd1);
    wire        dls      = (delim == 2'd2);
    // P29: runs, stuffing and CRC work on data bits; edges, idle, SE0 and readback on line levels
    wire        bit_in   = nrzi ? (a_in == rxl) : a_in;
    wire        rec      = (a_in == idle);
    // P20: IDLE_BITS recessive samples make the bus idle; in a frame that ends it without a verdict, never
    // while this unit is driving a bit, and never with DELIM = se0 (P29)
    wire [4:0]  icnt_r    = (icnt == 5'd31) ? icnt : icnt + 5'd1;   // the count if this sample is recessive
    wire [4:0]  icnt1     = rec ? icnt_r : 5'd0;
    wire        goes_idle = smp && rec && (icnt_r >= idle_bits) && (idle_bits != 5'd0) && !drv &&
                            !(dls && in_frame);
    // P29: with DELIM = se0 a frame ends (with its verdict) when pin S and pin B both sample low
    wire        se0_s    = smp && in_frame && dls && !a_in && !b_in;
    wire        fbit     = smp && in_frame && !goes_idle && !se0_s;  // P-G29: the idle-making sample is no frame bit

    // P23: a stuff bit is due after STUFF_N equal bits (of STUFF_LVL, if set)
    wire        lvl_ok   = !stuff_lvl[1] || (rl == stuff_lvl[0]);
    wire        s_due    = (stuff_n != 4'd0) && (rc == stuff_n) && lvl_ok && (stuff_on || post);
    wire        run_eq   = (bit_in == rl);
    wire        s_err    = fbit && s_due && run_eq && !dlf;
    wire        s_bit    = fbit && s_due && !run_eq;
    // P27: with DELIM = flag the (STUFF_N + 1)th one is no error; then the other level is a flag, one more an abort
    wire        six_s    = fbit && s_due && run_eq && dlf;
    wire        fl_s     = fbit && f6 && !run_eq;
    wire        ab_s     = fbit && f6 && run_eq;
    wire        open_fr  = words_on || stuff_on;              // destuffed bits count until FRAME's n
    wire        dbit     = fbit && !s_due && !f6 && open_fr;
    wire [3:0]  rc1      = run_eq ? ((rc == 4'hf) ? rc : rc + 4'd1) : 4'd1;
    // P27: a destuffed bit is committed when STUFF_N + 1 newer ones have arrived
    wire        hb_full  = (hbn == ({1'b0, stuff_n} + 5'd1));
    wire        cm       = dbit && (!dlf || hb_full);
    wire        cbit     = dlf ? hb[stuff_n] : bit_in;

    // CRC (P24, P25): MSB-first LFSR of CRC_WIDTH bits; RX after the first CRC_SKIP committed bits
    wire [4:0]  cw       = (crc_width > 5'd16) ? 5'd16 : crc_width;
    wire [15:0] cmask    = (cw == 5'd0) ? 16'd0 : (16'hffff >> (5'd16 - cw));
    wire [3:0]  ctop     = (cw == 5'd0) ? 4'd0 : (cw[3:0] - 4'd1);
    wire [15:0] cres     = crc_res & cmask;
    wire [15:0] cr0      = ({crc[14:0], 1'b0} ^ ( crc[ctop] ? crc_poly : 16'd0)) & cmask;
    wire [15:0] cr1      = ({crc[14:0], 1'b0} ^ (!crc[ctop] ? crc_poly : 16'd0)) & cmask;
    wire [15:0] crc1     = cbit ? cr1 : cr0;                     // the register after this bit
    wire        c_in     = cm && (dcnt >= {6'd0, crc_skip}) && (cw != 5'd0);

    // words
    wire [4:0]  wlen_c   = (rx_nbits == 5'd0) ? {1'b0, nbits} + 5'd1 : (rx_nbits > 5'd16) ? 5'd16 : rx_nbits;
    wire [4:0]  wlen     = (wlen_o != 5'd0) ? wlen_o : wlen_c;
    wire [4:0]  wn1      = wn + 5'd1;
    wire [15:0] w1       = order ? {w[14:0], cbit} : (w | ({15'd0, cbit} << wn));
    wire [10:0] dcnt1    = dcnt + 11'd1;
    wire        at_n     = cm && fr_v && (dcnt1 == fr_n);      // this bit is FRAME's n-th
    // the comparisons use registered state; the bit and c_in only select (timing, as the bit clock)
    wire        crc_ok   = c_in ? (cbit ? (cr1 == cres) : (cr0 == cres)) : (crc == cres);
    // P24/P-G30: at bit n the verdict carries the word (partial or complete) instead of a DATA word; a flag
    // (P27, if the frame has committed bits) or SE0 (P29) ends the frame with a verdict on the word so far
    wire        n_tok    = at_n && words_on;
    wire        fl_tok   = fl_s && words_on && (dcnt != 11'd0);
    wire        se_tok   = se0_s && words_on;
    wire        v_tok    = n_tok || fl_tok || se_tok;
    wire [11:0] vw       = n_tok ? w1[11:0] : w[11:0];
    wire        w_tok    = cm && words_on && !at_n && (wn1 == wlen);
    wire        err_tok  = s_err && (words_on || post);         // P23/P-G27: ERR 0x1nnn; P24: also the stuff bit after n
    wire        ab_tok   = ab_s && words_on && (dcnt != 11'd0); // P27/P-G37: ERR 0x2nnn, nnn = line bit

    // ------------------------------------------------------------------ TX queue (P25) and JAM (P28)
    reg  [15:0] q;             // queued bits, right-aligned: the next one is q[qn-1] (q_hi) or q[0]
    reg         q_hi;          // MSB first (ORDER, or TX CRC bits); else LSB first, shifting right
    reg         q_crc;         // they are TX CRC bits (not fed back into the TX CRC)
    reg         sync_p;        // SYNC: the queued bits start a new frame at bus idle (P21)
    reg         ts_on;         // LINE [2]: TX stuffing
    reg         ts_p;          // a stuff bit is due at the next bit start
    reg         trl;           // TX run: data level of the last bit sent
    reg  [3:0]  trc;           // and its length (stuff bits included, saturates at 15)
    reg  [15:0] tcrc;          // TX CRC register
    reg  [1:0]  rbm;           // LINE [1:0]: readback mode for the next bits
    reg  [1:0]  rbm_s;         // the mode of the bit a due stuff bit follows
    reg  [1:0]  tmode;         // the mode of the bit on the line
    reg         jbit;          // the bit on the line is a JAM bit (no readback)
    reg         se0_r;         // it is SE0
    reg         jp;            // a response JAM is pending
    reg  [2:0]  jc;            // non-stuff sample points still to pass
    reg  [3:0]  jb;            // its length - 1; while driving, the bits still to go
    reg         jl;            // its level
    reg         jdv;           // a JAM is being driven
    reg         av;            // an error JAM is armed
    reg  [3:0]  an;            // its length - 1
    reg         al;            // its level
    reg         af;            // an error was detected: the armed JAM fires at the next bit start

    wire        q_any    = (qn != 5'd0);
    wire        cur      = drv ? tlv : idle;                    // the line level we hold now
    // JAM bits come first at a bit start (P28). Listen-only needs no term here or below: switching it on clears
    // the queue and the JAMs, and while it is on no JAM, SYNC, DATA or LINE is accepted
    wire        j_start_a = bnd && af;
    wire        j_start_r = bnd && jp && (jc == 3'd0) && !af;
    wire        j_cont    = bnd && jdv && (jb != 4'd0);
    wire        j_bit     = j_start_a || j_start_r || j_cont;
    wire        j_lvl     = j_start_a ? al : jl;
    // the next bit from the queue: its data level, then its line level (P29: NRZI, a 0 is a change)
    wire [3:0]  q_top    = qn[3:0] - 4'd1;
    wire        q_out    = q_hi ? q[q_top] : q[0];
    wire        nd       = ts_p ? !trl : q_out;
    wire        nl       = nrzi ? (nd ? cur : !cur) : nd;
    // P21: another node's frame starts while ours waits for idle and our first bit is dominant: join it
    wire        jn       = f_start && sync_p && q_any && !ts_p && (nl != idle) && !j_bit;
    wire        go       = bnd && !j_bit && (ts_p || (q_any && (!sync_p || bus_idle)));
    wire        deq      = go || jn;                            // a bit of ours starts on this edge
    wire        se_go    = bnd && !j_bit && !ts_p && !q_any && (sq != 5'd0);
    wire        jj_go    = bnd && !j_bit && !ts_p && !q_any && (sq == 5'd0) && jq;
    // P-G32: our frame opens at the bit start of a SYNC frame's first bit, or of a dominant bit sent at bus idle
    wire        o_start  = go && !ts_p && bus_idle && (sync_p || (nl != idle));
    wire        new_run  = o_start || jn;
    wire        q_dbit   = deq && !ts_p;                        // a queued bit (data or CRC) leaves the queue
    wire [3:0]  trc1     = (new_run || (nd != trl)) ? 4'd1 : ((trc == 4'hf) ? trc : trc + 4'd1);
    wire        tlvl_ok  = !stuff_lvl[1] || (nd == stuff_lvl[0]);
    wire        ts_due   = ts_on && (stuff_n != 4'd0) && (trc1 == stuff_n) && tlvl_ok;
    wire        tcfb     = tcrc[ctop] ^ nd;
    wire [15:0] tcrc1    = (({tcrc[14:0], 1'b0}) ^ (tcfb ? crc_poly : 16'd0)) & cmask;
    wire [1:0]  tm_now   = ts_p ? rbm_s : rbm;

    // loading the queue: a DATA word (NBITS or length-in-token, ORDER) or the TX CRC (LINE [3], MSB first)
    wire [4:0]  nb       = (tx_lentok ? {1'b0, tx_data[15:12]} : {1'b0, nbits}) + 5'd1;
    wire [15:0] pay      = tx_lentok ? {4'h0, tx_data[11:0]} : tx_data;
    wire [15:0] crc_src  = arg[6] ? (crc_init & cmask) : tcrc;  // [6] acts before [3]
    wire        k_crc    = k_line && arg[3];
    // right-aligned (area: no barrel shifter); bits above the word's length are never read
    wire [15:0] ld_q     = k_crc ? ((crc_src ^ crc_xor) & cmask) : pay;

    assign tx_lvl = cur;                                        // no bit: released (recessive)
    assign tx_se0 = drv && se0_r;
    assign tx_drv = drv;

    // ------------------------------------------------------------------ readback and errors (P26)
    // for a bit we drive from the queue (P-G39: not a JAM bit), at its sample; the mode is the bit's own
    wire        rb_s     = smp && drv && !jbit && (tmode != 2'd0);
    wire        mism     = (a_in != tlv);
    wire        rb_lose  = rb_s && (tmode == 2'd1) && mism;
    wire        rb_rep   = rb_s && (tmode == 2'd2);
    wire        rb_bit   = rb_s && (tmode == 2'd3) && mism;
    wire        rb_ev    = rb_lose || rb_rep || rb_bit;
    wire        rb_err   = (rb_rep && !mism) || rb_bit;        // mode 2: nobody overrode our level
    // an error (or losing arbitration) stops our TX; a stuff error only stops a frame of ours (P-G40)
    wire        stop     = rb_lose || rb_err || (s_err && own);
    wire        err_any  = rb_err || s_err;

    // ------------------------------------------------------------------ producer
    // frame tokens first; status EVENTs wait in `st` (P-G41). With OE_AUTO our own frames are not reported.
    wire        rep_ok   = !(oe_auto && own);
    wire        fr_want  = live && rep_ok && (err_tok || ab_tok || v_tok || w_tok);
    wire [1:0]  fr_tag   = (err_tok || ab_tok) ? `TRW_TAG_ERR : v_tok ? (crc_ok ? `TRW_TAG_EVENT : `TRW_TAG_ERR) :
                           `TRW_TAG_DATA;
    wire [15:0] fr_data  = err_tok ? {4'h1, 1'b0, lcnt} : ab_tok ? {4'h2, 1'b0, lcnt} :
                           v_tok ? (crc_ok ? {1'b0, own, 2'b00, vw} : {4'h0, vw}) : w1;
    wire        sync_ev  = (o_start && sync_p) || jn;           // EVENT 0x9001: our SYNC frame started
    wire        ref_ev   = k_sync && txoff;                     // EVENT 0xC001: refused (listen-only)
    wire        st_new   = live && (rb_ev || sync_ev || ref_ev);
    wire [15:0] st_nd    = rb_ev ? {1'b1, a_in, tmode != 2'd1, tmode == 2'd3, lcnt, 1'b0} :
                           sync_ev ? 16'h9001 : 16'hc001;
    reg         st_v;
    reg  [15:0] st_d;
    wire        ld_fr    = fr_want && rx_free;
    wire        ld_sth   = !fr_want && st_v && rx_free;
    wire        ld_stn   = !fr_want && !st_v && st_new && rx_free;
    wire        st_keep  = st_v && !ld_sth;
    wire        st_hold  = st_new && !ld_stn;
    assign rx_load = ld_fr || ld_sth || ld_stn;
    assign rx_tag  = fr_want ? fr_tag : `TRW_TAG_EVENT;
    assign rx_data = fr_want ? fr_data : st_v ? st_d : st_nd;
    assign ovr_set = (fr_want && !rx_free) || (st_hold && st_keep);

    // FRAME without [11] is LATE with no frame in progress, word framing stopped, or the count at/after n
    wire f_now   = tx_take && c_frame && !arg[11];
    assign late_set = f_now && (!in_frame || !words_on || (dcnt >= arg[10:0]));

`ifdef TRW_ASSERT_ON
    wire st_clash = (rb_ev && (sync_ev || ref_ev)) || (sync_ev && ref_ev);
    wire q_clash  = (k_data || k_crc) && q_dbit;
    `TRW_ASSERT(!st_clash, "BITSYNC: two status EVENTs in one clock")
    `TRW_ASSERT(!q_clash, "BITSYNC: a load of the TX queue while a queued bit leaves it")
`endif

    always @(posedge clk) begin
        if (!rst_n || restart || !active) begin
            tb <= per;  smp_done <= 1'b0;  rs_done <= 1'b0;  icnt <= 5'd0;
            bus_idle <= 1'b0;  in_frame <= 1'b0;  w <= 16'd0;  wn <= 5'd0;  wlen_o <= 5'd0;
            rl <= 1'b0;  rc <= 4'd0;  stuff_on <= 1'b0;  words_on <= 1'b0;  lcnt <= 11'd0;  dcnt <= 11'd0;
            crc <= 16'd0;  fr_v <= 1'b0;  fr_n <= 11'd0;  fnx_v <= 1'b0;  fnx_n <= 11'd0;  post <= 1'b0;
            rxl <= idle;  hb <= 16'd0;  hbn <= 5'd0;  f6 <= 1'b0;
            q <= 16'd0;  q_hi <= 1'b0;  qn <= 5'd0;  q_crc <= 1'b0;  sync_p <= 1'b0;  wt_p <= 1'b0;  ts_on <= 1'b0;
            ts_p <= 1'b0;  trl <= 1'b0;  trc <= 4'd0;  tcrc <= 16'd0;  drv <= 1'b0;  tlv <= 1'b0;
            rbm <= 2'd0;  rbm_s <= 2'd0;  tmode <= 2'd0;  jbit <= 1'b0;  se0_r <= 1'b0;  sq <= 5'd0;  jq <= 1'b0;
            dsc <= 1'b0;  txoff <= 1'b0;  own <= 1'b0;  st_v <= 1'b0;  st_d <= 16'd0;
            jp <= 1'b0;  jc <= 3'd0;  jb <= 4'd0;  jl <= 1'b0;  jdv <= 1'b0;
            av <= 1'b0;  an <= 4'd0;  al <= 1'b0;  af <= 1'b0;
        end else begin
            tb       <= (bnd ? tb1 + per : tb1) - 25'd256;
            smp_done <= bnd ? 1'b0 : (done || smp);
            if (bnd)
                rs_done <= 1'b0;
            else if (rs_do)
                rs_done <= 1'b1;
            if (smp) begin
                icnt <= icnt1;
                rxl  <= a_in;
            end

            // ---------------------------------------------------------- the bit on the line
            if (j_bit) begin                                   // P28: a JAM bit, bypassing the queue
                drv <= 1'b1;  tlv <= j_lvl;  jbit <= 1'b1;  se0_r <= 1'b0;
            end else if (deq) begin                            // a bit of ours from this edge
                drv   <= 1'b1;
                tlv   <= nl;
                trl   <= nd;
                trc   <= trc1;
                ts_p  <= ts_due;
                tmode <= tm_now;
                rbm_s <= tm_now;
                jbit  <= 1'b0;
                se0_r <= 1'b0;
            end else if (se_go) begin                          // P29: SE0 (pin A and pin N low)
                drv <= 1'b1;  tlv <= 1'b0;  se0_r <= 1'b1;  jbit <= 1'b0;  tmode <= rbm;
                sq  <= sq - 5'd1;
            end else if (jj_go) begin                          // then the idle level for one bit
                drv <= 1'b1;  tlv <= idle;  se0_r <= 1'b0;  jbit <= 1'b0;  tmode <= rbm;
                jq  <= 1'b0;
            end else if (bnd) begin                            // nothing to send: release the line
                drv <= 1'b0;  tlv <= idle;  se0_r <= 1'b0;  jbit <= 1'b0;
            end

            // ---------------------------------------------------------- JAM (P28)
            if (j_start_a) begin
                jdv <= 1'b1;  jb <= an;  jl <= al;  av <= 1'b0;  af <= 1'b0;  jp <= 1'b0;
            end else if (j_start_r) begin
                jdv <= 1'b1;  jp <= 1'b0;
            end else if (j_cont) begin
                jb <= jb - 4'd1;
            end else if (bnd) begin
                jdv <= 1'b0;
            end
            if (smp && !s_bit && jp && (jc != 3'd0))           // d + 1 non-stuff sample points
                jc <= jc - 3'd1;
            if (err_any && av && !txoff)
                af <= 1'b1;
            if (jm_rsp) begin                                  // a new response replaces one in progress
                jp <= 1'b1;  jc <= {1'b0, arg[7:6]} + 3'd1;  jb <= arg[11:8];  jl <= arg[5];  jdv <= 1'b0;
            end
            if (jm_arm) begin
                av <= 1'b1;  an <= arg[11:8];  al <= arg[5];
            end
            if (jm_dis) begin
                av <= 1'b0;  af <= 1'b0;
            end
            if (jm_on)
                txoff <= 1'b0;

            // ---------------------------------------------------------- TX queue
            if (new_run) begin
                sync_p <= 1'b0;
                own    <= 1'b1;
            end
            if (q_dbit) begin
                if (!q_hi)
                    q <= {1'b0, q[15:1]};
                qn <= qn - 5'd1;
                if (!q_crc)
                    tcrc <= tcrc1;                             // P25: data bits only
            end
            if (k_data) begin
                q <= ld_q;  q_hi <= order;  qn <= nb;  q_crc <= 1'b0;
            end
            if (k_sync && !txoff) begin                        // SYNC also ends a readback abort (P26)
                sync_p <= 1'b1;
                tcrc   <= crc_init & cmask;
                dsc    <= 1'b0;
            end
            if (k_line) begin
                ts_on <= arg[2];
                rbm   <= arg[1:0];
                if (arg[6])
                    tcrc <= crc_init & cmask;
                if (arg[3]) begin
                    q <= ld_q;  q_hi <= 1'b1;  qn <= cw;  q_crc <= 1'b1;
                end
                if (arg[4]) begin                              // P29: SE0 for [11:8] + 1 bits, then J
                    sq <= {1'b0, arg[11:8]} + 5'd1;
                    jq <= 1'b1;
                end
            end
            if (k_wait) begin
                wt_p <= 1'b1;
                if (!txoff)
                    dsc <= 1'b0;
            end else if (smp) begin
                wt_p <= 1'b0;
            end
            if (stop) begin                                    // P26: clear the queue; discard until SYNC / WAIT [1]
                qn <= 5'd0;  ts_p <= 1'b0;  sync_p <= 1'b0;  sq <= 5'd0;  jq <= 1'b0;  dsc <= 1'b1;
                own <= 1'b0;
            end
            if (jm_off) begin                                  // P28: listen-only: nothing driven, queue cleared
                txoff <= 1'b1;  dsc <= 1'b1;  own <= 1'b0;
                qn <= 5'd0;  ts_p <= 1'b0;  sync_p <= 1'b0;  sq <= 5'd0;  jq <= 1'b0;
                drv <= 1'b0;  tlv <= idle;  se0_r <= 1'b0;  jbit <= 1'b0;
                jp <= 1'b0;  jdv <= 1'b0;  af <= 1'b0;
            end

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

            // ---------------------------------------------------------- status EVENT register
            if (st_hold && !st_keep) begin
                st_v <= 1'b1;
                st_d <= st_nd;
            end else if (ld_sth) begin
                st_v <= 1'b0;
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
                hbn <= 5'd0;  f6 <= 1'b0;
                if (!new_run)
                    own <= 1'b0;                               // another node's frame
            end else if (goes_idle) begin                      // P20: no verdict, the partial word is dropped
                bus_idle <= 1'b1;
                in_frame <= 1'b0;
                w <= 16'd0;  wn <= 5'd0;
                stuff_on <= 1'b0;  words_on <= 1'b0;  post <= 1'b0;  fr_v <= 1'b0;
                hbn <= 5'd0;  f6 <= 1'b0;  own <= 1'b0;
            end else if (se0_s) begin                          // P29: SE0 ends the frame (verdict above)
                in_frame <= 1'b0;
                w <= 16'd0;  wn <= 5'd0;
                stuff_on <= 1'b0;  words_on <= 1'b0;  post <= 1'b0;  fr_v <= 1'b0;
                own <= 1'b0;
            end else if (fbit) begin
                lcnt <= lcnt + 11'd1;
                f6   <= six_s;
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
                end else if (six_s) begin
                    // P27: a flag or an abort follows; this bit is neither data nor an error
                end else if (fl_s) begin                       // P27: a flag closes the frame and opens the next
                    lcnt <= 11'd0;  dcnt <= 11'd0;  crc <= crc_init & cmask;
                    w <= 16'd0;  wn <= 5'd0;  words_on <= 1'b1;  stuff_on <= 1'b1;  post <= 1'b0;
                    fr_v <= fnx_v;  fr_n <= fnx_n;  fnx_v <= 1'b0;  hbn <= 5'd0;
                end else if (ab_s) begin                       // P27: an abort: nothing more until the next flag
                    words_on <= 1'b0;  fr_v <= 1'b0;  hbn <= 5'd0;
                end else if (dbit) begin
                    if (dlf && !hb_full)
                        hbn <= hbn + 5'd1;
                    if (cm) begin
                        dcnt <= dcnt1;
                        if (c_in)
                            crc <= crc1;
                        if (at_n) begin                        // P24: verdict; stuffing stops (one more may be due)
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
                    end
                end else begin
                    post <= 1'b0;                              // after n: no stuff bit was due
                end
            end
            // P27 hold-back: its contents count only through hbn, which a frame open resets; shifting it outside
            // the frame's priority chain keeps it off the frame-start timing path (a frame bit never falls in the
            // clock a frame opens)
            if (dbit && dlf)
                hb <= {hb[14:0], bit_in};
            if (tx_take && c_rxs) begin                        // SETN rx restarts the framing (applies at once)
                w <= 16'd0;
                wn <= 5'd0;
            end
        end
    end
endmodule
