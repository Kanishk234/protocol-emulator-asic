// Pin unit, RX half (ARCHITECTURE.md §4.5, §7.4, §14 P2, P5, P8, P13, P15, P18, P19): samples pin A
// (SHIFT_RX, LINKED_RX, SAMPLE commands), frames the bits into words, generates events, and loads the
// unit's producer register. Lean feature set (no BITSYNC).
//
// Timing contract:
//   - Clock n: a sample reads `a_in` (the pad of clock n-2, P1); a completed word or an event is
//     loaded with `rx_load` at edge n (P2). `rx_load` is only raised when `rx_free` (§14 F3, the
//     producer's state at the start of clock n); a token that cannot be loaded is dropped and raises
//     `ovr_set` (§4.5).
//   - At most one load per clock, priority EVENT, then the LINKED_RX/SHIFT_RX word, then the SAMPLE
//     word (P19); a losing word sets `ovr_set`.
//   - `rxset` / `smp` come from the TX half in the clock they act; the sample and any word it
//     completes are handled first, then the framing restart (P18: RX runs before the TX stream).
//
// Choices the documents leave open are marked P-G<n> (docs/reports/PIN_UNIT_RTL.md §6).
`default_nettype none
`include "trw_defs.vh"

module trw_pin_rx (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        restart,
    input  wire        live,
    // configuration
    input  wire [1:0]  rxmode,
    input  wire        order,
    input  wire        idle,
    input  wire        autorearm,
    input  wire        rx_echo,
    input  wire        rx_edge,
    input  wire        ev_pin,
    input  wire [1:0]  ev_edge,
    input  wire [1:0]  ev_qual,
    input  wire        ev_reset,
    input  wire [23:0] period,
    input  wire [23:0] sampleofs,
    input  wire [7:0]  presc,
    input  wire [3:0]  nbits,
    input  wire [4:0]  rx_nbits,
    input  wire [4:0]  rx_nbits2,
    // pins
    input  wire        a_in,
    input  wire        a_prev,
    input  wire        b_in,
    input  wire        b_prev,
    input  wire        c_in,
    input  wire        c_prev,
    input  wire        sel,
    // from the TX half
    input  wire        echo,
    input  wire        rxset,
    input  wire [4:0]  rxset_n,
    input  wire        smp,
    // producer register
    input  wire        rx_free,
    output wire        rx_load,
    output wire [1:0]  rx_tag,
    output wire [15:0] rx_data,
    output wire        ovr_set
);
    wire m_srx = (rxmode == `TRW_PCE_RXMODE_SHIFT_RX);
    wire m_lrx = (rxmode == `TRW_PCE_RXMODE_LINKED_RX);

    // ------------------------------------------------------------------ event time (P8, D-024)
    // A 15-bit tick counter, +1 every PRESC clocks; a configuration write restarts it (D-035 J).
    reg [7:0]  pr;
    reg [14:0] tick;
    always @(posedge clk) begin
        if (!rst_n || restart) begin
            pr   <= 8'h00;
            tick <= 15'd0;
        end else if (pr == presc) begin
            pr   <= 8'h00;
            tick <= tick + 15'd1;
        end else begin
            pr <= pr + 8'h01;
        end
    end

    // ------------------------------------------------------------------ event generator (P8, P15)
    wire es   = ev_pin ? c_in : a_in;
    wire ep   = ev_pin ? c_prev : a_prev;
    wire rise = es && !ep;
    wire fall = !es && ep;
    wire edge_ok = (((ev_edge == `TRW_PCE_EV_EDGE_RISE) || (ev_edge == `TRW_PCE_EV_EDGE_BOTH)) && rise)
                || (((ev_edge == `TRW_PCE_EV_EDGE_FALL) || (ev_edge == `TRW_PCE_EV_EDGE_BOTH)) && fall);
    wire qlv = (ev_qual == `TRW_PCE_EV_QUAL_1);
    wire qual_ok = !((ev_qual == `TRW_PCE_EV_QUAL_0) || qlv) || ((b_in == qlv) && (b_prev == qlv));
    wire ev = edge_ok && qual_ok;

    // ------------------------------------------------------------------ SHIFT_RX (P5, P15)
    localparam S_IDLE = 2'd0, S_START = 2'd1, S_SAMP = 2'd2, S_STOP = 2'd3;
    reg [1:0]  sst;
    reg [23:0] rt;                              // 16.8 clocks from this clock to the next sample
    wire       srx_on  = m_srx && sel;
    wire       start   = srx_on && (sst == S_START) && (a_in != idle);
    wire [23:0] rt_cur = start ? sampleofs : rt;
    wire       srx_smp = srx_on && (start || (sst == S_SAMP)) && (rt_cur[23:8] == 16'd0);
    wire [24:0] rt_add = {1'b0, rt_cur} + (srx_smp ? {1'b0, period} : 25'd0);

    // ------------------------------------------------------------------ LINKED_RX, SAMPLE
    wire lrx_smp = m_lrx && sel && (rx_edge ? (b_prev && !b_in) : (!b_prev && b_in));
    wire ms      = srx_smp || lrx_smp;         // the RX mode's sample
    wire smp_ok  = smp && sel;                  // SAMPLE bits are discarded while deselected (P15)
    wire smp_lost = ms && smp_ok;               // P-G11: two bits in one clock: the SAMPLE bit is lost
    wire bit_v   = ms || smp_ok;

    // ------------------------------------------------------------------ word framing (P13, P18)
    reg [15:0] fw;
    reg [4:0]  fc;
    reg        fph, ftaint, fo_v;
    reg [4:0]  fo_n;
    wire [4:0] n1  = (rx_nbits == 5'd0) ? {1'b0, nbits} + 5'd1 : (rx_nbits > 5'd16) ? 5'd16 : rx_nbits;
    wire [4:0] n2  = (rx_nbits2 > 5'd16) ? 5'd16 : rx_nbits2;
    wire       two = !fo_v && (rx_nbits2 != 5'd0);
    wire [4:0] len = fo_v ? fo_n : (two && fph) ? n2 : n1;

    reg [15:0] fw_add;
    integer i;
    always @* begin
        if (order)
            fw_add = {fw[14:0], a_in};           // MSB first: the last bit ends in data[0]
        else
            for (i = 0; i < 16; i = i + 1)
                fw_add[i] = fw[i] || (a_in && (fc[3:0] == i[3:0]));
    end
    wire done  = bit_v && ((fc + 5'd1) == len);
    wire taint = ftaint || echo;
    wire emit  = done && (!taint || rx_echo);
    wire rst_fr = !sel || rxset || (ev && ev_reset);

    always @(posedge clk) begin
        if (!rst_n || restart) begin
            fw <= 16'h0000;  fc <= 5'd0;  fph <= 1'b0;  ftaint <= 1'b0;
            fo_v <= 1'b0;  fo_n <= 5'd0;
            sst <= S_IDLE;  rt <= 24'd0;
        end else begin
            if (rst_fr || done) begin
                fw <= 16'h0000;
                fc <= 5'd0;
                ftaint <= 1'b0;
                fph <= rst_fr ? 1'b0 : (two ? !fph : fph);
            end else if (bit_v) begin
                fw <= fw_add;
                fc <= fc + 5'd1;
                ftaint <= taint;
            end
            if (rxset) begin
                fo_v <= 1'b1;
                fo_n <= ((rxset_n == 5'd0) || (rxset_n > 5'd16)) ? 5'd16 : rxset_n;
            end

            // SHIFT_RX state
            rt <= rt_add[23:0] - 24'd256;
            if (!srx_on)
                sst <= S_IDLE;
            else case (sst)
                S_IDLE:  if (a_in == idle) sst <= S_START;
                S_START: if (start) sst <= (srx_smp && done) ? (autorearm ? S_IDLE : S_STOP) : S_SAMP;
                S_SAMP:  if (srx_smp && done) sst <= autorearm ? S_IDLE : S_STOP;
                default: if (rxset) sst <= S_IDLE;          // P-G10: SETN rx re-arms
            endcase
        end
    end

    // ------------------------------------------------------------------ load (P2, P19, §4.5)
    wire want = ev || emit;
    assign rx_load = live && want && rx_free;
    assign rx_tag  = ev ? `TRW_TAG_EVENT : `TRW_TAG_DATA;
    assign rx_data = ev ? {es, tick} : fw_add;
    assign ovr_set = live && ((want && !rx_free) || (ev && emit) || smp_lost);

    wire _unused = &{1'b0, rt_add[24]};
endmodule
