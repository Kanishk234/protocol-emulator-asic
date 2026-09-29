`default_nettype none

// User-fabric example: one-byte elastic buffer with a configurable XOR transform.
module warp_byte_bridge #(
    parameter [7:0] MASK = 8'h5A
) (
    input wire clk,
    input wire rst_n,
    input wire rx_valid,
    input wire [7:0] rx_data,
    output wire rx_ready,
    output wire tx_valid,
    output wire [7:0] tx_data,
    input wire tx_ready
);
    reg [7:0] data_q;
    reg full;

    assign rx_ready = rst_n && (!full || tx_ready);
    assign tx_valid = rst_n && full;
    assign tx_data = data_q ^ MASK;

    always @(posedge clk) begin
        if (!rst_n) begin
            data_q <= 8'd0;
            full <= 1'b0;
        end else if (rx_valid && rx_ready) begin
            data_q <= rx_data;
            full <= 1'b1;
        end else if (tx_valid && tx_ready) begin
            full <= 1'b0;
        end
    end
endmodule

`default_nettype wire
