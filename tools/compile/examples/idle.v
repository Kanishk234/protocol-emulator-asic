// A design that does nothing: every host-channel output 0 (never ready, never valid, status 0,
// no attention). The shell's pin-level tests run it when they need a RUNNING chip whose fabric
// drives defined values (test/test.py).
`default_nettype none

module idle (
    input  wire       clk,
    input  wire       rst_n,
    output wire       h_wready,
    output wire [7:0] h_rdata,
    output wire       h_rvalid,
    output wire [7:0] h_status,
    output wire       h_attention
);
    assign h_wready    = 1'b0;
    assign h_rdata     = 8'd0;
    assign h_rvalid    = 1'b0;
    assign h_status    = 8'd0;
    assign h_attention = 1'b0;
    wire _unused = &{clk, rst_n, 1'b0};
endmodule
