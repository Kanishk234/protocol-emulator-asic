`timescale 1ns/1ps
`default_nettype none
module loader_handshake_tb;
    reg clk=0, resetn=1, control_resetn=0;
    reg begin_load=0, abort_load=0, commit_image=0, strobe=0;
    reg [31:0] data=0, expected_crc;
    wire [27:0] pins_out,pins_t;
    wire hold_fabric,park,user_reset,load_allowed,ready,word_ready,valid_image,complete,error,write_word;
    wire [55:0] cfg_a,cfg_b;
    wire active,led;
    reg [31:0] words[0:3005];
    string image_path;
    integer checks=0, action, delay_index, i, r, frames=0, accepted=0;
    integer cycle=0,last_write=-10,cancel_cases=0;
    reg monitor_frames=0, old_frame=0;
    always #5 clk=~clk;
`ifdef WORD_CRC
    localparam SERIAL_CRC=0;
`else
    localparam SERIAL_CRC=1;
`endif
    reference_validated_top
`ifndef MAPPED_WRAPPER
        #(.SERIAL_CRC(SERIAL_CRC))
`endif
        dut (
        .CLK(clk),.resetn(resetn),.ControlResetn(control_resetn),
        .BeginLoad(begin_load),.AbortLoad(abort_load),.CommitImage(commit_image),
        .ArchitectureId(32'h46524231),.FormatVersion(16'd1),.ImageBytes(32'd12024),
        .ExpectedCRC(expected_crc),.SelfWriteStrobe(strobe),.SelfWriteData(data),
        .O_top(28'hfffffff),.I_top(pins_out),.T_top(pins_t),
        .A_config_C(cfg_a),.B_config_C(cfg_b),.Rx(1'b1),.s_clk(1'b0),.s_data(1'b0),
        .ComActive(active),.ReceiveLED(led),.ConfigHold(hold_fabric),
        .OutputPark(park),.UserReset(user_reset),.LoadAllowed(load_allowed),.Ready(ready),
        .WordReady(word_ready),.ImageValid(valid_image),.ImageComplete(complete),
        .ImageError(error),.FabricWrite(write_word)
    );
    task step;
        begin @(posedge clk); #1; checks=checks+1; @(negedge clk); end
    endtask
    task parked;
        begin
            if (ready !== 0 || hold_fabric !== 1 || park !== 1 ||
                pins_out !== 0 || pins_t !== 28'hfffffff)
                $fatal(1,"Unsafe output during cancelled/busy load");
        end
    endtask
    task arm;
        begin
            begin_load=1; step(); begin_load=0; step();
            parked();
            if (load_allowed !== 1 || word_ready !== 1 || valid_image !== 0 ||
                complete !== 0 || error !== 0) $fatal(1,"Bad fresh transaction");
        end
    endtask
    always @(posedge clk) begin
        cycle=cycle+1;
        if (monitor_frames) begin
            if (write_word) begin
                if (cycle-last_write<4) $fatal(1,"Word pacing violation");
                if (dut.fabric.LongFrameStrobe !== 0)
                    $fatal(1,"New write overlaps a frame pulse");
                if (dut.fabric.LocalWriteStrobe !== 1 || dut.fabric.LocalWriteData !== words[accepted])
                    $fatal(1,"Held-valid stream duplicated/lost a word");
                accepted=accepted+1; last_write=cycle;
            end
            if (dut.fabric.LongFrameStrobe && !old_frame) begin
                if (frames>=200 || dut.fabric.FrameAddressRegister !== ((frames/20)<<27 | (1<<(frames%20))))
                    $fatal(1,"Wrong frame address during write pulse");
                for(r=0;r<14;r=r+1)
                    if (dut.fabric.FrameRegister[r*32+:32] !== words[6+15*frames+13-r])
                        $fatal(1,"Frame %0d row %0d payload mismatch",frames,r);
                frames=frames+1;
            end
            old_frame=dut.fabric.LongFrameStrobe;
        end
    end
    initial begin
        if (!$value$plusargs("image=%s",image_path) || !$value$plusargs("crc=%h",expected_crc))
            $fatal(1,"Missing image metadata");
        $readmemh(image_path,words);
        step(); control_resetn=1;
        // Cancel at each of the three pending-byte positions. Include control
        // priorities with write+commit simultaneously asserted.
        for(action=0;action<5;action=action+1) begin
            for(delay_index=0;delay_index<3;delay_index=delay_index+1) begin
                arm(); data=words[0]; strobe=1; step(); strobe=0;
                repeat(delay_index) step();
                if (word_ready !== 0) $fatal(1,"Cancellation missed busy window");
                commit_image=1; strobe=1; begin_load=1;
                if(action==1 || action==4) abort_load=1;
                if(action==2) resetn=0;
                if(action==3 || action==4) control_resetn=0;
                #1;
                if(write_word !== 0 || word_ready !== 0) $fatal(1,"Cancellation accepted a word");
                step(); parked();
                if(valid_image !== 0 || complete !== 0 || error !== 0) $fatal(1,"Stale validation on cancellation");
                begin_load=0; abort_load=0; resetn=1; control_resetn=1;
                commit_image=0; strobe=0; step(); parked();
                if(load_allowed !== (action==0)) $fatal(1,"Cancellation priority failed");
                cancel_cases=cancel_cases+1;
            end
        end
        arm(); monitor_frames=1;
        // Continuous valid, changing to the next word only after acceptance.
        strobe=1;
        for(i=0;i<3006;i=i+1) begin
            data=words[i];
            while(word_ready !== 1) begin
                #1; if(write_word !== 0) $fatal(1,"Busy write forwarded");
                step(); parked();
            end
            step(); parked();
        end
        strobe=0; commit_image=1;
        repeat(2) begin step(); parked(); if(SERIAL_CRC && valid_image !== 0) $fatal(1,"CRC released before final byte"); end
        // Allow the complete guard sequence, including reset while pads parked.
        repeat(12) step();
        commit_image=0; monitor_frames=0;
        if(ready !== 1 || valid_image !== 1 || error !== 0 ||
           accepted!=3006 || frames!=200 || pins_out !== 28'h5a5a5a5 || pins_t !== 28'hffffffe)
            $fatal(1,"Held-valid complete-image release failed");
        // A running valid image must not survive a coincident restart/write/commit.
        begin_load=1; strobe=1; commit_image=1; #1;
        if(write_word !== 0) $fatal(1,"RUN restart forwarded a word");
        step(); parked();
        if(valid_image !== 0) $fatal(1,"RUN restart retained validity");
        $display("PASS: loader handshake; %0d busy cancellations; %0d words; %0d frame payloads; %0d steps",
                 cancel_cases,accepted,frames,checks);
        $finish;
    end
    initial begin #1000000; $fatal(1,"Handshake timeout"); end
endmodule
`resetall
