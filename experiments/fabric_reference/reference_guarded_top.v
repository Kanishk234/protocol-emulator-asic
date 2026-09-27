`default_nettype none
// Fixed wrapper for the two demo designs: io[0]=reset, io[1]=enable.
// The final design needs a defined user-reset ABI and a real image validator.
module reference_guarded_top (
    input wire CLK, resetn, ControlResetn,
    input wire BeginLoad, AbortLoad, CommitImage, ImageValid,
    input wire SelfWriteStrobe,
    input wire [31:0] SelfWriteData,
    input wire [27:0] O_top,
    output wire [27:0] I_top, T_top,
    output wire [55:0] A_config_C, B_config_C,
    input wire Rx, s_clk, s_data,
    output wire ComActive, ReceiveLED,
    output wire ConfigHold, OutputPark, UserReset, LoadAllowed, Ready
);
    wire [27:0] raw_output, raw_t;
    wire [27:0] user_input = UserReset ? {O_top[27:2], 2'b01} : O_top;
    wp_reload_guard guard (
        .clk(CLK), .rst_n(ControlResetn), .begin_load(BeginLoad),
        .abort_load(AbortLoad), .commit_image(CommitImage), .image_valid(ImageValid),
        .write_active(SelfWriteStrobe), .hold_fabric(ConfigHold),
        .park_outputs(OutputPark), .user_reset(UserReset),
        .load_allowed(LoadAllowed), .ready(Ready)
    );
    assign I_top = OutputPark ? 28'b0 : raw_output;
    assign T_top = OutputPark ? {28{1'b1}} : raw_t;
    eFPGA_top fabric (
        .CLK(CLK), .resetn(resetn && LoadAllowed && ControlResetn),
        .ReloadHold(ConfigHold), .SelfWriteStrobe(SelfWriteStrobe && LoadAllowed),
        .SelfWriteData(SelfWriteData), .O_top(user_input), .I_top(raw_output),
        .T_top(raw_t), .A_config_C(A_config_C), .B_config_C(B_config_C),
        // Serial configuration is disabled in this word-loader experiment.
        .Rx(1'b1), .s_clk(1'b0), .s_data(1'b0),
        .ComActive(ComActive), .ReceiveLED(ReceiveLED)
    );
    wire unused = &{1'b0, Rx, s_clk, s_data};
endmodule
`resetall
