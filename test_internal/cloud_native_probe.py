"""Prepare UART output connectivity then reuse the strict native cloud test.

Kept outside spikes/cloud so this diagnostic can run independently without
enqueuing another long routing job. No mapping, signal forcing or model edits.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import re
import gzip

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
work = Path(details["native_work"])
macro = next((work / "macro/nl").glob("*.nl.v"))
top = re.search(r"\bmodule\s+(\w+)", macro.read_text()).group(1)
tiles = sorted((work / "fabulous-tiles/tiles/tiny").glob("*/macro/ihp-sg13cmos5l/nl/*.nl.v"))
full = out / "actual_fabric_cone.json"
with (out / "fabric_cone_parse.log").open("w") as log:
    subprocess.run(["yosys", "-Q", "-T", "-p",
                    f"read_liberty -lib {library}; read_verilog {' '.join(str(p) for p in tiles)} {macro}; hierarchy -top {top}; write_json {full}"],
                   check=True, stdout=log, stderr=subprocess.STDOUT)
# Retain exact connectivity even if uncompressed JSON exceeds collector limit.
with gzip.open(out / "actual_fabric_cone.json.gz", "wb") as archive:
    archive.write(full.read_bytes())
env.update(WARP_COMPACT_FABRIC_CONE_JSON=str(full), WARP_COMPACT_FABRIC_TOP=top,
           WARP_COMPACT_SHADOW_RTL="1")
result = subprocess.run([sys.executable, str(ROOT / "spikes/cloud/native_fabric.py")], env=env)
from cloud_lut_formal import run_proofs
run_proofs(ROOT, work, library)
raise SystemExit(result.returncode)
