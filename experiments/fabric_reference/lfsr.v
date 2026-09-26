`default_nettype none
// Same host-facing interface, different user circuit and configuration image.
module sequential_16bit_en (
    input wire clk,
    input wire [27:0] io_in,
    output wire [27:0] io_out,
    output wire [27:0] io_oeb
);
    reg [15:0] state;
    always @(posedge clk)
        if (io_in[0]) state <= 16'hace1;
        else if (io_in[1])
            state <= {state[14:0], state[15] ^ state[13] ^ state[12] ^ state[10]};
    assign io_out = {12'b0, state};
    assign io_oeb = 28'b1;
endmodule
`resetall
