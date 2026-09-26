// Black-box view of the hardened fabric macro `warp_tiny` (macro/warp_tiny/, built by
// spikes/fabric_tiny/run.sh). Synthesis keeps it as a macro instance; LibreLane places the
// GDS/LEF from src/config.json MACROS. Simulation uses macro/warp_tiny/warp_tiny.v (RTL) or
// warp_tiny.nl.v (gate level) instead of this file.
`default_nettype none

(* blackbox *)
module warp_tiny (
`ifdef USE_POWER_PINS
    inout  wire         VPWR,
    inout  wire         VGND,
`endif
    input  wire         Tile_X0Y1_A_OUT_top, output wire Tile_X0Y1_A_IN_top, output wire Tile_X0Y1_A_EN_top,
    input  wire         Tile_X0Y1_B_OUT_top, output wire Tile_X0Y1_B_IN_top, output wire Tile_X0Y1_B_EN_top,
    input  wire         Tile_X0Y1_C_OUT_top, output wire Tile_X0Y1_C_IN_top, output wire Tile_X0Y1_C_EN_top,
    input  wire         Tile_X0Y1_D_OUT_top, output wire Tile_X0Y1_D_IN_top, output wire Tile_X0Y1_D_EN_top,
    input  wire         Tile_X2Y1_A_OUT_top, output wire Tile_X2Y1_A_IN_top, output wire Tile_X2Y1_A_EN_top,
    input  wire         Tile_X2Y1_B_OUT_top, output wire Tile_X2Y1_B_IN_top, output wire Tile_X2Y1_B_EN_top,
    input  wire         Tile_X2Y1_C_OUT_top, output wire Tile_X2Y1_C_IN_top, output wire Tile_X2Y1_C_EN_top,
    input  wire         Tile_X2Y1_D_OUT_top, output wire Tile_X2Y1_D_IN_top, output wire Tile_X2Y1_D_EN_top,
    input  wire         Tile_X0Y2_A_OUT_top, output wire Tile_X0Y2_A_IN_top, output wire Tile_X0Y2_A_EN_top,
    input  wire         Tile_X0Y2_B_OUT_top, output wire Tile_X0Y2_B_IN_top, output wire Tile_X0Y2_B_EN_top,
    input  wire         Tile_X0Y2_C_OUT_top, output wire Tile_X0Y2_C_IN_top, output wire Tile_X0Y2_C_EN_top,
    input  wire         Tile_X0Y2_D_OUT_top, output wire Tile_X0Y2_D_IN_top, output wire Tile_X0Y2_D_EN_top,
    input  wire         Tile_X2Y2_A_OUT_top, output wire Tile_X2Y2_A_IN_top, output wire Tile_X2Y2_A_EN_top,
    input  wire         Tile_X2Y2_B_OUT_top, output wire Tile_X2Y2_B_IN_top, output wire Tile_X2Y2_B_EN_top,
    input  wire         Tile_X2Y2_C_OUT_top, output wire Tile_X2Y2_C_IN_top, output wire Tile_X2Y2_C_EN_top,
    input  wire         Tile_X2Y2_D_OUT_top, output wire Tile_X2Y2_D_IN_top, output wire Tile_X2Y2_D_EN_top,
    input  wire         Tile_X0Y3_SYS_RESET_RESET_top,
    input  wire         Tile_X1Y3_A_OUT_top, output wire Tile_X1Y3_A_IN_top, output wire Tile_X1Y3_A_EN_top,
    input  wire         Tile_X1Y3_B_OUT_top, output wire Tile_X1Y3_B_IN_top, output wire Tile_X1Y3_B_EN_top,
    input  wire [127:0] FrameData,
    input  wire [59:0]  FrameStrobe
);
endmodule
