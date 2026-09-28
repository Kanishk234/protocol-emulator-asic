// UART receiver on the WARP hard primitives (ARCHITECTURE §8, D-026): same behaviour and
// interface as uart_rx.v, with the bit timer in a WP_TIMER (started at half a bit to sample
// mid-bit) and the data bits in a WP_SHIFT. The divisor is fixed in the bitstream (DIV >= 2).
`default_nettype none

module uart_rx_p #(
    parameter DIV = 434
) (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       rx,
    output wire [7:0] data,
    output reg        valid,
    output reg        ferr
);
    localparam integer  RELOAD_I = DIV - 1;
    localparam [15:0]   RELOAD   = RELOAD_I[15:0];

    reg  [1:0] sync;
    reg        busy;
    reg        started;     // start bit confirmed at its middle
    wire       line  = sync[1];
    wire       begin_ = !busy && !line;
    wire       tick, done, sout_unused;

    WP_TIMER #(.RELOAD(RELOAD), .ONESHOT(1'b0)) u_timer (
        .clk(clk), .rst(!rst_n), .load(begin_), .half(1'b1), .en(busy), .tc(tick));
    WP_SHIFT #(.LEN(4'd8), .MSB_FIRST(1'b0)) u_shift (
        .clk(clk), .rst(!rst_n), .load(begin_), .step(tick && started && !done), .sin(line),
        .d(8'h00), .sout(sout_unused), .done(done), .q(data));

    always @(posedge clk) begin
        if (!rst_n) begin
            sync    <= 2'b11;
            busy    <= 1'b0;
            started <= 1'b0;
            valid   <= 1'b0;
            ferr    <= 1'b0;
        end else begin
            sync  <= {sync[0], rx};
            valid <= 1'b0;
            if (begin_) begin
                busy    <= 1'b1;
                started <= 1'b0;
            end else if (tick) begin
                if (!started) begin
                    if (line) busy <= 1'b0;      // glitch, not a start bit
                    else      started <= 1'b1;
                end else if (done) begin         // stop bit
                    busy  <= 1'b0;
                    ferr  <= !line;
                    valid <= 1'b1;
                end
            end
        end
    end

    wire _unused = &{sout_unused, 1'b0};
endmodule
