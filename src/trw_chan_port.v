// Fabric consumer port (ARCHITECTURE.md §4.3, §14 F1, F2, F4, F5, F7) with its legal-source multiplexer:
// N sources in `sel` order (§4.6). The multiplexer sits next to the consumer.
//
// Registers: en, tap (0 = blocking), sel, accept (tag mask), last_seq, DROPPED (8-bit, saturating).
//
// Timing contract:
//   - `avail`/`head` are combinational from the port's registers and the selected producer's registers:
//     avail = en && src.valid && last_seq != src.seq && accept[src.tag] (F1, F7).
//   - `take` (from the consumer, same clock) sets last_seq := src.seq at the edge (F2). A take while
//     !avail does nothing.
//   - A present token whose tag is not accepted is dropped at the edge (last_seq := src.seq), as if taken
//     (F7), so a filtered port never holds its producer back.
//   - Tap: if the selected producer loads at this edge while the port had the token available and did
//     not take it, DROPPED counts one and the drop counts as a take (F4, BUGS #2).
//   - Configuration write (`cfg_we`): en, tap, sel and accept take the written values and
//     last_seq := the *newly selected* source's seq at the same edge (F5), so a re-pointed port never
//     sees a stale token. A write wins over a take in the same clock. A `sel` beyond the list selects
//     nothing (never available).
//   - `blocking`, `sel` and `last_seq` go to the fabric's release terms (§4.4); they are registers.
//   - `clr_dropped` clears DROPPED at the edge (a drop in the same clock wins). How the host reaches it
//     is the host's address map.
`default_nettype none

module trw_chan_port #(
    parameter N = 9                      // legal sources, 1..16
) (
    input  wire            clk,
    input  wire            rst_n,
    // configuration (host)
    input  wire            cfg_we,
    input  wire            cfg_en,
    input  wire            cfg_tap,
    input  wire [3:0]      cfg_sel,
    input  wire [3:0]      cfg_accept,
    input  wire            clr_dropped,
    // sources, in sel order
    input  wire [N-1:0]    src_valid,
    input  wire [N-1:0]    src_seq,
    input  wire [N-1:0]    src_load,     // the source loads a new token at this edge
    input  wire [18*N-1:0] src_tok,      // {tag, data} per source
    // consumer
    input  wire            take,
    output wire            avail,
    output wire [17:0]     head,
    // state (release terms, host readback)
    output reg             en,
    output reg             tap,
    output reg  [3:0]      sel,
    output reg  [3:0]      accept,
    output wire            blocking,
    output reg             last_seq,
    output reg  [7:0]      dropped
);
    // selected source; a sel beyond the list selects nothing
    reg        s_valid, s_seq, s_load, w_seq;
    reg [17:0] s_tok;
    integer n;
    always @* begin
        s_valid = 1'b0;
        s_seq   = 1'b0;
        s_load  = 1'b0;
        s_tok   = 18'd0;
        w_seq   = 1'b0;
        for (n = 0; n < N; n = n + 1) begin
            if ({28'd0, sel} == n) begin
                s_valid = src_valid[n];
                s_seq   = src_seq[n];
                s_load  = src_load[n];
                s_tok   = src_tok[18*n +: 18];
            end
            if ({28'd0, cfg_sel} == n)
                w_seq = src_seq[n];          // F5: the newly selected source's seq
        end
    end

    wire present  = en && s_valid && (last_seq != s_seq);      // F1 before the tag filter
    wire accepted = accept[s_tok[17:16]];                       // F7
    assign avail    = present && accepted;
    assign head     = s_tok;
    assign blocking = en && !tap;

    wire took     = avail && take;                              // F2
    wire filtered = present && !accepted;                       // F7
    wire drop     = tap && avail && !take && s_load;            // F4

    always @(posedge clk) begin
        if (!rst_n) begin
            en       <= 1'b0;
            tap      <= 1'b0;
            sel      <= 4'd0;
            accept   <= 4'd0;
            last_seq <= 1'b0;
        end else if (cfg_we) begin
            en       <= cfg_en;
            tap      <= cfg_tap;
            sel      <= cfg_sel;
            accept   <= cfg_accept;
            last_seq <= w_seq;
        end else if (took || filtered || drop) begin
            last_seq <= s_seq;
        end
    end

    always @(posedge clk) begin
        if (!rst_n)
            dropped <= 8'd0;
        else if (drop && !cfg_we)
            dropped <= (dropped == 8'hff) ? 8'hff : dropped + 8'd1;
        else if (clr_dropped)
            dropped <= 8'd0;
    end
endmodule
