"""Route an authenticated legal one-driver ECO, then run unrelaxed gates."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
source = root / "build/driver_source"
out = root / "build/driver_route"
out.mkdir(exist_ok=False)
placed = json.loads((source / "placement_result.json").read_text())
for key, value in {"placement_legal": True, "changed_logic_masters": 1,
                   "moved_logic_cells": 3, "connectivity_unchanged": True}.items():
    if placed.get(key) != value:
        raise RuntimeError(f"Placement evidence missing: {key}")
odb = source / "placement_only.odb"
expected = "7b2811c291443d4208bcb1154fbe37ab6eeb7be6702c52060f135d0318509adf"
if hashlib.sha256(odb.read_bytes()).hexdigest() != expected:
    raise RuntimeError("Driver placement source identity mismatch")
image = "ghcr.io/librelane/librelane@sha256:d109140b8f17fc54f4fca998beb8124f4949404ec52e339eebd2250854a18b5a"
command = ["docker", "run", "--rm", "-v", f"{root}:{root}", "-w", str(root)]
for key, value in {"SOURCE": odb, "OUT": out, "EXPECTED_MARKERS": "measure"}.items():
    command += ["-e", f"WARP_REPAIR_{key}={value}"]
command += [image, "openroad", "-exit", "test_internal/driver_route_repair.tcl"]
with (out / "repair.log").open("w") as log:
    subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=4800)
result = json.loads((out / "result.json").read_text())
if result.get("checked_markers") != 0 or result.get("step_markers") != 0 or result.get("topology_unchanged") is not True:
    raise RuntimeError("Resized driver route is not native zero/topology-preserving")
state = json.loads((root / "build/cloud_input/route_state.json").read_text())
for kind, name in {"odb": "final.odb", "def": "repair.def", "nl": "repair.nl.v", "pnl": "repair.pnl.v"}.items():
    path = out / name
    if not path.is_file():
        raise RuntimeError(f"Missing actual final view: {name}")
    state[kind] = str(path)
for key in list(state["metrics"]):
    if key.startswith("route__drc_errors"):
        del state["metrics"][key]
state["metrics"]["route__drc_errors"] = 0
initial = out / "checked_route_state.json"
initial.write_text(json.dumps(state) + "\n")
run = out / "native_checks"
run.mkdir()
command = [sys.executable, "-m", "librelane", "--docker-no-tty", "--dockerized",
    "--pdk", "ihp-sg13cmos5l", "--pdk-root", os.environ["PDK_ROOT"], "--manual-pdk",
    "--hide-progress-bar", "--force-run-dir", str(run), "--run-tag", "driver_native",
    "--from", "Odb.RemoveRoutingObstructions", "--to", "Checker.DisconnectedPins",
    "--with-initial-state", str(initial), str(root / "build/cloud_input/route_config.json")]
with (out / "native_checks.log").open("w") as log:
    subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=900)
states = list(run.glob("*-checker-disconnectedpins/state_out.json"))
if len(states) != 1:
    raise RuntimeError("Missing unique stock checked state")
checked = json.loads(states[0].read_text())
for key in ("route__drc_errors", "antenna__violating__nets", "antenna__violating__pins",
            "design__critical_disconnected_pin__count"):
    if checked["metrics"].get(key) != 0:
        raise RuntimeError(f"Missing/nonzero native gate: {key}")
native_hash = hashlib.sha256(Path(checked["odb"]).read_bytes()).hexdigest()
(out / "native_acceptance.json").write_text(json.dumps({
    "source_run": 37689324316, "source_sha256": expected,
    "checked_odb_sha256": native_hash, "metrics": checked["metrics"],
    "scope": "one_driver_ECO_native_route_only_not_geometry_or_configured_timing"}, indent=2) + "\n")
env = dict(os.environ, WARP_CLEAN_NATIVE_SOURCE=str(out),
    WARP_CLEAN_NATIVE_SHA256=native_hash,
    WARP_CLEAN_NATIVE_RUN=os.environ["GITHUB_RUN_ID"], WARP_CLEAN_ECO="one_driver")
subprocess.run([sys.executable, "test_internal/cloud_clean_layout.py"], env=env, check=True)
