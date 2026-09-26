`timescale 1ns/1ps
`default_nettype none
module reload_tb;
    reg clk = 0;
    always #500 clk = ~clk;
    reg resetn = 1;
    reg [27:0] pins_in = 0;
    wire [27:0] pins_out, pins_t;
    wire [55:0] cfg_a, cfg_b;
    reg strobe = 0;
    reg [31:0] data = 0;
    wire active, led;
    eFPGA_top dut (
        .I_top(pins_out), .T_top(pins_t), .O_top(pins_in),
        .A_config_C(cfg_a), .B_config_C(cfg_b), .CLK(clk),
        .resetn(resetn), .SelfWriteStrobe(strobe), .SelfWriteData(data),
        .Rx(1'b1), .ComActive(active), .ReceiveLED(led),
        .s_clk(1'b0), .s_data(1'b0)
    );
    reg [7:0] image [0:16383];
    string image_a, image_b;
    integer checks = 0;
    reg [15:0] expected;
    reg [31:0] random_state = 32'h731fac29;
    // Reload the same DUT; no internal state deposits or forces. Reset only
    // the public loader, write frames, then reset user state through its pin.
    task load(input string path);
        integer i;
        begin
            $display("LOAD: %s at %0t", path, $time);
            $fflush();
            @(negedge clk);
            pins_in = 1; strobe = 0; resetn = 0;
            repeat (4) @(negedge clk);
            resetn = 1;
            repeat (20) @(negedge clk);
            $readmemh(path, image);
            for (i = 0; i < 16384; i = i + 4) begin
                if (i % 1024 == 0 || $test$plusargs("trace_load")) begin
                    $display("FRAME-BYTE: %0d at %0t", i, $time);
                    $fflush();
                end
                data = {image[i], image[i+1], image[i+2], image[i+3]};
                repeat (2) @(negedge clk);
                strobe = 1;
                @(negedge clk);
                strobe = 0;
                repeat (2) @(negedge clk);
            end
            repeat (100) @(negedge clk);
            $display("LOADED at %0t", $time);
            $fflush();
        end
    endtask
    task tick(input bit lfsr_mode, input bit rst, input bit en);
        reg feedback;
        begin
            @(negedge clk);
            pins_in = {26'b0, en, rst};
            if (rst) expected = lfsr_mode ? 16'hace1 : 16'h0000;
            else if (en) begin
                if (lfsr_mode) begin
                    // Arithmetic oracle; no source-DUT instance is compiled.
                    feedback = ^(expected & 16'hb400);
                    expected = (expected << 1) | {15'b0, feedback};
                end else expected = expected + 1;
            end
            @(posedge clk);
            #100;
            if (pins_out !== {12'b0, expected} || pins_t !== 28'hffffffe)
                $fatal(1, "FAIL: functional mismatch mode=%0d rst=%0d en=%0d got=%h expected=%h oe=%h", lfsr_mode, rst, en, pins_out, expected, pins_t);
            checks = checks + 1;
        end
    endtask
    task exercise(input bit lfsr_mode, input integer cycles);
        integer i;
        begin
            tick(lfsr_mode, 1, 0);
            tick(lfsr_mode, 0, 0);
            tick(lfsr_mode, 0, 1);
            tick(lfsr_mode, 1, 0);
            tick(lfsr_mode, 1, 1);
            for (i = 0; i < cycles; i = i + 1) begin
                tick(lfsr_mode, 0, 1);
                if (i % 16384 == 0) begin
                    $display("CHECK: mode=%0d cycle=%0d at %0t", lfsr_mode, i, $time);
                    $fflush();
                end
            end
            for (i = 0; i < 128; i = i + 1) begin
                random_state = (random_state << 1) ^ (random_state[31] ? 32'h04c11db7 : 32'b0);
                tick(lfsr_mode, i % 17 == 0, random_state[0]);
            end
        end
    endtask
    initial begin
        if (!$value$plusargs("image_a=%s", image_a) || !$value$plusargs("image_b=%s", image_b))
            $fatal(1, "Missing images");
        if ($test$plusargs("cold_a")) begin
            load(image_a); exercise(0, 65540);
            $display("PASS: cold counter; %0d independently checked cycles", checks);
        end else if ($test$plusargs("cold_b")) begin
            load(image_b); exercise(1, 1024);
            $display("PASS: cold LFSR; %0d independently checked cycles", checks);
        end else begin
            load(image_a); exercise(0, $test$plusargs("quick") ? 32 : 65540);
            load(image_b); exercise(1, 1024);
            load(image_a); exercise(0, 1024);
            $display("PASS: A/B/A reload; %0d independently checked cycles", checks);
        end
        $finish;
    end
    initial begin
        #1000000000;
        $fatal(1, "Timeout");
    end
endmodule
`resetall
