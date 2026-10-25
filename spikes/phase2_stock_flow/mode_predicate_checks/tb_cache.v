`timescale 1ns/1ps
`include "trw_defs.vh"
module tb_cache;
parameter FULL=1;
reg clk=0, rst_n=0, we=0;
reg [4:0] addr=0;
reg [15:0] data=0;
wire [`TRW_PC_BITS-1:0] cfg, gold;
wire active, restart, gold_restart;
gold_pin_cfg #(.FULL(FULL)) g(.clk(clk),.rst_n(rst_n),.we(we),.waddr(addr),.wdata(data),.cfg(gold),.restart(gold_restart),.carrier_active(),.sample_delta());
trw_pin_cfg #(.FULL(FULL)) d(.clk(clk),.rst_n(rst_n),.we(we),.waddr(addr),.wdata(data),.cfg(cfg),.restart(restart),.carrier_active(),.sample_delta(),.bitsync_active(active));
reg valid=0;
integer i, j;
reg [31:0] random_word;
reg [31:0] rng=32'h93ab7c51;
task check;
begin
 if (cfg !== gold || restart !== gold_restart) $fatal(1,"cfg/restart mismatch");
 if ((FULL==0 || valid) && active !== ((FULL!=0) && (gold[2:0]==4) && (gold[4:3]==3)))
  $fatal(1,"cache mismatch data=%h addr=%d rst=%b",data,addr,rst_n);
end endtask
task tick;
begin
 #2; clk=1; #2;
 if (we && addr==0) valid=1;
 check;
 clk=0; #2; check;
end endtask
initial begin
 tick; rst_n=1;
 for(i=0;i<32;i=i+1) begin we=1;addr=i;data=0;tick;end
 for(i=0;i<65536;i=i+1) begin we=1;addr=0;data=i;tick;end
 for(j=0;j<10000;j=j+1) begin
  rng=rng^(rng<<13);rng=rng^(rng>>17);rng=rng^(rng<<5);random_word=rng;
  we=random_word[0];addr=random_word[5:1];data=random_word[21:6];rst_n=|random_word[25:22];tick;
 end
 $display("PASS cache: FULL=%d 65536 exhaustive word0 plus10000 random writes/reset/idle; both phases",FULL);
 $finish;
end
endmodule
