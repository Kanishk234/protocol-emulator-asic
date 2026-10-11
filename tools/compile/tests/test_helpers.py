"""Behavioral helper checks; EDA runs on cloud by default, not the user's laptop."""
import os
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[3]
CLOUD = os.environ.get("GITHUB_ACTIONS") == "true" or os.environ.get("WARP_HELPER_RTL_TESTS") == "1"


@pytest.mark.skipif(not CLOUD, reason="HDL helper simulation runs on cloud; local EDA opt-in required")
@pytest.mark.parametrize("bits,msb,cycles", [(8, 1, 3), (3, 0, 1), (15, 1, 65536)])
def test_transaction_helpers(tmp_path, bits, msb, cycles):
    assert shutil.which("iverilog"), "cloud helper checks require Icarus (do not silently skip)"
    bench = tmp_path / "bench.v"
    bench.write_text(f'''
`default_nettype none
module bench;
reg clk=0; always #5 clk=!clk;
reg rst_n=0,start=0,step=0,sin=0,enable=0;
reg [7:0] data=8'hA5;
wire ready,complete,serial; wire [7:0] result;
wire delay_ready,elapsed;
reg [7:0] expected;
integer i;
wp_shift_transaction #(.BITS({bits}), .MSB_FIRST({msb})) shift_u
(.clk(clk),.rst_n(rst_n),.start(start),.step(step),.sin(sin),.data(data),
 .ready(ready),.complete(complete),.serial(serial),.result(result));
wp_delay #(.CYCLES({cycles})) delay_u
(.clk(clk),.rst_n(rst_n),.start(start),.enable(enable),.ready(delay_ready),.elapsed(elapsed));
task edge_tick; begin @(posedge clk); #1; end endtask
task check; input condition; begin if (condition !== 1'b1) $fatal(1,"check failed at %0t",$time); end endtask
initial begin
edge_tick; check(!ready && !delay_ready && !elapsed && !complete);
@(negedge clk); rst_n=1; start=1; step=1;
edge_tick; check(result==8'hA5 && !ready && !delay_ready && !complete);
@(negedge clk); start=0; step=0;
repeat(3) begin edge_tick; check(result==8'hA5 && !complete && !elapsed); end
expected=8'hA5;
for(i=0;i<{bits};i=i+1) begin
 @(negedge clk); step=1; sin=(i%2); start=(i==0); data=8'hFF;
 check(serial==({msb} ? expected[7] : expected[0]));
 expected={msb} ? {{expected[6:0],sin}} : {{sin,expected[7:1]}};
 edge_tick; check(result==expected && complete==(i=={bits}-1));
end
@(negedge clk); start=0;
edge_tick; check(ready && !complete && result==expected);
repeat(3) begin edge_tick; check(result==expected); end
// Timer remained paused throughout shifting. Resume and check its exact edge count.
@(negedge clk); enable=1;
for(i=0;i<{cycles};i=i+1) begin
 check(elapsed==(i=={cycles}-1));
 edge_tick;
 if(i<{cycles}-1) @(negedge clk);
end
check(delay_ready && !elapsed);
// Reset cancels another transaction even with conflicting start/step/enable.
@(negedge clk); start=1;
edge_tick; check(!ready && !delay_ready);
@(negedge clk); rst_n=0; step=1;
edge_tick; check(result==0 && !complete && !elapsed);
@(negedge clk); rst_n=1; start=0; step=0; enable=0;
edge_tick; check(ready && delay_ready && result==0 && !elapsed);
$display("PASS helpers"); $finish;
end
endmodule
''')
    image = tmp_path / "sim"
    files = [bench, ROOT / "tools/compile/helpers/wp_delay.v",
             ROOT / "tools/compile/helpers/wp_shift_transaction.v",
             ROOT / "tools/compile/prims/warp_prims_sim.v",
             ROOT / "arch/prims/wp_timer.v", ROOT / "arch/prims/wp_shift.v"]
    subprocess.run(["iverilog", "-g2005", "-s", "bench", "-o", str(image), *map(str, files)],
                   check=True, capture_output=True, text=True, timeout=30)
    result = subprocess.run(["vvp", str(image)], check=True, capture_output=True, text=True, timeout=30)
    assert "PASS helpers" in result.stdout
