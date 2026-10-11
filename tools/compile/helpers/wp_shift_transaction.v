// Bounded serial transaction using one baseline shift register.
`default_nettype none
module wp_shift_transaction #(
    parameter integer BITS = 8,
    parameter MSB_FIRST = 1'b1
) (
    input wire clk,
    input wire rst_n,
    input wire start,
    input wire step,
    input wire sin,
    input wire [7:0] data,
    output wire ready,
    output wire complete,
    output wire serial,
    output wire [7:0] result
);
    reg busy;
    wire accept = start && !busy && rst_n;
    wire done;
    assign ready = !busy && rst_n;
    assign complete = busy && done && rst_n;
    WP_SHIFT #(.LEN(BITS), .MSB_FIRST(MSB_FIRST)) shifter (
        .clk(clk), .rst(!rst_n), .load(accept),
        .step(step && busy && !done && rst_n), .sin(sin), .d(data),
        .sout(serial), .done(done), .q(result));
    always @(posedge clk) begin
        if (!rst_n) busy <= 1'b0;
        else if (accept) busy <= 1'b1;
        else if (complete) busy <= 1'b0;
    end
endmodule
