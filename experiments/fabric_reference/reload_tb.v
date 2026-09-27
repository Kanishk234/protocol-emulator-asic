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
`ifdef RELOAD_HOLD
    reg reload_hold = 1;
`endif
`ifdef RELOAD_GUARD
    reg control_resetn = 0, begin_load = 0, abort_load = 0, commit_image = 0, image_valid = 0;
    wire config_hold, output_park, user_reset, load_allowed, guard_ready;
    integer parked_checks = 0;
`ifdef RELOAD_VALIDATED
    reg [31:0] expected_crc;
    reg [31:0] crc_a, crc_b, reject_crc;
    wire word_ready, validated, image_complete, image_error, fabric_write;
    string reject_image;
    integer reject_bytes=12024, reject_error=1;
    integer accepted_words=0, forwarded_words=0, frame_pulses=0;
    reg previous_frame_strobe=0;
    reference_validated_top
`ifdef BYTE_CRC
        #(.SERIAL_CRC(1))
`endif
        dut (
        .ArchitectureId(32'h46524231), .FormatVersion(16'd1), .ImageBytes(32'd12024),
        .ExpectedCRC(expected_crc), .WordReady(word_ready), .ImageValid(validated),
        .ImageComplete(image_complete), .ImageError(image_error), .FabricWrite(fabric_write),
`else
    reference_guarded_top dut (
        .ImageValid(image_valid),
`endif
        .ControlResetn(control_resetn), .BeginLoad(begin_load), .AbortLoad(abort_load),
        .CommitImage(commit_image),
        .ConfigHold(config_hold), .OutputPark(output_park), .UserReset(user_reset),
        .LoadAllowed(load_allowed), .Ready(guard_ready),
`else
    eFPGA_top dut (
`ifdef RELOAD_HOLD
        .ReloadHold(reload_hold),
`endif
`endif
        .I_top(pins_out), .T_top(pins_t), .O_top(pins_in),
        .A_config_C(cfg_a), .B_config_C(cfg_b), .CLK(clk),
        .resetn(resetn), .SelfWriteStrobe(strobe), .SelfWriteData(data),
        .Rx(1'b1), .ComActive(active), .ReceiveLED(led),
        .s_clk(1'b0), .s_data(1'b0)
    );
    reg [7:0] image [0:16383];
    string image_a, image_b, clear_image;
    bit clear_before_load = 0;
    integer checks = 0;
    integer interrupt_frames;
    reg [15:0] expected;
    reg [31:0] random_state = 32'h731fac29;
`ifdef RELOAD_VALIDATED
    // Read-only integration witness, separate from pin-level functional checks.
    // Confirms the disabled serial mux cannot substitute another stream.
    always @(posedge clk) begin
        if (!control_resetn || begin_load || abort_load || !resetn) begin
            accepted_words=0; forwarded_words=0; frame_pulses=0;
            previous_frame_strobe=0;
        end else if (load_allowed) begin
            if (strobe && word_ready) accepted_words=accepted_words+1;
            if (dut.fabric.LocalWriteStrobe !== fabric_write)
                $fatal(1,"FAIL: loader/validator strobe divergence");
            if (fabric_write) begin
                if (dut.fabric.LocalWriteData !== data)
                    $fatal(1,"FAIL: loader/validator data divergence");
                forwarded_words=forwarded_words+1;
            end
            if (dut.fabric.LongFrameStrobe && !previous_frame_strobe)
                frame_pulses=frame_pulses+1;
            previous_frame_strobe=dut.fabric.LongFrameStrobe;
        end
    end
`endif
`ifdef RELOAD_GUARD
    // Sample after clocked and combinational settling; this is not an SDF glitch check.
    always @(posedge clk) begin
        #100;
        if (output_park === 1'b1) begin
            if (pins_out !== 28'b0 || pins_t !== {28{1'b1}})
                $fatal(1, "FAIL: outputs not parked");
            parked_checks = parked_checks + 1;
        end
    end
    task arm_load;
        begin
            @(negedge clk); begin_load=1;
            @(negedge clk); begin_load=0;
            wait(load_allowed === 1'b1);
            @(negedge clk);
        end
    endtask
`endif
    // Reload the same DUT; no internal state deposits or forces. Reset only
    // the public loader, write frames, then reset user state through its pin.
    task load_raw(input string path, input integer byte_count);
        integer i;
        begin
            $display("LOAD: %s at %0t", path, $time);
            $fflush();
            @(negedge clk);
`ifdef RELOAD_VALIDATED
            // Begin/ARM owns the loader reset and validator lifetime together.
            pins_in=1; strobe=0;
`else
            pins_in = 1; strobe = 0; resetn = 0;
            repeat (4) @(negedge clk);
            resetn = 1;
`endif
            repeat (20) @(negedge clk);
            $readmemh(path, image);
            for (i = 0; i < byte_count; i = i + 4) begin
                if (i % 1024 == 0 || $test$plusargs("trace_load")) begin
                    $display("FRAME-BYTE: %0d at %0t", i, $time);
                    $fflush();
                end
                data = {image[i], image[i+1], image[i+2], image[i+3]};
`ifdef RELOAD_VALIDATED
                // Fast mode supplies a word as soon as the wrapper accepts it.
                if (!$test$plusargs("fast_words")) repeat (2) @(negedge clk);
                while (word_ready !== 1'b1) @(negedge clk);
`else
                repeat (2) @(negedge clk);
`endif
                strobe = 1;
                @(negedge clk);
                strobe = 0;
`ifdef RELOAD_VALIDATED
                if (!$test$plusargs("fast_words")) repeat (2) @(negedge clk);
`else
                repeat (2) @(negedge clk);
`endif
            end
`ifdef RELOAD_VALIDATED
            // Only the wrapper's cooldown drains the last write; no TB delay.
`else
            repeat (100) @(negedge clk);
`endif
            $display("LOADED at %0t", $time);
            $fflush();
        end
    endtask
    task load(input string path);
        begin
`ifdef RELOAD_GUARD
`ifdef RELOAD_VALIDATED
            expected_crc = (path == image_b) ? crc_b : crc_a;
`endif
            arm_load();
`else
`ifdef RELOAD_HOLD
            reload_hold = 1;
`endif
`endif
            if (clear_before_load) load_raw(clear_image, 624);
`ifdef RELOAD_VALIDATED
            load_raw(path, 12024);
            // Request commit while CRC/pacing may still be busy. Only the
            // wrapper can release; validity need not exist on the last word.
            @(negedge clk); commit_image=1;
            while (word_ready !== 1'b1) @(negedge clk);
            if (validated !== 1 || image_error !== 0 || image_complete !== 1)
                $fatal(1,"FAIL: complete image rejected");
            wait(guard_ready === 1'b1);
            @(negedge clk); commit_image=0;
            if (accepted_words != 3006 || forwarded_words != 3006 || frame_pulses != 200)
                $fatal(1,"FAIL: word/frame counts %0d/%0d/%0d",accepted_words,forwarded_words,frame_pulses);
            $display("VALIDATED: 3006 accepted/forwarded words; 200 frame pulses; parked=%0d",parked_checks);
`else
            load_raw(path, 16384);
`ifdef RELOAD_GUARD
            @(negedge clk); commit_image=1; image_valid=1;
            @(negedge clk); commit_image=0; image_valid=0;
            wait(guard_ready === 1'b1);
            @(negedge clk);
            $display("RELEASED: parked samples=%0d", parked_checks);
`else
`ifdef RELOAD_HOLD
            reload_hold = 0;
`endif
`endif
`endif
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
`ifdef RELOAD_GUARD
            if (guard_ready !== 1'b1 || pins_t !== 28'hffffffe ||
                pins_out !== (lfsr_mode ? 28'h000ace1 : 28'b0))
                $fatal(1, "FAIL: functional mismatch at guarded release mode=%0d got=%h oe=%h", lfsr_mode, pins_out, pins_t);
`endif
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
`ifdef RELOAD_GUARD
        repeat(2) @(negedge clk);
        control_resetn = 1;
`endif
        if (!$value$plusargs("image_a=%s", image_a) || !$value$plusargs("image_b=%s", image_b))
            $fatal(1, "Missing images");
        clear_before_load = $value$plusargs("clear_image=%s", clear_image);
`ifdef RELOAD_VALIDATED
        if (!$value$plusargs("crc_a=%h",crc_a) || !$value$plusargs("crc_b=%h",crc_b))
            $fatal(1,"Missing CRC metadata");
        if (clear_before_load) $fatal(1,"Clearing is outside validated canonical format");
        if ($value$plusargs("reject_image=%s",reject_image)) begin
            if (!$value$plusargs("reject_crc=%h",reject_crc)) $fatal(1,"Missing reject CRC");
            if ($value$plusargs("reject_bytes=%d",reject_bytes)) begin end
            if ($value$plusargs("reject_error=%d",reject_error)) begin end
            load(image_a); exercise(0,32);
            expected_crc=reject_crc; arm_load(); load_raw(reject_image,reject_bytes);
            if ($test$plusargs("reset_after_load")) begin
                @(negedge clk); resetn=0;
                @(negedge clk); resetn=1;
            end
            @(negedge clk); commit_image=1;
            repeat(12) @(negedge clk);
            if (guard_ready !== 0 || output_park !== 1 || config_hold !== 1 ||
                validated !== 0 || image_error !== (reject_error != 0))
                $fatal(1,"FAIL: rejected image escaped hold or incorrect error status");
            commit_image=0;
            $display("REJECTED: accepted=%0d forwarded=%0d frames=%0d error=%b",
                     accepted_words,forwarded_words,frame_pulses,image_error);
            // Restart without abort: begin must discard sticky error/validity.
            load(image_a); exercise(0,1024);
            $display("PASS: rejected-image recovery; %0d checked cycles",checks);
            $finish;
        end
`endif
        if ($value$plusargs("interrupt_frames=%d", interrupt_frames)) begin
            if (interrupt_frames < 0 || interrupt_frames > 200)
                $fatal(1, "interrupt_frames must be in 0..200");
            load(image_a); exercise(0, 32);
`ifdef RELOAD_GUARD
`ifdef RELOAD_VALIDATED
            expected_crc=crc_b;
`endif
            arm_load();
`else
`ifdef RELOAD_HOLD
            reload_hold = 1;
`endif
`endif
            if (clear_before_load) load_raw(clear_image, 624);
            // Stop on a completed frame boundary, without a desync word.
            load_raw(image_b, 20 + interrupt_frames * 60);
            $display("INTERRUPTED: after %0d LFSR frames", interrupt_frames);
            $fflush();
`ifdef RELOAD_GUARD
            // An invalid commit must keep the partially loaded image hidden.
            @(negedge clk); commit_image=1; image_valid=0;
            repeat(10) @(negedge clk);
            if (guard_ready !== 0 || output_park !== 1 || config_hold !== 1)
                $fatal(1,"FAIL: invalid commit exposed partial image");
            commit_image=0; abort_load=1;
            @(negedge clk); abort_load=0;
            repeat(3) @(negedge clk);
            if (load_allowed !== 0 || output_park !== 1)
                $fatal(1,"FAIL: abort left loader enabled");
`endif
            // Reset/restart the public loader, then recover the original design.
            load(image_a); exercise(0, 1024);
            $display("PASS: interrupted-load recovery; %0d checked cycles", checks);
        end else if ($test$plusargs("cold_a")) begin
            load(image_a); exercise(0, 65540);
            $display("PASS: cold counter; %0d independently checked cycles", checks);
        end else if ($test$plusargs("cold_b")) begin
            load(image_b); exercise(1, 1024);
            $display("PASS: cold LFSR; %0d independently checked cycles", checks);
        end else if ($test$plusargs("start_b")) begin
            load(image_b); exercise(1, 1024);
            load(image_a); exercise(0, $test$plusargs("quick") ? 32 : 65540);
            load(image_b); exercise(1, 1024);
            $display("PASS: B/A/B reload; %0d independently checked cycles", checks);
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
