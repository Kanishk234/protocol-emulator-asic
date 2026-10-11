// Compilation smoke example, not a complete protocol or achieved-rate claim.
`default_nettype none
module helper_demo (
    input wire clk,
    input wire rst_n,
    input wire request,
    input wire rx,
    output wire tx,
    output wire ready,
    output wire complete,
    output wire tick
);
    wire wait_ready;
    wire [7:0] result;
    wp_delay #(.CYCLES(4)) delay_u (
        .clk(clk), .rst_n(rst_n), .start(request), .enable(1'b1),
        .ready(wait_ready), .elapsed(tick));
    wp_shift_transaction #(.BITS(8), .MSB_FIRST(1'b1)) shift_u (
        .clk(clk), .rst_n(rst_n), .start(request), .step(tick),
        .sin(rx), .data(8'hA5), .ready(ready), .complete(complete),
        .serial(tx), .result(result));
endmodule
