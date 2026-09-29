`default_nettype none
// Small-fabric compilation probe: two inputs and two separate output pads.
module small_counter (
    input wire clk,
    input wire [3:0] io_in,
    output wire [3:0] io_out, io_oeb
);
    reg [1:0] counter;
    always @(posedge clk)
        if (io_in[0]) counter <= 0;
        else if (io_in[1]) counter <= counter + 1'b1;
    assign io_out = {counter, 2'b00};
    assign io_oeb = 4'b0011;
endmodule
`resetall
