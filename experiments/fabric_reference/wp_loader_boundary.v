`default_nettype none
// Simulation-only stand-in for the unimplemented fabric side of the boundary.
// Synthesis MUST read this file with -lib, discarding all assignments.
// Frame/control inputs then remain observable and output values unconstrained.
module wp_loader_boundary (
    input wire CLK, ReloadHold,
    input wire [27:0] O_top,
    output wire [27:0] I_top, T_top,
    output wire [55:0] A_config_C, B_config_C,
    input wire [447:0] FrameRegister,
    input wire [31:0] FrameAddressRegister,
    input wire LongFrameStrobe
);
    assign I_top=28'h5a5a5a5;
    assign T_top=28'hffffffe;
    assign A_config_C=0;
    assign B_config_C=0;
    wire unused=&{1'b0,CLK,ReloadHold,O_top,FrameRegister,FrameAddressRegister,LongFrameStrobe};
endmodule
`resetall
