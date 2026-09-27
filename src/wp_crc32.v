// CRC-32 (IEEE 802.3, reflected, as zlib) over 32-bit words taken as big-endian bytes
// (ARCHITECTURE.md §3). Bit-serial: a word takes 32 cycles (`busy`); the host interface delivers
// at most one word per 32 SCK bits = 256 clk, so words never overlap.
`default_nettype none

module wp_crc32 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        clear,
    input  wire        word_valid,
    input  wire [31:0] word,
    output wire [31:0] crc,
    output wire        busy
);
    reg [31:0] r;
    reg [31:0] w;      // bytes swapped so the first byte's bit 0 is w[0]
    reg [5:0]  n;

    always @(posedge clk) begin
        if (!rst_n || clear) begin
            r <= 32'hFFFF_FFFF;
            w <= 32'd0;
            n <= 6'd0;
        end else if (word_valid) begin
            w <= {word[7:0], word[15:8], word[23:16], word[31:24]};
            n <= 6'd32;
        end else if (n != 6'd0) begin
            r <= {1'b0, r[31:1]} ^ ((r[0] ^ w[0]) ? 32'hEDB8_8320 : 32'd0);
            w <= {1'b0, w[31:1]};
            n <= n - 6'd1;
        end
    end

    assign crc  = ~r;
    assign busy = (n != 6'd0);
endmodule
