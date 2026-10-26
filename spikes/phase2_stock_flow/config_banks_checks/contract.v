`include "trw_defs.vh"
module bank_contract #(parameter FULL=1)(input clk,rst_n,we,input [4:0] waddr,input [15:0] wdata);
wire [`TRW_PC_BITS-1:0] cfg,gold;
wire carrier,gcarrier,active,gactive,restart,grestart;
wire [24:0] delta,gdelta;
trw_pin_cfg #(.FULL(FULL)) d(.clk(clk),.rst_n(rst_n),.we(we),.waddr(waddr),.wdata(wdata),.cfg(cfg),.carrier_active(carrier),.sample_delta(delta),.bitsync_active(active),.restart(restart));
gold_pin_cfg #(.FULL(FULL)) g(.clk(clk),.rst_n(rst_n),.we(we),.waddr(waddr),.wdata(wdata),.cfg(gold),.carrier_active(gcarrier),.sample_delta(gdelta),.bitsync_active(gactive),.restart(grestart));
reg [`TRW_PC_WORDS-1:0] valid=0;
reg edge_seen=0;
always @(posedge clk) begin
 edge_seen<=1;
 if(we && waddr < `TRW_PC_WORDS) valid[waddr]<=1;
end
integer i;
always @(negedge clk) begin
 for(i=0;i<`TRW_PC_WORDS;i=i+1) if(valid[i]) assert(cfg[16*i+:16]==gold[16*i+:16]);
 if(edge_seen) assert(restart==grestart);
 if(valid[0]) assert(active==gactive);
 if(valid[13] && valid[14]) assert(carrier==gcarrier);
 if(valid[4] && valid[5] && valid[6] && valid[7]) assert(delta==gdelta);
end
reg past_valid=0;
always @($global_clock) begin
 past_valid<=1;
 if(!past_valid) assume(!clk);
 if(past_valid) begin
  assume(clk!=$past(clk));
  if(clk) assume($stable({rst_n,we,waddr,wdata}));
 end
end
endmodule
