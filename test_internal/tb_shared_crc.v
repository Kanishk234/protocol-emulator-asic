`default_nettype none
`timescale 1ns/1ps
module tb_shared_crc;
    reg clk, rst_n, clear, word_valid;
    reg [31:0] word;
    wire [31:0] crc, baseline_crc;
    wire busy, baseline_busy;
    wp_crc32_shared_word u_candidate (.clk(clk), .rst_n(rst_n), .clear(clear),
        .word_valid(word_valid), .word(word), .crc(crc), .busy(busy));
    wp_crc32 u_baseline (.clk(clk), .rst_n(rst_n), .clear(clear),
        .word_valid(word_valid), .word(word), .crc(baseline_crc), .busy(baseline_busy));
endmodule
