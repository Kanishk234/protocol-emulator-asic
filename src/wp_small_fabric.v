`default_nettype none
// Reference-only validated wrapper. Demo ABI: input bit 0 reset, bit 1 enable.
// One accepted word followed by three idle edges lets ConfigFSM's two-cycle
// frame strobe drain before another address can replace its frame register.
module wp_small_fabric #(
    parameter SERIAL_CRC = 0
) (
    input wire CLK, resetn, ControlResetn,
    input wire BeginLoad, AbortLoad, CommitImage,
    input wire [31:0] ArchitectureId, ImageBytes, ExpectedCRC,
    input wire [15:0] FormatVersion,
    input wire SelfWriteStrobe,
    input wire [31:0] SelfWriteData,
    input wire [3:0] O_top,
    output wire [3:0] I_top, T_top,
    output wire [7:0] A_config_C, B_config_C,
    input wire Rx, s_clk, s_data,
    output wire ComActive, ReceiveLED,
    output wire ConfigHold, OutputPark, UserReset, LoadAllowed, Ready,
    output wire WordReady, ImageValid, ImageComplete, ImageError,
    output wire FabricWrite
);
    reg [1:0] cooldown;
    wire cancel_load = AbortLoad || !resetn;
    wire accept_word = SelfWriteStrobe && WordReady;
    wire crc_word_ready;
    wire [3:0] raw_output, raw_t;
    wire [3:0] user_input = UserReset ? {O_top[3:2], 2'b01} : O_top;
    // Keep ready after completion/error during LOAD: an extra word must be
    // observed by the validator and rejected, never silently discarded.
    assign WordReady = ControlResetn && resetn && !BeginLoad && !AbortLoad &&
                       LoadAllowed && cooldown == 0 && crc_word_ready;
    always @(posedge CLK) begin
        if (!ControlResetn || cancel_load || BeginLoad) cooldown <= 0;
        else if (FabricWrite) cooldown <= 3;
        else if (cooldown != 0) cooldown <= cooldown - 1'b1;
    end
    wp_small_validated_reload #(.SERIAL_CRC(SERIAL_CRC)) management (
        .clk(CLK), .rst_n(ControlResetn), .begin_load(BeginLoad),
        .abort_load(cancel_load),
        .commit_image(CommitImage && cooldown == 0 && !SelfWriteStrobe),
        .architecture_id(ArchitectureId), .image_bytes(ImageBytes),
        .expected_crc(ExpectedCRC), .format_version(FormatVersion),
        .word_valid(accept_word), .word_data(SelfWriteData),
        .hold_fabric(ConfigHold), .park_outputs(OutputPark),
        .user_reset(UserReset), .load_allowed(LoadAllowed), .ready(Ready),
        .image_valid(ImageValid), .complete(ImageComplete), .error(ImageError),
        .fabric_write(FabricWrite), .word_ready(crc_word_ready)
    );
    assign I_top = OutputPark ? 4'b0 : raw_output;
    assign T_top = OutputPark ? 4'b0 : raw_t;
    eFPGA_top fabric (
        .CLK(CLK), .resetn(resetn && LoadAllowed && ControlResetn && !BeginLoad && !AbortLoad),
        .ReloadHold(ConfigHold), .SelfWriteStrobe(FabricWrite),
        .SelfWriteData(SelfWriteData), .O_top(user_input), .I_top(raw_output),
        .T_top(raw_t), .A_config_C(A_config_C), .B_config_C(B_config_C),
        .Rx(1'b1), .s_clk(1'b0), .s_data(1'b0),
        .ComActive(ComActive), .ReceiveLED(ReceiveLED)
    );
    wire unused = &{1'b0, Rx, s_clk, s_data};
endmodule
`resetall
