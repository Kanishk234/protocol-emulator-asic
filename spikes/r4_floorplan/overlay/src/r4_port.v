// R4 spike (branch spike/r4-floorplan only): one fabric consumer port with its source multiplexer
// (ARCHITECTURE.md §4.3, §14 F1, F2, F4, F5, F7). Stand-in for phase 2's trw_chan_port: the structure
// and the registers are the real ones, so its area and wiring are representative.
//   cfg = {accept[3:0], sel[3:0], tap, en}, host-written; cfg_wr = 1 in the clock it changes (F5).
`default_nettype none

module r4_port #(
    parameter N = 9                     // legal sources, in `sel` order
) (
    input  wire            clk,
    input  wire            rst_n,
    input  wire [9:0]      cfg,
    input  wire            cfg_wr,
    input  wire [N-1:0]    src_valid,
    input  wire [N-1:0]    src_seq,
    input  wire [N-1:0]    src_load,     // the source loads a new token at this edge (tap drops, F4)
    input  wire [18*N-1:0] src_tok,      // {tag, data} per source
    input  wire            take,
    output wire            avail,
    output wire [17:0]     head,
    output wire            blocking,     // this port holds its selected source (for the release term)
    output wire [3:0]      sel,
    output reg             last_seq,
    output reg  [7:0]      dropped
);
    wire       en     = cfg[0];
    wire       tap    = cfg[1];
    wire [3:0] accept = cfg[9:6];
    assign sel      = cfg[5:2];
    assign blocking = en && !tap;

    reg        s_valid, s_seq, s_load;
    reg [17:0] s_tok;
    integer n;
    always @* begin
        s_valid = 1'b0;
        s_seq   = 1'b0;
        s_load  = 1'b0;
        s_tok   = 18'd0;
        for (n = 0; n < N; n = n + 1) begin
            if ({28'd0, sel} == n) begin
                s_valid = src_valid[n];
                s_seq   = src_seq[n];
                s_load  = src_load[n];
                s_tok   = src_tok[18*n +: 18];
            end
        end
    end

    wire present  = en && s_valid && (last_seq != s_seq);              // F1
    wire accepted = accept[s_tok[17:16]];
    assign avail  = present && accepted;
    assign head   = s_tok;
    wire drop     = tap && present && accepted && !take && s_load;      // F4

    always @(posedge clk) begin
        if (!rst_n) begin
            last_seq <= 1'b0;
            dropped  <= 8'd0;
        end else begin
            if (cfg_wr || (avail && take) || (present && !accepted) || drop)   // F5, F2, F7, F4
                last_seq <= s_seq;
            if (drop && (dropped != 8'hff))
                dropped <= dropped + 8'd1;
        end
    end
endmodule
