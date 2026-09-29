`timescale 1ns/1ps
`default_nettype none

module tb_event_lanes;
    reg clk = 1'b0;
    always #5 clk = ~clk;

    reg rst_n = 1'b0;
    reg start0 = 1'b0;
    reg start1 = 1'b0;
    reg [2:0] start_pc0 = 3'd0;
    reg [2:0] start_pc1 = 3'd0;
    reg [7:0] pins_in = 8'd0;
    reg prog_we = 1'b0;
    reg [2:0] prog_addr = 3'd0;
    reg [23:0] prog_wdata = 24'd0;
    wire prog_ready;
    wire [7:0] pins_out0, pins_out1, pins_oe0, pins_oe1;
    wire [7:0] sample0, sample1;
    wire busy0, busy1, irq0, irq1;
    reg irq_seen0 = 1'b0;
    reg irq_seen1 = 1'b0;

    always @(posedge clk)
        if (irq0)
            irq_seen0 <= 1'b1;
        else if (irq1)
            irq_seen1 <= 1'b1;

    warp_event_lanes dut (
        .clk(clk), .rst_n(rst_n), .start0(start0), .start1(start1),
        .start_pc0(start_pc0), .start_pc1(start_pc1), .pins_in(pins_in),
        .prog_we(prog_we), .prog_addr(prog_addr), .prog_wdata(prog_wdata),
        .prog_ready(prog_ready), .pins_out0(pins_out0), .pins_out1(pins_out1),
        .pins_oe0(pins_oe0), .pins_oe1(pins_oe1), .sample0(sample0),
        .sample1(sample1), .busy0(busy0), .busy1(busy1), .irq0(irq0), .irq1(irq1)
    );

    task automatic check(input condition, input [8*100-1:0] message);
        begin
            if (!condition) begin
                $display("FAIL: %0s at %0t", message, $time);
                $fatal(1);
            end
        end
    endtask

    task automatic write_instruction(input [2:0] address, input [23:0] data);
        begin
            @(negedge clk);
            check(prog_ready, "program image should be writable while idle");
            prog_addr = address;
            prog_wdata = data;
            prog_we = 1'b1;
            @(negedge clk);
            prog_we = 1'b0;
        end
    endtask

    task automatic tick;
        begin
            @(negedge clk);
        end
    endtask

    initial begin
        // WAIT_PINS(mask=1,value=1), DELAY(3), SAMPLE, BRANCH_SAMPLE(mask=1,value=1,target=6),
        // SHIFT_OUT(pin=1, MSB first, data=A5, 4 bits), HALT, DRIVE(mask=3,value=1), HALT.
        repeat (2) @(negedge clk);
        rst_n = 1'b1;
        write_instruction(3'd0, 24'h3010_10);
        write_instruction(3'd1, 24'h4000_30);
        write_instruction(3'd2, 24'h5000_00);
        write_instruction(3'd3, 24'h6010_16);
        write_instruction(3'd4, 24'h909A_54);
        write_instruction(3'd5, 24'h8000_00);
        write_instruction(3'd6, 24'h1030_10);
        write_instruction(3'd7, 24'h8000_00);
        check(prog_ready, "image ready after programming");

        @(negedge clk);
        start0 = 1'b1;
        start1 = 1'b1;
        start_pc0 = 3'd0;
        start_pc1 = 3'd4;
        @(negedge clk);
        start0 = 1'b0;
        start1 = 1'b0;
        check(busy0 && busy1, "both lanes start independently");

        // The running image is immutable, and lane 0 remains blocked on its input condition.
        @(negedge clk);
        check(!prog_ready, "program write lock while a lane runs");
        prog_addr = 3'd6;
        prog_wdata = 24'h1030_20;
        prog_we = 1'b1;
        tick();
        check(pins_out1[1] == 1'b1 && pins_oe1 == 8'h02,
              "shift-out emits the first MSB on the selected pin");
        tick();
        check(pins_out1[1] == 1'b0, "shift-out emits the second bit on the next clock");
        tick();
        check(pins_out1[1] == 1'b1, "shift-out preserves bit order");
        tick();
        check(pins_out1[1] == 1'b0, "shift-out emits the fourth bit and completes");
        tick();
        prog_we = 1'b0;
        check(busy0, "lane 0 waits for its pin predicate");
        check(!busy1 && pins_out1 == 8'h00 && pins_oe1 == 8'h02,
              "lane 1 completes while lane 0 is waiting");
        check(!prog_ready, "image stays locked while lane 0 remains active");

        pins_in = 8'h01;
        repeat (12) tick();
        check(!busy0 && irq_seen0, "lane 0 finishes its independent wait, delay and branch path");
        check(pins_out0 == 8'h01 && pins_oe0 == 8'h03,
              "sample branch reaches the original shared-image instruction");
        check(sample0 == 8'h01, "sample captures live input pins");
        check(pins_out1 == 8'h00 && sample1 == 8'h00,
              "lane 0 state changes do not alter lane 1 state");
        check(prog_ready, "programming becomes available when both lanes are idle");

        // Update only while idle. Lane 1 releases its pin then wraps to the replacement HALT.
        write_instruction(3'd7, 24'h2020_00);
        write_instruction(3'd0, 24'h8000_00);
        @(negedge clk);
        start1 = 1'b1;
        start_pc1 = 3'd7;
        @(negedge clk);
        start1 = 1'b0;
        repeat (3) tick();
        check(!busy1 && irq_seen1, "halt IRQ is observed after a lane restarts");
        check(pins_oe1 == 8'h00 && pins_out1 == 8'h00,
              "release disconnects outputs while retaining their values");

        // A second run tests input shifting independently of lane 0.
        write_instruction(3'd6, 24'hA080_04);
        write_instruction(3'd7, 24'h8000_00);
        @(negedge clk);
        start1 = 1'b1;
        start_pc1 = 3'd6;
        @(negedge clk);
        start1 = 1'b0;
        repeat (7) tick();
        check(!busy1 && sample1 == 8'h0F,
              "four MSB-first input samples are collected into the lane shift state");

        $display("PASS: event lanes, shared image lock, waits, delay, sample, branch, serial shifts and release");
        $finish;
    end
endmodule

`default_nettype wire
