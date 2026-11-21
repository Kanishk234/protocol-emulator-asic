`include "trw_defs.vh"
// Verification only: native RX plus native producer. A second native RX with
// free=1 exposes completion intent without peeking at DUT internal signals.
module pin_rx_overrun(input wire clk);
    (* anyseq *) reg rst_n, restart, live, all_taken;
    (* anyseq *) reg [1:0] rxmode, ev_edge, ev_qual;
    (* anyseq *) reg order, idle, autorearm, rx_echo, rx_edge, ev_pin, ev_reset;
    (* anyseq *) reg [23:0] period, sampleofs;
    (* anyseq *) reg [7:0] presc;
    (* anyseq *) reg [3:0] nbits;
    (* anyseq *) reg [4:0] rx_nbits, rx_nbits2, rxset_n;
    (* anyseq *) reg a_in, a_prev, b_in, b_prev, c_in, c_prev, sel, echo, rxset, smp;
    reg past_valid = 0;
    always @(posedge clk) begin
        past_valid <= 1;
        if (!past_valid) assume(!rst_n); else assume(rst_n);
    end
    wire free, load, valid, seq;
    wire [17:0] token;
    wire [1:0] candidate, overrun;
    wire [3:0] tag;
    wire [31:0] data;
    genvar g;
    generate for (g=0; g<2; g=g+1) begin: receivers
        trw_pin_rx rx (
            .clk(clk), .rst_n(rst_n), .restart(restart), .live(live),
            .rxmode(rxmode), .order(order), .idle(idle), .autorearm(autorearm),
            .rx_echo(rx_echo), .rx_edge(rx_edge), .ev_pin(ev_pin),
            .ev_edge(ev_edge), .ev_qual(ev_qual), .ev_reset(ev_reset),
            .period(period), .sampleofs(sampleofs), .presc(presc), .nbits(nbits),
            .rx_nbits(rx_nbits), .rx_nbits2(rx_nbits2),
            .a_in(a_in), .a_prev(a_prev), .b_in(b_in),
`ifdef TRW_RX_SHARED_EDGES
            .b_rise(b_in && !b_prev), .b_fall(!b_in && b_prev),
`else
            .b_prev(b_prev),
`endif
            .c_in(c_in), .c_prev(c_prev), .sel(sel), .echo(echo),
            .rxset(rxset), .rxset_n(rxset_n), .smp(smp),
            .rx_free(g == 0 ? free : 1'b1), .rx_load(candidate[g]),
            .rx_tag(tag[2*g +:2]), .rx_data(data[16*g +:16]), .ovr_set(overrun[g])
        );
    end endgenerate
    trw_chan_prod producer (
        .clk(clk), .rst_n(rst_n), .load_req(candidate[0]),
        .tok_in({tag[1:0],data[15:0]}), .all_taken(all_taken),
        .free(free), .load(load), .valid(valid), .seq(seq), .tok(token)
    );
    // Independent observable event condition, including qualification stability.
    wire event_level = ev_pin ? c_in : a_in;
    wire previous_level = ev_pin ? c_prev : a_prev;
    wire rising = event_level && !previous_level;
    wire falling = !event_level && previous_level;
    wire qualified = ev_qual == `TRW_PCE_EV_QUAL_NONE || ev_qual == 1 ||
                     (ev_qual == `TRW_PCE_EV_QUAL_0 && !b_in && !b_prev) ||
                     (ev_qual == `TRW_PCE_EV_QUAL_1 && b_in && b_prev);
    wire event_now = qualified && ((rising && (ev_edge == 1 || ev_edge == 3)) ||
                                  (falling && (ev_edge == 2 || ev_edge == 3)));
    reg [1:0] accepted;
    reg saw_overrun;
    always @(posedge clk) begin
        if (!rst_n) begin accepted <= 0; saw_overrun <= 0; end
        else begin
            assert(candidate[0] == (candidate[1] && free));
            assert(tag[1:0] == tag[3:2]);
            assert(data[15:0] == data[31:16]);
            assert(!live || !event_now || candidate[1]);
            assert(!live || !event_now || tag[1:0] == `TRW_TAG_EVENT);
            assert(!candidate[1] || free || overrun[0]);
            assert(overrun[0] == (overrun[1] || (candidate[1] && !free)));
            if (past_valid && $past(rst_n)) begin
                if (!$past(free)) begin
                    assert(token == $past(token));
                    assert(seq == $past(seq));
                    assert(valid == $past(valid));
                end
                if ($past(load)) begin
                    assert(valid);
                    assert(token == $past({tag[1:0],data[15:0]}));
                    assert(seq != $past(seq));
                end
            end
            if (load && accepted != 3) accepted <= accepted + 1'b1;
            if (candidate[1] && !free && overrun[0]) saw_overrun <= 1;
            cover(saw_overrun && accepted >= 2);
            cover(candidate[1] && !free && overrun[0] && event_now);
            cover(candidate[1] && !free && overrun[0] && !event_now);
        end
    end
endmodule
