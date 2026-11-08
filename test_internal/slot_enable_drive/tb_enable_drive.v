`timescale 1ns/1ps
`default_nettype none
`include "trw_defs.vh"
module tb_enable_drive;
    reg clk = 1'b0;
    always #10 clk = ~clk;
    reg rst_n = 1'b0, we = 1'b0;
    reg [5:0] waddr = 0;
    reg [15:0] wdata = 0;
    wire [12*`TRW_SLOT_BITS-1:0] gold_slots, gate_slots;
    wire [63:0] gold_k, gate_k;
    trw_slots_gold gold(.clk(clk),.rst_n(rst_n),.we(we),.waddr(waddr),.wdata(wdata),.slots(gold_slots),.k(gold_k));
    trw_slots_gate gate(.clk(clk),.rst_n(rst_n),.we(we),.waddr(waddr),.wdata(wdata),.slots(gate_slots),.k(gate_k));
    integer cycles = 0, phase_checks = 0, seeded = 0;
    integer a, r, e, p, i;
    integer seed = 32'h1208cafe;
    reg [15:0] pattern;
    task compare;
        begin
            if (seeded) begin
                phase_checks = phase_checks + 1;
                if ((gold_slots !== gate_slots) || (gold_k !== gate_k)) begin
                    $display("FAIL_SLOT_ENABLE_DRIVE cycle=%0d address=%0d reset=%0d write=%0d",cycles,waddr,rst_n,we);
                    $fatal(1);
                end
                if ((^gold_slots === 1'bx) || (^gold_k === 1'bx)) begin
                    $display("FAIL_UNKNOWN_REFERENCE_AFTER_INITIALIZATION");
                    $fatal(1);
                end
            end
        end
    endtask
    task cycle;
        input reset_value, write_value;
        input [5:0] address_value;
        input [15:0] data_value;
        begin
            @(negedge clk); #1;
            rst_n=reset_value; we=write_value; waddr=address_value; wdata=data_value;
            #1; compare;
            @(posedge clk); #1; compare;
            #4; compare;
            @(negedge clk); #1; compare;
            cycles=cycles+1;
        end
    endtask
    initial begin
        // Slot latches deliberately have no reset. Initialize every host word.
        for (a=0;a<52;a=a+1) cycle(1'b1,1'b1,a,16'h0000);
        cycle(1'b1,1'b0,6'd63,16'h0000);
        seeded=1;
        for (r=0;r<2;r=r+1)
            for (e=0;e<2;e=e+1)
                for (a=0;a<64;a=a+1)
                    for (p=0;p<4;p=p+1) begin
                        case(p)
                            0:pattern=16'h0000;
                            1:pattern=16'hffff;
                            2:pattern=16'ha5a5;
                            default:pattern=16'h5a5a;
                        endcase
                        cycle(r,e,a,pattern);
                    end
        for (i=0;i<2048;i=i+1)
            cycle(($random(seed)&3)!=0,$random(seed)&1,$random(seed)&63,$random(seed));
        $display("PASS_SLOT_ENABLE_DRIVE cycles=%0d phase_checks=%0d",cycles,phase_checks);
        $finish;
    end
endmodule
