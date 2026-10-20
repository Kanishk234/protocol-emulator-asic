// Differential phase-boundary check. The runner supplies frozen gold and trial gate modules.
`default_nettype none
`timescale 1ns/1ps
`include "trw_defs.vh"
module tb_cfg_staging;
    parameter FULL = 1;
    reg clk = 0;
    reg rst_n = 0;
    reg we = 0;
    reg [4:0] waddr = 0;
    reg [15:0] wdata = 0;
    wire [`TRW_PC_BITS-1:0] gold_cfg, gate_cfg;
    wire gold_active, gate_active, gold_restart, gate_restart;
    integer checks = 0;
    integer cycle;
    reg [31:0] rng = 32'h6e204c31;
    trw_pin_cfg_gold #(.FULL(FULL)) gold (
        .clk(clk), .rst_n(rst_n), .we(we), .waddr(waddr), .wdata(wdata),
        .cfg(gold_cfg), .carrier_active(gold_active), .restart(gold_restart));
    trw_pin_cfg_gate #(.FULL(FULL)) gate (
        .clk(clk), .rst_n(rst_n), .we(we), .waddr(waddr), .wdata(wdata),
        .cfg(gate_cfg), .carrier_active(gate_active), .restart(gate_restart));

    task compare;
        begin
            checks = checks + 1;
            if ({gold_cfg, gold_active, gold_restart} !== {gate_cfg, gate_active, gate_restart}) begin
                $display("FAIL cycle=%0d clk=%b reset=%b we=%b addr=%0d data=%h", cycle, clk, rst_n, we, waddr, wdata);
                $fatal(1, "Configuration staging changes observable phase behavior");
            end
        end
    endtask
    task randomize;
        begin
            rng = rng ^ (rng << 13);
            rng = rng ^ (rng >> 17);
            rng = rng ^ (rng << 5);
        end
    endtask
    initial begin
        // Initialize every address, then mix back-to-back writes, idle bus motion,
        // invalid addresses, reset with writes, and control changes in both phases.
        for (cycle = 0; cycle < 2080; cycle = cycle + 1) begin
            clk = 0;
            randomize;
            rst_n = (cycle >= 2) && ((cycle % 173) != 0);
            we = (cycle < 66) || rng[0] || rng[1];
            waddr = (cycle < 66) ? cycle[4:0] : rng[6:2];
            wdata = rng[31:16];
            #2; compare;
            // Bus motion during low phase must be captured by both gate and staging.
            randomize; wdata = rng[15:0];
            #2; compare;
            clk = 1;
            #2; compare;
            // Host registers may move during high phase; the existing enable latch
            // and staging registers determine visibility, not the live input bus.
            randomize; wdata = rng[31:16]; we = rng[0]; waddr = rng[5:1];
            #2; compare;
            clk = 0;
            #2; compare;
        end
        $display("PASS full=%0d cycles=%0d phase_checks=%0d", FULL, cycle, checks);
        $finish;
    end
endmodule
