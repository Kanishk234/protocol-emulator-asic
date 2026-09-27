// WARP hard primitive: loadable 16-bit down-counter (ARCHITECTURE.md §8.1, cycle-exact spec v2).
// A FABulous BEL: the configuration (RELOAD, ONESHOT) arrives on ConfigBits from the tile's
// configuration latches; rst/load/half/en/tc connect to the tile's switch matrix; CLK is the
// tile's global clock. D-026.
//   tc   = en & armed & (count == 0)
//   edge: rst -> count = RELOAD, armed = 1
//         load -> count = half ? RELOAD >> 1 : RELOAD, armed = 1
//         en & armed -> count == 0 ? (count = RELOAD, armed = !ONESHOT) : count - 1
`default_nettype none

(* FABulous, BelMap,
RELOAD0=0, RELOAD1=1, RELOAD2=2, RELOAD3=3, RELOAD4=4, RELOAD5=5, RELOAD6=6, RELOAD7=7,
RELOAD8=8, RELOAD9=9, RELOAD10=10, RELOAD11=11, RELOAD12=12, RELOAD13=13, RELOAD14=14,
RELOAD15=15, ONESHOT=16
*)
module wp_timer #(
    parameter integer NoConfigBits = 17
) (
    input  wire CLK,
    input  wire rst,
    input  wire load,
    input  wire half,
    input  wire en,
    output wire tc,
`ifdef FORMAL
    output wire [15:0] f_count,       // state, for formal/f4_timer.sv only
    output wire        f_armed,
`endif
    (* FABulous, GLOBAL *) input wire [NoConfigBits-1:0] ConfigBits
);
    wire [15:0] reload  = ConfigBits[15:0];
    wire        oneshot = ConfigBits[16];

    reg  [15:0] count;
    reg         armed;

    assign tc = en && armed && (count == 16'd0);
`ifdef FORMAL
    assign f_count = count;
    assign f_armed = armed;
`endif

    always @(posedge CLK) begin
        if (rst) begin
            count <= reload;
            armed <= 1'b1;
        end else if (load) begin
            count <= half ? {1'b0, reload[15:1]} : reload;
            armed <= 1'b1;
        end else if (en && armed) begin
            if (count == 16'd0) begin
                count <= reload;
                armed <= !oneshot;
            end else begin
                count <= count - 16'd1;
            end
        end
    end
endmodule
