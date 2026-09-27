// 2-FF synchronisers for pad inputs (ARCHITECTURE.md §3, §14 P1).
//
// Timing contract: `q` in clock n is `d` as sampled at edge n-2, i.e. the pad value of clock n-2 (P1).
// No reset: the stages are known two clocks after the pads are, and nothing reads them during reset.
`default_nettype none

module trw_sync #(
    parameter W = 16
) (
    input  wire         clk,
    input  wire [W-1:0] d,
    output reg  [W-1:0] q
);
    reg [W-1:0] s1;
    always @(posedge clk) begin
        s1 <= d;
        q  <= s1;
    end
endmodule
