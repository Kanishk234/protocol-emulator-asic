// UART receiver, 8N1, LSB first. Two-flop synchronizer, start detected on a low level,
// start re-checked half a bit later (a glitch shorter than that is ignored), then each bit
// sampled one bit time apart. `valid` pulses for one clock with `data` and `ferr`
// (stop bit read as 0). Each bit lasts `div` clocks (div >= 2).
`default_nettype none

module uart_rx #(
    parameter DIV_W = 16
) (
    input  wire             clk,
    input  wire             rst_n,
    input  wire [DIV_W-1:0] div,
    input  wire             rx,
    output reg  [7:0]       data,
    output reg              valid,
    output reg              ferr
);
    reg [1:0]       sync;
    reg             busy;
    reg [3:0]       nbit;   // 0 = start, 1..8 = data, 9 = stop
    reg [7:0]       shift;
    reg [DIV_W-1:0] cnt;

    wire line = sync[1];

    always @(posedge clk) begin
        if (!rst_n) begin
            sync  <= 2'b11;
            busy  <= 1'b0;
            nbit  <= 4'd0;
            shift <= 8'h00;
            cnt   <= {DIV_W{1'b0}};
            data  <= 8'h00;
            valid <= 1'b0;
            ferr  <= 1'b0;
        end else begin
            sync  <= {sync[0], rx};
            valid <= 1'b0;
            if (!busy) begin
                if (!line) begin
                    busy <= 1'b1;
                    nbit <= 4'd0;
                    cnt  <= (div >> 1) - 1'b1;   // to the middle of the start bit
                end
            end else if (cnt == 0) begin
                cnt <= div - 1'b1;
                if (nbit == 0) begin
                    if (line) busy <= 1'b0;      // glitch, not a start bit
                    else      nbit <= 4'd1;
                end else if (nbit != 4'd9) begin
                    shift <= {line, shift[7:1]};
                    nbit  <= nbit + 1'b1;
                end else begin
                    busy  <= 1'b0;
                    data  <= shift;
                    ferr  <= !line;
                    valid <= 1'b1;
                end
            end else begin
                cnt <= cnt - 1'b1;
            end
        end
    end
endmodule
