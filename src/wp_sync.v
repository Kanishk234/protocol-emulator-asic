// Two-flop synchronizer (ARCHITECTURE.md §2.1, §6). RESET_VAL is the value held in reset,
// e.g. 1 for an active-low chip select.
`default_nettype none

module wp_sync #(
    parameter integer WIDTH = 1,
    parameter [WIDTH-1:0] RESET_VAL = {WIDTH{1'b0}}
) (
    input  wire             clk,
    input  wire             rst_n,
    input  wire [WIDTH-1:0] d,
    output wire [WIDTH-1:0] q
);
    reg [WIDTH-1:0] s1, s2;
    always @(posedge clk) begin
        if (!rst_n) begin
            s1 <= RESET_VAL;
            s2 <= RESET_VAL;
        end else begin
            s1 <= d;
            s2 <= s1;
        end
    end
    assign q = s2;
endmodule
