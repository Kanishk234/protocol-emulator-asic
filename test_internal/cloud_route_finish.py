"""Bounded repair of saved iteration52, then no-decap physical checks.

Independent from frozen G1; native acceptance gates downstream geometry.
The macro stays black-boxed in STA and original native function is unqualified.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
out = ROOT / "build/cloud_run"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("stage", choices=["native", "geometry"])
args = parser.parse_args()
common = [sys.executable, "-m", "librelane", "--docker-no-tty", "--dockerized",
    "--pdk", "ihp-sg13cmos5l", "--pdk-root", os.environ["PDK_ROOT"], "--manual-pdk",
    "--hide-progress-bar"]
if args.stage == "native":
    out.mkdir(parents=True, exist_ok=False)
    source = ROOT / "build/physical_source/last_complete_drt.odb"
    expected = "33dceb8d52df9d5ea8cc3741b71b9b3e1e79ae4fb95b1eb559b3ca3eb40390bc"
    if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
        raise ValueError("Source is not authenticated completed iteration52")
    state = json.loads((ROOT / "build/cloud_input/route_state.json").read_text())
    state["odb"] = str(source)
    for key in list(state["metrics"]):
        if key.startswith("route__drc_errors"):
            del state["metrics"][key]
    state["metrics"]["route__drc_errors"] = 3
    initial = out / "initial_state.json"
    initial.write_text(json.dumps(state) + "\n")
    config = json.loads((ROOT / "build/cloud_input/route_config.json").read_text())
    config["DRT_OPT_ITERS"] = 16
    config["DECAP_CELLS"] = []
    (out / "config.json").write_text(json.dumps(config, indent=2) + "\n")
    (out / "scope.json").write_text(json.dumps({"source_run": 37516794406,
        "source_sha256": expected, "source_markers": 3, "iteration_budget": 16,
        "physical_change": "DECAP_CELLS empty", "driver_resize": False,
        "native_function_or_configured_timing_acceptance": False}) + "\n")
    run = out / "runs/native_route"
    run.mkdir(parents=True)
    command = common + ["--force-run-dir", str(run), "--run-tag", "native_route",
        "--from", "OpenROAD.DetailedRouting", "--to", "Checker.DisconnectedPins",
        "--with-initial-state", str(initial), str(out / "config.json")]
else:
    states = list((out / "runs/native_route").glob("*-checker-disconnectedpins/state_out.json"))
    if len(states) != 1:
        raise RuntimeError("Missing unique completed native checked state")
    state = json.loads(states[0].read_text())
    for key in ("route__drc_errors", "antenna__violating__nets", "antenna__violating__pins",
                "design__critical_disconnected_pin__count"):
        if state["metrics"].get(key) != 0:
            raise RuntimeError(f"Native acceptance missing/nonzero: {key}")
    run = out / "runs/geometry_and_timing"
    run.mkdir()
    command = common + ["--force-run-dir", str(run), "--run-tag", "geometry_and_timing",
        "--from", "Odb.ReportWireLength", "--to", "Checker.LVS",
        "--with-initial-state", str(states[0]), str(out / "config.json")]
with (out / f"{args.stage}.log").open("w") as log:
    result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
summary = {"returncode": result.returncode,
    "scope": "compact_physical_experiment_no_native_function_or_configured_timing_acceptance"}
if args.stage == "geometry":
    for pattern, key in (("*-klayout-drc", "klayout__drc_error__count"),
                         ("*-magic-drc", "magic__drc_error__count"),
                         ("*-netgen-lvs", "design__lvs_error__count")):
        states = list(run.glob(pattern + "/state_out.json"))
        summary[key] = json.loads(states[0].read_text())["metrics"].get(key) if len(states) == 1 else None
    summary["all_three_geometry_checks_zero"] = all(summary.get(key) == 0 for key in (
        "klayout__drc_error__count", "magic__drc_error__count", "design__lvs_error__count"))
    if result.returncode == 0 and any(summary.get(key) != 0 for key in (
            "klayout__drc_error__count", "design__lvs_error__count")):
        summary["returncode"] = 1
(out / f"{args.stage}_exit.json").write_text(json.dumps(summary, indent=2) + "\n")
raise SystemExit(summary["returncode"])
