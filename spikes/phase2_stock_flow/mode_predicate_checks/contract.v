`include "trw_defs.vh"
module mode_contract #(parameter FULL=1)(input clk, rst_n, we, input [4:0] waddr, input [15:0] wdata);
wire [`TRW_PC_BITS-1:0] cfg;
wire bitsync_active;
trw_pin_cfg #(.FULL(FULL)) d(.clk(clk),.rst_n(rst_n),.we(we),.waddr(waddr),.wdata(wdata),.cfg(cfg),.bitsync_active(bitsync_active),.carrier_active(),.sample_delta(),.restart());
reg valid=0;
always @(posedge clk) if(we && waddr==0) valid<=1;
always @(negedge clk) if(valid) assert(bitsync_active == ((FULL != 0) && (cfg[2:0]==4) && (cfg[4:3]==3)));
reg past_valid=0;
always @($global_clock) begin
 past_valid<=1;
 if(!past_valid) assume(!clk);
 if(past_valid) begin
  assume(clk != $past(clk));
  if(clk) assume($stable({rst_n,we,waddr,wdata}));
 end
end
endmodule
