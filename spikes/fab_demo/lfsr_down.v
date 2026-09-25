// Phase 0 FABulous demo, second user design: behaves differently from the stock
// sequential_16bit_en counter so two bitstreams in one fabric can be told apart.
// Same port shape as the stock demo design (FABulous gen_user_design_wrapper).
`default_nettype none

module lfsr_down (
    input  wire        clk,
    input  wire [27:0] io_in,
    output wire [27:0] io_out,
    output wire [27:0] io_oeb
);
    wire rst = io_in[0];
    wire en  = io_in[1];
    reg [15:0] lfsr;  // Galois LFSR, x^16 + x^14 + x^13 + x^11 + 1
    reg [7:0]  down;

    always @(posedge clk)
        if (en)
            if (rst) begin
                lfsr <= 16'hACE1;
                down <= 8'hFF;
            end else begin
                lfsr <= {1'b0, lfsr[15:1]} ^ (lfsr[0] ? 16'hB400 : 16'h0000);
                down <= down - 1'b1;
            end

    assign io_out = {4'b0, down, lfsr};
    assign io_oeb = 28'b0000000000000000000000000011;
endmodule
