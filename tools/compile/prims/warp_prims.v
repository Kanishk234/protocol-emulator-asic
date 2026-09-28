// WARP hard primitives for user designs (ARCHITECTURE.md §8, D-026). The compile flow reads this
// file with every design on an architecture that has them (arch.yaml `primitives`).
//
//   WP_TIMER #(.RELOAD(n), .ONESHOT(0)) t (.clk, .rst, .load, .half, .en, .tc);
//   WP_SHIFT #(.LEN(8), .MSB_FIRST(1)) s (.clk, .rst, .load, .step, .sin, .d(byte), .sout, .done, .q);
//
// Behaviour: ARCHITECTURE §8 (cycle-exact). The wrappers pass each parameter bit to the BEL's
// configuration feature of the same name (RELOAD0..15, ONESHOT, LEN0..3, MSB_FIRST) and split the
// byte ports into the BEL's per-bit pins, which is how the fabric describes the blocks
// (macro/<fabric>/fabulous/.FABulous/bel.v2.txt).
`default_nettype none

module WP_TIMER #(
    parameter [15:0] RELOAD  = 16'd0,
    parameter        ONESHOT = 1'b0
) (
    input  wire clk,
    input  wire rst,
    input  wire load,
    input  wire half,
    input  wire en,
    output wire tc
);
    wp_timer #(
        .RELOAD0(RELOAD[0]),   .RELOAD1(RELOAD[1]),   .RELOAD2(RELOAD[2]),   .RELOAD3(RELOAD[3]),
        .RELOAD4(RELOAD[4]),   .RELOAD5(RELOAD[5]),   .RELOAD6(RELOAD[6]),   .RELOAD7(RELOAD[7]),
        .RELOAD8(RELOAD[8]),   .RELOAD9(RELOAD[9]),   .RELOAD10(RELOAD[10]), .RELOAD11(RELOAD[11]),
        .RELOAD12(RELOAD[12]), .RELOAD13(RELOAD[13]), .RELOAD14(RELOAD[14]), .RELOAD15(RELOAD[15]),
        .ONESHOT(ONESHOT)
    ) u_bel (.CLK(clk), .rst(rst), .load(load), .half(half), .en(en), .tc(tc));
endmodule

module WP_SHIFT #(
    parameter [3:0] LEN       = 4'd8,
    parameter       MSB_FIRST = 1'b1
) (
    input  wire       clk,
    input  wire       rst,
    input  wire       load,
    input  wire       step,
    input  wire       sin,
    input  wire [7:0] d,
    output wire       sout,
    output wire       done,
    output wire [7:0] q
);
    wp_shift #(
        .LEN0(LEN[0]), .LEN1(LEN[1]), .LEN2(LEN[2]), .LEN3(LEN[3]), .MSB_FIRST(MSB_FIRST)
    ) u_bel (
        .CLK(clk), .rst(rst), .load(load), .step(step), .sin(sin),
        .d0(d[0]), .d1(d[1]), .d2(d[2]), .d3(d[3]), .d4(d[4]), .d5(d[5]), .d6(d[6]), .d7(d[7]),
        .sout(sout), .done(done),
        .q0(q[0]), .q1(q[1]), .q2(q[2]), .q3(q[3]), .q4(q[4]), .q5(q[5]), .q6(q[6]), .q7(q[7])
    );
endmodule
