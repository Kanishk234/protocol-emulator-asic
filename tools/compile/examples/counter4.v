// Smoke-test user design for the compile flow and the fabric simulation: a 4-bit counter on
// FAB_OUT0..3 that counts while `en` (FAB_IN0) is high, and a bidirectional pin that echoes the
// counter's LSB when `dir` (FAB_IN1) is high and is an input otherwise; its input is readable as
// the counter's reset value source through FAB_IO1 (an output).
`default_nettype none

module counter4 (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       en,
    input  wire       dir,
    output wire [3:0] q,
    output wire       io0_o,
    output wire       io0_oe,
    input  wire       io0_i,
    output wire       io1_o
);
    reg [3:0] c;
    always @(posedge clk) begin
        if (!rst_n)  c <= 4'd0;
        else if (en) c <= c + 4'd1;
    end
    assign q      = c;
    assign io0_o  = c[0];
    assign io0_oe = dir;
    assign io1_o  = io0_i;   // loops FAB_IO0's pad value back out on FAB_IO1
endmodule
