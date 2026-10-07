"""Validate late-cost native route before stock antenna/connectivity checks."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
out = root / "build/late_route"
source = root / "build/physical_source/last_complete_drt.odb"
expected = "33dceb8d52df9d5ea8cc3741b71b9b3e1e79ae4fb95b1eb559b3ca3eb40390bc"
if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
    raise RuntimeError("Not authenticated original iteration52")
result = json.loads((out / "result.json").read_text())
if result.get("checked_markers") != 0 or result.get("step_markers") != 0 or result.get("topology_unchanged") is not True:
    raise RuntimeError("Late repair native full check/topology did not pass")
state = json.loads((root / "build/cloud_input/route_state.json").read_text())
for kind, name in {"odb": "final.odb", "def": "repair.def", "nl": "repair.nl.v", "pnl": "repair.pnl.v"}.items():
    path = out / name
    if not path.is_file():
        raise RuntimeError(f"Missing committed final view {name}")
    state[kind] = str(path)
for key in list(state["metrics"]):
    if key.startswith("route__drc_errors"):
        del state["metrics"][key]
state["metrics"]["route__drc_errors"] = result["checked_markers"]
initial = out / "checked_route_state.json"
initial.write_text(json.dumps(state) + "\n")
run = out / "native_checks"
run.mkdir()
command = [sys.executable, "-m", "librelane", "--docker-no-tty", "--dockerized",
    "--pdk", "ihp-sg13cmos5l", "--pdk-root", os.environ["PDK_ROOT"], "--manual-pdk",
    "--hide-progress-bar", "--force-run-dir", str(run), "--run-tag", "late_native",
    "--from", "Odb.RemoveRoutingObstructions", "--to", "Checker.DisconnectedPins",
    "--with-initial-state", str(initial), str(root / "build/cloud_input/route_config.json")]
with (out / "native_checks.log").open("w") as log:
    completed = subprocess.run(command, cwd=root, stdout=log, stderr=subprocess.STDOUT)
if completed.returncode:
    raise SystemExit(completed.returncode)
states = list(run.glob("*-checker-disconnectedpins/state_out.json"))
if len(states) != 1:
    raise RuntimeError("Missing unique stock checked native state")
checked = json.loads(states[0].read_text())
for key in ("route__drc_errors", "antenna__violating__nets", "antenna__violating__pins",
            "design__critical_disconnected_pin__count"):
    if checked["metrics"].get(key) != 0:
        raise RuntimeError(f"Missing/nonzero acceptance metric {key}")
(out / "native_acceptance.json").write_text(json.dumps({"source_run": 37516794406,
    "source_sha256": expected, "checked_state": str(states[0]), "metrics": checked["metrics"],
    "scope": "native_route_only_not_full_geometry_function_or_configured_timing"}, indent=2) + "\n")
