// Pin unit, BITSYNC engine (ARCHITECTURE.md §14 P20-P29, D-023, D-025-D-027): one bit clock recovered from the
// line, shared by TX and RX. Full units only (U0-U1, D-040). Active while TXMODE and RXMODE are both `bitsync`;
// it then owns the unit's token takes, pin A and the producer loads.
//
// Built so far (docs/reports/PIN_UNIT_RTL.md §9):
//   B2a: the bit clock (P20), bus idle, frame start with hard sync (P21), resync limited to SJW (P22).
//   B2b: RX bit stuffing and stuff errors (P23), the RX CRC, RX words and `FRAME n` with its verdict (P24);
//        the RX commands `FRAME` and `SETN` rx are taken at once (P25).
// Next: the TX queue with LINE/SYNC and the TX CRC (B2c, P25), then P26-P29 (B3). Until B2c no TX token is taken.
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
//   - A token taken in clock n (tx_take) acts at edge n.
// Readings where the text leaves a choice are marked P-G<n> (PIN_UNIT_RTL.md §9).
`default_nettype none
`include "trw_defs.vh"

module trw_pin_bs (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        restart,
    input  wire        live,
    input  wire        active,       // TXMODE and RXMODE are bitsync (and this is a full unit)
    // configuration (static while running)
    input  wire        idle,         // the recessive level
    input  wire        order,
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
    // sensed pin (S, else A), this clock and the previous one
    input  wire        a_in,
    input  wire        a_prev,
    // consumer port head (RX commands now; TX tokens from B2c)
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
    // state, for the TX side and debug
    output reg         bus_idle,
    output reg         in_frame,
    output wire        bnd,          // a bit boundary at this clock's edge
    output wire        smp           // a sample in this clock
);
    // ------------------------------------------------------------------ edges on the sensed pin
    wire dom_edge = (a_prev == idle) && (a_in != idle);        // recessive to dominant
    wire any_edge = (a_prev != a_in);

    // ------------------------------------------------------------------ bit clock
    reg  [24:0] tb;            // 1/256 clocks to the next boundary, from this clock's start
    reg         smp_done;      // this bit's sample has been taken
    reg         rs_done;       // one resync per bit (P22)
    reg  [4:0]  icnt;          // consecutive recessive samples

    wire f_start = active && bus_idle && dom_edge;              // P21 (at idle: another node's first bit)
    wire rs_edge = active && !f_start && !rs_done && (resync_both ? any_edge : dom_edge);

    wire [24:0] per  = {1'b0, period};
    wire [24:0] sof  = {1'b0, sampleofs};
    wire [24:0] sj   = {1'b0, sjw};
    wire [24:0] tb0  = f_start ? per : tb;
    wire        done = !f_start && smp_done;
    // P22: e = time since the bit start; before the sample move later by min(e, SJW), after it end earlier
    wire [24:0] e    = per - tb0;
    wire [24:0] d    = !done ? ((e < sj) ? e : sj) : ((tb0 < sj) ? tb0 : sj);
    wire        rs_do = rs_edge && (d != 25'd0);
    wire [24:0] tb1  = !rs_do ? tb0 : (!done ? tb0 + d : tb0 - d);
    wire [24:0] x    = sof - (per - tb1);                        // the sample time, from this clock's start

    assign bnd = active && (tb1 < 25'd256);
    assign smp = active && !done && (x[24] || (x < 25'd256));   // at or before the end of this clock

    // ------------------------------------------------------------------ RX commands (P25: taken at once)
    wire [3:0]  op     = tx_data[15:12];
    wire [11:0] arg    = tx_data[11:0];
    wire        t_ctrl = (tx_tag == `TRW_TAG_CTRL);
    wire        c_frame = t_ctrl && (op == `TRW_CMD_FRAME);
    wire        c_rxs   = t_ctrl && (op == `TRW_CMD_SETN) && arg[5];
    assign tx_take = live && active && tx_avail && (c_frame || c_rxs);

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
    // P20: IDLE_BITS recessive samples make the bus idle; in a frame that ends it without a verdict
    wire [4:0]  icnt1     = rec ? ((icnt == 5'd31) ? icnt : icnt + 5'd1) : 5'd0;
    wire        goes_idle = smp && rec && (icnt1 >= idle_bits) && (idle_bits != 5'd0);
    wire        fbit     = smp && in_frame && !goes_idle;        // P-G29: the idle-making sample is no frame bit

    // P23: a stuff bit is due after STUFF_N equal line bits (of STUFF_LVL, if set)
    wire        lvl_ok   = !stuff_lvl[1] || (rl == stuff_lvl[0]);
    wire        s_due    = (stuff_n != 4'd0) && (rc == stuff_n) && lvl_ok && (stuff_on || post);
    wire        s_err    = fbit && s_due && (bit_in == rl);
    wire        s_bit    = fbit && s_due && (bit_in != rl);
    wire        open_fr  = words_on || stuff_on;              // destuffed bits count until FRAME's n
    wire        dbit     = fbit && !s_due && open_fr;
    wire [3:0]  rc1      = (bit_in == rl) ? ((rc == 4'hf) ? rc : rc + 4'd1) : 4'd1;

    // RX CRC (P24): MSB-first LFSR of CRC_WIDTH bits, after the first CRC_SKIP destuffed bits
    wire [15:0] cmask    = (crc_width == 5'd0) ? 16'd0 : (16'hffff >> (5'd16 - ((crc_width > 5'd16) ? 5'd16 : crc_width)));
    wire [3:0]  ctop     = (crc_width == 5'd0) ? 4'd0 : ((crc_width > 5'd16) ? 4'd15 : crc_width[3:0] - 4'd1);
    wire        cfb      = crc[ctop] ^ bit_in;
    wire [15:0] crc1     = (({crc[14:0], 1'b0}) ^ (cfb ? crc_poly : 16'd0)) & cmask;
    wire        c_in     = dbit && (dcnt >= {6'd0, crc_skip}) && (crc_width != 5'd0);

    // words
    wire [4:0]  wlen_c   = (rx_nbits == 5'd0) ? {1'b0, nbits} + 5'd1 : (rx_nbits > 5'd16) ? 5'd16 : rx_nbits;
    wire [4:0]  wlen     = (wlen_o != 5'd0) ? wlen_o : wlen_c;
    wire [4:0]  wn1      = wn + 5'd1;
    wire [15:0] w1       = order ? {w[14:0], bit_in} : (w | ({15'd0, bit_in} << wn));
    wire [10:0] dcnt1    = dcnt + 11'd1;
    wire        at_n     = dbit && fr_v && (dcnt1 == fr_n);    // this bit is FRAME's n-th
    wire        crc_ok   = ((c_in ? crc1 : crc) == (crc_res & cmask));
    // P24/P-G30: at bit n the verdict carries the word (partial or complete) instead of a DATA word
    wire        v_tok    = at_n && words_on;
    wire        w_tok    = dbit && words_on && !at_n && (wn1 == wlen);
    wire        err_tok  = s_err && (words_on || post);         // P23/P-G27: ERR 0x1nnn; P24: also the stuff bit after n

    assign rx_tag  = err_tok ? `TRW_TAG_ERR : v_tok ? (crc_ok ? `TRW_TAG_EVENT : `TRW_TAG_ERR) : `TRW_TAG_DATA;
    assign rx_data = err_tok ? {4'h1, 1'b0, lcnt} :
                     v_tok   ? (crc_ok ? {4'h0, w1[11:0]} : {4'h0, w1[11:0]}) : w1;
    wire   want    = live && (err_tok || v_tok || w_tok);
    assign rx_load = want && rx_free;
    assign ovr_set = want && !rx_free;

    // FRAME without [11] is LATE with no frame in progress, word framing stopped, or the count at/after n
    wire f_now   = tx_take && c_frame && !arg[11];
    assign late_set = f_now && (!in_frame || !words_on || (dcnt >= arg[10:0]));

    always @(posedge clk) begin
        if (!rst_n || restart || !active) begin
            tb <= per;  smp_done <= 1'b0;  rs_done <= 1'b0;  icnt <= 5'd0;
            bus_idle <= 1'b0;  in_frame <= 1'b0;  w <= 16'd0;  wn <= 5'd0;  wlen_o <= 5'd0;
            rl <= 1'b0;  rc <= 4'd0;  stuff_on <= 1'b0;  words_on <= 1'b0;  lcnt <= 11'd0;  dcnt <= 11'd0;
            crc <= 16'd0;  fr_v <= 1'b0;  fr_n <= 11'd0;  fnx_v <= 1'b0;  fnx_n <= 11'd0;  post <= 1'b0;
        end else begin
            tb       <= (bnd ? tb1 + per : tb1) - 25'd256;
            smp_done <= bnd ? 1'b0 : (done || smp);
            if (bnd)
                rs_done <= 1'b0;
            else if (rs_do)
                rs_done <= 1'b1;
            if (smp)
                icnt <= icnt1;

            // RX commands
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

            if (f_start) begin                                 // P21: a frame opens; its first bit follows
                bus_idle <= 1'b0;
                in_frame <= 1'b1;
                w <= 16'd0;  wn <= 5'd0;
                rl <= !idle;  rc <= 4'd0;                      // the first bit (dominant) starts the run
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
