// AREA-ESTIMATE SKETCH ONLY (phase 1 capacity go/no-go). Not a WARP primitive.
//
// Shift register with bit count: up to 10 bits, MSB- or LSB-first (config bit), length
// (config bits). `load` takes a parallel byte; each `step` shifts one bit in from `sin` and out
// on `sout`; `done` goes high after `length` steps. Parallel read on `q`.
`default_nettype none
module shift_sketch (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [3:0] cfg_len,      // configuration bits
    input  wire       cfg_msb,      // configuration bit
    input  wire       load,
    input  wire [9:0] d,
    input  wire       step,
    input  wire       sin,
    output wire       sout,
    output wire [9:0] q,
    output wire       done
);
    reg [9:0] sh;
    reg [3:0] n;
    assign q    = sh;
    assign sout = cfg_msb ? sh[9] : sh[0];
    assign done = (n == cfg_len);
    always @(posedge clk) begin
        if (!rst_n) begin
            sh <= 10'd0;
            n  <= 4'd0;
        end else if (load) begin
            sh <= d;
            n  <= 4'd0;
        end else if (step) begin
            sh <= cfg_msb ? {sh[8:0], sin} : {sin, sh[9:1]};
            n  <= n + 1'b1;
        end
    end
endmodule
