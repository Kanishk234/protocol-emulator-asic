`default_nettype none

// Reference counter. Reset takes priority over enable, including while held.
module sequential_16bit_en (
    input wire clk,
    input wire [27:0] io_in,
    output wire [27:0] io_out,
    output wire [27:0] io_oeb
);
    wire rst = io_in[0];
    wire en = io_in[1];
    reg [15:0] ctr;
    wire [15:0] ctr_d = rst ? 16'b0 : (en ? ctr + 16'b1 : ctr);

    always @(posedge clk)
        ctr <= ctr_d;

    assign io_out = {12'b0, ctr};
    assign io_oeb = 28'b0000000000000000000000000001;
endmodule

`resetall
