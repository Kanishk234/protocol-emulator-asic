`default_nettype none
`include "trw_defs.vh"
module wrapper_gate(input wire clk, rst_n, host_we,
 input wire [4:0] host_addr, input wire [15:0] host_data,
 output wire [`TRW_PC_BITS-1:0] cfg, output wire carrier_active, restart, output wire [24:0] sample_delta);
 reg we; reg [4:0] waddr; reg [15:0] wdata;
 always @(posedge clk) begin we <= host_we; waddr <= host_addr; wdata <= host_data; end
 trw_pin_cfg_gate #(.FULL(1)) u_cfg (.clk(clk),.rst_n(rst_n),.we(we),.waddr(waddr),.wdata(wdata),
 .cfg(cfg),.carrier_active(carrier_active),.restart(restart),.sample_delta(sample_delta));
endmodule
