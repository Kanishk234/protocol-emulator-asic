"""One physical feature trial: eight generic user-D delay cells in copied C2.

Reuse the authenticated original macro flow, pre-buffer mapped input and pin
policy. No synthesis, frozen views or architecture edits. Diagnostic physical
checks remain distinct from the original virtual-clock flow's timing rejection.
"""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile

import cloud_c2_delay_screen as delay
import cloud_tile_harden as harden
import cloud_tile_preflight as preflight

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/c2_delay_harden"
INPUT = ROOT / "build/c2_delay_harden_input"
ARCHIVE_SHA = "356c909c1415d2d56f7925e304b3d862055ed471af585cc206af92257c2bb2d8"
SCREEN_SHA = "c2955785c0c3e1820a1500f4a1b50830e5da2751d974666a75c048df91639ef5"
ORIGINAL_INPUT_SHA = preflight.PASSING_SHA


def validate_screen(path):
    if harden.sha(path) != SCREEN_SHA:
        raise ValueError("Wrong actual intrinsic delay result")
    result = json.loads(path.read_text())
    if not result.get("diagnostic_completed") or len(result["cases"]) != 12:
        raise ValueError("Incomplete intrinsic screen")
    if result["physical_acceptance"] or result["configured_timing_acceptance"]:
        raise ValueError("Intrinsic screen incorrectly claims qualification")
    for name, case in result["cases"].items():
        if not case["completed"] or len(case["actual_clock_arrivals"]) != 8:
            raise ValueError("Intrinsic screen lacks actual clock coverage")
        if name.startswith("delay/"):
            for mode in ("min", "max"):
                if case["internal_paths"][mode]["violated_paths"] or case["internal_paths"][mode]["worst_slack_ns"] <= 0:
                    raise ValueError("Intrinsic candidate did not clear examined timing")
    return result


def derive_input(source):
    if harden.sha(source) != ORIGINAL_INPUT_SHA:
        raise ValueError("Wrong original pre-buffer mapped netlist")
    candidate, inventory = delay.delay_copy(source.read_text(), {f"_{i}_" for i in range(1821, 1829)})
    return candidate, inventory


def inner():
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise ValueError("Native physical execution is GitHub-only")
    candidate, inventory = derive_input(INPUT / "passing.nl.v")
    original_file = INPUT / "original_passing.nl.v"
    original_file.write_bytes((INPUT / "passing.nl.v").read_bytes())
    (INPUT / "passing.nl.v").write_text(candidate)
    (OUT / "candidate_prebuffer.nl.v").write_text(candidate)
    candidate_sha = harden.sha(INPUT / "passing.nl.v")
    record = {"scope": "eight generic user-D delay cells only; copied mapped source",
              "original_prebuffer_nl_sha256": ORIGINAL_INPUT_SHA,
              "candidate_prebuffer_nl_sha256": candidate_sha,
              "identity_contraction_exact": True, "added_cells": inventory,
              "original_output_buffer_flow_unchanged": True,
              "physical_acceptance": False, "configured_timing_acceptance": False}
    (OUT / "input_change.json").write_text(json.dumps(record, indent=2) + "\n")
    # This process-local source identity is deliberately the new copied input.
    # The original archive/manifest and original mapped source remain retained.
    preflight.PASSING_SHA = candidate_sha
    harden.OUT, harden.INPUT = OUT, INPUT
    flow_error = None
    try:
        harden.inner()
    except Exception as exc:
        flow_error = str(exc)
    path = OUT / "result.json"
    if not path.is_file():
        raise RuntimeError("Native hardening failed without retained result: " + str(flow_error))
    result = json.loads(path.read_text())
    result["original_prebuffer_nl_sha256"] = ORIGINAL_INPUT_SHA
    result["candidate_prebuffer_nl_sha256"] = candidate_sha
    result["intrinsic_source_run"] = 38113263802
    result["intrinsic_result_sha256"] = SCREEN_SHA
    result["underlying_flow_passed"] = flow_error is None
    result["underlying_flow_error"] = flow_error
    result["physical_acceptance"] = False
    result["configured_timing_acceptance"] = False
    summary_path = OUT / "physical_summary.json"
    summary = json.loads(summary_path.read_text()) if summary_path.is_file() else {}
    checkpoints = [OUT / "final", OUT / "last_completed"]
    netlists = [p / "nl/LUT4x8_ha_C2.nl.v" for p in checkpoints if (p / "nl/LUT4x8_ha_C2.nl.v").is_file()]
    delays = []
    if netlists:
        delays = re.findall(r"\b" + delay.MASTER + r"\s+(\w+)\s*\(", netlists[0].read_text())
        result["retained_final_nl_sha256"] = harden.sha(netlists[0])
    result["retained_delay_instances"] = sorted(delays)
    result["physical_diagnostic_completed"] = (summary.get("physical_gate_metrics_zero") is True
        and summary.get("original_signal_power_interfaces_match") is True
        and set(delays) == {delay.PREFIX + str(i) for i in range(8)})
    path.write_text(json.dumps(result, indent=2) + "\n")
    if not result["physical_diagnostic_completed"]:
        raise RuntimeError("Required native geometry/route/interfaces/live delay cells did not pass: " + str(flow_error))
    # Any virtual-clock timing failure remains recorded. This return value
    # qualifies physical diagnostic collection only, never full chip or timing.


def run():
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise ValueError("Physical hardening is GitHub-only")
    validate_screen(ROOT / "build/c2_delay_physical_reference/result.json")
    archive = ROOT / "build/tile-harden-c2.tar.gz"
    if harden.sha(archive) != ARCHIVE_SHA:
        raise ValueError("Original physical source archive differs")
    OUT.mkdir(exist_ok=False)
    with tarfile.open(archive) as tf:
        tf.extractall(OUT, filter="data")
    source = OUT / "source"
    manifest = json.loads((source / "manifest.json").read_text())
    for name, digest in manifest["files"].items():
        path = (source / name).resolve()
        if not path.is_relative_to(source.resolve()) or harden.sha(path) != digest:
            raise ValueError("Original authenticated flow source changed")
    preflight.INPUT = INPUT
    preflight.unpack(source / "tile-preflight-c2.tar.gz")
    derive_input(INPUT / "passing.nl.v")
    with (OUT / "harden.log").open("w") as log:
        subprocess.run(["docker", "run", "--rm", "-v", f"{ROOT}:{ROOT}", "-w", str(ROOT),
            "-e", "PDK_ROOT=" + os.environ["PDK_ROOT"], "-e", "GITHUB_ACTIONS=true", "--entrypoint", "python3", preflight.IMAGE,
            str(Path(__file__).resolve()), "--inside"], stdout=log, stderr=subprocess.STDOUT,
            timeout=3000, check=True)


if __name__ == "__main__":
    if sys.argv[1:] == ["--inside"]:
        inner()
    elif not sys.argv[1:]:
        run()
    else:
        raise SystemExit("Unsupported invocation")
