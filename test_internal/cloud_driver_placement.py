"""Authenticate fresh physical source before bounded placement-only ECO."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[1]
source = root / "build/driver_source"
accepted = json.loads((source / "result.json").read_text())
for key in ("verified_native_markers", "fresh_magic_errors",
            "klayout__drc_error__count", "design__lvs_error__count", "flow_returncode"):
    if accepted.get(key) != 0:
        raise RuntimeError(f"Source physical gate missing: {key}")
out = root / "build/driver_placement"
out.mkdir(exist_ok=False)
odb = source / "fresh_streamout/04-odb-cellfrequencytables/tt_um_warp.odb"
if hashlib.sha256(odb.read_bytes()).hexdigest() != "02b8bd30f3fb12e4a66e2322b5f3906c236dd93eed8b8cd1eeeff95f6e796a61":
    raise RuntimeError("Unexpected extracted placement database")
pdk = Path(os.environ["PDK_ROOT"]) / "ihp-sg13cmos5l/libs.ref"
inputs = {"ODB": odb,
    "STD_LIB": pdk / "sg13cmos5l_stdcell/lib/sg13cmos5l_stdcell_slow_1p08V_125C.lib",
    "IO_LIB": pdk / "sg13cmos5l_io/lib/sg13cmos5l_io_slow_1p08V_3p0V_125C.lib"}
(out / "inputs.json").write_text(json.dumps({key: {
    "path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    for key, path in inputs.items()}, indent=2) + "\n")
command = ["docker", "run", "--rm", "-v", f"{root}:{root}", "-w", str(root)]
for key, path in {**inputs, "OUT": out}.items():
    command += ["-e", f"WARP_SCREEN_{key}={path}"]
command += ["ghcr.io/librelane/librelane@sha256:d109140b8f17fc54f4fca998beb8124f4949404ec52e339eebd2250854a18b5a",
    "openroad", "-exit", "test_internal/driver_placement_probe.tcl"]
with (out / "placement.log").open("w") as log:
    subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=180)
