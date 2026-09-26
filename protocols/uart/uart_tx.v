// UART transmitter, 8N1, LSB first, idle high.
// A byte is accepted when valid && ready. Each bit lasts `div` clocks (div >= 2).
// Back-to-back bytes follow each other with no idle gap.
`default_nettype none

module uart_tx #(
    parameter DIV_W = 16
) (
    input  wire             clk,
    input  wire             rst_n,
    input  wire [DIV_W-1:0] div,
    input  wire [7:0]       data,
    input  wire             valid,
    output wire             ready,
    output reg              tx
);
    reg             busy;
    reg [8:0]       shift;  // data bits then the stop bit
    reg [3:0]       nleft;  // bits still to send after the current one
    reg [DIV_W-1:0] cnt;

    assign ready = !busy;

    always @(posedge clk) begin
        if (!rst_n) begin
            busy  <= 1'b0;
            tx    <= 1'b1;
            shift <= 9'h1FF;
            nleft <= 4'd0;
            cnt   <= {DIV_W{1'b0}};
        end else if (!busy) begin
            if (valid) begin
                busy  <= 1'b1;
                tx    <= 1'b0;           // start bit
                shift <= {1'b1, data};
                nleft <= 4'd9;
                cnt   <= div - 1'b1;
            end
        end else if (cnt == 0) begin
            if (nleft == 0) begin
                busy <= 1'b0;            // stop bit done
            end else begin
                tx    <= shift[0];
                shift <= {1'b1, shift[8:1]};
                nleft <= nleft - 1'b1;
                cnt   <= div - 1'b1;
            end
        end else begin
            cnt <= cnt - 1'b1;
        end
    end
endmodule
