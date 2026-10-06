// Scratch CRC experiment: reuse the shell's stable word register while busy.
// Requires word unchanged until busy falls; the SPI shell has >32 cycles
// between complete words. Do not substitute this in a standalone CRC client.
`default_nettype none
module wp_crc32_shared_word (
    input wire clk,
    input wire rst_n,
    input wire clear,
    input wire word_valid,
    input wire [31:0] word,
    output wire [31:0] crc,
    output wire busy
);
    reg [31:0] r;
    reg [4:0] bit_number;
    reg active;
    wire feedback = r[0] ^ word[bit_number];
    always @(posedge clk) begin
        if (!rst_n || clear) begin
            r <= 32'hFFFF_FFFF;
            bit_number <= 5'd24;
            active <= 1'b0;
        end else if (word_valid) begin
            bit_number <= 5'd24;
            active <= 1'b1;
        end else if (active) begin
            r <= {1'b0, r[31:1]} ^ (feedback ? 32'hEDB8_8320 : 32'd0);
            // Bytes 31:24, 23:16, 15:8, 7:0; LSB first within each byte.
            if (bit_number[2:0] == 3'd7)
                bit_number <= {bit_number[4:3] - 2'd1, 3'd0};
            else
                bit_number <= bit_number + 5'd1;
            if (bit_number == 5'd7)
                active <= 1'b0;
        end
    end
    assign crc = ~r;
    assign busy = active;
endmodule
