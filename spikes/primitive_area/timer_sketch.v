// AREA-ESTIMATE SKETCH ONLY (phase 1 capacity go/no-go). Not a WARP primitive: the real one is
// designed in phase 3 with a DECISIONS entry, tool mapping and tests.
//
// Loadable down-counter / timer: counts down from RELOAD when enabled; `tc` pulses when it
// wraps and it reloads. `load` restarts it (e.g. at a start bit; `half` loads RELOAD/2 for
// mid-bit sampling). RELOAD and the half option are configuration bits (fixed per bitstream),
// modelled here as ports so synthesis cannot optimise them away (they become latches on chip).
`default_nettype none
module timer_sketch (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [15:0] cfg_reload,   // configuration bits
    input  wire        en,
    input  wire        load,
    input  wire        half,
    output wire        tc
);
    reg [15:0] cnt;
    assign tc = en && (cnt == 16'd0);
    always @(posedge clk) begin
        if (!rst_n)          cnt <= 16'd0;
        else if (load)       cnt <= half ? {1'b0, cfg_reload[15:1]} : cfg_reload;
        else if (en) begin
            if (cnt == 16'd0) cnt <= cfg_reload;
            else              cnt <= cnt - 1'b1;
        end
    end
endmodule
