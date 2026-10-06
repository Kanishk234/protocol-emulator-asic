"""Replay geometry only from saved iteration52; never certify routing/timing."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "build/physical_source/last_complete_drt.odb"
EXPECTED = "33dceb8d52df9d5ea8cc3741b71b9b3e1e79ae4fb95b1eb559b3ca3eb40390bc"
if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != EXPECTED:
    raise ValueError("Physical source ODB does not match authenticated iteration52")
out = ROOT / "build/geometry_probe"
run = out / "run"
run.mkdir(parents=True, exist_ok=False)
state = json.loads((ROOT / "build/cloud_input/route_state.json").read_text())
state["odb"] = str(SOURCE)
# The saved database is the completed3-marker iteration52, not the final0 ODB.
for key in list(state["metrics"]):
    if key.startswith("route__drc_errors"):
        del state["metrics"][key]
state["metrics"]["route__drc_errors"] = 3
initial = out / "initial_state.json"
initial.write_text(json.dumps(state) + "\n")
command = [sys.executable, "-m", "librelane", "--docker-no-tty", "--dockerized",
           "--pdk", "ihp-sg13cmos5l", "--pdk-root", os.environ["PDK_ROOT"], "--manual-pdk",
           "--hide-progress-bar", "--run-tag", "geometry_probe", "--force-run-dir", str(run),
           "--from", "Odb.ReportWireLength", "--to", "KLayout.DRC",
           "--with-initial-state", str(initial), str(ROOT / "build/cloud_input/route_config.json")]
with (out / "flow.log").open("w") as log:
    result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
final = list(run.glob("*-klayout-drc/state_out.json"))
metrics = json.loads(final[0].read_text())["metrics"] if len(final) == 1 else {}
errors = metrics.get("klayout__drc_error__count")
(out / "result.json").write_text(json.dumps({
    "source_run": 37516794406, "source_sha256": EXPECTED, "source_routing_markers": 3,
    "scope": "geometry_replay_only_not_final_route_or_timing_acceptance",
    "flow_returncode": result.returncode, "klayout_errors": errors,
}, indent=2) + "\n")
raise SystemExit(result.returncode or (0 if errors == 0 else 1))
