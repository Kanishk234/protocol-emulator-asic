// Smoke-test user design for the hard primitives (D-026, ARCHITECTURE §8) on fabrics that have
// them: one timer and one shift register.
//   - the timer (RELOAD 5, periodic) pulses tc every 6 enabled cycles while `en` (FAB_IN0) is high;
//     tick toggles FAB_OUT0, and tc itself is on FAB_OUT1;
//   - the shift register is a 6-bit LSB-first serialiser: `load` (FAB_IN1) takes the byte 8'hA5
//     (its low 6 bits), `step` (FAB_IN2) shifts one bit out (sout on FAB_OUT2), FAB_IN3 is sin,
//     done is FAB_OUT3, and q[3:0] are on FAB_OUT4, FAB_OUT5, FAB_IO0, FAB_IO1.
`default_nettype none

module prims2 (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       en,
    input  wire       load,
    input  wire       step,
    input  wire       sin,
    output wire [5:0] out,
    output wire [1:0] io
);
    wire tc, sout, done;
    wire [7:0] q;
    reg tog;

    WP_TIMER #(.RELOAD(16'd5), .ONESHOT(1'b0)) u_t (
        .clk(clk), .rst(!rst_n), .load(1'b0), .half(1'b0), .en(en), .tc(tc));
    WP_SHIFT #(.LEN(4'd6), .MSB_FIRST(1'b0)) u_s (
        .clk(clk), .rst(!rst_n), .load(load), .step(step), .sin(sin), .d(8'hA5),
        .sout(sout), .done(done), .q(q));

    always @(posedge clk) begin
        if (!rst_n)  tog <= 1'b0;
        else if (tc) tog <= !tog;
    end
    assign out = {q[1], q[0], done, sout, tc, tog};
    assign io  = q[3:2];
endmodule
