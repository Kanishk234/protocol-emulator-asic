// Experimental pinned-reference format only; not the production image ABI.
`default_nettype none
module wp_image_validator #(
    parameter SERIAL_CRC = 0
) (
    input wire clk, rst_n, begin_load, abort_load,
    input wire [31:0] architecture_id, image_bytes, expected_crc,
    input wire [15:0] format_version,
    input wire word_valid,
    input wire [31:0] word_data,
    output wire image_valid, word_ready,
    output reg complete, error
);
    // "FRB1": this experiment's 10-column, 14-row, 20-frame reference.
    localparam [31:0] ARCHITECTURE_ID = 32'h46524231;
    reg active;
    reg [11:0] count;
    reg [3:0] column, row_word;
    reg [4:0] frame;
    reg [31:0] crc, wanted_crc;
    reg [1:0] crc_remaining;
    reg [23:0] pending_bytes;
    reg structure_ok;
    wire [31:0] frame_select = (32'b1 << frame) | ({28'b0,column} << 27);

    // CRC-32/ISO-HDLC: reflected polynomial, init/xorout all ones.
    // Each 32-bit bus word contains four bytes, most-significant byte first.
    function [31:0] crc_word;
        input [31:0] prior, data;
        reg [31:0] value;
        integer byte_index, bit_index;
        begin
            value = prior;
            for (byte_index=3; byte_index>=0; byte_index=byte_index-1) begin
                value = value ^ ((data >> (byte_index*8)) & 32'hff);
                for (bit_index=0; bit_index<8; bit_index=bit_index+1)
                    value = (value >> 1) ^ (value[0] ? 32'hedb88320 : 32'b0);
            end
            crc_word = value;
        end
    endfunction
    function [31:0] crc_byte;
        input [31:0] prior;
        input [7:0] data;
        reg [31:0] value;
        integer bit_index;
        begin
            value = prior ^ {24'b0,data};
            for (bit_index=0; bit_index<8; bit_index=bit_index+1)
                value = (value >> 1) ^ (value[0] ? 32'hedb88320 : 32'b0);
            crc_byte = value;
        end
    endfunction
    wire busy = SERIAL_CRC && crc_remaining != 0;
    wire [31:0] next_crc = SERIAL_CRC ?
        crc_byte(crc, busy ? pending_bytes[23:16] : word_data[31:24]) :
        crc_word(crc, word_data);
    assign word_ready = !busy;
    assign image_valid = active && complete && !busy && !error;

    always @* begin
        structure_ok = 1'b1;
        case (count)
            0: structure_ok = word_data == 32'h00aaff01;
            1: structure_ok = word_data == 32'h00000001;
            2,3: structure_ok = word_data == 0;
            4: structure_ok = word_data == 32'hfab0fab1;
            3005: structure_ok = word_data == 32'h00100000;
            default: if (row_word == 0) structure_ok = word_data == frame_select;
        endcase
    end

    always @(posedge clk) begin
        if (!rst_n || abort_load) begin
            active <= 0;
            complete <= 0;
            error <= 0;
            count <= 0;
            column <= 0;
            frame <= 0;
            row_word <= 0;
            crc <= 32'hffffffff;
            wanted_crc <= 0;
            crc_remaining <= 0;
            pending_bytes <= 0;
        end else if (begin_load) begin
            active <= 1;
            complete <= 0;
            error <= architecture_id != ARCHITECTURE_ID ||
                     format_version != 16'd1 || image_bytes != 32'd12024;
            count <= 0;
            column <= 0;
            frame <= 0;
            row_word <= 0;
            crc <= 32'hffffffff;
            wanted_crc <= expected_crc;
            crc_remaining <= 0;
            pending_bytes <= 0;
        end else if (busy) begin
            crc <= next_crc;
            pending_bytes <= {pending_bytes[15:0],8'b0};
            crc_remaining <= crc_remaining - 1'b1;
            if (crc_remaining == 1 && complete &&
                (next_crc ^ 32'hffffffff) != wanted_crc) error <= 1;
        end else if (word_valid) begin
            if (!active || complete) error <= 1;
            else if (!error) begin
                crc <= next_crc;
                if (SERIAL_CRC) begin
                    pending_bytes <= word_data[23:0];
                    crc_remaining <= 3;
                end
                if (!structure_ok) error <= 1;
                if (count == 3005) begin
                    complete <= 1;
                    if (!SERIAL_CRC && (next_crc ^ 32'hffffffff) != wanted_crc) error <= 1;
                end else begin
                    count <= count + 1'b1;
                    if (count >= 5) begin
                        if (row_word == 14) begin
                            row_word <= 0;
                            if (frame == 19) begin
                                frame <= 0;
                                column <= column + 1'b1;
                            end else frame <= frame + 1'b1;
                        end else row_word <= row_word + 1'b1;
                    end
                end
            end
        end
    end
endmodule
`resetall
