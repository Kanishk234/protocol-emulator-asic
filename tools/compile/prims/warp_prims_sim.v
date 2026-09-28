// Simulation of the WARP hard primitives for user-design tests (protocols/*/test): WP_TIMER and
// WP_SHIFT with the same parameters and ports as warp_prims.v, built on the fabric's own primitive
// RTL (arch/prims/wp_timer.v, wp_shift.v) with the parameters as its configuration bits (BelMap
// order: RELOAD0..15, ONESHOT; LEN0..3, MSB_FIRST). Compile with those two files instead of
// warp_prims.v. Not for synthesis.
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
    wp_timer u_bel (.CLK(clk), .rst(rst), .load(load), .half(half), .en(en), .tc(tc),
                    .ConfigBits({ONESHOT, RELOAD}));
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
    wp_shift u_bel (.CLK(clk), .rst(rst), .load(load), .step(step), .sin(sin), .d(d),
                    .sout(sout), .done(done), .q(q), .ConfigBits({MSB_FIRST, LEN}));
endmodule
