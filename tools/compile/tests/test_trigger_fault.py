"""Cloud-only source checks of the documented autonomous fault timing contract.

The existing UART wrapper is replaced by a transparent fixture here to isolate
schedule behavior. Real loaded UART/event coexistence is checked separately.
"""
import os
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[3]
CLOUD = os.environ.get("GITHUB_ACTIONS") == "true" or os.environ.get("WARP_HELPER_RTL_TESTS") == "1"


@pytest.mark.skipif(not CLOUD, reason="fault RTL simulation runs on cloud; local EDA opt-in required")
@pytest.mark.parametrize("delay,width,bits", [(0, 1, 1), (0, 8, 3), (8, 8, 3), (3, 2, 2)])
def test_trigger_fault_schedule(tmp_path, delay, width, bits):
    assert shutil.which("iverilog"), "cloud fault checks require Icarus"
    bench = tmp_path / "bench.v"
    bench.write_text(f'''
`default_nettype none
// Deliberately transparent fixture; does not model UART or event counting.
module uart_fault_monitor_top #(parameter DIV=16)
(input wire clk,rst_n,rx_i,event_i,fault_i,output wire tx_o,
 input wire [7:0] h_wdata,input wire h_wvalid,output wire h_wready,
 output wire [7:0] h_rdata,output wire h_rvalid,input wire h_rready,
 output wire [7:0] h_status);
assign tx_o=1'b1 ^ fault_i;
assign h_wready=1'b0; assign h_rdata=8'd0;
assign h_rvalid=1'b0; assign h_status=8'd0;
endmodule
module bench;
reg clk=0; always #5 clk=!clk;
reg rst_n=0,trigger=0;
wire tx;
integer t;
uart_trigger_fault_top #(.DELAY_CYCLES({delay}),.WINDOW_CYCLES({width}),.COUNTER_BITS({bits})) dut
(.clk(clk),.rst_n(rst_n),.rx_i(1'b1),.event_i(1'b0),.fault_i(trigger),.tx_o(tx),
 .h_wdata(8'd0),.h_wvalid(1'b0),.h_wready(),.h_rdata(),.h_rvalid(),.h_rready(1'b0),.h_status());
task edge_tick; begin @(posedge clk); #1; end endtask
task verify_level; input integer offset; begin
 if(tx !== !((offset >= {delay}) && (offset < {delay+width})))
  $fatal(1,"schedule offset %0d tx=%b",offset,tx);
end endtask
initial begin
edge_tick;
if(tx !== 1'b1) $fatal(1,"reset transparency");
// Long-held trigger: exactly one operation, including D=0/W=1 corner.
@(negedge clk); rst_n=1; trigger=1;
for(t=0;t<{delay+width+5};t=t+1) begin edge_tick; verify_level(t); end
@(negedge clk); trigger=0;
edge_tick;
// A new edge is accepted. For multi-cycle operations, inject another rising
// edge while busy; the interval must remain fixed, with no queued operation.
@(negedge clk); trigger=1;
for(t=0;t<{delay+width+5};t=t+1) begin
 edge_tick; verify_level(t);
 @(negedge clk);
 if(t==0) trigger=0;
 if(t==1 && {delay+width}>2) trigger=1;
 if(t==2) trigger=0;
end
trigger=0; edge_tick;
// Start one more operation, stop at its first active cycle, then reset.
@(negedge clk); trigger=1;
for(t=0;t<={delay};t=t+1) begin edge_tick; verify_level(t); end
if(tx !== 1'b0) $fatal(1,"not active before reset");
@(negedge clk); rst_n=0; trigger=1;
edge_tick;
if(tx !== 1'b1) $fatal(1,"active reset must immediately cancel window");
// Trigger kept high through reset is a fresh edge after reset release.
@(negedge clk); rst_n=1;
for(t=0;t<{delay+width+5};t=t+1) begin edge_tick; verify_level(t); end
@(negedge clk); trigger=0;
edge_tick;
$display("PASS fault schedule"); $finish;
end
endmodule
''')
    image = tmp_path / "sim"
    subprocess.run(["iverilog", "-g2005", "-s", "bench", "-o", str(image), str(bench),
                    str(ROOT / "protocols/uart_monitor/uart_trigger_fault_top.v")],
                   check=True, capture_output=True, text=True, timeout=30)
    result = subprocess.run(["vvp", str(image)], check=True, capture_output=True, text=True, timeout=30)
    assert "PASS fault schedule" in result.stdout
