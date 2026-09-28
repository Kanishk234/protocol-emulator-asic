// Pin unit, BITSYNC engine (ARCHITECTURE.md §14 P20-P29, D-023, D-025-D-027): one bit clock recovered from the
// line, shared by TX and RX. Full units only (U0-U1, D-040). Active while TXMODE and RXMODE are both `bitsync`;
// it then owns the unit's token takes, pin A and the producer loads.
//
// Milestone B2a (this file so far): the bit clock (P20), bus idle, frame start with hard sync (P21), resync
// limited to SJW (P22), and RX word framing of the sampled bits. Stuffing, CRC and FRAME (P23, P24), the TX
// queue (P25) and P26-P29 follow (docs/reports/PIN_UNIT_RTL.md §9).
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
//   - A word completed by the sample in clock n is loaded at edge n if the producer is free, else it is
//     dropped and `ovr_set` rises (§4.5).
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
    // sensed pin (S, else A), this clock and the previous one
    input  wire        a_in,
    input  wire        a_prev,
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

    // ------------------------------------------------------------------ RX words
    wire [4:0] wlen = (rx_nbits == 5'd0) ? {1'b0, nbits} + 5'd1 : (rx_nbits > 5'd16) ? 5'd16 : rx_nbits;
    reg  [15:0] w;             // the word so far (right-aligned as it will be emitted)
    reg  [4:0]  wn;            // bits in it
    wire        bit_in   = a_in;
    wire        rec      = (bit_in == idle);
    wire        take_bit = smp && in_frame;
    // P20: IDLE_BITS recessive samples make the bus idle; in a frame that ends it without a verdict
    wire [4:0]  icnt1     = rec ? ((icnt == 5'd31) ? icnt : icnt + 5'd1) : 5'd0;
    wire        goes_idle = smp && rec && (icnt1 >= idle_bits) && (idle_bits != 5'd0);
    wire [4:0]  wn1    = wn + 5'd1;
    wire [15:0] w1     = order ? {w[14:0], bit_in} : (w | ({15'd0, bit_in} << wn));
    wire        w_done = take_bit && (wn1 == wlen) && !goes_idle;   // P-G29: the idle-making sample is no frame bit

    assign rx_tag  = `TRW_TAG_DATA;
    assign rx_data = w1;
    assign rx_load = live && w_done && rx_free;
    assign ovr_set = live && w_done && !rx_free;

    always @(posedge clk) begin
        if (!rst_n || restart || !active) begin
            tb <= per;  smp_done <= 1'b0;  rs_done <= 1'b0;  icnt <= 5'd0;
            bus_idle <= 1'b0;  in_frame <= 1'b0;  w <= 16'd0;  wn <= 5'd0;
        end else begin
            tb       <= (bnd ? tb1 + per : tb1) - 25'd256;
            smp_done <= bnd ? 1'b0 : (done || smp);
            if (bnd)
                rs_done <= 1'b0;
            else if (rs_do)
                rs_done <= 1'b1;
            if (smp)
                icnt <= icnt1;
            if (f_start) begin
                bus_idle <= 1'b0;
                in_frame <= 1'b1;
                w <= 16'd0;
                wn <= 5'd0;
            end
            if (goes_idle) begin
                bus_idle <= 1'b1;
                in_frame <= 1'b0;                              // P20: no verdict, the partial word is dropped
                w <= 16'd0;
                wn <= 5'd0;
            end else if (take_bit && !f_start) begin
                if (w_done) begin
                    w <= 16'd0;
                    wn <= 5'd0;
                end else begin
                    w <= w1;
                    wn <= wn1;
                end
            end
        end
    end
endmodule
