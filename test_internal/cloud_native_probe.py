"""Prepare UART output connectivity then reuse the strict native cloud test.

Kept outside spikes/cloud so this diagnostic can run independently without
enqueuing another long routing job. No mapping, signal forcing or model edits.
"""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
details = json.loads((ROOT / "build/cloud_input/materialized.json").read_text())
tile = Path(details["native_work"]) / "fabulous-tiles/tiles/tiny/E_IO4_wide/macro/ihp-sg13cmos5l/nl/E_IO4_wide.nl.v"
library = Path(os.environ["PDK_ROOT"]) / "ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell/lib/sg13cmos5l_stdcell_slow_1p08V_125C.lib"
out = ROOT / "build/cloud_setup"
out.mkdir(parents=True, exist_ok=True)
cone = out / "actual_uart_io_cone.json"
with (out / "uart_io_parse.log").open("w") as log:
    subprocess.run(["yosys", "-Q", "-T", "-p",
                    f"read_liberty -lib {library}; read_verilog {tile}; hierarchy -top E_IO4_wide; write_json {cone}"],
                   check=True, stdout=log, stderr=subprocess.STDOUT)
env = dict(os.environ, WARP_COMPACT_IO_CONE_JSON=str(cone))
result = subprocess.run([sys.executable, str(ROOT / "spikes/cloud/native_fabric.py")], env=env)
raise SystemExit(result.returncode)
