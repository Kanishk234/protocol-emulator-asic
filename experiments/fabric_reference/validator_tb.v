`timescale 1ns/1ps
`default_nettype none
module validator_tb;
    reg clk=0, rst_n=0, begin_load=0, abort_load=0, commit_image=0, word_valid=0;
    reg [31:0] architecture_id=0, image_bytes=0, expected_crc=0, word_data=0;
    reg [15:0] format_version=0;
    wire hold_fabric, park_outputs, user_reset, load_allowed, ready;
    wire image_valid, complete, error, fabric_write, word_ready;
    reg [31:0] words[0:4095];
    reg [31:0] manifest_crc, manifest_arch;
    integer fd, fields, size, version, length, mode, wanted_valid, wanted_error;
    integer i, j, checks=0, cases=0, forwarded;
    reg [1023:0] name;
    wp_validated_reload
`ifndef MAPPED_VALIDATOR
`ifdef BYTE_CRC
        #(.SERIAL_CRC(1))
`endif
`endif
        dut (.*);
    always #5 clk=~clk;
    task step;
        begin @(posedge clk); #1; checks=checks+1; @(negedge clk); end
    endtask
    task parked;
        begin
            if (ready !== 0 || park_outputs !== 1 || user_reset !== 1 || hold_fabric !== 1)
                $fatal(1,"Unsafe release in %0s at word %0d",name,i);
        end
    endtask
    initial begin
        step(); rst_n=1;
        fd=$fopen("cases.txt","r");
        if (!fd) $fatal(1,"Missing cases manifest");
        while (!$feof(fd)) begin
            fields=$fscanf(fd,"%s %d %h %h %d %d %d %d %d\n",
                           name,size,manifest_crc,manifest_arch,version,length,
                           mode,wanted_valid,wanted_error);
            if (fields != 9) $fatal(1,"Malformed cases manifest");
            cases=cases+1;
            if (size>0) $readmemh({name,".hex"},words,0,size-1);
            architecture_id=manifest_arch; format_version=version;
            image_bytes=length; expected_crc=manifest_crc;
            // A simultaneous write/commit with begin must not reach the fabric.
            begin_load=1; word_valid=1; commit_image=1; #1;
            if (fabric_write !== 0) $fatal(1,"Write accepted during begin");
            step(); begin_load=0; word_valid=0; commit_image=0;
            parked(); step(); parked();
            if (load_allowed !== 1) $fatal(1,"Load not armed");
            if (mode==5) begin
                architecture_id=0; format_version=0; image_bytes=0; expected_crc=0;
            end
            forwarded=0;
            for (i=0; i<size; i=i+1) begin
                // Deterministic idle gaps: no repeat-counting idle bus contents.
                if (i%17==0) begin
                    word_valid=0; word_data=32'hdeadbeef; step(); parked();
                end
                word_data=words[i]; word_valid=1;
                if ((mode==1 && i==size-1) || (mode==2 && i==33) ||
                    (mode==6 && i==size-1)) commit_image=1;
                if (i==33 && mode==3) abort_load=1;
                if (i==33 && mode==4) rst_n=0;
                // Keep valid/data asserted across CRC backpressure. Cancellation
                // is deliberately allowed during a pending word's CRC work.
                while (word_ready !== 1) begin
                    #1;
                    if (fabric_write !== 0) $fatal(1,"Write accepted during CRC busy");
                    step(); parked();
                end
                #1;
                if ((abort_load || !rst_n) && fabric_write !== 0)
                    $fatal(1,"Cancellation did not suppress write");
                if (fabric_write) forwarded=forwarded+1;
                step(); parked();
                abort_load=0; rst_n=1; commit_image=0;
            end
            word_valid=0;
            // Commit during the final checksum's busy window must not release.
            commit_image=1;
            while (word_ready !== 1) begin step(); parked(); end
            commit_image=0;
            if (image_valid !== (wanted_valid != 0) || error !== (wanted_error != 0))
                $fatal(1,"%0s valid=%b error=%b expected %0d/%0d",
                       name,image_valid,error,wanted_valid,wanted_error);
            if (wanted_valid && (complete !== 1 || forwarded != 3006))
                $fatal(1,"Complete image did not forward exactly 3006 words");
            if (forwarded>3006) $fatal(1,"Forwarded padding or extra words");
            // This idle commit is the only event permitted to release a good image.
            commit_image=1; step(); commit_image=0;
            repeat(10) step();
            if (ready !== (wanted_valid != 0)) $fatal(1,"Incorrect guard release: %0s",name);
            if (!wanted_valid) parked();
            else begin
                if (park_outputs !== 0 || user_reset !== 0 || hold_fabric !== 0)
                    $fatal(1,"Guard did not enter RUN");
                // Stray RUN-state word must never reconfigure the live fabric.
                word_valid=1; #1;
                if (fabric_write !== 0) $fatal(1,"Write allowed in RUN");
                step(); word_valid=0;
            end
            $display("PASS case %0s: valid=%b error=%b forwarded=%0d",
                     name,image_valid,error,forwarded);
        end
        $fclose(fd);
        // Abort wins over begin/commit/write, even after a previously valid load.
        abort_load=1; begin_load=1; commit_image=1; word_valid=1; step();
        abort_load=0; begin_load=0; commit_image=0; word_valid=0;
        parked();
        if (image_valid !== 0 || complete !== 0 || error !== 0 || load_allowed !== 0)
            $fatal(1,"Abort priority/stale validity");
        rst_n=0; begin_load=1; step(); rst_n=1; begin_load=0; parked();
        $display("PASS: validated reload %0d cases; %0d steps",cases,checks);
        $finish;
    end
    initial begin #10000000; $fatal(1,"Validator test timeout"); end
endmodule
`resetall
