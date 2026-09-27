`timescale 1ns/1ps
`default_nettype none
module guard_tb;
    reg clk=0, rst_n=0, begin_load=0, abort_load=0, commit_image=0, image_valid=0, write_active=0;
    always #5 clk=~clk;
    wire hold_fabric, park_outputs, user_reset, load_allowed, ready;
    integer checks=0, delay_index, step_index;
    wp_reload_guard dut (.*);
    task step;
        begin @(posedge clk); #1; checks=checks+1; @(negedge clk); end
    endtask
    task parked;
        begin
            if (ready !== 0 || park_outputs !== 1 || user_reset !== 1)
                $fatal(1,"Unsafe external release");
        end
    endtask
    task start;
        begin
            begin_load=1; step(); begin_load=0;
            parked();
            if (hold_fabric !== 1 || load_allowed !== 0) $fatal(1,"Missing hold arm interval");
            step();
            if (load_allowed !== 1) $fatal(1,"Loader not enabled");
        end
    endtask
    task commit_valid;
        begin commit_image=1; image_valid=1; step(); commit_image=0; image_valid=0; end
    endtask
    initial begin
        step(); rst_n=1; parked();
        // No commit can release an unstarted/invalid/in-progress transaction.
        commit_image=1; image_valid=1; repeat(12) begin step(); parked(); end
        commit_image=0; image_valid=0; start();
        commit_image=1; repeat(12) begin step(); parked(); end
        image_valid=1; write_active=1; repeat(12) begin step(); parked(); end
        write_active=0; commit_valid();
        parked(); if (hold_fabric !== 1 || load_allowed !== 0) $fatal(1,"Invalid settle state");
        step(); parked(); if (hold_fabric !== 1) $fatal(1,"Hold released too soon");
        // Five complete user-clock reset opportunities, with pads still parked.
        repeat(5) begin step(); parked(); if (hold_fabric !== 0) $fatal(1,"User reset cannot propagate"); end
        step();
        if (ready !== 1 || park_outputs !== 0 || user_reset !== 0 || hold_fabric !== 0 || load_allowed !== 0)
            $fatal(1,"Run release failed");
        // Abort and restart at each point from commit through RUN.
        for (delay_index=0; delay_index<9; delay_index=delay_index+1) begin
            start(); commit_valid();
            for (step_index=0; step_index<delay_index; step_index=step_index+1) step();
            abort_load=1; begin_load=1; step(); abort_load=0; begin_load=0;
            parked(); if (hold_fabric !== 1 || load_allowed !== 0) $fatal(1,"Abort priority failed");
        end
        // Reset overrides even valid commit and begin requests.
        rst_n=0; begin_load=1; commit_image=1; image_valid=1; step(); parked();
        if (hold_fabric !== 1 || load_allowed !== 0) $fatal(1,"Reset priority failed");
        $display("PASS: guard sequencing, invalid commits and abort/reset priority; %0d steps", checks);
        $finish;
    end
endmodule
`resetall
