// Second smoke-test user design (a different bitstream from counter4): combinational functions of
// the inputs on FAB_OUT0..2, a registered copy on FAB_OUT3, and an open-drain output on FAB_IO2
// (pulled low while FAB_IN3 is high, released otherwise) whose pad value is echoed on FAB_IO3.
`default_nettype none

module logic4 (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [3:0] a,
    output wire [3:0] y,
    output wire       od_oe,
    input  wire       od_i,
    output wire       echo
);
    reg r;
    always @(posedge clk) begin
        if (!rst_n) r <= 1'b0;
        else        r <= a[2] ^ a[3];
    end
    assign y     = {r, ~a[2], a[0] ^ a[1], a[0] & a[1]};
    assign od_oe = a[3];
    assign echo  = od_i;
endmodule
