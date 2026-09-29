`timescale 1ns/1ps
`default_nettype none

module tb_event_lanes_static;
    reg clk = 1'b0;
    always #5 clk = ~clk;

    reg rst_n = 1'b0;
    reg start0 = 1'b0;
    reg start1 = 1'b0;
    reg [2:0] start_pc0 = 3'd0;
    reg [2:0] start_pc1 = 3'd4;
    reg [7:0] pins_in = 8'd0;
    reg [191:0] program_image = 192'd0;
    reg tx_valid0 = 1'b0, tx_valid1 = 1'b0;
    reg [7:0] tx_data0 = 8'd0, tx_data1 = 8'd0;
    reg rx_ready0 = 1'b1, rx_ready1 = 1'b1;
    wire [7:0] pins_out0, pins_out1, pins_oe0, pins_oe1;
    wire [7:0] sample0, sample1;
    wire tx_ready0, tx_ready1, rx_valid0, rx_valid1;
    wire [7:0] rx_data0, rx_data1;
    wire busy0, busy1, irq0, irq1;

    warp_event_lanes_static dut (
        .clk(clk), .rst_n(rst_n), .start0(start0), .start1(start1),
        .start_pc0(start_pc0), .start_pc1(start_pc1), .pins_in(pins_in),
        .tx_valid0(tx_valid0), .tx_data0(tx_data0), .rx_ready0(rx_ready0),
        .tx_valid1(tx_valid1), .tx_data1(tx_data1), .rx_ready1(rx_ready1),
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

    initial begin
        // The image is static in the candidate. This models the configuration latches' Q outputs.
        program_image[24*0 +: 24] = 24'h908A_54; // SHIFT_OUT pin 0, MSB first, A5, 4 bits
        program_image[24*1 +: 24] = 24'h8000_00; // HALT
        program_image[24*4 +: 24] = 24'h3010_10; // WAIT_PINS(mask=1,value=1)
        program_image[24*5 +: 24] = 24'h5000_00; // SAMPLE
        program_image[24*6 +: 24] = 24'h8000_00; // HALT

        repeat (2) @(negedge clk);
        rst_n = 1'b1;
        @(negedge clk);
        start0 = 1'b1;
        start1 = 1'b1;
        @(negedge clk);
        start0 = 1'b0;
        start1 = 1'b0;
        repeat (7) @(negedge clk);
        check(!busy0 && busy1, "configured lane 0 finishes while lane 1 waits");
        check(pins_oe0 == 8'h01, "static image drives the selected serial pin");
        check(sample1 == 8'h00, "waiting lane has not sampled early");

        pins_in = 8'h01;
        repeat (4) @(negedge clk);
        check(!busy1 && sample1 == 8'h01, "second static-image lane observes its live input");
        check(pins_out0[0] == 1'b0, "serial lane retains its final shifted bit");

        $display("PASS: configured image drives independent lanes without a runtime write port");
        $finish;
    end
endmodule

`default_nettype wire
