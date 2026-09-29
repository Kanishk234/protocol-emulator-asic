// SPDX-License-Identifier: Apache-2.0
`default_nettype none
// FSB1 prototype: synchronous byte data ui_in, valid/begin/commit/abort uio[4:7].
// Four CRC32 bytes MSB first, then 504 image bytes. uo[0:3]: ready/run/error/done.
module tt_um_warp (
    input wire [7:0] ui_in, uio_in,
    output wire [7:0] uo_out, uio_out, uio_oe,
    input wire ena, clk, rst_n
);
    reg [2:0] metadata_count;
    reg [1:0] byte_count;
    reg [31:0] expected_crc, assembled_word;
    reg [23:0] byte_shift;
    reg begin_image, word_valid;
    wire start = uio_in[5];
    wire abort_load = uio_in[7];
    wire control_resetn = rst_n && ena && !start && !abort_load;
    wire word_ready, running, complete, image_error;
    wire [3:0] fabric_output, fabric_enable;
    wire [7:0] cfg_a, cfg_b;
    wire hold_fabric, parked, user_reset, load_allowed, validated, fabric_write;
    wire com_active, receive_led;
    wire header = metadata_count < 4;
    wire byte_ready = control_resetn && !begin_image && !word_valid &&
                      (header || word_ready);
    always @(posedge clk) begin
        if (!control_resetn) begin
            metadata_count <= 0;
            byte_count <= 0;
            expected_crc <= 0;
            assembled_word <= 0;
            byte_shift <= 0;
            begin_image <= 0;
            word_valid <= 0;
        end else begin
            begin_image <= 0;
            word_valid <= 0;
            if (uio_in[4] && byte_ready) begin
                if (header) begin
                    expected_crc <= {expected_crc[23:0],ui_in};
                    metadata_count <= metadata_count + 1'b1;
                    if (metadata_count == 3) begin_image <= 1;
                end else begin
                    byte_shift <= {byte_shift[15:0],ui_in};
                    byte_count <= byte_count + 1'b1;
                    if (byte_count == 3) begin
                        assembled_word <= {byte_shift,ui_in};
                        word_valid <= 1;
                    end
                end
            end
        end
    end
    wp_small_fabric #(.SERIAL_CRC(1)) fabric (
        .CLK(clk), .resetn(control_resetn), .ControlResetn(control_resetn),
        .BeginLoad(begin_image), .AbortLoad(abort_load),
        .CommitImage(uio_in[6] && byte_count == 0 && !uio_in[4]),
        .ArchitectureId(32'h46534231), .FormatVersion(16'd1),
        .ImageBytes(32'd504), .ExpectedCRC(expected_crc),
        .SelfWriteStrobe(word_valid), .SelfWriteData(assembled_word),
        .O_top(uio_in[3:0]), .I_top(fabric_output), .T_top(fabric_enable),
        .A_config_C(cfg_a), .B_config_C(cfg_b),
        .Rx(1'b1), .s_clk(1'b0), .s_data(1'b0),
        .ComActive(com_active), .ReceiveLED(receive_led),
        .ConfigHold(hold_fabric), .OutputPark(parked), .UserReset(user_reset),
        .LoadAllowed(load_allowed), .Ready(running), .WordReady(word_ready),
        .ImageValid(validated), .ImageComplete(complete), .ImageError(image_error),
        .FabricWrite(fabric_write)
    );
    assign uio_out = {4'b0, (control_resetn && running) ? fabric_output : 4'b0};
    assign uio_oe = {4'b0, (control_resetn && running) ? fabric_enable : 4'b0};
    assign uo_out = {4'b0,complete,image_error,running,byte_ready};
    wire unused = &{1'b0,cfg_a,cfg_b,hold_fabric,parked,user_reset,load_allowed,
                    validated,fabric_write,com_active,receive_led};
endmodule
`resetall
