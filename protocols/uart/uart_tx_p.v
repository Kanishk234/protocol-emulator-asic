// UART transmitter on the WARP hard primitives (ARCHITECTURE §8, D-026): same behaviour and
// interface as uart_tx.v, with the bit timer in a WP_TIMER and the data bits in a WP_SHIFT.
// The divisor is fixed in the bitstream (DIV clocks per bit, DIV >= 2).
//   start (valid && ready): load the byte, tx = 0 (start bit), the timer restarts;
//   each timer pulse: tx takes the next bit (8 data bits, then the 1 shifted in = stop bit);
//   the pulse after the stop bit (the shift register's done) ends the frame.
`default_nettype none

module uart_tx_p #(
    parameter DIV = 434
) (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [7:0] data,
    input  wire       valid,
    output wire       ready,
    output reg        tx
);
    localparam integer  RELOAD_I = DIV - 1;
    localparam [15:0]   RELOAD   = RELOAD_I[15:0];

    reg  busy;
    wire start = valid && !busy;
    wire tick, done, sout;
    wire [7:0] q_unused;

    WP_TIMER #(.RELOAD(RELOAD), .ONESHOT(1'b0)) u_timer (
        .clk(clk), .rst(!rst_n), .load(start), .half(1'b0), .en(busy), .tc(tick));
    // 9 steps: 8 data bits out, then the stop bit (sin = 1 fills the register)
    WP_SHIFT #(.LEN(4'd9), .MSB_FIRST(1'b0)) u_shift (
        .clk(clk), .rst(!rst_n), .load(start), .step(tick && !done), .sin(1'b1), .d(data),
        .sout(sout), .done(done), .q(q_unused));

    assign ready = !busy;

    always @(posedge clk) begin
        if (!rst_n) begin
            busy <= 1'b0;
            tx   <= 1'b1;
        end else if (start) begin
            busy <= 1'b1;
            tx   <= 1'b0;
        end else if (tick) begin
            if (done) busy <= 1'b0;
            else      tx   <= sout;
        end
    end

    wire _unused = &{q_unused, 1'b0};
endmodule
