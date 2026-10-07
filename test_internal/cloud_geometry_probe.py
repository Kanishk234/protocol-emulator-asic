"""Replay geometry only from saved iteration52; never certify routing/timing."""
import hashlib
import json
import os
import re
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
config_path = ROOT / "build/cloud_input/route_config.json"
filler_only = os.environ.get("WARP_GEOMETRY_FILLER_ONLY") == "1"
if filler_only:
    config = json.loads(config_path.read_text())
    config["DECAP_CELLS"] = []
    config_path = out / "plain_fill_config.json"
    config_path.write_text(json.dumps(config, indent=2) + "\n")
common = [sys.executable, "-m", "librelane", "--docker-no-tty", "--dockerized",
           "--pdk", "ihp-sg13cmos5l", "--pdk-root", os.environ["PDK_ROOT"], "--manual-pdk",
           "--hide-progress-bar", "--run-tag", "geometry_probe"]
if filler_only:
    fill_run = out / "fill_audit"
    fill_run.mkdir()
    fill_command = common + ["--force-run-dir", str(fill_run),
        "--from", "Odb.ReportWireLength", "--to", "OpenROAD.FillInsertion",
        "--with-initial-state", str(initial), str(config_path)]
    with (out / "fill.log").open("w") as log:
        subprocess.run(fill_command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
    fill_states = list(fill_run.glob("*-openroad-fillinsertion/state_out.json"))
    if len(fill_states) != 1:
        raise RuntimeError("Missing unique completed filler state")
    filled = json.loads(fill_states[0].read_text())
    components = Path(filled["def"]).read_text().split("COMPONENTS", 1)[1].split("END COMPONENTS", 1)[0]
    decaps = re.findall(r"(?m)^\s*-\s+\S+\s+(sg13cmos5l_decap_\w+)", components)
    plain = re.findall(r"(?m)^\s*-\s+\S+\s+(sg13cmos5l_fill_\w+)", components)
    (out / "filler_audit.json").write_text(json.dumps({
        "decap_instances": len(decaps), "plain_fill_instances": len(plain),
        "state": str(fill_states[0]), "passed": not decaps and bool(plain),
    }, indent=2) + "\n")
    if decaps or not plain:
        raise RuntimeError("Actual filler inventory does not implement the experiment")
    initial = fill_states[0]
command = common + ["--force-run-dir", str(run),
           "--from", "Odb.CellFrequencyTables" if filler_only else "Odb.ReportWireLength",
           "--to", "Checker.LVS" if filler_only else "KLayout.DRC",
           "--with-initial-state", str(initial), str(config_path)]
with (out / "flow.log").open("w") as log:
    result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
def step_metric(pattern, key):
    states = list(run.glob(pattern + "/state_out.json"))
    return json.loads(states[0].read_text())["metrics"].get(key) if len(states) == 1 else None
errors = step_metric("*-klayout-drc", "klayout__drc_error__count")
lvs_errors = step_metric("*-netgen-lvs", "design__lvs_error__count")
(out / "result.json").write_text(json.dumps({
    "source_run": 37516794406, "source_sha256": EXPECTED, "source_routing_markers": 3,
    "scope": "geometry_replay_only_not_final_route_or_timing_acceptance",
    "flow_returncode": result.returncode, "klayout_errors": errors, "lvs_errors": lvs_errors,
    "plain_filler_only": filler_only,
    "physical_change": "DECAP_CELLS empty; actual inserted inventory audited" if filler_only else "none",
}, indent=2) + "\n")
raise SystemExit(result.returncode or (0 if errors == 0 and (not filler_only or lvs_errors == 0) else 1))
