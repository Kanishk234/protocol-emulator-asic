// One-shot delay using one baseline timer. Synchronous active-low reset.
`default_nettype none
module wp_delay #(
    parameter integer CYCLES = 2
) (
    input wire clk,
    input wire rst_n,
    input wire start,
    input wire enable,
    output wire ready,
    output wire elapsed
);
    reg busy;
    wire accept = start && !busy && rst_n;
    wire tc;
    assign ready = !busy && rst_n;
    assign elapsed = busy && tc && rst_n;
    WP_TIMER #(.RELOAD(CYCLES - 1), .ONESHOT(1'b1)) timer (
        .clk(clk), .rst(!rst_n), .load(accept), .half(1'b0),
        .en(busy && enable && rst_n), .tc(tc));
    always @(posedge clk) begin
        if (!rst_n) busy <= 1'b0;
        else if (accept) busy <= 1'b1;
        else if (elapsed) busy <= 1'b0;
    end
endmodule
