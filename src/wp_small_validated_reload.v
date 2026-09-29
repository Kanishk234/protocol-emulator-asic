`default_nettype none
// Synchronous word-transaction boundary: hold valid/data until word_ready.
// Not an asynchronous host strobe. SERIAL_CRC=1 processes one byte per clock.
module wp_small_validated_reload #(
    parameter SERIAL_CRC = 0
) (
    input wire clk, rst_n, begin_load, abort_load, commit_image,
    input wire [31:0] architecture_id, image_bytes, expected_crc, word_data,
    input wire [15:0] format_version,
    input wire word_valid,
    output wire hold_fabric, park_outputs, user_reset, load_allowed, ready,
    output wire image_valid, complete, error, fabric_write, word_ready
);
    // Begin/abort/reset suppress writes on that same sampling edge.
    assign fabric_write = rst_n && !begin_load && !abort_load &&
                          load_allowed && !complete && !error && word_valid && word_ready;
    wp_small_image_validator #(.SERIAL_CRC(SERIAL_CRC)) validator (
        .clk(clk), .rst_n(rst_n), .begin_load(begin_load), .abort_load(abort_load),
        .architecture_id(architecture_id), .image_bytes(image_bytes),
        .expected_crc(expected_crc), .format_version(format_version),
        .word_valid(word_valid && load_allowed), .word_data(word_data),
        .image_valid(image_valid), .complete(complete), .error(error), .word_ready(word_ready)
    );
    wp_reload_guard guard (
        .clk(clk), .rst_n(rst_n), .begin_load(begin_load), .abort_load(abort_load),
        .commit_image(commit_image), .image_valid(image_valid),
        .write_active(word_valid), .hold_fabric(hold_fabric),
        .park_outputs(park_outputs), .user_reset(user_reset),
        .load_allowed(load_allowed), .ready(ready)
    );
endmodule
`resetall
