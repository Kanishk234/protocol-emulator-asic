// Fabric producer register (ARCHITECTURE.md §4.2, §14 F3, F4, F6): depth 1, {valid, seq, tag, data}.
// Used for the pin units' RX halves and HOST_IN; each lane keeps its O0/O1 producer registers inside
// trw_lane (same rules).
//
// Timing contract:
//   - `free` (F3) is combinational from registered state only: `!valid`, or `all_taken`, which the
//     fabric computes from its ports' registers. Takes made in the same clock do not count.
//   - `load` = `load_req && free`: the token `tok_in` is loaded at the edge (seq toggles, valid := 1).
//     A request while not free is ignored here; the owner decides what that means (a pin RX half
//     discards the token and sets OVERRUN, §4.5; HOST_IN reports busy to the host).
//   - `valid` stays set until the next load (F6).
`default_nettype none

module trw_chan_prod (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        load_req,
    input  wire [17:0] tok_in,      // {tag, data}
    input  wire        all_taken,   // §4.4 release term, from the fabric
    output wire        free,
    output wire        load,        // to the fabric: a load at this edge (tap drop counting, F4)
    output reg         valid,
    output reg         seq,
    output reg  [17:0] tok
);
    assign free = !valid || all_taken;
    assign load = load_req && free;

    always @(posedge clk) begin
        if (!rst_n) begin
            valid <= 1'b0;
            seq   <= 1'b0;
            tok   <= 18'd0;
        end else if (load) begin
            valid <= 1'b1;
            seq   <= !seq;
            tok   <= tok_in;
        end
    end
endmodule
