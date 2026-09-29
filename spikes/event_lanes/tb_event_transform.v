`timescale 1ns/1ps
`default_nettype none

module tb_event_transform;
    reg clk = 1'b0;
    always #5 clk = ~clk;

    reg rst_n = 1'b0;
    reg start0 = 1'b0;
    reg start1 = 1'b0;
    reg [2:0] start_pc0 = 3'd0;
    reg [2:0] start_pc1 = 3'd4;
    reg [7:0] pins_in = 8'd0;
    reg [191:0] program_image = 192'd0;
    wire [7:0] pins_out0, pins_out1, pins_oe0, pins_oe1;
    wire [7:0] sample0, sample1;
    wire tx_ready0, tx_ready1, rx_valid0, rx_valid1;
    wire [7:0] rx_data0, rx_data1;
    wire busy0, busy1, irq0, irq1;
    wire tx_valid1, rx_ready0;
    wire [7:0] tx_data1;

    warp_byte_bridge #(.MASK(8'h5A)) user_logic (
        .clk(clk), .rst_n(rst_n), .rx_valid(rx_valid0), .rx_data(rx_data0),
        .rx_ready(rx_ready0), .tx_valid(tx_valid1), .tx_data(tx_data1),
        .tx_ready(tx_ready1)
    );

    warp_event_lanes_static dut (
        .clk(clk), .rst_n(rst_n), .start0(start0), .start1(start1),
        .start_pc0(start_pc0), .start_pc1(start_pc1), .pins_in(pins_in),
        .tx_valid0(1'b0), .tx_data0(8'd0), .rx_ready0(rx_ready0),
        .tx_valid1(tx_valid1), .tx_data1(tx_data1), .rx_ready1(1'b1),
        .program_image(program_image), .pins_out0(pins_out0), .pins_out1(pins_out1),
        .pins_oe0(pins_oe0), .pins_oe1(pins_oe1), .sample0(sample0),
        .sample1(sample1), .tx_ready0(tx_ready0), .rx_data0(rx_data0),
        .rx_valid0(rx_valid0), .tx_ready1(tx_ready1), .rx_data1(rx_data1),
        .rx_valid1(rx_valid1), .busy0(busy0), .busy1(busy1), .irq0(irq0), .irq1(irq1)
    );

    task automatic check(input condition, input [8*100-1:0] message);
        begin
            if (!condition) begin
                $display("FAIL: %0s at %0t", message, $time);
                $fatal(1);
            end
        end
    endtask

    integer bit_index;
    reg [7:0] input_byte;
    reg [7:0] transformed_byte;
    initial begin
        input_byte = 8'hA6;
        transformed_byte = input_byte ^ 8'h5A;
        // Lane 0 receives one byte. Lane 1 consumes the transformed byte from user logic and sends it.
        program_image[24*0 +: 24] = 24'hA080_00; // SHIFT_IN pin 0, MSB first, 8 bits
        program_image[24*1 +: 24] = 24'h8000_00; // HALT
        program_image[24*4 +: 24] = 24'hB090_00; // TX_SHIFT to pin 1, MSB first, 8 bits
        program_image[24*5 +: 24] = 24'h8000_00; // HALT

        repeat (2) @(negedge clk);
        rst_n = 1'b1;
        @(negedge clk);
        start0 = 1'b1;
        start1 = 1'b1;
        @(negedge clk);
        start0 = 1'b0;
        start1 = 1'b0;
        @(negedge clk); // both lanes have decoded their first instruction

        for (bit_index = 7; bit_index >= 0; bit_index = bit_index - 1) begin
            pins_in[0] = input_byte[bit_index];
            @(negedge clk);
        end
        check(rx_valid0 && rx_data0 == input_byte,
              "receiver publishes a complete byte and holds it for the transform");
        check(tx_ready1, "transmitter is waiting with backpressure ready");

        // The next handshake edge transfers the transformed byte to lane 1.
        @(negedge clk);
        check(!rx_valid0, "source lane retires its byte only after downstream acceptance");
        check(tx_valid1 && tx_ready1, "bridge presents transformed data to the waiting lane");
        @(negedge clk); // lane 1 accepts the byte and begins its shift operation
        for (bit_index = 7; bit_index >= 0; bit_index = bit_index - 1) begin
            @(negedge clk);
            check(pins_out1[1] == transformed_byte[bit_index],
                  "user logic transforms the received byte before timed serial output");
        end
        repeat (2) @(negedge clk);
        check(!busy0 && !busy1 && pins_oe1[1], "both event lanes complete independently");
        check(sample0 == input_byte, "captured input remains visible to user logic");

        $display("PASS: user-logic byte transform runs between two timed event lanes");
        $finish;
    end
endmodule

`default_nettype wire
