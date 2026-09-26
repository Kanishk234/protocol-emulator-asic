`default_nettype none
// User circuit for the upstream reference fabric, not ASIC chip RTL.
// Inputs on pins 0..7, output signature on pins 8..15, others released.
module wp_smoke_signature (
    input wire clk,
    input wire [27:0] io_in,
    output wire [27:0] io_out,
    output wire [27:0] io_oeb
);
    assign io_out = {12'b0, (io_in[7:0] ^ 8'ha5), 8'b0};
    assign io_oeb = 28'hfff00ff;
    wire unused = &{1'b0, clk, io_in[27:8]};
endmodule
`resetall
