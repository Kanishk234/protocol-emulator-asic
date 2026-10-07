"""Combine measured filler policy with the authenticated zero native route."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
source = root / "build/native_zero_source"
out = root / "build/clean_layout"
out.mkdir(parents=True, exist_ok=False)
acceptance = json.loads((source / "native_acceptance.json").read_text())
states = list((source / "native_checks").glob("*-checker-disconnectedpins/state_out.json"))
if len(states) != 1:
    raise RuntimeError("Missing unique checked zero-native state")
state = json.loads(states[0].read_text())
def rebase(value):
    if isinstance(value, dict):
        return {key: rebase(item) for key, item in value.items()}
    if isinstance(value, str) and "/build/late_route/" in value:
        return str(source / value.split("/build/late_route/", 1)[1])
    return value
state = rebase(state)
expected = "9cac79d86dd15707efdd385c32d3990347cb4695874bc802d0bfe20a5e90e9ba"
if hashlib.sha256(Path(state["odb"]).read_bytes()).hexdigest() != expected:
    raise RuntimeError("Native final checked ODB identity mismatch")
for key in ("route__drc_errors", "antenna__violating__nets", "antenna__violating__pins",
            "design__critical_disconnected_pin__count"):
    if state["metrics"].get(key) != 0 or acceptance["metrics"].get(key) != 0:
        raise RuntimeError(f"Native acceptance missing/nonzero: {key}")
cfg = json.loads((root / "build/cloud_input/route_config.json").read_text())
cfg["DECAP_CELLS"] = []
config = out / "config.json"
config.write_text(json.dumps(cfg, indent=2) + "\n")
initial = out / "native_zero.json"
initial.write_text(json.dumps(state) + "\n")
common = [sys.executable, "-m", "librelane", "--docker-no-tty", "--dockerized",
    "--pdk", "ihp-sg13cmos5l", "--pdk-root", os.environ["PDK_ROOT"], "--manual-pdk", "--hide-progress-bar"]
def run_flow(name, first, last, input_state):
    run = out / name
    run.mkdir()
    command = common + ["--force-run-dir", str(run), "--run-tag", name,
        "--from", first, "--to", last, "--with-initial-state", str(input_state), str(config)]
    with (out / (name + ".log")).open("w") as log:
        result = subprocess.run(command, cwd=root, stdout=log, stderr=subprocess.STDOUT)
    return run, result.returncode
run, code = run_flow("fresh_streamout", "Odb.ReportWireLength", "KLayout.StreamOut", initial)
if code:
    raise SystemExit(code)
states = list(run.glob("*-klayout-streamout/state_out.json"))
if len(states) != 1:
    raise RuntimeError("Missing unique fresh GDS state")
fresh = json.loads(states[0].read_text())
components = Path(fresh["def"]).read_text().split("COMPONENTS", 1)[1].split("END COMPONENTS", 1)[0]
if "sg13cmos5l_decap_" in components:
    raise RuntimeError("Decap policy not applied")
gds = Path(fresh["gds"])
overlay = out / "overlay"
overlay.mkdir()
env = {"WARP_CHIP_GDS": str(gds), "WARP_FILLER_OUT": str(overlay),
    "WARP_CHIP_EXPECTED_SHA256": hashlib.sha256(gds.read_bytes()).hexdigest(),
    "WARP_CHIP_SOURCE_RUN": "37669731197", "WARP_CHIP_NATIVE_MARKERS": "0"}
image = "ghcr.io/librelane/librelane@sha256:d109140b8f17fc54f4fca998beb8124f4949404ec52e339eebd2250854a18b5a"
docker = ["docker", "run", "--rm", "-v", f"{root}:{root}", "-w", str(root)]
def run_tool(name, command):
    with (out / (name + ".log")).open("w") as log:
        subprocess.run(docker + [item for pair in env.items() for item in ("-e", "=".join(pair))]
            + [image] + command, cwd=root, stdout=log, stderr=subprocess.STDOUT, check=True)
run_tool("overlay", ["klayout", "-b", "-r", "test_internal/filler_chip_trial.py"])
run_tool("magic", ["magic", "-dnull", "-noconsole", "-rcfile",
    str(Path(os.environ["PDK_ROOT"]) / "ihp-sg13cmos5l/libs.tech/magic/ihp-sg13cmos5l.magicrc"),
    "test_internal/filler_chip_drc.tcl"])
if (overlay / "chip_trial.rpt").read_text().strip() != "count 0":
    raise RuntimeError("Fresh combined layout fails full Magic; inspect report")
fresh["gds"] = fresh["klayout_gds"] = str(overlay / "chip_trial.gds")
fresh["metrics"]["magic__drc_error__count"] = 0
checked = out / "overlay_state.json"
checked.write_text(json.dumps(fresh) + "\n")
cfg["MAGIC_EXT_USE_GDS"] = True
config.write_text(json.dumps(cfg, indent=2) + "\n")
run, code = run_flow("gds_lvs", "KLayout.DRC", "Checker.LVS", checked)
metrics = {}
for pattern, key in (("*-klayout-drc", "klayout__drc_error__count"),
                     ("*-netgen-lvs", "design__lvs_error__count")):
    states = list(run.glob(pattern + "/state_out.json"))
    metrics[key] = json.loads(states[0].read_text())["metrics"].get(key) if len(states) == 1 else None
(out / "result.json").write_text(json.dumps({"native_source_run": 37669731197,
    "native_checked_odb_sha256": expected, "verified_native_markers": 0,
    "fresh_magic_errors": 0, **metrics, "flow_returncode": code,
    "scope": "scratch_combined_physical_checks_shell_STA_macro_abstract_not_configured_timing"}, indent=2) + "\n")
raise SystemExit(code or (0 if all(value == 0 for value in metrics.values()) else 1))
