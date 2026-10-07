"""Check the verified filler GDS; source routing remains unqualified."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
out = root / "build/filler_checks"
out.mkdir(parents=True, exist_ok=False)
trial = root / "build/filler_trial_source/chip_trial.gds"
expected = "3ee36af59b8b5964f1796b7b2756e7dad859572d3e23266c848b05fc58ae9f9b"
if hashlib.sha256(trial.read_bytes()).hexdigest() != expected:
    raise RuntimeError("Not the verified full-Magic-zero filler trial GDS")
manifest = json.loads((trial.parent / "chip_trial_manifest.json").read_text())
if manifest["replaced_instances"] != 20714 or manifest["other_layers_xor_empty"] is not True:
    raise RuntimeError("Overlay identity checks missing")
if (trial.parent / "chip_trial.rpt").read_text().strip() != "count 0":
    raise RuntimeError("Missing zero full Magic report")
state = json.loads((root / "build/cloud_input/route_state.json").read_text())
source = root / "build/filler_original_source/run/final"
for kind, directory, suffix in (("odb", "odb", "odb"), ("def", "def", "def"),
                                ("nl", "nl", "nl.v"), ("pnl", "pnl", "pnl.v"),
                                ("sdc", "sdc", "sdc")):
    path = source / directory / ("tt_um_warp." + suffix)
    if not path.is_file():
        raise RuntimeError(f"Missing original final {kind}")
    state[kind] = str(path)
state["gds"] = state["klayout_gds"] = str(trial)
state["metrics"]["magic__drc_error__count"] = 0
state["metrics"]["route__drc_errors"] = 3
initial = out / "initial.json"
initial.write_text(json.dumps(state) + "\n")
config = json.loads((root / "build/cloud_input/route_config.json").read_text())
config["DECAP_CELLS"] = []
# DEF/LEF extraction would silently use old, unpatched filler geometry.
# Preserve the stock macro abstraction list; electrical scope stays explicit.
config["MAGIC_EXT_USE_GDS"] = True
cfg = out / "config.json"
cfg.write_text(json.dumps(config, indent=2) + "\n")
run = out / "run"
run.mkdir()
command = [sys.executable, "-m", "librelane", "--docker-no-tty", "--dockerized",
    "--pdk", "ihp-sg13cmos5l", "--pdk-root", os.environ["PDK_ROOT"], "--manual-pdk",
    "--hide-progress-bar", "--force-run-dir", str(run), "--run-tag", "filler_gds",
    "--from", "KLayout.DRC", "--to", "Checker.LVS",
    "--with-initial-state", str(initial), str(cfg)]
with (out / "flow.log").open("w") as log:
    completed = subprocess.run(command, cwd=root, stdout=log, stderr=subprocess.STDOUT)
metrics = {}
for pattern, key in (("*-klayout-drc", "klayout__drc_error__count"),
                     ("*-netgen-lvs", "design__lvs_error__count")):
    states = list(run.glob(pattern + "/state_out.json"))
    metrics[key] = json.loads(states[0].read_text())["metrics"].get(key) if len(states) == 1 else None
summary = {"source_magic_run": 37669173193, "source_gds_sha256": expected,
    "source_native_markers": 3, "verified_magic_errors": 0,
    "GDS_based_extraction": True, "macro_abstraction": "stock configuration preserved",
    "scope": "scratch_filler_GDS_geometry_and_shell_LVS_not_native_or_configured_timing",
    "flow_returncode": completed.returncode, **metrics}
(out / "result.json").write_text(json.dumps(summary, indent=2) + "\n")
raise SystemExit(completed.returncode or (0 if all(value == 0 for value in metrics.values()) else 1))
