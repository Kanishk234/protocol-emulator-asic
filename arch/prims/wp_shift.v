// WARP hard primitive: 8-bit shift register with a step count (ARCHITECTURE.md §8.2, cycle-exact
// spec v2). A FABulous BEL: configuration (LEN, MSB_FIRST) on ConfigBits; CLK is the tile's global
// clock. D-026.
//   sout = MSB_FIRST ? sr[7] : sr[0];  q = sr;  done = (n == LEN)
//   edge: rst -> sr = 0, n = 0
//         load -> sr = d, n = 0
//         step -> sr shifts one place (sin enters at the far end), n = (n == LEN) ? n : n + 1
`default_nettype none

(* FABulous, BelMap,
LEN0=0, LEN1=1, LEN2=2, LEN3=3, MSB_FIRST=4
*)
module wp_shift #(
    parameter integer NoConfigBits = 5
) (
    input  wire       CLK,
    input  wire       rst,
    input  wire       load,
    input  wire       step,
    input  wire       sin,
    input  wire [7:0] d,
    output wire       sout,
    output wire       done,
    output wire [7:0] q,
`ifdef FORMAL
    output wire [3:0] f_n,            // state, for formal/f4_shift.sv only (sr is q)
`endif
    (* FABulous, GLOBAL *) input wire [NoConfigBits-1:0] ConfigBits
);
    wire [3:0] len       = ConfigBits[3:0];
    wire       msb_first = ConfigBits[4];

    reg  [7:0] sr;
    reg  [3:0] n;

    assign sout = msb_first ? sr[7] : sr[0];
    assign q    = sr;
    assign done = (n == len);
`ifdef FORMAL
    assign f_n = n;
`endif

    always @(posedge CLK) begin
        if (rst) begin
            sr <= 8'd0;
            n  <= 4'd0;
        end else if (load) begin
            sr <= d;
            n  <= 4'd0;
        end else if (step) begin
            sr <= msb_first ? {sr[6:0], sin} : {sin, sr[7:1]};
            if (n != len)
                n <= n + 4'd1;
        end
    end
endmodule
